"""
InsureTrust AI — Claims Router
================================
POST /claims/submit — Full pipeline with SSE streaming
GET /claims/{claim_id} — Get claim details
GET /claims/{claim_id}/summary — Get LLM summary
PATCH /claims/{claim_id}/decision — Adjuster decision
GET /claims/ — List all claims
"""

import uuid
import time
import json
import asyncio
import os
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from models.database import get_db, Claim
from models.schemas import ClaimForm, AdjusterDecision, ClaimResponse
from services.ingestion import validate_claim, normalize_claim, mask_name, build_features, ValidationError
from services.model_stubs import get_image_score, get_nlp_score, get_tabular_score, get_gnn_score
from services.graph_engine import analyze_claim_in_graph
from services.rfi_engine import run_all_rfis
from services.ensemble import compute_ensemble
from services.audit_logger import (
    log_claim_received, log_validation_passed, log_validation_failed,
    log_image_scored, log_nlp_scored, log_tabular_scored,
    log_graph_scored, log_rfi_checked, log_final_decision, log_adjuster_action
)
from services.llm_summary import generate_claim_summary

router = APIRouter(prefix="/claims", tags=["claims"])


@router.post("/submit")
async def submit_claim(
    background_tasks: BackgroundTasks,
    claim_form: str = Form(...),
    damage_photo: Optional[UploadFile] = File(None),
    supporting_doc: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
):
    """
    Submit a new insurance claim for fraud analysis.
    Returns SSE stream with real-time processing updates.
    """
    async def event_stream():
        start_time = time.time()
        claim_id = f"CLM_{uuid.uuid4().hex[:8].upper()}"

        try:
            # Parse claim form JSON
            try:
                claim_data = json.loads(claim_form)
            except json.JSONDecodeError:
                yield f"data: {json.dumps({'step': 'error', 'status': 'failed', 'message': 'Invalid JSON in claim_form'})}\n\n"
                return

            # Step 1: Validate inputs
            step_start = time.time()
            yield f"data: {json.dumps({'step': 'validating_inputs', 'status': 'running', 'ms': 0})}\n\n"
            await asyncio.sleep(0.05)  # Small delay for visual effect

            try:
                claim_data = validate_claim(claim_data, db)
                claim_data = normalize_claim(claim_data)
                log_claim_received(db, claim_id, {
                    "policy_id": claim_data.get("policy_id"),
                    "claim_amount": claim_data.get("claim_amount"),
                    "hospital_code": claim_data.get("hospital_code"),
                    "has_photo": damage_photo is not None,
                    "has_doc": supporting_doc is not None,
                })
                log_validation_passed(db, claim_id)
            except ValidationError as e:
                log_validation_failed(db, claim_id, str(e.message))
                yield f"data: {json.dumps({'step': 'validating_inputs', 'status': 'failed', 'message': e.message, 'ms': round((time.time() - step_start) * 1000)})}\n\n"
                return

            ms_validation = round((time.time() - step_start) * 1000)
            yield f"data: {json.dumps({'step': 'validating_inputs', 'status': 'done', 'ms': ms_validation})}\n\n"

            # Save uploaded files
            photo_path = None
            if damage_photo:
                upload_dir = os.path.join("uploads", claim_id)
                os.makedirs(upload_dir, exist_ok=True)
                photo_path = os.path.join(upload_dir, damage_photo.filename or "photo.jpg")
                with open(photo_path, "wb") as f:
                    content = await damage_photo.read()
                    f.write(content)

            doc_path = None
            if supporting_doc:
                upload_dir = os.path.join("uploads", claim_id)
                os.makedirs(upload_dir, exist_ok=True)
                doc_path = os.path.join(upload_dir, supporting_doc.filename or "doc.pdf")
                with open(doc_path, "wb") as f:
                    content = await supporting_doc.read()
                    f.write(content)

            # Step 2: Image Forensics
            step_start = time.time()
            elapsed = round((time.time() - start_time) * 1000)
            yield f"data: {json.dumps({'step': 'image_forensics', 'status': 'running', 'ms': elapsed})}\n\n"
            await asyncio.sleep(0.08)

            image_result = get_image_score(photo_path or "no_image.jpg")
            ms_image = round((time.time() - step_start) * 1000)
            log_image_scored(db, claim_id, image_result["image_score"], ms_image)
            yield f"data: {json.dumps({'step': 'image_forensics', 'status': 'done', 'ms': ms_image})}\n\n"

            # Step 3: NLP Analysis
            step_start = time.time()
            elapsed = round((time.time() - start_time) * 1000)
            yield f"data: {json.dumps({'step': 'nlp_analysis', 'status': 'running', 'ms': elapsed})}\n\n"
            await asyncio.sleep(0.08)

            statement = claim_data.get("incident_description", "")
            doc_text = ""  # Would be extracted from supporting_doc
            nlp_result = get_nlp_score(statement, doc_text)
            ms_nlp = round((time.time() - step_start) * 1000)
            log_nlp_scored(db, claim_id, nlp_result["nlp_score"], ms_nlp)
            yield f"data: {json.dumps({'step': 'nlp_analysis', 'status': 'done', 'ms': ms_nlp})}\n\n"

            # Step 4: Tabular Scoring
            step_start = time.time()
            elapsed = round((time.time() - start_time) * 1000)
            yield f"data: {json.dumps({'step': 'tabular_scoring', 'status': 'running', 'ms': elapsed})}\n\n"
            await asyncio.sleep(0.06)

            features = build_features(claim_data)
            tabular_result = get_tabular_score(features)
            ms_tabular = round((time.time() - step_start) * 1000)
            log_tabular_scored(db, claim_id, tabular_result["tabular_score"], ms_tabular)
            yield f"data: {json.dumps({'step': 'tabular_scoring', 'status': 'done', 'ms': ms_tabular})}\n\n"

            # Step 5: Graph Analysis
            step_start = time.time()
            elapsed = round((time.time() - start_time) * 1000)
            yield f"data: {json.dumps({'step': 'graph_analysis', 'status': 'running', 'ms': elapsed})}\n\n"
            await asyncio.sleep(0.08)

            graph_claim_data = {
                **claim_data,
                "id": claim_id,
                "claimant_name_masked": mask_name(claim_data.get("claimant_name", "")),
            }
            graph_result = analyze_claim_in_graph(graph_claim_data)
            ms_graph = round((time.time() - step_start) * 1000)
            log_graph_scored(db, claim_id, graph_result["graph_score"],
                           graph_result["ring_detected"], ms_graph)
            yield f"data: {json.dumps({'step': 'graph_analysis', 'status': 'done', 'ms': ms_graph})}\n\n"

            # Step 6: RFI Check
            step_start = time.time()
            elapsed = round((time.time() - start_time) * 1000)
            yield f"data: {json.dumps({'step': 'rfi_check', 'status': 'running', 'ms': elapsed})}\n\n"
            await asyncio.sleep(0.05)

            rfi_result = run_all_rfis(claim_data, image_result, graph_result)
            ms_rfi = round((time.time() - step_start) * 1000)
            log_rfi_checked(db, claim_id, rfi_result["triggered_rfis"], ms_rfi)
            yield f"data: {json.dumps({'step': 'rfi_check', 'status': 'done', 'ms': ms_rfi})}\n\n"

            # Step 7: Ensemble Fusion
            step_start = time.time()
            elapsed = round((time.time() - start_time) * 1000)
            yield f"data: {json.dumps({'step': 'ensemble_fusion', 'status': 'running', 'ms': elapsed})}\n\n"
            await asyncio.sleep(0.04)

            # Pass graph analysis results to GNN stub
            gnn_result = get_gnn_score(claim_data.get("claimant_id", ""), graph_result)
            # Merge GNN score into graph result
            graph_result["graph_score"] = max(graph_result["graph_score"], gnn_result["gnn_score"])

            ensemble_result = compute_ensemble(
                image_result, nlp_result, tabular_result, graph_result, rfi_result
            )

            total_ms = round((time.time() - start_time) * 1000)
            log_final_decision(db, claim_id, ensemble_result["final_score"],
                             ensemble_result["routing"], total_ms)

            # Store claim in DB
            claim_record = Claim(
                id=claim_id,
                claimant_name_masked=mask_name(claim_data.get("claimant_name", "")),
                claimant_id=claim_data.get("claimant_id", f"C_{uuid.uuid4().hex[:6]}"),
                aadhaar_hash=claim_data.get("aadhaar_hash"),
                aadhaar_last4=claim_data.get("aadhaar_last4"),
                mobile_hash=claim_data.get("mobile_hash"),
                mobile_last4=claim_data.get("mobile_last4"),
                policy_id=claim_data.get("policy_id"),
                policy_start_date=datetime.fromisoformat(claim_data["policy_start_date"]) if claim_data.get("policy_start_date") else None,
                policy_max_coverage=claim_data.get("policy_max_coverage"),
                sum_insured=claim_data.get("sum_insured"),
                claim_amount=claim_data.get("claim_amount"),
                claim_date=datetime.fromisoformat(claim_data["claim_date"]) if claim_data.get("claim_date") else datetime.utcnow(),
                hospital_code=claim_data.get("hospital_code"),
                hospital_name=claim_data.get("hospital_name"),
                diagnosis_code=claim_data.get("diagnosis_code"),
                treatment_code=claim_data.get("treatment_code"),
                incident_description=claim_data.get("incident_description"),
                incident_lat=claim_data.get("incident_lat"),
                incident_lng=claim_data.get("incident_lng"),
                doctor_id=claim_data.get("doctor_id"),
                workshop_id=claim_data.get("workshop_id"),
                witness_id=claim_data.get("witness_id"),
                ip_address=claim_data.get("ip_address"),
                risk_score=ensemble_result["final_score"],
                routing=ensemble_result["routing"],
                image_score=image_result["image_score"],
                nlp_score=nlp_result["nlp_score"],
                tabular_score=tabular_result["tabular_score"],
                graph_score=graph_result["graph_score"],
                rfi_total_points=rfi_result["total_rfi_points"],
                ring_detected=graph_result.get("ring_detected", False),
                ring_id=graph_result.get("ring_id"),
                shap_values=tabular_result.get("shap_values"),
                triggered_rfis=rfi_result.get("triggered_rfis"),
                score_breakdown=ensemble_result["score_breakdown"],
                image_result=image_result,
                nlp_result=nlp_result,
                graph_result={
                    "connected_claims": graph_result.get("connected_claims"),
                    "shared_doctor": graph_result.get("shared_doctor"),
                    "shared_workshop": graph_result.get("shared_workshop"),
                    "ring_detected": graph_result.get("ring_detected"),
                    "ring_id": graph_result.get("ring_id"),
                    "ring_members": graph_result.get("ring_members"),
                    "graph_score": graph_result.get("graph_score"),
                },
                status="PENDING",
                damage_photo_path=photo_path,
                supporting_doc_path=doc_path,
                processing_ms=total_ms,
                created_at=datetime.utcnow(),
            )
            db.add(claim_record)
            db.commit()

            # Final SSE event with complete result
            final_event = {
                "step": "complete",
                "status": "done",
                "claim_id": claim_id,
                "risk_score": ensemble_result["final_score"],
                "routing": ensemble_result["routing"],
                "ms": total_ms,
                "result": {
                    **ensemble_result,
                    "image_result": image_result,
                    "nlp_result": nlp_result,
                    "tabular_result": tabular_result,
                }
            }
            yield f"data: {json.dumps(final_event)}\n\n"

            # Trigger async LLM summary in background
            background_tasks.add_task(
                _generate_summary_background,
                claim_data, ensemble_result["final_score"],
                rfi_result["triggered_rfis"],
                graph_result.get("ring_detected", False),
                claim_id
            )

        except Exception as e:
            yield f"data: {json.dumps({'step': 'error', 'status': 'failed', 'message': str(e)})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


async def _generate_summary_background(
    claim_data: dict,
    final_score: float,
    triggered_rfis: list,
    ring_detected: bool,
    claim_id: str
):
    """Background task to generate LLM summary."""
    from models.database import SessionLocal
    db = SessionLocal()
    try:
        await generate_claim_summary(
            claim_data, final_score, triggered_rfis,
            ring_detected, db, claim_id
        )
    finally:
        db.close()


@router.get("/{claim_id}")
async def get_claim(claim_id: str, db: Session = Depends(get_db)):
    """Get full claim details by ID."""
    claim = db.query(Claim).filter(Claim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    return {
        "id": claim.id,
        "claimant_name_masked": claim.claimant_name_masked,
        "claimant_id": claim.claimant_id,
        "aadhaar_display": f"AADHAAR: ****-****-{claim.aadhaar_last4}" if claim.aadhaar_last4 else None,
        "mobile_display": f"****{claim.mobile_last4}" if claim.mobile_last4 else None,
        "policy_id": claim.policy_id,
        "claim_amount": claim.claim_amount,
        "claim_date": claim.claim_date.isoformat() if claim.claim_date else None,
        "hospital_name": claim.hospital_name,
        "hospital_code": claim.hospital_code,
        "diagnosis_code": claim.diagnosis_code,
        "treatment_code": claim.treatment_code,
        "incident_description": claim.incident_description,
        "incident_lat": claim.incident_lat,
        "incident_lng": claim.incident_lng,
        "risk_score": claim.risk_score,
        "routing": claim.routing,
        "status": claim.status,
        "image_score": claim.image_score,
        "nlp_score": claim.nlp_score,
        "tabular_score": claim.tabular_score,
        "graph_score": claim.graph_score,
        "rfi_total_points": claim.rfi_total_points,
        "ring_detected": claim.ring_detected,
        "ring_id": claim.ring_id,
        "shap_values": claim.shap_values,
        "triggered_rfis": claim.triggered_rfis,
        "score_breakdown": claim.score_breakdown,
        "image_result": claim.image_result,
        "nlp_result": claim.nlp_result,
        "graph_result": claim.graph_result,
        "llm_summary": claim.llm_summary,
        "damage_photo_path": claim.damage_photo_path,
        "processing_ms": claim.processing_ms,
        "created_at": claim.created_at.isoformat() if claim.created_at else None,
        "adjuster_action": claim.adjuster_action,
        "adjuster_reason": claim.adjuster_reason,
        "adjuster_action_at": claim.adjuster_action_at.isoformat() if claim.adjuster_action_at else None,
    }


@router.get("/{claim_id}/summary")
async def get_summary(claim_id: str, db: Session = Depends(get_db)):
    """Get LLM-generated claim summary."""
    from services.llm_summary import get_claim_summary
    summary = get_claim_summary(db, claim_id)
    if not summary:
        return {"status": "pending", "summary": None}
    return {"status": "ready", "summary": summary}


@router.patch("/{claim_id}/decision")
async def adjuster_decision(
    claim_id: str,
    decision: AdjusterDecision,
    db: Session = Depends(get_db)
):
    """Record adjuster decision on a claim."""
    claim = db.query(Claim).filter(Claim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    # If approving a high-risk claim, require override confirmation
    if decision.action == "APPROVE" and claim.risk_score and claim.risk_score > 75:
        if not decision.override_confirmed:
            raise HTTPException(
                status_code=400,
                detail=f"This claim scores {claim.risk_score}/100. Set override_confirmed=true to confirm."
            )

    # Update claim
    claim.status = decision.action + "D" if decision.action != "APPROVE" else "APPROVED"
    if decision.action == "APPROVE":
        claim.status = "APPROVED"
    elif decision.action == "ESCALATE":
        claim.status = "ESCALATED"
    elif decision.action == "REJECT":
        claim.status = "REJECTED"

    claim.adjuster_id = decision.adjuster_id
    claim.adjuster_action = decision.action
    claim.adjuster_reason = decision.reason
    claim.adjuster_action_at = datetime.utcnow()

    # Log to audit trail
    log_adjuster_action(db, claim_id, decision.action, decision.reason, decision.adjuster_id)

    db.commit()

    return {
        "claim_id": claim_id,
        "status": claim.status,
        "action": decision.action,
        "message": f"Claim {claim_id} has been {claim.status.lower()}"
    }


@router.get("/")
async def list_claims(
    skip: int = 0,
    limit: int = 50,
    routing: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List all claims with optional filters."""
    query = db.query(Claim)

    if routing:
        query = query.filter(Claim.routing == routing)
    if status:
        query = query.filter(Claim.status == status)

    total = query.count()
    claims = query.order_by(Claim.created_at.desc()).offset(skip).limit(limit).all()

    return {
        "total": total,
        "claims": [
            {
                "id": c.id,
                "claimant_name_masked": c.claimant_name_masked,
                "policy_id": c.policy_id,
                "claim_amount": c.claim_amount,
                "risk_score": c.risk_score,
                "routing": c.routing,
                "status": c.status,
                "ring_detected": c.ring_detected,
                "processing_ms": c.processing_ms,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in claims
        ]
    }

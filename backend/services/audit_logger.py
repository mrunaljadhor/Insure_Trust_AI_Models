"""
InsureTrust AI — Audit Logger
===============================
Append-only SQLite audit log. No UPDATE or DELETE operations.
IRDAI-required tamper-proof trail.
"""

from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from models.database import AuditLog


def log_event(
    db: Session,
    claim_id: str,
    event_type: str,
    payload: Optional[Dict[str, Any]] = None,
    processing_ms: Optional[float] = None,
    model_version: str = "stub-v1.0"
):
    """
    Append an audit log entry. NEVER updates or deletes existing entries.
    """
    entry = AuditLog(
        claim_id=claim_id,
        timestamp=datetime.utcnow(),
        event_type=event_type,
        payload_json=payload or {},
        processing_ms=processing_ms,
        model_version=model_version
    )
    db.add(entry)
    db.commit()
    return entry


def get_claim_audit_trail(db: Session, claim_id: str) -> list:
    """Get full chronological audit trail for a claim."""
    entries = db.query(AuditLog).filter(
        AuditLog.claim_id == claim_id
    ).order_by(AuditLog.timestamp.asc()).all()

    return [
        {
            "id": e.id,
            "claim_id": e.claim_id,
            "timestamp": e.timestamp.isoformat() if e.timestamp else None,
            "event_type": e.event_type,
            "payload_json": e.payload_json,
            "processing_ms": e.processing_ms,
            "model_version": e.model_version,
        }
        for e in entries
    ]


# ─── Convenience functions for standard event types ──────────────────

def log_claim_received(db: Session, claim_id: str, metadata: dict):
    """Log CLAIM_RECEIVED — raw input metadata (no PII)."""
    safe_meta = {
        "policy_id": metadata.get("policy_id"),
        "claim_amount": metadata.get("claim_amount"),
        "hospital_code": metadata.get("hospital_code"),
        "has_photo": metadata.get("has_photo", False),
        "has_doc": metadata.get("has_doc", False),
    }
    return log_event(db, claim_id, "CLAIM_RECEIVED", safe_meta)


def log_validation_passed(db: Session, claim_id: str):
    return log_event(db, claim_id, "VALIDATION_PASSED")


def log_validation_failed(db: Session, claim_id: str, errors: str):
    return log_event(db, claim_id, "VALIDATION_FAILED", {"errors": errors})


def log_image_scored(db: Session, claim_id: str, score: float, ms: float):
    return log_event(db, claim_id, "IMAGE_SCORED",
                     {"image_score": score}, processing_ms=ms)


def log_nlp_scored(db: Session, claim_id: str, score: float, ms: float):
    return log_event(db, claim_id, "NLP_SCORED",
                     {"nlp_score": score}, processing_ms=ms)


def log_tabular_scored(db: Session, claim_id: str, score: float, ms: float):
    return log_event(db, claim_id, "TABULAR_SCORED",
                     {"tabular_score": score}, processing_ms=ms)


def log_graph_scored(db: Session, claim_id: str, score: float, ring_detected: bool, ms: float):
    return log_event(db, claim_id, "GRAPH_SCORED",
                     {"graph_score": score, "ring_detected": ring_detected},
                     processing_ms=ms)


def log_rfi_checked(db: Session, claim_id: str, triggered_rfis: list, ms: float):
    return log_event(db, claim_id, "RFI_CHECKED",
                     {"triggered_rfis": triggered_rfis}, processing_ms=ms)


def log_final_decision(db: Session, claim_id: str, final_score: float, routing: str, ms: float):
    return log_event(db, claim_id, "FINAL_DECISION",
                     {"final_score": final_score, "routing": routing},
                     processing_ms=ms)


def log_adjuster_action(db: Session, claim_id: str, action: str, reason: str, adjuster_id: str):
    return log_event(db, claim_id, "ADJUSTER_ACTION",
                     {"action": action, "reason": reason, "adjuster_id": adjuster_id})

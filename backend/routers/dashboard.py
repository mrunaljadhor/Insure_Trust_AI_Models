"""
InsureTrust AI — Dashboard Router
====================================
GET /dashboard/stats — Aggregated statistics
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from models.database import get_db, Claim

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats")
async def get_dashboard_stats(db: Session = Depends(get_db)):
    """
    Returns aggregated dashboard statistics.
    """
    total = db.query(Claim).count()
    auto_approved = db.query(Claim).filter(Claim.routing == "AUTO_APPROVED").count()
    manual_review = db.query(Claim).filter(Claim.routing == "MANUAL_REVIEW").count()
    high_risk = db.query(Claim).filter(Claim.routing == "HIGH_RISK_REVIEW").count()
    auto_escalated = db.query(Claim).filter(Claim.routing == "AUTO_ESCALATED").count()

    # Count distinct rings
    rings = db.query(func.count(func.distinct(Claim.ring_id))).filter(
        Claim.ring_detected == True
    ).scalar() or 0

    # Average processing time
    avg_ms = db.query(func.avg(Claim.processing_ms)).scalar() or 0

    # RFI breakdown
    rfi_breakdown = {}
    claims_with_rfis = db.query(Claim).filter(Claim.triggered_rfis.isnot(None)).all()
    for claim in claims_with_rfis:
        if claim.triggered_rfis:
            for rfi in claim.triggered_rfis:
                code = rfi.get("rfi_code", "UNKNOWN")
                rfi_breakdown[code] = rfi_breakdown.get(code, 0) + 1

    # Recent claims
    recent = db.query(Claim).order_by(Claim.created_at.desc()).limit(20).all()
    recent_claims = [
        {
            "id": c.id,
            "claimant_name_masked": c.claimant_name_masked,
            "claim_amount": c.claim_amount,
            "risk_score": c.risk_score,
            "routing": c.routing,
            "status": c.status,
            "ring_detected": c.ring_detected,
            "processing_ms": c.processing_ms,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in recent
    ]

    return {
        "total_claims": total,
        "auto_approved": auto_approved,
        "manual_review": manual_review,
        "high_risk": high_risk,
        "auto_escalated": auto_escalated,
        "rings_detected": rings,
        "avg_processing_ms": round(avg_ms, 1),
        "rfi_breakdown": rfi_breakdown,
        "recent_claims": recent_claims,
    }

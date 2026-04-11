"""
InsureTrust AI — LLM Summary Service (Groq)
=============================================
The ONLY place Groq API is called.
Runs async after main pipeline, never blocks risk score display.
Uses llama-3.1-8b-instant model for claim analysis summaries.
"""

import os
import json
import asyncio
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session


# Safe fallback if LLM call fails
FALLBACK_SUMMARY = {
    "red_flags": ["Manual review required — AI summary unavailable"],
    "recommended_action": "REVIEW",
    "confidence_note": "Summary generation failed. Review raw scores.",
    "adjuster_instructions": "Please review all flagged indicators manually."
}


async def generate_claim_summary(
    claim_data: dict,
    final_score: float,
    triggered_rfis: list,
    ring_detected: bool,
    db: Session = None,
    claim_id: str = None,
) -> dict:
    """
    Call Groq API with llama-3.1-8b-instant for claim analysis.
    This is async and non-blocking. The result is stored in DB when ready.
    """
    groq_api_key = os.getenv("GROQ_API_KEY", "")

    if not groq_api_key or groq_api_key == "your_groq_key_here":
        # No API key configured, return fallback
        summary = FALLBACK_SUMMARY.copy()
        summary["confidence_note"] = "Groq API key not configured. Using fallback summary."
        if db and claim_id:
            _store_summary(db, claim_id, summary)
        return summary

    try:
        from groq import Groq

        client = Groq(api_key=groq_api_key)

        # Build safe claim JSON (no PII)
        safe_claim = {
            "claim_amount": claim_data.get("claim_amount"),
            "hospital_name": claim_data.get("hospital_name"),
            "diagnosis_code": claim_data.get("diagnosis_code"),
            "treatment_code": claim_data.get("treatment_code"),
            "incident_description": claim_data.get("incident_description"),
            "claim_frequency": claim_data.get("claim_frequency"),
            "weekend_claim": claim_data.get("weekend_claim"),
            "policy_age_days": claim_data.get("policy_age_days"),
        }

        rfi_list = [f"{r['rfi_code']}: {r['description']}" for r in triggered_rfis]

        prompt = f"""You are an insurance fraud analyst. Given this claim data and risk analysis, return ONLY a valid JSON object with these keys:
- red_flags: array of exactly 5 strings, each a specific red flag found
- recommended_action: one of APPROVE / REVIEW / ESCALATE / REJECT  
- confidence_note: one sentence explaining AI confidence level
- adjuster_instructions: 2-3 sentences for the human adjuster

Claim data: {json.dumps(safe_claim)}
Risk score: {final_score}
Triggered RFIs: {json.dumps(rfi_list)}
Ring detected: {ring_detected}"""

        # Run sync Groq call in executor to not block event loop
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, lambda: client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are an expert insurance fraud analyst. Respond ONLY with valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=500,
        ))

        content = response.choices[0].message.content.strip()

        # Parse JSON response
        # Handle markdown code blocks
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()

        summary = json.loads(content)

        # Validate required keys
        required_keys = ["red_flags", "recommended_action", "confidence_note", "adjuster_instructions"]
        for key in required_keys:
            if key not in summary:
                summary = FALLBACK_SUMMARY.copy()
                break

        if db and claim_id:
            _store_summary(db, claim_id, summary)

        return summary

    except Exception as e:
        print(f"[LLM] Groq API error: {e}")
        summary = FALLBACK_SUMMARY.copy()
        summary["confidence_note"] = f"LLM error: {str(e)[:100]}. Review raw scores."
        if db and claim_id:
            _store_summary(db, claim_id, summary)
        return summary


def _store_summary(db: Session, claim_id: str, summary: dict):
    """Store LLM summary in the claims table."""
    try:
        from models.database import Claim
        claim = db.query(Claim).filter(Claim.id == claim_id).first()
        if claim:
            claim.llm_summary = summary
            db.commit()
    except Exception as e:
        print(f"[LLM] Failed to store summary: {e}")


def get_claim_summary(db: Session, claim_id: str) -> Optional[dict]:
    """Retrieve stored LLM summary for a claim."""
    from models.database import Claim
    claim = db.query(Claim).filter(Claim.id == claim_id).first()
    if claim and claim.llm_summary:
        return claim.llm_summary
    return None

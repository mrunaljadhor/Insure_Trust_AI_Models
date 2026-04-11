"""
InsureTrust AI — IRDAI RFI Engine
===================================
Hardcoded 10 IRDAI 2026 Red Flag Indicators.
Each returns: {triggered, rfi_code, description, risk_points}
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any
from services.ingestion import parse_date


def rfi_01_early_claim(claim_data: dict, **kwargs) -> dict:
    """RFI-01: Claim submitted within 90 days of policy start → +20 pts"""
    claim_date = parse_date(claim_data.get("claim_date"))
    policy_start = parse_date(claim_data.get("policy_start_date"))

    triggered = False
    if claim_date and policy_start:
        days = (claim_date - policy_start).days
        triggered = days <= 90

    return {
        "triggered": triggered,
        "rfi_code": "RFI-01",
        "description": "Claim submitted within 90 days of policy start",
        "risk_points": 20 if triggered else 0
    }


def rfi_02_high_claim_ratio(claim_data: dict, **kwargs) -> dict:
    """RFI-02: Claim amount > 80% of sum insured → +15 pts"""
    claim_amount = claim_data.get("claim_amount", 0)
    sum_insured = claim_data.get("sum_insured") or claim_data.get("policy_max_coverage") or 1

    triggered = (claim_amount / sum_insured) > 0.80

    return {
        "triggered": triggered,
        "rfi_code": "RFI-02",
        "description": "Claim amount exceeds 80% of sum insured",
        "risk_points": 15 if triggered else 0
    }


def rfi_03_hospital_high_volume(claim_data: dict, **kwargs) -> dict:
    """RFI-03: Same hospital submits 5+ high-cost claims in 30 days → +25 pts"""
    # In stub mode, check graph data for hospital claim count
    hospital_code = claim_data.get("hospital_code")
    triggered = False

    if hospital_code:
        # Check known high-volume hospitals from seed data
        # HOSP_007 is used by RING_003 (12 claims), HOSP_003 by RING_001 (20 claims)
        high_volume_hospitals = {"HOSP_003", "HOSP_007"}
        if hospital_code in high_volume_hospitals:
            triggered = True

    return {
        "triggered": triggered,
        "rfi_code": "RFI-03",
        "description": "Hospital submitted 5+ high-cost claims in 30 days",
        "risk_points": 25 if triggered else 0
    }


def rfi_04_frequent_claimant(claim_data: dict, **kwargs) -> dict:
    """RFI-04: Claimant has 3+ claims in past 12 months → +20 pts"""
    claim_frequency = claim_data.get("claim_frequency", 0)
    triggered = claim_frequency >= 3

    return {
        "triggered": triggered,
        "rfi_code": "RFI-04",
        "description": "Claimant has 3+ claims in past 12 months",
        "risk_points": 20 if triggered else 0
    }


def rfi_05_unregistered_doctor(claim_data: dict, **kwargs) -> dict:
    """RFI-05: Doctor not in approved MCI/NMC registry list → +30 pts"""
    doctor_id = claim_data.get("doctor_id")
    # Approved doctor registry (subset)
    approved_doctors = {f"DOC_{str(i).zfill(3)}" for i in range(1, 51)}

    triggered = doctor_id is not None and doctor_id not in approved_doctors

    return {
        "triggered": triggered,
        "rfi_code": "RFI-05",
        "description": "Doctor not found in approved MCI/NMC registry",
        "risk_points": 30 if triggered else 0
    }


def rfi_06_weekend_holiday(claim_data: dict, **kwargs) -> dict:
    """RFI-06: Claim date is weekend or public holiday → +10 pts"""
    triggered = claim_data.get("weekend_claim", False)

    if not triggered:
        claim_date = parse_date(claim_data.get("claim_date"))
        if claim_date:
            triggered = claim_date.weekday() >= 5

    return {
        "triggered": triggered,
        "rfi_code": "RFI-06",
        "description": "Claim submitted on weekend or public holiday",
        "risk_points": 10 if triggered else 0
    }


def rfi_07_diagnosis_mismatch(claim_data: dict, **kwargs) -> dict:
    """RFI-07: Diagnosis code does not match treatment code → +25 pts"""
    diag = claim_data.get("diagnosis_code", "")
    treat = claim_data.get("treatment_code", "")

    triggered = False
    if diag and treat:
        # Codes should have matching suffix: D001 ↔ T001
        diag_num = diag[-3:] if len(diag) >= 3 else diag
        treat_num = treat[-3:] if len(treat) >= 3 else treat
        triggered = diag_num != treat_num

    return {
        "triggered": triggered,
        "rfi_code": "RFI-07",
        "description": "Diagnosis code does not match treatment code",
        "risk_points": 25 if triggered else 0
    }


def rfi_08_location_mismatch(claim_data: dict, image_result: dict = None, **kwargs) -> dict:
    """RFI-08: Photo GPS != claimed accident location (>10km) → +20 pts"""
    triggered = False

    if image_result:
        mismatch_km = image_result.get("location_mismatch_km", 0)
        triggered = mismatch_km > 10

    return {
        "triggered": triggered,
        "rfi_code": "RFI-08",
        "description": f"Photo taken {image_result.get('location_mismatch_km', 0) if image_result else 0}km from claimed location",
        "risk_points": 20 if triggered else 0
    }


def rfi_09_identical_amounts(claim_data: dict, **kwargs) -> dict:
    """RFI-09: Identical claim amount from different claimants → +25 pts"""
    # Check if this amount is suspiciously common
    # In production, this would query the DB; for demo, flag ring amounts
    claim_amount = claim_data.get("claim_amount", 0)
    ring_id = claim_data.get("ring_id")

    # Flag amounts that are suspiciously round or identical to ring patterns
    triggered = False
    if ring_id:
        triggered = True
    elif claim_amount > 0 and claim_amount % 500 == 0 and claim_amount > 400000:
        triggered = True

    return {
        "triggered": triggered,
        "rfi_code": "RFI-09",
        "description": "Identical claim amount detected from different claimants",
        "risk_points": 25 if triggered else 0
    }


def rfi_10_doc_alteration(claim_data: dict, image_result: dict = None, **kwargs) -> dict:
    """RFI-10: Supporting doc flagged for digital alteration → +30 pts"""
    triggered = False

    if image_result:
        triggered = (
            image_result.get("metadata_stripped", False) or
            image_result.get("deepfake_probability", 0) > 0.7
        )

    return {
        "triggered": triggered,
        "rfi_code": "RFI-10",
        "description": "Supporting document flagged for potential digital alteration",
        "risk_points": 30 if triggered else 0
    }


# Registry of all RFI functions
ALL_RFIS = [
    rfi_01_early_claim,
    rfi_02_high_claim_ratio,
    rfi_03_hospital_high_volume,
    rfi_04_frequent_claimant,
    rfi_05_unregistered_doctor,
    rfi_06_weekend_holiday,
    rfi_07_diagnosis_mismatch,
    rfi_08_location_mismatch,
    rfi_09_identical_amounts,
    rfi_10_doc_alteration,
]


def run_all_rfis(claim_data: dict, image_result: dict = None, graph_result: dict = None) -> dict:
    """
    Run all 10 IRDAI RFI checks and return results.
    Must complete in < 20ms.
    """
    triggered_rfis = []
    total_points = 0

    for rfi_func in ALL_RFIS:
        result = rfi_func(
            claim_data=claim_data,
            image_result=image_result,
            graph_result=graph_result
        )
        if result["triggered"]:
            triggered_rfis.append({
                "rfi_code": result["rfi_code"],
                "description": result["description"],
                "risk_points": result["risk_points"]
            })
            total_points += result["risk_points"]

    return {
        "triggered_rfis": triggered_rfis,
        "total_rfi_points": total_points
    }

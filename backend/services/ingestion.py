"""
InsureTrust AI — Ingestion Service
====================================
Impossible-data validator + feature normalizer.
Runs BEFORE any model stubs are called.
"""

import hashlib
import re
from datetime import datetime, timedelta
from typing import Optional


# Approved hospital network
APPROVED_HOSPITALS = [
    "HOSP_001", "HOSP_002", "HOSP_003", "HOSP_004", "HOSP_005",
    "HOSP_006", "HOSP_007", "HOSP_008", "HOSP_009", "HOSP_010",
]


class ValidationError(Exception):
    """Raised when impossible-data is detected."""
    def __init__(self, message: str, error_code: str = "VALIDATION_FAILED"):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


def validate_claim(claim_data: dict, db_session=None) -> dict:
    """
    Run impossible-data validation. Returns 400-equivalent errors instantly.
    Must complete in < 10ms.
    """
    errors = []

    # Parse dates
    claim_date = parse_date(claim_data.get("claim_date"))
    policy_start = parse_date(claim_data.get("policy_start_date"))

    # Rule 1: claim_date < policy_start_date
    if claim_date and policy_start and claim_date < policy_start:
        errors.append("Claim predates policy start date")

    # Rule 2: claim_amount > policy_max_coverage
    claim_amount = claim_data.get("claim_amount", 0)
    max_coverage = claim_data.get("policy_max_coverage") or claim_data.get("sum_insured")
    if max_coverage and claim_amount > max_coverage:
        errors.append("Amount exceeds coverage limit")

    # Rule 3: hospital_code not in approved_network
    hospital_code = claim_data.get("hospital_code")
    if hospital_code:
        hospital_code = hospital_code.strip().upper()
        if hospital_code not in APPROVED_HOSPITALS:
            errors.append("Out-of-network provider")

    # Rule 4: Duplicate claim within 30 days (same claimant, same amount)
    if db_session:
        from models.database import Claim
        claimant_id = claim_data.get("claimant_id")
        if claimant_id and claim_date:
            thirty_days_ago = claim_date - timedelta(days=30)
            duplicate = db_session.query(Claim).filter(
                Claim.claimant_id == claimant_id,
                Claim.claim_amount == claim_amount,
                Claim.claim_date >= thirty_days_ago,
                Claim.claim_date <= claim_date,
            ).first()
            if duplicate:
                errors.append(f"Duplicate claim detected (matches {duplicate.id})")

    if errors:
        raise ValidationError("; ".join(errors))

    return claim_data


def normalize_claim(claim_data: dict) -> dict:
    """
    Normalize all claim fields to standard formats.
    Must complete in < 5ms.
    """
    normalized = dict(claim_data)

    # Dates → ISO 8601
    for date_field in ["claim_date", "policy_start_date"]:
        if date_field in normalized and normalized[date_field]:
            dt = parse_date(normalized[date_field])
            if dt:
                normalized[date_field] = dt.isoformat()

    # Amounts → float with 2 decimal places
    for amount_field in ["claim_amount", "policy_max_coverage", "sum_insured"]:
        if amount_field in normalized and normalized[amount_field] is not None:
            normalized[amount_field] = round(float(normalized[amount_field]), 2)

    # Hospital codes → uppercase stripped
    if "hospital_code" in normalized and normalized["hospital_code"]:
        normalized["hospital_code"] = normalized["hospital_code"].strip().upper()

    # GPS coordinates → decimal degrees
    for coord_field in ["incident_lat", "incident_lng"]:
        if coord_field in normalized and normalized[coord_field] is not None:
            normalized[coord_field] = convert_to_decimal_degrees(normalized[coord_field])

    # Aadhaar → SHA-256 hash (store hash only, display last 4 digits)
    if "aadhaar_number" in normalized and normalized["aadhaar_number"]:
        aadhaar = str(normalized["aadhaar_number"]).strip()
        normalized["aadhaar_hash"] = hashlib.sha256(aadhaar.encode()).hexdigest()
        normalized["aadhaar_last4"] = aadhaar[-4:]
        del normalized["aadhaar_number"]  # Never store raw

    # Mobile → SHA-256 hash (display last 4 digits only)
    if "mobile_number" in normalized and normalized["mobile_number"]:
        mobile = str(normalized["mobile_number"]).strip()
        normalized["mobile_hash"] = hashlib.sha256(mobile.encode()).hexdigest()
        normalized["mobile_last4"] = mobile[-4:]
        del normalized["mobile_number"]  # Never store raw

    # Determine weekend_claim from date if not set
    if "claim_date" in normalized:
        dt = parse_date(normalized["claim_date"])
        if dt:
            normalized["weekend_claim"] = dt.weekday() >= 5

    return normalized


def parse_date(date_val) -> Optional[datetime]:
    """Parse various date formats to datetime."""
    if date_val is None:
        return None
    if isinstance(date_val, datetime):
        return date_val
    if isinstance(date_val, str):
        date_val = date_val.strip()
        for fmt in [
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%d",
            "%d/%m/%Y",
            "%d-%m-%Y",
            "%m/%d/%Y",
        ]:
            try:
                return datetime.strptime(date_val, fmt)
            except ValueError:
                continue
    return None


def convert_to_decimal_degrees(coord) -> float:
    """Convert DMS or other formats to decimal degrees."""
    if isinstance(coord, (int, float)):
        return round(float(coord), 6)
    if isinstance(coord, str):
        # Try DMS format: 18°31'12"N
        dms_match = re.match(
            r"""(\d+)[°]\s*(\d+)[\']\s*([\d.]+)[\"]\s*([NSEW])""",
            coord.strip()
        )
        if dms_match:
            d, m, s, direction = dms_match.groups()
            decimal = float(d) + float(m) / 60 + float(s) / 3600
            if direction in ('S', 'W'):
                decimal = -decimal
            return round(decimal, 6)
        try:
            return round(float(coord), 6)
        except ValueError:
            return 0.0
    return 0.0


def mask_name(name: str) -> str:
    """Mask a name for privacy. Show only last 3 characters."""
    if not name:
        return "****"
    if len(name) <= 3:
        return "***" + name[-1:]
    return "****" + name[-3:]


def compute_policy_age_days(claim_date: str, policy_start: str) -> int:
    """Compute days between policy start and claim date."""
    cd = parse_date(claim_date)
    ps = parse_date(policy_start)
    if cd and ps:
        return (cd - ps).days
    return 365  # default to safe value


def build_features(claim_data: dict) -> dict:
    """Build feature dict for tabular model from normalized claim data."""
    policy_age = compute_policy_age_days(
        claim_data.get("claim_date"),
        claim_data.get("policy_start_date")
    )
    sum_insured = claim_data.get("sum_insured") or claim_data.get("policy_max_coverage") or 1000000
    claim_amount = claim_data.get("claim_amount", 0)

    return {
        "claim_amount": claim_amount,
        "policy_age_days": policy_age,
        "claim_frequency": claim_data.get("claim_frequency", 0),
        "hospital_risk_score": 0.3,  # default; real system would look up hospital
        "diagnosis_treatment_match": (
            1.0 if claim_data.get("diagnosis_code") and claim_data.get("treatment_code") and
            claim_data["diagnosis_code"][-3:] == claim_data["treatment_code"][-3:]
            else 0.0
        ),
        "weekend_claim": claim_data.get("weekend_claim", False),
        "claim_amount_ratio": round(claim_amount / sum_insured, 4) if sum_insured else 0,
        "sum_insured": sum_insured,
    }

"""
InsureTrust AI — Synthetic Dataset Generator
=============================================
Generates 500 claims + 3 embedded fraud rings.
Seeds the SQLite database and NetworkX graph on startup.
"""

import json
import random
import hashlib
import uuid
import os
from datetime import datetime, timedelta

# ─── Config ──────────────────────────────────────────────────────────

HOSPITALS = [
    ("HOSP_001", "City General Hospital"),
    ("HOSP_002", "Metro Healthcare"),
    ("HOSP_003", "Apollo Care Center"),
    ("HOSP_004", "Max Super Specialty"),
    ("HOSP_005", "Fortis Medical"),
    ("HOSP_006", "Narayana Health"),
    ("HOSP_007", "Ring Hospital Seven"),     # Used by RING_003
    ("HOSP_008", "AIIMS Satellite"),
    ("HOSP_009", "Medanta Regional"),
    ("HOSP_010", "Manipal Clinic"),
]

APPROVED_HOSPITALS = [h[0] for h in HOSPITALS]

DOCTORS = [f"DOC_{str(i).zfill(3)}" for i in range(1, 51)]
WORKSHOPS = [f"WRK_{str(i).zfill(3)}" for i in range(1, 21)]
WITNESSES = [f"WIT_{str(i).zfill(3)}" for i in range(1, 31)]

DIAGNOSIS_CODES = ["D001", "D002", "D003", "D004", "D005", "D006", "D007", "D008"]
TREATMENT_CODES = ["T001", "T002", "T003", "T004", "T005", "T006", "T007", "T008"]

FIRST_NAMES = [
    "Aarav", "Vivaan", "Aditya", "Vihaan", "Arjun", "Sai", "Reyansh", "Ayaan",
    "Krishna", "Ishaan", "Ananya", "Diya", "Priya", "Sneha", "Kavya", "Riya",
    "Meera", "Pooja", "Neha", "Shruti", "Rahul", "Amit", "Suresh", "Vikram", "Rohan"
]

LAST_NAMES = [
    "Sharma", "Patel", "Gupta", "Singh", "Kumar", "Verma", "Joshi", "Rao",
    "Nair", "Reddy", "Mehta", "Shah", "Das", "Mishra", "Chopra", "Malhotra",
    "Kapoor", "Bhat", "Iyer", "Pillai"
]

DESCRIPTIONS_LEGIT = [
    "Minor collision at intersection. Front bumper damaged.",
    "Slipped on wet floor at workplace. Fractured left wrist.",
    "Rear-ended by another vehicle at traffic signal.",
    "Kitchen accident resulting in burns on forearm.",
    "Fall from stairs causing knee injury.",
    "Bike accident on highway, minor abrasions.",
    "Water damage to vehicle during monsoon flooding.",
    "Food poisoning requiring overnight hospitalization.",
    "Sports injury - torn ligament during cricket match.",
    "Tree branch fell on parked car causing dent.",
]

DESCRIPTIONS_FRAUD = [
    "Major accident on highway. Total vehicle damage. Need urgent payout.",
    "Severe injury requiring emergency surgery and extended ICU stay.",
    "Complete theft of vehicle with all belongings. Maximum claim needed.",
    "House fire destroyed everything. Claiming full insured amount.",
    "Multiple bone fractures from alleged hit and run accident.",
]


def sha256_hash(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def mask_name(name: str) -> str:
    if len(name) <= 3:
        return "***" + name[-1]
    return "****" + name[-3:]


def generate_aadhaar(rng: random.Random) -> tuple:
    digits = ''.join([str(rng.randint(0, 9)) for _ in range(12)])
    return sha256_hash(digits), digits[-4:]


def generate_mobile(rng: random.Random, prefix: str = None) -> tuple:
    if prefix:
        digits = prefix + ''.join([str(rng.randint(0, 9)) for _ in range(10 - len(prefix))])
    else:
        digits = str(rng.randint(7, 9)) + ''.join([str(rng.randint(0, 9)) for _ in range(9)])
    return sha256_hash(digits), digits[-4:]


def generate_ip(rng: random.Random, fixed: str = None) -> str:
    if fixed:
        return fixed
    return f"{rng.randint(10, 223)}.{rng.randint(0, 255)}.{rng.randint(0, 255)}.{rng.randint(1, 254)}"


def random_date(rng: random.Random, start: datetime, end: datetime) -> datetime:
    delta = end - start
    random_days = rng.randint(0, delta.days)
    return start + timedelta(days=random_days)


def generate_claims():
    rng = random.Random(42)
    claims = []
    claim_id_counter = 0
    now = datetime(2025, 3, 1)

    # ─── 350 LEGITIMATE claims ────────────────────────────────────
    for i in range(350):
        claim_id_counter += 1
        cid = f"CLM_{str(claim_id_counter).zfill(5)}"
        claimant_id = f"C_{str(i + 200).zfill(4)}"
        name = f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}"
        sum_insured = rng.choice([200000, 500000, 1000000, 1500000, 2000000])
        claim_amount = round(sum_insured * rng.uniform(0.10, 0.60), 2)
        policy_start = random_date(rng, datetime(2023, 1, 1), datetime(2024, 6, 1))
        claim_date = random_date(rng, policy_start + timedelta(days=120), now)
        hospital = rng.choice(HOSPITALS)
        doctor = rng.choice(DOCTORS)
        workshop = rng.choice(WORKSHOPS) if rng.random() > 0.5 else None
        witness = rng.choice(WITNESSES) if rng.random() > 0.6 else None
        diag = rng.choice(DIAGNOSIS_CODES)
        treat_idx = DIAGNOSIS_CODES.index(diag)
        treatment = TREATMENT_CODES[treat_idx]  # matching treatment
        lat = round(rng.uniform(8.0, 34.0), 4)
        lng = round(rng.uniform(68.0, 97.0), 4)
        aadhaar_hash, aadhaar_last4 = generate_aadhaar(rng)
        mobile_hash, mobile_last4 = generate_mobile(rng)
        ip = generate_ip(rng)
        weekday = claim_date.weekday()

        claims.append({
            "id": cid,
            "claimant_id": claimant_id,
            "claimant_name": name,
            "claimant_name_masked": mask_name(name),
            "aadhaar_hash": aadhaar_hash,
            "aadhaar_last4": aadhaar_last4,
            "mobile_hash": mobile_hash,
            "mobile_last4": mobile_last4,
            "policy_id": f"POL_{str(rng.randint(10000, 99999))}",
            "policy_start_date": policy_start.isoformat(),
            "policy_max_coverage": sum_insured,
            "sum_insured": sum_insured,
            "claim_amount": claim_amount,
            "claim_date": claim_date.isoformat(),
            "hospital_code": hospital[0],
            "hospital_name": hospital[1],
            "doctor_id": doctor,
            "workshop_id": workshop,
            "witness_id": witness,
            "diagnosis_code": diag,
            "treatment_code": treatment,
            "incident_description": rng.choice(DESCRIPTIONS_LEGIT),
            "incident_lat": lat,
            "incident_lng": lng,
            "ip_address": ip,
            "claim_frequency": rng.randint(0, 1),
            "weekend_claim": weekday >= 5,
            "fraud_type": "legitimate",
            "expected_score_range": [5, 30],
        })

    # ─── 100 INDIVIDUAL FRAUD claims ──────────────────────────────
    for i in range(100):
        claim_id_counter += 1
        cid = f"CLM_{str(claim_id_counter).zfill(5)}"
        claimant_id = f"C_{str(i + 600).zfill(4)}"
        name = f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}"
        sum_insured = rng.choice([500000, 1000000, 1500000, 2000000])
        claim_amount = round(sum_insured * rng.uniform(0.85, 0.98), 2)  # 85%+ of SI
        policy_start = random_date(rng, now - timedelta(days=55), now - timedelta(days=10))
        claim_date = random_date(rng, policy_start + timedelta(days=5), now)
        hospital = rng.choice(HOSPITALS)
        doctor = rng.choice(DOCTORS)
        diag = rng.choice(DIAGNOSIS_CODES)
        treatment = rng.choice(TREATMENT_CODES)  # mismatched treatment!
        lat = round(rng.uniform(8.0, 34.0), 4)
        lng = round(rng.uniform(68.0, 97.0), 4)
        aadhaar_hash, aadhaar_last4 = generate_aadhaar(rng)
        mobile_hash, mobile_last4 = generate_mobile(rng)
        ip = generate_ip(rng)
        weekday = claim_date.weekday()

        claims.append({
            "id": cid,
            "claimant_id": claimant_id,
            "claimant_name": name,
            "claimant_name_masked": mask_name(name),
            "aadhaar_hash": aadhaar_hash,
            "aadhaar_last4": aadhaar_last4,
            "mobile_hash": mobile_hash,
            "mobile_last4": mobile_last4,
            "policy_id": f"POL_{str(rng.randint(10000, 99999))}",
            "policy_start_date": policy_start.isoformat(),
            "policy_max_coverage": sum_insured,
            "sum_insured": sum_insured,
            "claim_amount": claim_amount,
            "claim_date": claim_date.isoformat(),
            "hospital_code": hospital[0],
            "hospital_name": hospital[1],
            "doctor_id": doctor,
            "workshop_id": None,
            "witness_id": None,
            "diagnosis_code": diag,
            "treatment_code": treatment,
            "incident_description": rng.choice(DESCRIPTIONS_FRAUD),
            "incident_lat": lat,
            "incident_lng": lng,
            "ip_address": ip,
            "claim_frequency": rng.randint(3, 6),  # High frequency
            "weekend_claim": True,  # Weekend claims
            "fraud_type": "individual",
            "expected_score_range": [55, 80],
        })

    # ─── 50 RING FRAUD claims — 3 embedded rings ─────────────────

    # RING_001: 20 claims (C001–C020), shared doctor_D001, workshop_W001
    shared_doctor_1 = "DOC_001"
    shared_workshop_1 = "WRK_001"
    for i in range(20):
        claim_id_counter += 1
        cid = f"CLM_{str(claim_id_counter).zfill(5)}"
        claimant_id = f"C_{str(i + 1).zfill(4)}"
        name = f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}"
        sum_insured = 1000000
        claim_amount = round(sum_insured * rng.uniform(0.70, 0.95), 2)
        policy_start = random_date(rng, datetime(2024, 1, 1), datetime(2024, 6, 1))
        claim_date = random_date(rng, datetime(2024, 12, 1), now)
        lat = round(18.52 + rng.uniform(-0.05, 0.05), 4)
        lng = round(73.85 + rng.uniform(-0.05, 0.05), 4)
        aadhaar_hash, aadhaar_last4 = generate_aadhaar(rng)
        mobile_hash, mobile_last4 = generate_mobile(rng)
        ip = generate_ip(rng)

        claims.append({
            "id": cid,
            "claimant_id": claimant_id,
            "claimant_name": name,
            "claimant_name_masked": mask_name(name),
            "aadhaar_hash": aadhaar_hash,
            "aadhaar_last4": aadhaar_last4,
            "mobile_hash": mobile_hash,
            "mobile_last4": mobile_last4,
            "policy_id": f"POL_{str(rng.randint(10000, 99999))}",
            "policy_start_date": policy_start.isoformat(),
            "policy_max_coverage": sum_insured,
            "sum_insured": sum_insured,
            "claim_amount": claim_amount,
            "claim_date": claim_date.isoformat(),
            "hospital_code": "HOSP_003",
            "hospital_name": "Apollo Care Center",
            "doctor_id": shared_doctor_1,
            "workshop_id": shared_workshop_1,
            "witness_id": f"WIT_{str(rng.choice([1, 2, 3])).zfill(3)}",
            "diagnosis_code": "D003",
            "treatment_code": "T003",
            "incident_description": rng.choice(DESCRIPTIONS_FRAUD),
            "incident_lat": lat,
            "incident_lng": lng,
            "ip_address": ip,
            "claim_frequency": rng.randint(2, 5),
            "weekend_claim": rng.random() > 0.4,
            "fraud_type": "ring",
            "ring_id": "RING_001",
            "expected_score_range": [75, 95],
        })

    # RING_002: 18 claims (C021–C038), shared witness_W002, same mobile prefix 98765
    shared_witness_2 = "WIT_002"
    for i in range(18):
        claim_id_counter += 1
        cid = f"CLM_{str(claim_id_counter).zfill(5)}"
        claimant_id = f"C_{str(i + 21).zfill(4)}"
        name = f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}"
        sum_insured = rng.choice([500000, 1000000])
        claim_amount = round(sum_insured * rng.uniform(0.65, 0.90), 2)
        policy_start = random_date(rng, datetime(2024, 3, 1), datetime(2024, 8, 1))
        claim_date = random_date(rng, datetime(2024, 11, 1), now)
        lat = round(19.07 + rng.uniform(-0.05, 0.05), 4)
        lng = round(72.87 + rng.uniform(-0.05, 0.05), 4)
        aadhaar_hash, aadhaar_last4 = generate_aadhaar(rng)
        mobile_hash, mobile_last4 = generate_mobile(rng, prefix="98765")
        ip = generate_ip(rng)

        claims.append({
            "id": cid,
            "claimant_id": claimant_id,
            "claimant_name": name,
            "claimant_name_masked": mask_name(name),
            "aadhaar_hash": aadhaar_hash,
            "aadhaar_last4": aadhaar_last4,
            "mobile_hash": mobile_hash,
            "mobile_last4": mobile_last4,
            "policy_id": f"POL_{str(rng.randint(10000, 99999))}",
            "policy_start_date": policy_start.isoformat(),
            "policy_max_coverage": sum_insured,
            "sum_insured": sum_insured,
            "claim_amount": claim_amount,
            "claim_date": claim_date.isoformat(),
            "hospital_code": rng.choice(["HOSP_002", "HOSP_004"]),
            "hospital_name": "Metro Healthcare",
            "doctor_id": rng.choice(DOCTORS[:10]),
            "workshop_id": None,
            "witness_id": shared_witness_2,
            "diagnosis_code": rng.choice(DIAGNOSIS_CODES),
            "treatment_code": rng.choice(TREATMENT_CODES),
            "incident_description": rng.choice(DESCRIPTIONS_FRAUD),
            "incident_lat": lat,
            "incident_lng": lng,
            "ip_address": ip,
            "claim_frequency": rng.randint(2, 4),
            "weekend_claim": rng.random() > 0.5,
            "fraud_type": "ring",
            "ring_id": "RING_002",
            "expected_score_range": [70, 90],
        })

    # RING_003: 12 claims (C039–C050), same IP, HOSP_007, amounts differ by ₹500
    shared_ip_3 = "192.168.1.50"
    base_amount_3 = 450000
    for i in range(12):
        claim_id_counter += 1
        cid = f"CLM_{str(claim_id_counter).zfill(5)}"
        claimant_id = f"C_{str(i + 39).zfill(4)}"
        name = f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}"
        sum_insured = 1500000
        claim_amount = base_amount_3 + (i * 500)  # Differ by exactly ₹500
        policy_start = random_date(rng, datetime(2024, 6, 1), datetime(2024, 10, 1))
        claim_date = random_date(rng, datetime(2025, 1, 1), now)
        lat = round(12.97 + rng.uniform(-0.02, 0.02), 4)
        lng = round(77.59 + rng.uniform(-0.02, 0.02), 4)
        aadhaar_hash, aadhaar_last4 = generate_aadhaar(rng)
        mobile_hash, mobile_last4 = generate_mobile(rng)

        claims.append({
            "id": cid,
            "claimant_id": claimant_id,
            "claimant_name": name,
            "claimant_name_masked": mask_name(name),
            "aadhaar_hash": aadhaar_hash,
            "aadhaar_last4": aadhaar_last4,
            "mobile_hash": mobile_hash,
            "mobile_last4": mobile_last4,
            "policy_id": f"POL_{str(rng.randint(10000, 99999))}",
            "policy_start_date": policy_start.isoformat(),
            "policy_max_coverage": sum_insured,
            "sum_insured": sum_insured,
            "claim_amount": claim_amount,
            "claim_date": claim_date.isoformat(),
            "hospital_code": "HOSP_007",
            "hospital_name": "Ring Hospital Seven",
            "doctor_id": rng.choice(DOCTORS[10:20]),
            "workshop_id": None,
            "witness_id": rng.choice(WITNESSES[10:15]),
            "diagnosis_code": "D005",
            "treatment_code": "T005",
            "incident_description": rng.choice(DESCRIPTIONS_FRAUD),
            "incident_lat": lat,
            "incident_lng": lng,
            "ip_address": shared_ip_3,
            "claim_frequency": rng.randint(3, 6),
            "weekend_claim": True,
            "fraud_type": "ring",
            "ring_id": "RING_003",
            "expected_score_range": [75, 95],
        })

    return claims


def generate_demo_claims():
    """Create 3 ready-to-upload demo claim files."""
    demo_legit = {
        "claimant_name": "Priya Sharma",
        "claimant_id": "C_9001",
        "aadhaar_number": "123456789012",
        "mobile_number": "9876543210",
        "policy_id": "POL_DEMO_001",
        "policy_start_date": "2023-06-15T00:00:00",
        "policy_max_coverage": 1000000,
        "sum_insured": 1000000,
        "claim_amount": 35000,
        "claim_date": "2025-02-15T10:30:00",
        "hospital_code": "HOSP_001",
        "hospital_name": "City General Hospital",
        "doctor_id": "DOC_025",
        "workshop_id": None,
        "witness_id": None,
        "diagnosis_code": "D001",
        "treatment_code": "T001",
        "incident_description": "Minor fender bender at parking lot. Small dent on rear bumper. No injuries reported. Police report filed.",
        "incident_lat": 19.076,
        "incident_lng": 72.877,
        "ip_address": "103.22.45.67",
        "claim_frequency": 0,
        "weekend_claim": False
    }

    demo_individual_fraud = {
        "claimant_name": "Vikram Malhotra",
        "claimant_id": "C_9002",
        "aadhaar_number": "987654321098",
        "mobile_number": "8765432109",
        "policy_id": "POL_DEMO_002",
        "policy_start_date": "2025-01-10T00:00:00",
        "policy_max_coverage": 500000,
        "sum_insured": 500000,
        "claim_amount": 465000,
        "claim_date": "2025-02-22T23:45:00",
        "hospital_code": "HOSP_004",
        "hospital_name": "Max Super Specialty",
        "doctor_id": "DOC_048",
        "workshop_id": None,
        "witness_id": None,
        "diagnosis_code": "D004",
        "treatment_code": "T007",
        "incident_description": "Severe injury from alleged hit and run. Emergency surgery required. Claiming maximum coverage for ICU stay and rehabilitation.",
        "incident_lat": 28.6139,
        "incident_lng": 77.209,
        "ip_address": "45.67.89.12",
        "claim_frequency": 4,
        "weekend_claim": True
    }

    demo_ring_fraud = {
        "claimant_name": "Rahul Joshi",
        "claimant_id": "C_0005",
        "aadhaar_number": "555666777888",
        "mobile_number": "9871234560",
        "policy_id": "POL_DEMO_003",
        "policy_start_date": "2024-11-01T00:00:00",
        "policy_max_coverage": 1000000,
        "sum_insured": 1000000,
        "claim_amount": 890000,
        "claim_date": "2025-02-28T14:00:00",
        "hospital_code": "HOSP_003",
        "hospital_name": "Apollo Care Center",
        "doctor_id": "DOC_001",
        "workshop_id": "WRK_001",
        "witness_id": "WIT_001",
        "diagnosis_code": "D003",
        "treatment_code": "T003",
        "incident_description": "Major accident on expressway. Complete vehicle damage as per the usual procedure. Need urgent maximum payout following established protocol.",
        "incident_lat": 18.53,
        "incident_lng": 73.86,
        "ip_address": "172.16.0.99",
        "claim_frequency": 3,
        "weekend_claim": True
    }

    return demo_legit, demo_individual_fraud, demo_ring_fraud


def seed_database(db_session):
    """Seed database with 500 synthetic claims if empty."""
    from models.database import Claim, GraphNode, GraphEdge
    from services.graph_engine import get_graph

    # Check if already seeded
    existing = db_session.query(Claim).count()
    if existing > 0:
        print(f"[SEED] Database already has {existing} claims. Skipping seed.")
        return

    print("[SEED] Generating 500 synthetic claims...")
    claims = generate_claims()

    graph = get_graph()

    for c in claims:
        # Create DB claim
        claim = Claim(
            id=c["id"],
            claimant_name_masked=c["claimant_name_masked"],
            claimant_id=c["claimant_id"],
            aadhaar_hash=c["aadhaar_hash"],
            aadhaar_last4=c["aadhaar_last4"],
            mobile_hash=c["mobile_hash"],
            mobile_last4=c["mobile_last4"],
            policy_id=c["policy_id"],
            policy_start_date=datetime.fromisoformat(c["policy_start_date"]),
            policy_max_coverage=c["policy_max_coverage"],
            sum_insured=c["sum_insured"],
            claim_amount=c["claim_amount"],
            claim_date=datetime.fromisoformat(c["claim_date"]),
            hospital_code=c["hospital_code"],
            hospital_name=c["hospital_name"],
            doctor_id=c["doctor_id"],
            workshop_id=c.get("workshop_id"),
            witness_id=c.get("witness_id"),
            diagnosis_code=c["diagnosis_code"],
            treatment_code=c["treatment_code"],
            incident_description=c["incident_description"],
            incident_lat=c["incident_lat"],
            incident_lng=c["incident_lng"],
            ip_address=c["ip_address"],
            risk_score=random.uniform(*c["expected_score_range"]),
            routing=(
                "AUTO_APPROVED" if c["fraud_type"] == "legitimate"
                else "HIGH_RISK_REVIEW" if c["fraud_type"] == "individual"
                else "AUTO_ESCALATED"
            ),
            ring_detected=c["fraud_type"] == "ring",
            ring_id=c.get("ring_id"),
            status="PENDING",
            processing_ms=random.uniform(100, 500),
            created_at=datetime.fromisoformat(c["claim_date"]),
        )
        db_session.add(claim)

        # Add to NetworkX graph
        claimant_node = c["claimant_id"]
        if not graph.has_node(claimant_node):
            graph.add_node(claimant_node, type="claimant", label=c["claimant_name_masked"],
                          risk_score=claim.risk_score, claim_count=1)
        else:
            graph.nodes[claimant_node]["claim_count"] = graph.nodes[claimant_node].get("claim_count", 0) + 1

        # Doctor edge
        if c["doctor_id"]:
            doc_node = c["doctor_id"]
            if not graph.has_node(doc_node):
                graph.add_node(doc_node, type="doctor", label=f"Dr. {doc_node}", risk_score=0, claim_count=0)
            graph.nodes[doc_node]["claim_count"] = graph.nodes[doc_node].get("claim_count", 0) + 1
            graph.add_edge(claimant_node, doc_node, relationship="TREATED_BY", claim_id=c["id"])

        # Workshop edge
        if c.get("workshop_id"):
            wrk_node = c["workshop_id"]
            if not graph.has_node(wrk_node):
                graph.add_node(wrk_node, type="workshop", label=f"Workshop {wrk_node}", risk_score=0, claim_count=0)
            graph.nodes[wrk_node]["claim_count"] = graph.nodes[wrk_node].get("claim_count", 0) + 1
            graph.add_edge(claimant_node, wrk_node, relationship="REPAIRED_AT", claim_id=c["id"])

        # Witness edge
        if c.get("witness_id"):
            wit_node = c["witness_id"]
            if not graph.has_node(wit_node):
                graph.add_node(wit_node, type="witness", label=f"Witness {wit_node}", risk_score=0, claim_count=0)
            graph.nodes[wit_node]["claim_count"] = graph.nodes[wit_node].get("claim_count", 0) + 1
            graph.add_edge(claimant_node, wit_node, relationship="WITNESSED_BY", claim_id=c["id"])

        # Mobile edge (hashed)
        if c.get("mobile_hash"):
            mob_node = f"mobile_{c['mobile_hash'][:12]}"
            if not graph.has_node(mob_node):
                graph.add_node(mob_node, type="mobile", label=f"****{c['mobile_last4']}", risk_score=0, claim_count=0)
            graph.nodes[mob_node]["claim_count"] = graph.nodes[mob_node].get("claim_count", 0) + 1
            graph.add_edge(claimant_node, mob_node, relationship="USES_MOBILE", claim_id=c["id"])

        # IP edge
        if c.get("ip_address"):
            ip_node = f"ip_{c['ip_address']}"
            if not graph.has_node(ip_node):
                graph.add_node(ip_node, type="ip_address", label=c["ip_address"], risk_score=0, claim_count=0)
            graph.nodes[ip_node]["claim_count"] = graph.nodes[ip_node].get("claim_count", 0) + 1
            graph.add_edge(claimant_node, ip_node, relationship="SUBMITTED_FROM", claim_id=c["id"])

    db_session.commit()
    print(f"[SEED] Seeded {len(claims)} claims. Graph: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges.")

    # Save demo claims
    demo_legit, demo_individual, demo_ring = generate_demo_claims()
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "demo_claims")
    os.makedirs(data_dir, exist_ok=True)

    with open(os.path.join(data_dir, "demo_legit.json"), "w") as f:
        json.dump(demo_legit, f, indent=2)
    with open(os.path.join(data_dir, "demo_individual_fraud.json"), "w") as f:
        json.dump(demo_individual, f, indent=2)
    with open(os.path.join(data_dir, "demo_ring_fraud.json"), "w") as f:
        json.dump(demo_ring, f, indent=2)

    # Save full synthetic dataset
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "synthetic_claims.json"), "w") as f:
        json.dump(claims, f, indent=2, default=str)

    print(f"[SEED] Demo claims saved to {data_dir}")


if __name__ == "__main__":
    claims = generate_claims()
    print(f"Generated {len(claims)} claims")
    legit = sum(1 for c in claims if c["fraud_type"] == "legitimate")
    individual = sum(1 for c in claims if c["fraud_type"] == "individual")
    ring = sum(1 for c in claims if c["fraud_type"] == "ring")
    print(f"  Legitimate: {legit}, Individual Fraud: {individual}, Ring Fraud: {ring}")

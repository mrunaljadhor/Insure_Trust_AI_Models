"""
InsureTrust AI — Model Stub File
================================
This file contains stub functions for all ML models.
Each stub returns realistic mock data so the full pipeline
and frontend work correctly from day one.

When the ML team has their models ready, replace each stub
function body with the real model inference call. The function
signatures and return schemas MUST remain identical.
"""

import random
import hashlib


def get_image_score(image_path: str) -> dict:
    """
    # REPLACE THIS STUB with the real model call from the ML team
    # Expected: EfficientNet-B4 deepfake classifier + EXIF analysis
    # Real model will accept image_path, return this exact schema:
    """
    # Generate deterministic but varied scores based on image path
    seed = int(hashlib.md5(image_path.encode()).hexdigest()[:8], 16) % 1000
    rng = random.Random(seed)

    deepfake_prob = round(rng.uniform(0.1, 0.95), 2)
    loc_mismatch = round(rng.uniform(0, 200), 1)
    ts_mismatch = round(rng.uniform(0, 72), 0)

    return {
        "deepfake_probability": deepfake_prob,
        "exif_gps": {"lat": round(rng.uniform(8, 35), 2), "lng": round(rng.uniform(68, 97), 2)},
        "exif_timestamp": "2024-11-03T14:22:00",
        "claimed_location": {"lat": round(rng.uniform(8, 35), 2), "lng": round(rng.uniform(68, 97), 2)},
        "location_mismatch_km": loc_mismatch,
        "timestamp_mismatch_hours": ts_mismatch,
        "metadata_stripped": rng.random() > 0.7,
        "gradcam_heatmap_b64": None,  # real model returns base64 PNG
        "image_score": round(min(1.0, deepfake_prob * 0.6 + (loc_mismatch / 200) * 0.4), 2)
    }


def get_nlp_score(statement: str, doc_text: str) -> dict:
    """
    # REPLACE THIS STUB with the real model call from the ML team
    # Expected: sentence-transformers contradiction + ring phrase detection
    # Real model will accept statement + doc_text, return this schema:
    """
    # Generate deterministic scores based on statement content
    text = (statement or "") + (doc_text or "")
    seed = int(hashlib.md5(text.encode()).hexdigest()[:8], 16) % 1000
    rng = random.Random(seed)

    contradiction = round(rng.uniform(0.1, 0.9), 2)
    volatility = round(rng.uniform(0.1, 0.7), 2)

    ring_phrases_pool = [
        "as per the usual procedure",
        "refer to the standard process",
        "following established protocol",
        "in accordance with practice",
        "as discussed previously"
    ]

    detected = [p for p in ring_phrases_pool if rng.random() > 0.7]

    return {
        "contradiction_score": contradiction,
        "sentiment_volatility": volatility,
        "professional_ring_phrases": detected,
        "nlp_score": round(contradiction * 0.6 + volatility * 0.4, 2)
    }


def get_tabular_score(features: dict) -> dict:
    """
    # REPLACE THIS STUB with the real model call from the ML team
    # Expected: XGBoost classifier trained on synthetic dataset
    # Real model accepts features dict, returns this schema:
    # features keys: claim_amount, policy_age_days, claim_frequency,
    #   hospital_risk_score, diagnosis_treatment_match, weekend_claim
    """
    # Compute a realistic score based on feature values
    seed_str = str(sorted(features.items()))
    seed = int(hashlib.md5(seed_str.encode()).hexdigest()[:8], 16) % 1000
    rng = random.Random(seed)

    # Weight features that indicate fraud
    claim_freq = features.get("claim_frequency", 0)
    policy_age = features.get("policy_age_days", 365)
    claim_amount = features.get("claim_amount", 50000)
    hospital_risk = features.get("hospital_risk_score", 0.3)
    weekend = features.get("weekend_claim", False)

    base = 0.3
    if claim_freq > 2:
        base += 0.15
    if policy_age < 90:
        base += 0.12
    if claim_amount > 500000:
        base += 0.1
    if hospital_risk > 0.5:
        base += 0.08
    if weekend:
        base += 0.05

    tabular_score = round(min(0.99, base + rng.uniform(-0.1, 0.15)), 2)

    return {
        "tabular_score": tabular_score,
        "shap_values": {
            "claim_frequency": round(max(0, claim_freq * 0.08 + rng.uniform(-0.02, 0.05)), 2),
            "policy_age_days": round(max(0, (365 - policy_age) / 365 * 0.25 + rng.uniform(-0.02, 0.03)), 2),
            "hospital_risk_score": round(max(0, hospital_risk * 0.2 + rng.uniform(-0.02, 0.03)), 2),
            "claim_amount_ratio": round(max(0, min(1, claim_amount / 1000000) * 0.15 + rng.uniform(-0.02, 0.03)), 2),
            "diagnosis_mismatch": round(rng.uniform(0.02, 0.12), 2),
            "weekend_claim": round(0.05 if weekend else 0.01, 2)
        }
    }


def get_gnn_score(claimant_id: str, graph_data: dict) -> dict:
    """
    # REPLACE THIS STUB with the real model call from the ML team
    # Expected: PyTorch Geometric GCN link prediction
    # Real model accepts claimant_id + serialized graph, returns:
    """
    seed = int(hashlib.md5(claimant_id.encode()).hexdigest()[:8], 16) % 1000
    rng = random.Random(seed)

    # Higher scores if graph indicates connections
    connected = graph_data.get("connected_claims", 0)
    ring = graph_data.get("ring_detected", False)

    if ring:
        gnn_score = round(rng.uniform(0.75, 0.98), 2)
        ring_prob = round(rng.uniform(0.80, 0.99), 2)
    elif connected > 2:
        gnn_score = round(rng.uniform(0.50, 0.80), 2)
        ring_prob = round(rng.uniform(0.40, 0.70), 2)
    else:
        gnn_score = round(rng.uniform(0.05, 0.35), 2)
        ring_prob = round(rng.uniform(0.01, 0.20), 2)

    suspicious = []
    if graph_data.get("shared_doctor"):
        suspicious.append(graph_data.get("doctor_id", "doctor_D001"))
    if graph_data.get("shared_workshop"):
        suspicious.append(graph_data.get("workshop_id", "workshop_W001"))

    return {
        "gnn_score": gnn_score,
        "ring_probability": ring_prob,
        "suspicious_links": suspicious
    }

"""
InsureTrust AI — Ensemble Score Fusion + Routing
==================================================
Weighted combination of all model scores + RFI points.
Routes claims to appropriate review queue.
"""

from typing import Dict, Any


# Score weights
WEIGHTS = {
    "image": 0.30,
    "nlp": 0.25,
    "tabular": 0.25,
    "graph": 0.20,
}

# Routing thresholds
ROUTING_THRESHOLDS = [
    (0, 30, "AUTO_APPROVED", "green"),
    (31, 60, "MANUAL_REVIEW", "yellow"),
    (61, 79, "HIGH_RISK_REVIEW", "orange"),
    (80, 100, "AUTO_ESCALATED", "red"),
]


def compute_ensemble(
    image_result: dict,
    nlp_result: dict,
    tabular_result: dict,
    graph_result: dict,
    rfi_result: dict
) -> dict:
    """
    Compute final risk score from all model outputs + RFI points.
    Must complete in < 5ms.

    Formula:
    base_score = (image_score × 0.30 + nlp_score × 0.25 +
                  tabular_score × 0.25 + graph_score × 0.20) × 100
    final_score = min(100, base_score + total_rfi_points)
    """
    image_score = image_result.get("image_score", 0)
    nlp_score = nlp_result.get("nlp_score", 0)
    tabular_score = tabular_result.get("tabular_score", 0)
    graph_score = graph_result.get("graph_score", 0)
    total_rfi_points = rfi_result.get("total_rfi_points", 0)

    # Weighted sum
    base_score = (
        image_score * WEIGHTS["image"] +
        nlp_score * WEIGHTS["nlp"] +
        tabular_score * WEIGHTS["tabular"] +
        graph_score * WEIGHTS["graph"]
    ) * 100

    # Add RFI points
    final_score = min(100, round(base_score + total_rfi_points))

    # Determine routing
    routing = "MANUAL_REVIEW"
    routing_color = "yellow"
    for low, high, route, color in ROUTING_THRESHOLDS:
        if low <= final_score <= high:
            routing = route
            routing_color = color
            break

    return {
        "final_score": final_score,
        "routing": routing,
        "routing_color": routing_color,
        "base_score": round(base_score, 2),
        "rfi_points_added": total_rfi_points,
        "score_breakdown": {
            "image": round(image_score, 2),
            "nlp": round(nlp_score, 2),
            "tabular": round(tabular_score, 2),
            "graph": round(graph_score, 2),
        },
        "weights": WEIGHTS,
        "shap_values": tabular_result.get("shap_values", {}),
        "triggered_rfis": rfi_result.get("triggered_rfis", []),
        "ring_detected": graph_result.get("ring_detected", False),
        "ring_id": graph_result.get("ring_id"),
        "ring_members": graph_result.get("ring_members", []),
        "new_graph_nodes": graph_result.get("new_nodes", []),
        "new_graph_edges": graph_result.get("new_edges", []),
    }


def get_routing_label(score: float) -> str:
    """Get routing label for a given score."""
    for low, high, route, _ in ROUTING_THRESHOLDS:
        if low <= score <= high:
            return route
    return "MANUAL_REVIEW"


def get_routing_color(routing: str) -> str:
    """Get color for a routing label."""
    colors = {
        "AUTO_APPROVED": "green",
        "MANUAL_REVIEW": "yellow",
        "HIGH_RISK_REVIEW": "orange",
        "AUTO_ESCALATED": "red",
    }
    return colors.get(routing, "yellow")

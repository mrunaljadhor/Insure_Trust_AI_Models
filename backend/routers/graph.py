"""
InsureTrust AI — Graph Router
================================
GET /graph/data — Full serialized graph for D3.js
"""

from fastapi import APIRouter
from services.graph_engine import get_full_graph_data, get_ring_subgraph

router = APIRouter(prefix="/graph", tags=["graph"])


@router.get("/data")
async def get_graph_data():
    """
    Returns full serialized graph for D3.js visualization.
    {
      "nodes": [{"id": "...", "type": "claimant", "label": "...",
                 "risk_score": 87, "claim_count": 3}],
      "edges": [{"source": "...", "target": "...",
                 "relationship": "TREATED_BY"}]
    }
    """
    return get_full_graph_data()


@router.get("/ring/{ring_id}")
async def get_ring_data(ring_id: str):
    """Get subgraph for a specific fraud ring."""
    return get_ring_subgraph(ring_id)

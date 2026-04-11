"""
Pydantic schemas for InsureTrust AI API request/response validation.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime


# ─── Claim Submission ────────────────────────────────────────────────

class ClaimForm(BaseModel):
    claimant_name: str = Field(..., min_length=2, max_length=100)
    claimant_id: Optional[str] = None
    aadhaar_number: Optional[str] = None
    mobile_number: Optional[str] = None
    policy_id: str = Field(..., min_length=3)
    policy_start_date: Optional[str] = None
    policy_max_coverage: Optional[float] = None
    sum_insured: Optional[float] = None
    claim_amount: float = Field(..., gt=0)
    claim_date: str
    hospital_code: Optional[str] = None
    hospital_name: Optional[str] = None
    diagnosis_code: Optional[str] = None
    treatment_code: Optional[str] = None
    incident_description: Optional[str] = None
    incident_lat: Optional[float] = None
    incident_lng: Optional[float] = None
    doctor_id: Optional[str] = None
    workshop_id: Optional[str] = None
    witness_id: Optional[str] = None
    ip_address: Optional[str] = None
    claim_frequency: Optional[int] = 0
    weekend_claim: Optional[bool] = False


# ─── SSE Event ───────────────────────────────────────────────────────

class SSEEvent(BaseModel):
    step: str
    status: str
    ms: Optional[float] = 0
    claim_id: Optional[str] = None
    risk_score: Optional[float] = None
    routing: Optional[str] = None
    result: Optional[Dict[str, Any]] = None


# ─── Ensemble Result ─────────────────────────────────────────────────

class ScoreBreakdown(BaseModel):
    image: float
    nlp: float
    tabular: float
    graph: float


class EnsembleResult(BaseModel):
    final_score: float
    routing: str
    score_breakdown: ScoreBreakdown
    shap_values: Dict[str, float]
    triggered_rfis: List[Dict[str, Any]]
    ring_detected: bool
    ring_id: Optional[str] = None
    new_graph_nodes: List[Dict[str, Any]] = []
    new_graph_edges: List[Dict[str, Any]] = []


# ─── Graph Data ──────────────────────────────────────────────────────

class GraphNodeSchema(BaseModel):
    id: str
    type: str
    label: Optional[str] = None
    risk_score: Optional[float] = None
    claim_count: int = 0


class GraphEdgeSchema(BaseModel):
    source: str
    target: str
    relationship: str


class GraphDataResponse(BaseModel):
    nodes: List[GraphNodeSchema]
    edges: List[GraphEdgeSchema]


# ─── RFI ─────────────────────────────────────────────────────────────

class RFIResult(BaseModel):
    triggered: bool
    rfi_code: str
    description: str
    risk_points: int


class RFICheckResponse(BaseModel):
    triggered_rfis: List[RFIResult]
    total_rfi_points: int


# ─── LLM Summary ────────────────────────────────────────────────────

class LLMSummaryResponse(BaseModel):
    red_flags: List[str]
    recommended_action: str
    confidence_note: str
    adjuster_instructions: str


# ─── Adjuster Decision ──────────────────────────────────────────────

class AdjusterDecision(BaseModel):
    action: str = Field(..., pattern="^(APPROVE|ESCALATE|REJECT)$")
    reason: str = Field(..., min_length=5)
    adjuster_id: str = Field(..., min_length=1)
    override_confirmed: Optional[bool] = False


# ─── Dashboard Stats ────────────────────────────────────────────────

class DashboardStats(BaseModel):
    total_claims: int
    auto_approved: int
    manual_review: int
    high_risk: int
    auto_escalated: int
    rings_detected: int
    avg_processing_ms: float
    rfi_breakdown: Dict[str, int]


# ─── Audit Log ───────────────────────────────────────────────────────

class AuditLogEntry(BaseModel):
    id: int
    claim_id: str
    timestamp: datetime
    event_type: str
    payload_json: Optional[Dict[str, Any]] = None
    processing_ms: Optional[float] = None
    model_version: Optional[str] = None

    class Config:
        from_attributes = True


# ─── Claim Response ─────────────────────────────────────────────────

class ClaimResponse(BaseModel):
    id: str
    claimant_name_masked: Optional[str] = None
    claimant_id: Optional[str] = None
    policy_id: Optional[str] = None
    claim_amount: float
    claim_date: Optional[datetime] = None
    hospital_name: Optional[str] = None
    risk_score: Optional[float] = None
    routing: Optional[str] = None
    status: Optional[str] = None
    ring_detected: Optional[bool] = False
    ring_id: Optional[str] = None
    image_score: Optional[float] = None
    nlp_score: Optional[float] = None
    tabular_score: Optional[float] = None
    graph_score: Optional[float] = None
    rfi_total_points: Optional[int] = None
    shap_values: Optional[Dict[str, float]] = None
    triggered_rfis: Optional[List[Dict[str, Any]]] = None
    score_breakdown: Optional[Dict[str, float]] = None
    image_result: Optional[Dict[str, Any]] = None
    nlp_result: Optional[Dict[str, Any]] = None
    graph_result: Optional[Dict[str, Any]] = None
    llm_summary: Optional[Dict[str, Any]] = None
    damage_photo_path: Optional[str] = None
    processing_ms: Optional[float] = None
    created_at: Optional[datetime] = None
    adjuster_action: Optional[str] = None
    adjuster_reason: Optional[str] = None

    class Config:
        from_attributes = True

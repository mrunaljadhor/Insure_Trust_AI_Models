"""
SQLAlchemy database models for InsureTrust AI.
Tables: Claim, GraphNode, GraphEdge, AuditLog, Feedback
"""

from sqlalchemy import (
    create_engine, Column, Integer, String, Float, DateTime,
    Text, Boolean, JSON, ForeignKey, Index
)
from sqlalchemy.orm import sessionmaker, relationship, DeclarativeBase
from datetime import datetime
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./insuretrust.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass


def get_db():
    """Dependency: yields a DB session, auto-closes."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class Claim(Base):
    __tablename__ = "claims"

    id = Column(String, primary_key=True, index=True)
    claimant_name_masked = Column(String, nullable=False)          # "****rma"
    claimant_id = Column(String, nullable=False, index=True)       # internal ID
    aadhaar_hash = Column(String, nullable=True)                   # SHA-256
    aadhaar_last4 = Column(String(4), nullable=True)
    mobile_hash = Column(String, nullable=True)                    # SHA-256
    mobile_last4 = Column(String(4), nullable=True)
    policy_id = Column(String, nullable=False, index=True)
    policy_start_date = Column(DateTime, nullable=True)
    policy_max_coverage = Column(Float, nullable=True)
    claim_amount = Column(Float, nullable=False)
    claim_date = Column(DateTime, nullable=False)
    hospital_code = Column(String, nullable=True)
    hospital_name = Column(String, nullable=True)
    diagnosis_code = Column(String, nullable=True)
    treatment_code = Column(String, nullable=True)
    incident_description = Column(Text, nullable=True)
    incident_lat = Column(Float, nullable=True)
    incident_lng = Column(Float, nullable=True)
    doctor_id = Column(String, nullable=True)
    workshop_id = Column(String, nullable=True)
    witness_id = Column(String, nullable=True)
    ip_address = Column(String, nullable=True)
    sum_insured = Column(Float, nullable=True)

    # Scoring results
    risk_score = Column(Float, nullable=True)
    routing = Column(String, nullable=True)                        # AUTO_APPROVED, MANUAL_REVIEW, etc.
    image_score = Column(Float, nullable=True)
    nlp_score = Column(Float, nullable=True)
    tabular_score = Column(Float, nullable=True)
    graph_score = Column(Float, nullable=True)
    rfi_total_points = Column(Integer, nullable=True)
    ring_detected = Column(Boolean, default=False)
    ring_id = Column(String, nullable=True)

    # Score details stored as JSON
    shap_values = Column(JSON, nullable=True)
    triggered_rfis = Column(JSON, nullable=True)
    score_breakdown = Column(JSON, nullable=True)
    image_result = Column(JSON, nullable=True)
    nlp_result = Column(JSON, nullable=True)
    graph_result = Column(JSON, nullable=True)

    # LLM summary (populated async)
    llm_summary = Column(JSON, nullable=True)

    # Adjuster decision
    status = Column(String, default="PENDING")                     # PENDING, APPROVED, ESCALATED, REJECTED
    adjuster_id = Column(String, nullable=True)
    adjuster_action = Column(String, nullable=True)
    adjuster_reason = Column(Text, nullable=True)
    adjuster_action_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    processing_ms = Column(Float, nullable=True)

    # Photo path
    damage_photo_path = Column(String, nullable=True)
    supporting_doc_path = Column(String, nullable=True)

    # Relationships
    audit_logs = relationship("AuditLog", back_populates="claim", lazy="dynamic")
    feedbacks = relationship("Feedback", back_populates="claim", lazy="dynamic")


class GraphNode(Base):
    __tablename__ = "graph_nodes"

    id = Column(String, primary_key=True)
    node_type = Column(String, nullable=False, index=True)         # claimant, doctor, workshop, witness, mobile, ip_address
    label = Column(String, nullable=True)
    risk_score = Column(Float, nullable=True)
    claim_count = Column(Integer, default=0)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class GraphEdge(Base):
    __tablename__ = "graph_edges"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_id = Column(String, ForeignKey("graph_nodes.id"), nullable=False, index=True)
    target_id = Column(String, ForeignKey("graph_nodes.id"), nullable=False, index=True)
    relationship = Column(String, nullable=False)                  # TREATED_BY, REPAIRED_AT, etc.
    claim_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    claim_id = Column(String, ForeignKey("claims.id"), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    event_type = Column(String, nullable=False, index=True)
    payload_json = Column(JSON, nullable=True)
    processing_ms = Column(Float, nullable=True)
    model_version = Column(String, default="stub-v1.0")

    claim = relationship("Claim", back_populates="audit_logs")

    # Indexes for fast querying
    __table_args__ = (
        Index("idx_audit_claim_time", "claim_id", "timestamp"),
    )


class Feedback(Base):
    __tablename__ = "feedbacks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    claim_id = Column(String, ForeignKey("claims.id"), nullable=False, index=True)
    adjuster_id = Column(String, nullable=False)
    action = Column(String, nullable=False)                        # APPROVE, ESCALATE, REJECT
    reason = Column(Text, nullable=True)
    override_confirmed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    claim = relationship("Claim", back_populates="feedbacks")


def init_db():
    """Create all tables."""
    Base.metadata.create_all(bind=engine)

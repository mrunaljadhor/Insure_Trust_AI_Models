"""
InsureTrust AI — FastAPI Application Entry Point
===================================================
Real-time fraudulent insurance claim detection platform.
"""

import os
import sys
import io
from contextlib import asynccontextmanager

# Fix Windows console encoding
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from models.database import init_db, SessionLocal
from routers import claims, graph, reports, dashboard


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    print("=" * 60)
    print("  [SHIELD] InsureTrust AI - Starting Up")
    print("=" * 60)

    # Initialize database
    init_db()
    print("[STARTUP] Database tables created.")

    # Seed data if DB is empty
    db = SessionLocal()
    try:
        from data.seed_dataset import seed_database
        seed_database(db)
    except Exception as e:
        print(f"[STARTUP] Seed error: {e}")
    finally:
        db.close()

    # Create uploads directory
    os.makedirs("uploads", exist_ok=True)

    print("[STARTUP] InsureTrust AI ready on port 8000")
    print("=" * 60)

    yield

    print("[SHUTDOWN] InsureTrust AI shutting down.")


app = FastAPI(
    title="InsureTrust AI",
    description="Real-time fraudulent insurance claim detection platform",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Register routers
app.include_router(claims.router)
app.include_router(graph.router)
app.include_router(reports.router)
app.include_router(dashboard.router)


# Audit route
from fastapi import Depends
from sqlalchemy.orm import Session
from models.database import get_db
from services.audit_logger import get_claim_audit_trail


@app.get("/audit/{claim_id}", tags=["audit"])
async def get_audit_trail(claim_id: str, db: Session = Depends(get_db)):
    """Get full chronological audit trail for a claim (IRDAI-required)."""
    trail = get_claim_audit_trail(db, claim_id)
    return {"claim_id": claim_id, "audit_trail": trail}


@app.get("/", tags=["health"])
async def root():
    """Health check endpoint."""
    return {
        "name": "InsureTrust AI",
        "version": "1.0.0",
        "status": "operational",
        "description": "Real-time fraudulent insurance claim detection platform"
    }


@app.get("/health", tags=["health"])
async def health_check():
    """Detailed health check."""
    from services.graph_engine import get_graph
    g = get_graph()
    return {
        "status": "healthy",
        "database": "connected",
        "graph_nodes": g.number_of_nodes(),
        "graph_edges": g.number_of_edges(),
    }

"""
InsureTrust AI — Reports Router
==================================
GET /reports/{claim_id}/pdf — Generate PDF audit report
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from io import BytesIO
from datetime import datetime

from models.database import get_db, Claim
from services.audit_logger import get_claim_audit_trail

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/{claim_id}/pdf")
async def generate_pdf_report(claim_id: str, db: Session = Depends(get_db)):
    """Generate IRDAI-compliant PDF audit report for a claim."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch, mm
    from reportlab.lib.colors import HexColor, black, white, red, green, orange
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        HRFlowable, PageBreak
    )
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

    claim = db.query(Claim).filter(Claim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=20 * mm, rightMargin=20 * mm,
        topMargin=20 * mm, bottomMargin=25 * mm
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle', parent=styles['Heading1'],
        fontSize=22, textColor=HexColor('#1a1a2e'),
        spaceAfter=6, alignment=TA_CENTER
    )
    subtitle_style = ParagraphStyle(
        'Subtitle', parent=styles['Normal'],
        fontSize=10, textColor=HexColor('#666666'),
        alignment=TA_CENTER, spaceAfter=16
    )
    section_style = ParagraphStyle(
        'Section', parent=styles['Heading2'],
        fontSize=14, textColor=HexColor('#16213e'),
        spaceBefore=16, spaceAfter=8,
        borderColor=HexColor('#0f3460'),
        borderWidth=1, borderPadding=4
    )
    body_style = ParagraphStyle(
        'Body', parent=styles['Normal'],
        fontSize=10, leading=14
    )
    small_style = ParagraphStyle(
        'Small', parent=styles['Normal'],
        fontSize=8, textColor=HexColor('#888888'),
        alignment=TA_CENTER
    )

    elements = []

    # ─── 1. Header ────────────────────────────────────────────────
    elements.append(Paragraph("🛡️ InsureTrust AI", title_style))
    elements.append(Paragraph(
        f"Claim ID: {claim.id}  |  Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
        subtitle_style
    ))
    elements.append(Paragraph(
        "IRDAI Anti-Fraud Policy 2025 Compliant — Confidential",
        ParagraphStyle('Conf', parent=small_style, textColor=HexColor('#cc0000'))
    ))
    elements.append(HRFlowable(width="100%", color=HexColor('#0f3460'), thickness=2))
    elements.append(Spacer(1, 12))

    # ─── 2. Claim Summary ─────────────────────────────────────────
    elements.append(Paragraph("📋 Claim Summary", section_style))
    summary_data = [
        ["Claimant", claim.claimant_name_masked or "N/A"],
        ["Policy ID", claim.policy_id or "N/A"],
        ["Claim Amount", f"₹{claim.claim_amount:,.2f}" if claim.claim_amount else "N/A"],
        ["Claim Date", claim.claim_date.strftime("%Y-%m-%d") if claim.claim_date else "N/A"],
        ["Hospital", claim.hospital_name or "N/A"],
        ["Hospital Code", claim.hospital_code or "N/A"],
    ]
    t = Table(summary_data, colWidths=[120, 350])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), HexColor('#f0f0f5')),
        ('TEXTCOLOR', (0, 0), (0, -1), HexColor('#333333')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#cccccc')),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 12))

    # ─── 3. Risk Score ─────────────────────────────────────────────
    elements.append(Paragraph("🎯 Risk Assessment", section_style))
    score = claim.risk_score or 0
    routing = claim.routing or "PENDING"
    score_color = (
        '#27ae60' if score <= 30 else
        '#f39c12' if score <= 60 else
        '#e67e22' if score <= 79 else
        '#e74c3c'
    )
    elements.append(Paragraph(
        f'<font size="28" color="{score_color}"><b>{int(score)}</b></font>'
        f'<font size="12" color="#666666"> / 100</font>',
        ParagraphStyle('Score', parent=body_style, alignment=TA_CENTER)
    ))
    elements.append(Paragraph(
        f'<font size="14" color="{score_color}"><b>{routing}</b></font>',
        ParagraphStyle('Routing', parent=body_style, alignment=TA_CENTER)
    ))
    elements.append(Spacer(1, 12))

    # ─── 4. RFI Violations ────────────────────────────────────────
    elements.append(Paragraph("🚩 RFI Violations", section_style))
    rfis = claim.triggered_rfis or []
    if rfis:
        rfi_data = [["Code", "Description", "Points"]]
        for rfi in rfis:
            rfi_data.append([
                rfi.get("rfi_code", ""),
                rfi.get("description", ""),
                str(rfi.get("risk_points", 0))
            ])
        rfi_data.append(["", "Total RFI Points", str(claim.rfi_total_points or 0)])
        t = Table(rfi_data, colWidths=[70, 330, 70])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#e74c3c')),
            ('TEXTCOLOR', (0, 0), (-1, 0), white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#cccccc')),
            ('BACKGROUND', (0, -1), (-1, -1), HexColor('#fff0f0')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ]))
        elements.append(t)
    else:
        elements.append(Paragraph("No RFI violations triggered.", body_style))
    elements.append(Spacer(1, 12))

    # ─── 5. Score Breakdown ───────────────────────────────────────
    elements.append(Paragraph("📊 Score Breakdown", section_style))
    breakdown = claim.score_breakdown or {}
    weights = {"image": 0.30, "nlp": 0.25, "tabular": 0.25, "graph": 0.20}
    breakdown_data = [["Layer", "Score", "Weight", "Contribution"]]
    for layer in ["image", "nlp", "tabular", "graph"]:
        s = breakdown.get(layer, 0)
        w = weights[layer]
        breakdown_data.append([
            layer.upper(),
            f"{s:.2f}",
            f"{w:.0%}",
            f"{s * w * 100:.1f}"
        ])
    t = Table(breakdown_data, colWidths=[100, 100, 100, 170])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#16213e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#cccccc')),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 12))

    # ─── 6. Fraud Ring Connections ────────────────────────────────
    elements.append(Paragraph("🕸️ Fraud Ring Analysis", section_style))
    if claim.ring_detected:
        graph_result = claim.graph_result or {}
        elements.append(Paragraph(
            f'<font color="#e74c3c"><b>⚠ FRAUD RING DETECTED — {claim.ring_id}</b></font>',
            ParagraphStyle('Ring', parent=body_style, fontSize=12)
        ))
        members = graph_result.get("ring_members", [])
        if members:
            elements.append(Paragraph(f"Ring Members: {', '.join(members[:10])}", body_style))
        elements.append(Paragraph(
            f"Connected Claims: {graph_result.get('connected_claims', 'N/A')}",
            body_style
        ))
    else:
        elements.append(Paragraph("No fraud ring connections detected.", body_style))
    elements.append(Spacer(1, 12))

    # ─── 7. Adjuster Decision ────────────────────────────────────
    elements.append(Paragraph("👤 Adjuster Decision", section_style))
    if claim.adjuster_action:
        elements.append(Paragraph(f"Action: {claim.adjuster_action}", body_style))
        elements.append(Paragraph(f"Reason: {claim.adjuster_reason or 'N/A'}", body_style))
        elements.append(Paragraph(
            f"Timestamp: {claim.adjuster_action_at.isoformat() if claim.adjuster_action_at else 'N/A'}",
            body_style
        ))
    else:
        elements.append(Paragraph("Pending adjuster review.", body_style))
    elements.append(Spacer(1, 12))

    # ─── 8. Audit Trail ──────────────────────────────────────────
    elements.append(Paragraph("📝 Full Audit Trail", section_style))
    audit_trail = get_claim_audit_trail(db, claim_id)
    if audit_trail:
        audit_data = [["Event", "Timestamp", "Details"]]
        for entry in audit_trail[:20]:  # Limit to 20 entries
            details = ""
            payload = entry.get("payload_json", {})
            if payload:
                details = str(payload)[:80]
            audit_data.append([
                entry.get("event_type", ""),
                entry.get("timestamp", "")[:19],
                details
            ])
        t = Table(audit_data, colWidths=[120, 130, 220])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#2c3e50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#cccccc')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        elements.append(t)
    else:
        elements.append(Paragraph("No audit trail entries found.", body_style))

    # ─── 9. Footer ────────────────────────────────────────────────
    elements.append(Spacer(1, 30))
    elements.append(HRFlowable(width="100%", color=HexColor('#cccccc'), thickness=1))
    elements.append(Paragraph(
        "Generated by InsureTrust AI. AI decisions require human oversight "
        "as per IRDAI Anti-Fraud Policy 2025.",
        small_style
    ))

    # Build PDF
    doc.build(elements)
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=InsureTrust_Report_{claim_id}.pdf"
        }
    )

"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import RiskGauge from "@/components/RiskGauge";
import ShapWaterfall from "@/components/ShapWaterfall";
import RFIBadges from "@/components/RFIBadges";
import FraudRingGraph from "@/components/FraudRingGraph";
import GradCamOverlay from "@/components/GradCamOverlay";
import AdjusterPanel from "@/components/AdjusterPanel";
import ClaimSummary from "@/components/ClaimSummary";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function ClaimDetailPage() {
  const params = useParams();
  const claimId = params.id as string;
  const [claim, setClaim] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (claimId) {
      fetchClaim();
    }
  }, [claimId]);

  const fetchClaim = async () => {
    try {
      const res = await fetch(`${API_URL}/claims/${claimId}`);
      if (res.ok) {
        const data = await res.json();
        setClaim(data);
      }
    } catch (e) {
      console.error("Failed to fetch claim:", e);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-blue-500/30 border-t-blue-500 rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-500">Loading claim {claimId}...</p>
        </div>
      </div>
    );
  }

  if (!claim) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="text-6xl mb-4">🔍</div>
          <h2 className="text-xl font-bold text-gray-300 mb-2">Claim Not Found</h2>
          <p className="text-gray-500">Claim ID: {claimId}</p>
          <a href="/" className="text-blue-400 hover:underline mt-4 inline-block">← Back to Upload</a>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-fade-in-up">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <a href="/" className="text-sm text-gray-500 hover:text-blue-400 transition-colors mb-1 inline-block">
            ← Back
          </a>
          <h2 className="text-2xl font-bold text-gray-200">
            Claim {claim.id}
          </h2>
          <div className="flex items-center gap-3 mt-2">
            <span className="text-sm text-gray-500">{claim.claimant_name_masked}</span>
            <span className="text-sm text-gray-600">|</span>
            <span className="text-sm text-gray-500">₹{claim.claim_amount?.toLocaleString()}</span>
            <span className="text-sm text-gray-600">|</span>
            <span className="text-sm text-gray-500">{claim.hospital_name}</span>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <span className={`px-4 py-1.5 rounded-full text-sm font-semibold ${
            claim.routing === "AUTO_APPROVED" ? "badge-green" :
            claim.routing === "MANUAL_REVIEW" ? "badge-yellow" :
            claim.routing === "HIGH_RISK_REVIEW" ? "badge-orange" :
            "badge-red"
          }`}>
            {claim.routing?.replace(/_/g, " ")}
          </span>
          <a
            href={`${API_URL}/reports/${claimId}/pdf`}
            target="_blank"
            className="px-4 py-1.5 rounded-xl bg-gradient-to-r from-blue-600 to-purple-600 text-white text-sm font-medium hover:from-blue-500 hover:to-purple-500 transition-all"
          >
            📄 PDF Report
          </a>
        </div>
      </div>

      {/* Score Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="glass-card flex flex-col items-center justify-center">
          <h3 className="text-lg font-semibold mb-4 text-gray-300">Risk Score</h3>
          <RiskGauge score={claim.risk_score || 0} routing={claim.routing || "PENDING"} />
        </div>
        <div className="glass-card">
          <h3 className="text-lg font-semibold mb-4 text-gray-300">SHAP Analysis</h3>
          <ShapWaterfall shapValues={claim.shap_values || {}} />
        </div>
        <div className="glass-card">
          <h3 className="text-lg font-semibold mb-4 text-gray-300">RFI Violations</h3>
          <RFIBadges rfis={claim.triggered_rfis || []} />
        </div>
      </div>

      {/* Fraud Ring Graph */}
      <div className="glass-card">
        <FraudRingGraph
          ringDetected={claim.ring_detected}
          ringId={claim.ring_id}
          newNodes={[]}
          newEdges={[]}
        />
      </div>

      {/* Details Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="glass-card">
          <GradCamOverlay imageResult={claim.image_result} />
        </div>
        <div className="glass-card">
          <AdjusterPanel
            claimId={claimId}
            riskScore={claim.risk_score || 0}
            routing={claim.routing || "PENDING"}
          />
        </div>
        <div className="glass-card">
          <ClaimSummary claimId={claimId} />
        </div>
      </div>

      {/* Claim Details */}
      <div className="glass-card">
        <h3 className="text-lg font-semibold text-gray-300 mb-4">Claim Details</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { label: "Policy ID", value: claim.policy_id },
            { label: "Claim Date", value: claim.claim_date?.slice(0, 10) },
            { label: "Hospital", value: claim.hospital_name },
            { label: "Hospital Code", value: claim.hospital_code },
            { label: "Diagnosis", value: claim.diagnosis_code },
            { label: "Treatment", value: claim.treatment_code },
            { label: "Aadhaar", value: claim.aadhaar_display || "N/A" },
            { label: "Processing", value: claim.processing_ms ? `${Math.round(claim.processing_ms)}ms` : "N/A" },
          ].map((item) => (
            <div key={item.label} className="bg-white/5 rounded-xl p-3">
              <p className="text-[10px] text-gray-500 uppercase tracking-wider mb-1">{item.label}</p>
              <p className="text-sm text-gray-300 font-medium">{item.value || "N/A"}</p>
            </div>
          ))}
        </div>
        {claim.incident_description && (
          <div className="mt-4 bg-white/5 rounded-xl p-4">
            <p className="text-[10px] text-gray-500 uppercase tracking-wider mb-2">Incident Description</p>
            <p className="text-sm text-gray-300">{claim.incident_description}</p>
          </div>
        )}
      </div>
    </div>
  );
}

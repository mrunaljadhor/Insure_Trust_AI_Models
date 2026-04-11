"use client";

import { useState } from "react";
import ClaimUploader from "@/components/ClaimUploader";
import StreamingProgress from "@/components/StreamingProgress";
import RiskGauge from "@/components/RiskGauge";
import ShapWaterfall from "@/components/ShapWaterfall";
import RFIBadges from "@/components/RFIBadges";
import FraudRingGraph from "@/components/FraudRingGraph";
import GradCamOverlay from "@/components/GradCamOverlay";
import AdjusterPanel from "@/components/AdjusterPanel";
import ClaimSummary from "@/components/ClaimSummary";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function Home() {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [steps, setSteps] = useState<any[]>([]);
  const [result, setResult] = useState<any>(null);
  const [claimId, setClaimId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (formData: FormData) => {
    setIsAnalyzing(true);
    setSteps([]);
    setResult(null);
    setClaimId(null);
    setError(null);

    try {
      const response = await fetch(`${API_URL}/claims/submit`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Server error: ${response.status}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) throw new Error("No response body");

      let buffer = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const event = JSON.parse(line.slice(6));
              
              if (event.step === "error") {
                setError(event.message);
                setIsAnalyzing(false);
                return;
              }

              setSteps(prev => {
                const existing = prev.findIndex(s => s.step === event.step);
                if (existing >= 0) {
                  const updated = [...prev];
                  updated[existing] = event;
                  return updated;
                }
                return [...prev, event];
              });

              if (event.step === "complete" && event.status === "done") {
                setResult(event.result);
                setClaimId(event.claim_id);
                setIsAnalyzing(false);
              }
            } catch (e) {
              // Skip unparseable lines
            }
          }
        }
      }
    } catch (err: any) {
      setError(err.message);
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="space-y-8 animate-fade-in-up">
      {/* Hero Section */}
      <section className="text-center py-8">
        <h2 className="text-4xl font-bold mb-3 bg-gradient-to-r from-blue-400 via-purple-400 to-cyan-400 bg-clip-text text-transparent">
          AI-Powered Fraud Detection
        </h2>
        <p className="text-gray-400 text-lg max-w-2xl mx-auto">
          Upload insurance claims for real-time multi-model analysis. Detect individual fraud, 
          organized rings, and IRDAI red flag violations in under 500ms.
        </p>
      </section>

      {/* Uploader */}
      <ClaimUploader onSubmit={handleSubmit} isAnalyzing={isAnalyzing} error={error} />

      {/* Streaming Progress */}
      {steps.length > 0 && (
        <div className="animate-fade-in-up">
          <StreamingProgress steps={steps} />
        </div>
      )}

      {/* Results */}
      {result && claimId && (
        <div className="space-y-8 animate-fade-in-up">
          {/* Top Row: Gauge + SHAP + RFIs */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="glass-card flex flex-col items-center justify-center">
              <h3 className="text-lg font-semibold mb-4 text-gray-300">Risk Score</h3>
              <RiskGauge score={result.final_score} routing={result.routing} />
            </div>
            <div className="glass-card">
              <h3 className="text-lg font-semibold mb-4 text-gray-300">SHAP Analysis</h3>
              <ShapWaterfall shapValues={result.shap_values} />
            </div>
            <div className="glass-card">
              <h3 className="text-lg font-semibold mb-4 text-gray-300">RFI Violations</h3>
              <RFIBadges rfis={result.triggered_rfis} />
            </div>
          </div>

          {/* Fraud Ring Graph — Full Width */}
          <div className="glass-card">
            <FraudRingGraph
              ringDetected={result.ring_detected}
              ringId={result.ring_id}
              newNodes={result.new_graph_nodes}
              newEdges={result.new_graph_edges}
            />
          </div>

          {/* Bottom Row: GradCam + Adjuster + Summary */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="glass-card">
              <GradCamOverlay imageResult={result.image_result} />
            </div>
            <div className="glass-card">
              <AdjusterPanel
                claimId={claimId}
                riskScore={result.final_score}
                routing={result.routing}
              />
            </div>
            <div className="glass-card">
              <ClaimSummary claimId={claimId} />
            </div>
          </div>

          {/* Actions */}
          <div className="flex justify-center gap-4">
            <a
              href={`${API_URL}/reports/${claimId}/pdf`}
              target="_blank"
              className="px-6 py-3 rounded-xl bg-gradient-to-r from-blue-600 to-purple-600 text-white font-medium hover:from-blue-500 hover:to-purple-500 transition-all shadow-lg shadow-blue-500/25 flex items-center gap-2"
            >
              📄 Download PDF Report
            </a>
            <a
              href={`/claim/${claimId}`}
              className="px-6 py-3 rounded-xl border border-blue-500/30 text-blue-400 font-medium hover:bg-blue-500/10 transition-all flex items-center gap-2"
            >
              🔍 View Full Details
            </a>
          </div>
        </div>
      )}
    </div>
  );
}

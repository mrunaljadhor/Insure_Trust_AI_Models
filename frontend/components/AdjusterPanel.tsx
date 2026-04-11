"use client";

import { useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface AdjusterPanelProps {
  claimId: string;
  riskScore: number;
  routing: string;
}

export default function AdjusterPanel({ claimId, riskScore, routing }: AdjusterPanelProps) {
  const [reason, setReason] = useState("");
  const [showConfirm, setShowConfirm] = useState(false);
  const [pendingAction, setPendingAction] = useState<string | null>(null);
  const [actionTaken, setActionTaken] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const getRoutingColor = (r: string) => {
    switch (r) {
      case "AUTO_APPROVED": return "text-green-400";
      case "MANUAL_REVIEW": return "text-yellow-400";
      case "HIGH_RISK_REVIEW": return "text-orange-400";
      case "AUTO_ESCALATED": return "text-red-400";
      default: return "text-gray-400";
    }
  };

  const handleAction = async (action: string, overrideConfirmed = false) => {
    if (!reason.trim()) return;

    // Check if approve needs confirmation
    if (action === "APPROVE" && riskScore > 75 && !overrideConfirmed) {
      setPendingAction(action);
      setShowConfirm(true);
      return;
    }

    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/claims/${claimId}/decision`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          action,
          reason: reason.trim(),
          adjuster_id: "ADJ_001",
          override_confirmed: overrideConfirmed,
        }),
      });

      if (res.ok) {
        setActionTaken(action);
      } else {
        const err = await res.json();
        alert(err.detail || "Action failed");
      }
    } catch (e) {
      alert("Failed to submit decision");
    } finally {
      setLoading(false);
      setShowConfirm(false);
    }
  };

  if (actionTaken) {
    return (
      <div className="flex flex-col items-center justify-center h-full py-8">
        <div className="text-4xl mb-3">
          {actionTaken === "APPROVE" ? "✅" : actionTaken === "REJECT" ? "❌" : "⚠️"}
        </div>
        <p className="text-lg font-semibold text-gray-200 mb-1">
          Claim {actionTaken === "APPROVE" ? "Approved" : actionTaken === "REJECT" ? "Rejected" : "Escalated"}
        </p>
        <p className="text-sm text-gray-500 text-center max-w-xs">
          Decision recorded and audit trail updated.
        </p>
        <div className={`mt-4 px-4 py-1.5 rounded-full text-sm font-semibold
          ${actionTaken === "APPROVE" ? "badge-green" : actionTaken === "REJECT" ? "badge-red" : "badge-orange"}`}>
          {actionTaken}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-gray-300 flex items-center gap-2">
        👤 Adjuster Panel
      </h3>

      {/* AI recommendation */}
      <div className="bg-white/5 rounded-xl p-3 space-y-1">
        <div className="flex items-center justify-between">
          <span className="text-xs text-gray-500">AI Confidence</span>
          <span className={`text-sm font-bold ${getRoutingColor(routing)}`}>
            {riskScore}%
          </span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-xs text-gray-500">Recommended</span>
          <span className={`text-sm font-semibold ${getRoutingColor(routing)}`}>
            {routing?.replace(/_/g, " ")}
          </span>
        </div>
      </div>

      {/* Reason textarea */}
      <div>
        <label className="block text-xs text-gray-500 mb-1">Decision Reason *</label>
        <textarea
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          placeholder="Enter reason for decision..."
          rows={3}
          className="w-full px-3 py-2 rounded-xl bg-white/5 border border-white/10 text-gray-200 placeholder-gray-600 text-sm focus:border-blue-500/50 focus:outline-none resize-none"
        />
      </div>

      {/* Action buttons */}
      <div className="grid grid-cols-3 gap-2">
        <button
          onClick={() => handleAction("APPROVE")}
          disabled={!reason.trim() || loading}
          className="px-3 py-2.5 rounded-xl text-sm font-semibold bg-green-500/15 text-green-400 border border-green-500/20 hover:bg-green-500/25 transition-all disabled:opacity-40 disabled:cursor-not-allowed"
        >
          ✓ Approve
        </button>
        <button
          onClick={() => handleAction("ESCALATE")}
          disabled={!reason.trim() || loading}
          className="px-3 py-2.5 rounded-xl text-sm font-semibold bg-orange-500/15 text-orange-400 border border-orange-500/20 hover:bg-orange-500/25 transition-all disabled:opacity-40 disabled:cursor-not-allowed"
        >
          ⚠ Escalate
        </button>
        <button
          onClick={() => handleAction("REJECT")}
          disabled={!reason.trim() || loading}
          className="px-3 py-2.5 rounded-xl text-sm font-semibold bg-red-500/15 text-red-400 border border-red-500/20 hover:bg-red-500/25 transition-all disabled:opacity-40 disabled:cursor-not-allowed"
        >
          ✗ Reject
        </button>
      </div>

      {/* Override confirmation modal */}
      {showConfirm && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-[100]">
          <div className="glass-card max-w-md mx-4 p-6 space-y-4 animate-fade-in-up">
            <div className="text-center">
              <div className="text-4xl mb-3">⚠️</div>
              <h3 className="text-lg font-bold text-gray-200 mb-2">High-Risk Override</h3>
              <p className="text-sm text-gray-400">
                This claim scores <span className="text-red-400 font-bold">{riskScore}/100</span>.
                Are you sure you want to approve it?
              </p>
            </div>
            <div className="flex gap-3 justify-center">
              <button
                onClick={() => setShowConfirm(false)}
                className="px-5 py-2 rounded-xl border border-white/10 text-gray-400 hover:bg-white/5 transition-all text-sm"
              >
                Cancel
              </button>
              <button
                onClick={() => handleAction("APPROVE", true)}
                className="px-5 py-2 rounded-xl bg-red-500/20 text-red-400 border border-red-500/30 hover:bg-red-500/30 transition-all text-sm font-semibold"
              >
                Confirm Override
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

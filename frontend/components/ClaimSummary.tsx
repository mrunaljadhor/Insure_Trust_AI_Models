"use client";

import { useEffect, useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface ClaimSummaryProps {
  claimId: string;
}

export default function ClaimSummary({ claimId }: ClaimSummaryProps) {
  const [summary, setSummary] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [retryCount, setRetryCount] = useState(0);

  useEffect(() => {
    const fetchSummary = async () => {
      try {
        const res = await fetch(`${API_URL}/claims/${claimId}/summary`);
        const data = await res.json();

        if (data.status === "ready" && data.summary) {
          setSummary(data.summary);
          setLoading(false);
        } else {
          // Retry in 3 seconds
          if (retryCount < 10) {
            setTimeout(() => setRetryCount((c) => c + 1), 3000);
          } else {
            setSummary({
              red_flags: ["Manual review required — AI summary unavailable"],
              recommended_action: "REVIEW",
              confidence_note: "Summary generation timed out. Review raw scores.",
              adjuster_instructions: "Please review all flagged indicators manually.",
            });
            setLoading(false);
          }
        }
      } catch {
        setSummary({
          red_flags: ["Manual review required — AI summary unavailable"],
          recommended_action: "REVIEW",
          confidence_note: "Failed to load summary. Review raw scores.",
          adjuster_instructions: "Please review all flagged indicators manually.",
        });
        setLoading(false);
      }
    };

    fetchSummary();
  }, [claimId, retryCount]);

  const getActionColor = (action: string) => {
    switch (action) {
      case "APPROVE": return "badge-green";
      case "REVIEW": return "badge-yellow";
      case "ESCALATE": return "badge-orange";
      case "REJECT": return "badge-red";
      default: return "badge-yellow";
    }
  };

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-gray-300 flex items-center gap-2">
        🤖 AI Summary
        {loading && <span className="text-xs text-blue-400 animate-pulse">(loading...)</span>}
      </h3>

      {loading ? (
        /* Skeleton loader */
        <div className="space-y-3">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="skeleton h-4 rounded" style={{ width: `${85 - i * 10}%` }} />
          ))}
          <div className="skeleton h-8 w-32 rounded-full mt-4" />
          <div className="skeleton h-12 rounded mt-2" />
        </div>
      ) : summary ? (
        <div className="space-y-4">
          {/* Red flags */}
          <div className="space-y-2">
            <p className="text-xs text-red-400/70 uppercase tracking-wider font-semibold">Red Flags</p>
            <ul className="space-y-1.5">
              {summary.red_flags?.map((flag: string, i: number) => (
                <li
                  key={i}
                  className="flex items-start gap-2 text-sm text-gray-300 animate-fade-in-up"
                  style={{ animationDelay: `${i * 100}ms` }}
                >
                  <span className="text-red-400 mt-0.5 flex-shrink-0">🚩</span>
                  <span>{flag}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Recommended action */}
          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-500">Recommended:</span>
            <span className={`px-3 py-1 rounded-full text-xs font-semibold ${getActionColor(summary.recommended_action)}`}>
              {summary.recommended_action}
            </span>
          </div>

          {/* Confidence note */}
          <p className="text-xs text-gray-500 italic">{summary.confidence_note}</p>

          {/* Adjuster instructions */}
          <div className="bg-white/5 rounded-xl p-3 border-l-2 border-blue-500/50">
            <p className="text-xs text-blue-400/70 uppercase tracking-wider font-semibold mb-1">
              Adjuster Instructions
            </p>
            <p className="text-sm text-gray-300">{summary.adjuster_instructions}</p>
          </div>
        </div>
      ) : null}
    </div>
  );
}

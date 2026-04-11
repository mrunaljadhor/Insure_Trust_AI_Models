"use client";

import { useEffect, useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface DashboardStats {
  total_claims: number;
  auto_approved: number;
  manual_review: number;
  high_risk: number;
  auto_escalated: number;
  rings_detected: number;
  avg_processing_ms: number;
  rfi_breakdown: Record<string, number>;
  recent_claims: any[];
}

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, 10000);
    return () => clearInterval(interval);
  }, []);

  const fetchStats = async () => {
    try {
      const res = await fetch(`${API_URL}/dashboard/stats`);
      const data = await res.json();
      setStats(data);
    } catch {
      console.error("Failed to fetch stats");
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-blue-500/30 border-t-blue-500 rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-500">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (!stats) return null;

  const routingData = [
    { label: "Auto Approved", value: stats.auto_approved, color: "#00e676" },
    { label: "Manual Review", value: stats.manual_review, color: "#ffea00" },
    { label: "High Risk", value: stats.high_risk, color: "#ff9100" },
    { label: "Auto Escalated", value: stats.auto_escalated, color: "#ff1744" },
  ];

  const totalRouted = routingData.reduce((s, d) => s + d.value, 0);

  // Top 5 RFIs
  const rfiEntries = Object.entries(stats.rfi_breakdown || {})
    .sort(([, a], [, b]) => b - a)
    .slice(0, 5);

  const maxRfi = rfiEntries.length > 0 ? rfiEntries[0][1] : 1;

  const getRoutingColor = (routing: string) => {
    switch (routing) {
      case "AUTO_APPROVED": return "text-green-400";
      case "MANUAL_REVIEW": return "text-yellow-400";
      case "HIGH_RISK_REVIEW": return "text-orange-400";
      case "AUTO_ESCALATED": return "text-red-400";
      default: return "text-gray-400";
    }
  };

  return (
    <div className="space-y-8 animate-fade-in-up">
      <div className="text-center">
        <h2 className="text-3xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent mb-2">
          Adjuster Dashboard
        </h2>
        <p className="text-gray-500">Real-time fraud detection analytics</p>
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          icon="📊"
          label="Total Claims"
          value={stats.total_claims.toLocaleString()}
          gradient="from-blue-500/20 to-blue-600/10"
          borderColor="border-blue-500/20"
        />
        <StatCard
          icon="🚨"
          label="Fraud Detected"
          value={(stats.high_risk + stats.auto_escalated).toLocaleString()}
          gradient="from-red-500/20 to-red-600/10"
          borderColor="border-red-500/20"
          subtext={`${Math.round(((stats.high_risk + stats.auto_escalated) / Math.max(1, stats.total_claims)) * 100)}% detection rate`}
        />
        <StatCard
          icon="🕸️"
          label="Rings Found"
          value={stats.rings_detected.toString()}
          gradient="from-purple-500/20 to-purple-600/10"
          borderColor="border-purple-500/20"
        />
        <StatCard
          icon="⚡"
          label="Avg Latency"
          value={`${Math.round(stats.avg_processing_ms)}ms`}
          gradient="from-cyan-500/20 to-cyan-600/10"
          borderColor="border-cyan-500/20"
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Routing Distribution (CSS-based pie chart alternative) */}
        <div className="glass-card">
          <h3 className="text-lg font-semibold text-gray-300 mb-6">Claim Routing Distribution</h3>
          <div className="flex items-center gap-8">
            {/* Donut chart with CSS conic-gradient */}
            <div className="relative w-44 h-44 flex-shrink-0">
              <div
                className="w-full h-full rounded-full"
                style={{
                  background: totalRouted > 0
                    ? `conic-gradient(
                        #00e676 0deg ${(stats.auto_approved / totalRouted) * 360}deg,
                        #ffea00 ${(stats.auto_approved / totalRouted) * 360}deg ${((stats.auto_approved + stats.manual_review) / totalRouted) * 360}deg,
                        #ff9100 ${((stats.auto_approved + stats.manual_review) / totalRouted) * 360}deg ${((stats.auto_approved + stats.manual_review + stats.high_risk) / totalRouted) * 360}deg,
                        #ff1744 ${((stats.auto_approved + stats.manual_review + stats.high_risk) / totalRouted) * 360}deg 360deg
                      )`
                    : "rgba(255,255,255,0.05)",
                }}
              />
              <div className="absolute inset-4 rounded-full bg-[var(--bg-card)] flex items-center justify-center">
                <div className="text-center">
                  <p className="text-2xl font-bold text-gray-200">{totalRouted}</p>
                  <p className="text-[10px] text-gray-500">Total</p>
                </div>
              </div>
            </div>

            {/* Legend */}
            <div className="space-y-3 flex-1">
              {routingData.map((item) => (
                <div key={item.label} className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full" style={{ backgroundColor: item.color }} />
                    <span className="text-sm text-gray-400">{item.label}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-semibold text-gray-200">{item.value}</span>
                    <span className="text-xs text-gray-600">
                      {totalRouted > 0 ? `${Math.round((item.value / totalRouted) * 100)}%` : "0%"}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Top RFIs Bar Chart */}
        <div className="glass-card">
          <h3 className="text-lg font-semibold text-gray-300 mb-6">Top Triggered RFIs</h3>
          {rfiEntries.length > 0 ? (
            <div className="space-y-4">
              {rfiEntries.map(([code, count], index) => (
                <div key={code} className="space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-400 font-mono">{code}</span>
                    <span className="text-sm font-semibold text-gray-200">{count}</span>
                  </div>
                  <div className="h-6 bg-white/5 rounded-md overflow-hidden">
                    <div
                      className="h-full rounded-md transition-all duration-1000 ease-out"
                      style={{
                        width: `${(count / maxRfi) * 100}%`,
                        background: `linear-gradient(90deg, rgba(74, 125, 255, 0.6), rgba(124, 77, 255, 0.6))`,
                        animationDelay: `${index * 200}ms`,
                      }}
                    />
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500 text-sm">No RFI data yet</p>
          )}
        </div>
      </div>

      {/* Recent Claims Table */}
      <div className="glass-card">
        <h3 className="text-lg font-semibold text-gray-300 mb-4">Recent Claims</h3>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-white/10">
                <th className="text-left py-3 px-4 text-xs text-gray-500 font-semibold uppercase tracking-wider">ID</th>
                <th className="text-left py-3 px-4 text-xs text-gray-500 font-semibold uppercase tracking-wider">Claimant</th>
                <th className="text-right py-3 px-4 text-xs text-gray-500 font-semibold uppercase tracking-wider">Amount</th>
                <th className="text-center py-3 px-4 text-xs text-gray-500 font-semibold uppercase tracking-wider">Score</th>
                <th className="text-center py-3 px-4 text-xs text-gray-500 font-semibold uppercase tracking-wider">Routing</th>
                <th className="text-center py-3 px-4 text-xs text-gray-500 font-semibold uppercase tracking-wider">Status</th>
                <th className="text-right py-3 px-4 text-xs text-gray-500 font-semibold uppercase tracking-wider">Time</th>
              </tr>
            </thead>
            <tbody>
              {stats.recent_claims?.map((claim: any) => (
                <tr
                  key={claim.id}
                  className="border-b border-white/5 hover:bg-white/[0.02] transition-colors cursor-pointer"
                  onClick={() => window.location.href = `/claim/${claim.id}`}
                >
                  <td className="py-3 px-4 text-sm font-mono text-blue-400">{claim.id}</td>
                  <td className="py-3 px-4 text-sm text-gray-300">{claim.claimant_name_masked || "****"}</td>
                  <td className="py-3 px-4 text-sm text-gray-300 text-right">
                    ₹{claim.claim_amount?.toLocaleString() || "0"}
                  </td>
                  <td className="py-3 px-4 text-center">
                    <span className={`text-sm font-bold ${
                      (claim.risk_score || 0) <= 30 ? "text-green-400" :
                      (claim.risk_score || 0) <= 60 ? "text-yellow-400" :
                      (claim.risk_score || 0) <= 79 ? "text-orange-400" :
                      "text-red-400"
                    }`}>
                      {Math.round(claim.risk_score || 0)}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-center">
                    <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold ${
                      claim.routing === "AUTO_APPROVED" ? "badge-green" :
                      claim.routing === "MANUAL_REVIEW" ? "badge-yellow" :
                      claim.routing === "HIGH_RISK_REVIEW" ? "badge-orange" :
                      "badge-red"
                    }`}>
                      {claim.routing?.replace(/_/g, " ")}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-center">
                    <span className="text-xs text-gray-400">
                      {claim.status || "PENDING"}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-right text-xs text-gray-500">
                    {claim.processing_ms ? `${Math.round(claim.processing_ms)}ms` : "-"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function StatCard({
  icon,
  label,
  value,
  gradient,
  borderColor,
  subtext,
}: {
  icon: string;
  label: string;
  value: string;
  gradient: string;
  borderColor: string;
  subtext?: string;
}) {
  return (
    <div className={`glass-card bg-gradient-to-br ${gradient} border ${borderColor} hover:scale-[1.02] transition-transform`}>
      <div className="flex items-center gap-3">
        <span className="text-2xl">{icon}</span>
        <div>
          <p className="text-xs text-gray-500 uppercase tracking-wider">{label}</p>
          <p className="text-2xl font-bold text-gray-100">{value}</p>
          {subtext && <p className="text-[10px] text-gray-500 mt-0.5">{subtext}</p>}
        </div>
      </div>
    </div>
  );
}

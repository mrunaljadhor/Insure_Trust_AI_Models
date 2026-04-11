"use client";

interface ShapWaterfallProps {
  shapValues: Record<string, number>;
}

const FEATURE_LABELS: Record<string, string> = {
  claim_frequency: "Claim Frequency",
  policy_age_days: "Policy Age",
  hospital_risk_score: "Hospital Risk Score",
  claim_amount_ratio: "Claim Amount Ratio",
  diagnosis_mismatch: "Diagnosis Mismatch",
  weekend_claim: "Weekend Claim",
};

export default function ShapWaterfall({ shapValues }: ShapWaterfallProps) {
  if (!shapValues || Object.keys(shapValues).length === 0) {
    return <p className="text-gray-500 text-sm">No SHAP values available</p>;
  }

  // Sort by absolute value, take top 6
  const sorted = Object.entries(shapValues)
    .sort(([, a], [, b]) => Math.abs(b) - Math.abs(a))
    .slice(0, 6);

  const maxVal = Math.max(...sorted.map(([, v]) => Math.abs(v)));

  return (
    <div className="space-y-3">
      {sorted.map(([key, value], index) => {
        const isPositive = value > 0;
        const width = maxVal > 0 ? (Math.abs(value) / maxVal) * 100 : 0;
        const label = FEATURE_LABELS[key] || key.replace(/_/g, " ");

        return (
          <div key={key} className="group" style={{ animationDelay: `${index * 100}ms` }}>
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs text-gray-400 truncate max-w-[140px]">{label}</span>
              <span className={`text-xs font-mono font-semibold ${isPositive ? "text-red-400" : "text-green-400"}`}>
                {isPositive ? "+" : ""}{value.toFixed(3)}
              </span>
            </div>
            <div className="relative h-6 bg-white/5 rounded-md overflow-hidden">
              <div
                className={`
                  absolute top-0 h-full rounded-md transition-all duration-700 ease-out
                  ${isPositive
                    ? "bg-gradient-to-r from-red-600/60 to-red-500/80 left-1/2"
                    : "bg-gradient-to-l from-green-600/60 to-green-500/80 right-1/2"
                  }
                `}
                style={{
                  width: `${width / 2}%`,
                  ...(isPositive ? {} : { right: "50%" }),
                }}
              />
              {/* Center line */}
              <div className="absolute left-1/2 top-0 w-px h-full bg-white/20" />
            </div>
          </div>
        );
      })}
      <div className="flex justify-between text-[10px] text-gray-600 mt-2 px-1">
        <span>← Legitimacy</span>
        <span>Base</span>
        <span>Fraud →</span>
      </div>
    </div>
  );
}

"use client";

interface RFIBadgesProps {
  rfis: Array<{
    rfi_code: string;
    description: string;
    risk_points: number;
  }>;
}

export default function RFIBadges({ rfis }: RFIBadgesProps) {
  if (!rfis || rfis.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full py-8">
        <div className="text-4xl mb-3">✅</div>
        <p className="text-green-400 font-medium">No RFI Violations</p>
        <p className="text-xs text-gray-500 mt-1">All IRDAI checks passed</p>
      </div>
    );
  }

  const getBadgeColor = (points: number) => {
    if (points > 20) return "badge-red";
    if (points > 10) return "badge-orange";
    return "badge-yellow";
  };

  const totalPoints = rfis.reduce((sum, r) => sum + r.risk_points, 0);

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-2">
        {rfis.map((rfi, index) => (
          <div
            key={rfi.rfi_code}
            className="group relative animate-fade-in-up"
            style={{ animationDelay: `${index * 100}ms` }}
          >
            <span
              className={`
                inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold
                cursor-default transition-all duration-200 hover:scale-105
                ${getBadgeColor(rfi.risk_points)}
              `}
            >
              <span>🚩</span>
              <span>{rfi.rfi_code}</span>
              <span className="opacity-70">+{rfi.risk_points}</span>
            </span>

            {/* Tooltip */}
            <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-2 rounded-lg bg-gray-900/95 border border-white/10 text-xs text-gray-200 whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none z-50 shadow-xl">
              {rfi.description}
              <div className="absolute top-full left-1/2 -translate-x-1/2 -mt-px">
                <div className="w-2 h-2 bg-gray-900/95 rotate-45 border-r border-b border-white/10"></div>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-4 pt-3 border-t border-white/5">
        <div className="flex items-center justify-between">
          <span className="text-xs text-gray-500">Total RFI Points</span>
          <span className={`text-lg font-bold ${totalPoints > 50 ? "text-red-400" : totalPoints > 25 ? "text-orange-400" : "text-yellow-400"}`}>
            +{totalPoints}
          </span>
        </div>
      </div>
    </div>
  );
}

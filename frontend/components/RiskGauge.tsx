"use client";

import { useEffect, useState } from "react";

interface RiskGaugeProps {
  score: number;
  routing: string;
}

export default function RiskGauge({ score, routing }: RiskGaugeProps) {
  const [animatedScore, setAnimatedScore] = useState(0);

  useEffect(() => {
    let start = 0;
    const duration = 1500;
    const startTime = Date.now();
    
    const animate = () => {
      const elapsed = Date.now() - startTime;
      const progress = Math.min(elapsed / duration, 1);
      // Easing function for smooth animation
      const eased = 1 - Math.pow(1 - progress, 3);
      const current = Math.round(eased * score);
      setAnimatedScore(current);
      
      if (progress < 1) {
        requestAnimationFrame(animate);
      }
    };
    
    requestAnimationFrame(animate);
  }, [score]);

  const getColor = (s: number) => {
    if (s <= 30) return { main: "#00e676", glow: "rgba(0, 230, 118, 0.3)" };
    if (s <= 60) return { main: "#ffea00", glow: "rgba(255, 234, 0, 0.3)" };
    if (s <= 79) return { main: "#ff9100", glow: "rgba(255, 145, 0, 0.3)" };
    return { main: "#ff1744", glow: "rgba(255, 23, 68, 0.3)" };
  };

  const getRoutingBadge = (r: string) => {
    switch (r) {
      case "AUTO_APPROVED": return "badge-green";
      case "MANUAL_REVIEW": return "badge-yellow";
      case "HIGH_RISK_REVIEW": return "badge-orange";
      case "AUTO_ESCALATED": return "badge-red";
      default: return "badge-yellow";
    }
  };

  const color = getColor(animatedScore);
  const angle = (animatedScore / 100) * 180;
  const radius = 85;
  const cx = 100;
  const cy = 100;

  // Calculate arc path
  const startAngle = Math.PI;
  const endAngle = Math.PI + (angle * Math.PI / 180);
  const x1 = cx + radius * Math.cos(startAngle);
  const y1 = cy + radius * Math.sin(startAngle);
  const x2 = cx + radius * Math.cos(endAngle);
  const y2 = cy + radius * Math.sin(endAngle);
  const largeArc = angle > 180 ? 1 : 0;

  return (
    <div className="flex flex-col items-center">
      <svg viewBox="0 0 200 130" className="w-64 h-40">
        {/* Background arc */}
        <path
          d={`M ${cx - radius} ${cy} A ${radius} ${radius} 0 0 1 ${cx + radius} ${cy}`}
          fill="none"
          stroke="rgba(255,255,255,0.06)"
          strokeWidth="16"
          strokeLinecap="round"
        />
        
        {/* Color zone arcs */}
        {[
          { start: 0, end: 30, color: "rgba(0, 230, 118, 0.15)" },
          { start: 30, end: 60, color: "rgba(255, 234, 0, 0.15)" },
          { start: 60, end: 79, color: "rgba(255, 145, 0, 0.15)" },
          { start: 79, end: 100, color: "rgba(255, 23, 68, 0.15)" },
        ].map((zone, i) => {
          const sa = Math.PI + (zone.start / 100) * Math.PI;
          const ea = Math.PI + (zone.end / 100) * Math.PI;
          const sx = cx + radius * Math.cos(sa);
          const sy = cy + radius * Math.sin(sa);
          const ex = cx + radius * Math.cos(ea);
          const ey = cy + radius * Math.sin(ea);
          const la = (zone.end - zone.start) > 50 ? 1 : 0;
          return (
            <path
              key={i}
              d={`M ${sx} ${sy} A ${radius} ${radius} 0 ${la} 1 ${ex} ${ey}`}
              fill="none"
              stroke={zone.color}
              strokeWidth="16"
            />
          );
        })}

        {/* Animated score arc */}
        {animatedScore > 0 && (
          <path
            d={`M ${x1} ${y1} A ${radius} ${radius} 0 ${largeArc} 1 ${x2} ${y2}`}
            fill="none"
            stroke={color.main}
            strokeWidth="16"
            strokeLinecap="round"
            style={{
              filter: `drop-shadow(0 0 8px ${color.glow})`,
            }}
          />
        )}

        {/* Score text */}
        <text x={cx} y={cy - 8} textAnchor="middle" className="text-4xl font-bold" fill={color.main} fontSize="36">
          {animatedScore}
        </text>
        <text x={cx} y={cy + 14} textAnchor="middle" fill="rgba(255,255,255,0.4)" fontSize="12">
          / 100
        </text>
      </svg>

      {/* Routing badge */}
      <span className={`px-4 py-1.5 rounded-full text-sm font-semibold ${getRoutingBadge(routing)}`}>
        {routing?.replace(/_/g, " ")}
      </span>
    </div>
  );
}

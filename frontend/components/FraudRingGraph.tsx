"use client";

import { useEffect, useRef, useState, useCallback } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface FraudRingGraphProps {
  ringDetected?: boolean;
  ringId?: string | null;
  newNodes?: any[];
  newEdges?: any[];
}

const NODE_COLORS: Record<string, string> = {
  claimant: "#4a7dff",
  doctor: "#7c4dff",
  workshop: "#ff9100",
  witness: "#9e9e9e",
  mobile: "#ffea00",
  ip_address: "#00e5ff",
};

const NODE_LABELS: Record<string, string> = {
  claimant: "Claimant",
  doctor: "Doctor",
  workshop: "Workshop",
  witness: "Witness",
  mobile: "Mobile",
  ip_address: "IP Address",
};

export default function FraudRingGraph({
  ringDetected = false,
  ringId = null,
  newNodes = [],
  newEdges = [],
}: FraudRingGraphProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [graphLoaded, setGraphLoaded] = useState(false);
  const [tooltip, setTooltip] = useState<{
    visible: boolean;
    x: number;
    y: number;
    data: any;
  }>({ visible: false, x: 0, y: 0, data: null });
  const [sidePanel, setSidePanel] = useState<any>(null);
  const simulationRef = useRef<any>(null);

  const initGraph = useCallback(async () => {
    if (!svgRef.current || !containerRef.current) return;

    // Dynamically import D3
    const d3 = await import("d3");

    const container = containerRef.current;
    const width = container.clientWidth;
    const height = 550;

    // Clear previous
    d3.select(svgRef.current).selectAll("*").remove();

    const svg = d3
      .select(svgRef.current)
      .attr("width", width)
      .attr("height", height)
      .attr("viewBox", `0 0 ${width} ${height}`);

    // Add zoom
    const g = svg.append("g");
    const zoom = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.1, 4])
      .on("zoom", (event) => {
        g.attr("transform", event.transform);
      });
    svg.call(zoom);

    // Fetch graph data
    let graphData: { nodes: any[]; edges: any[] };
    try {
      const res = await fetch(`${API_URL}/graph/data`);
      graphData = await res.json();
    } catch {
      graphData = { nodes: [], edges: [] };
    }

    if (graphData.nodes.length === 0) {
      svg
        .append("text")
        .attr("x", width / 2)
        .attr("y", height / 2)
        .attr("text-anchor", "middle")
        .attr("fill", "rgba(255,255,255,0.3)")
        .attr("font-size", "16px")
        .text("Submit a claim to see the fraud graph");
      return;
    }

    // Limit nodes for performance (show max 200 most connected)
    let nodes = graphData.nodes;
    let edges = graphData.edges;

    if (nodes.length > 200) {
      const topNodes = new Set(
        nodes
          .sort((a, b) => (b.claim_count || 0) - (a.claim_count || 0))
          .slice(0, 200)
          .map((n) => n.id)
      );
      // Also include new nodes
      newNodes.forEach((n) => topNodes.add(n.id));
      nodes = nodes.filter((n) => topNodes.has(n.id));
      edges = edges.filter(
        (e) => topNodes.has(e.source) && topNodes.has(e.target)
      );
    }

    // Mark new nodes/edges
    const newNodeIds = new Set(newNodes.map((n) => n.id));
    const newEdgeKeys = new Set(
      newEdges.map((e) => `${e.source}-${e.target}`)
    );

    // Create simulation
    const simulation = d3
      .forceSimulation(nodes as any)
      .force(
        "link",
        d3
          .forceLink(edges as any)
          .id((d: any) => d.id)
          .distance(60)
      )
      .force("charge", d3.forceManyBody().strength(-120))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collision", d3.forceCollide().radius(20));

    simulationRef.current = simulation;

    // Draw edges
    const link = g
      .append("g")
      .selectAll("line")
      .data(edges)
      .enter()
      .append("line")
      .attr("stroke", (d: any) => {
        const key = `${typeof d.source === 'object' ? d.source.id : d.source}-${typeof d.target === 'object' ? d.target.id : d.target}`;
        if (newEdgeKeys.has(key)) return "#ff1744";
        return "rgba(255,255,255,0.08)";
      })
      .attr("stroke-width", (d: any) => {
        const key = `${typeof d.source === 'object' ? d.source.id : d.source}-${typeof d.target === 'object' ? d.target.id : d.target}`;
        return newEdgeKeys.has(key) ? 2.5 : 0.8;
      })
      .attr("stroke-dasharray", (d: any) => {
        const key = `${typeof d.source === 'object' ? d.source.id : d.source}-${typeof d.target === 'object' ? d.target.id : d.target}`;
        return newEdgeKeys.has(key) ? "8 4" : "none";
      })
      .style("opacity", 0)
      .transition()
      .duration(800)
      .style("opacity", 1);

    // Animate new edges dash offset
    g.selectAll("line")
      .filter((d: any) => {
        const key = `${typeof d.source === 'object' ? d.source.id : d.source}-${typeof d.target === 'object' ? d.target.id : d.target}`;
        return newEdgeKeys.has(key);
      })
      .attr("stroke-dashoffset", 100)
      .transition()
      .duration(1500)
      .attr("stroke-dashoffset", 0);

    // Draw nodes
    const node = g
      .append("g")
      .selectAll("circle")
      .data(nodes)
      .enter()
      .append("circle")
      .attr("r", (d: any) => {
        const count = d.claim_count || 1;
        return Math.min(24, Math.max(8, 6 + count * 2));
      })
      .attr("fill", (d: any) => NODE_COLORS[d.type] || "#666")
      .attr("stroke", (d: any) => {
        if (newNodeIds.has(d.id)) return "#ff1744";
        return "rgba(255,255,255,0.1)";
      })
      .attr("stroke-width", (d: any) => (newNodeIds.has(d.id) ? 3 : 1))
      .style("cursor", "pointer")
      .style("filter", (d: any) => {
        const color = NODE_COLORS[d.type] || "#666";
        return `drop-shadow(0 0 4px ${color}40)`;
      });

    // New nodes fly in from top
    node
      .filter((d: any) => newNodeIds.has(d.id))
      .attr("cy", -50)
      .style("opacity", 0)
      .transition()
      .duration(500)
      .attr("cy", (d: any) => d.y || height / 2)
      .style("opacity", 1);

    // Node labels (small)
    const labels = g
      .append("g")
      .selectAll("text")
      .data(nodes.filter((n: any) => (n.claim_count || 0) >= 2 || newNodeIds.has(n.id)))
      .enter()
      .append("text")
      .text((d: any) => d.label?.slice(0, 12) || d.id.slice(0, 8))
      .attr("font-size", "8px")
      .attr("fill", "rgba(255,255,255,0.5)")
      .attr("text-anchor", "middle")
      .attr("dy", (d: any) => {
        const r = Math.min(24, Math.max(8, 6 + (d.claim_count || 1) * 2));
        return r + 12;
      });

    // Drag behavior
    const drag = d3
      .drag<SVGCircleElement, any>()
      .on("start", (event, d: any) => {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
      })
      .on("drag", (event, d: any) => {
        d.fx = event.x;
        d.fy = event.y;
      })
      .on("end", (event, d: any) => {
        if (!event.active) simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
      });

    (node as any).call(drag);

    // Hover/click events
    (node as any)
      .on("mouseover", function (event: any, d: any) {
        d3.select(this)
          .transition()
          .duration(200)
          .attr("r", (d: any) => Math.min(28, Math.max(12, 8 + (d.claim_count || 1) * 2)));
        
        const rect = container.getBoundingClientRect();
        setTooltip({
          visible: true,
          x: event.clientX - rect.left + 15,
          y: event.clientY - rect.top - 10,
          data: d,
        });
      })
      .on("mouseout", function (event: any, d: any) {
        d3.select(this)
          .transition()
          .duration(200)
          .attr("r", (d: any) => Math.min(24, Math.max(8, 6 + (d.claim_count || 1) * 2)));
        setTooltip({ visible: false, x: 0, y: 0, data: null });
      })
      .on("click", (event: any, d: any) => {
        setSidePanel(d);
      });

    // Tick update
    simulation.on("tick", () => {
      (g.selectAll("line") as any)
        .attr("x1", (d: any) => d.source.x)
        .attr("y1", (d: any) => d.source.y)
        .attr("x2", (d: any) => d.target.x)
        .attr("y2", (d: any) => d.target.y);

      (node as any).attr("cx", (d: any) => d.x).attr("cy", (d: any) => d.y);

      (labels as any)
        .attr("x", (d: any) => d.x)
        .attr("y", (d: any) => d.y);
    });

    // Ring detection animation
    if (ringDetected) {
      setTimeout(() => {
        // Pulse all ring-related nodes
        (node as any)
          .filter((d: any) => newNodeIds.has(d.id) || (d.claim_count || 0) > 2)
          .transition()
          .duration(300)
          .attr("stroke", "#ff1744")
          .attr("stroke-width", 4)
          .transition()
          .duration(300)
          .attr("stroke-width", 2)
          .transition()
          .duration(300)
          .attr("stroke-width", 4)
          .transition()
          .duration(300)
          .attr("stroke-width", 2);

        // Turn ring edges red
        (g.selectAll("line") as any)
          .filter((d: any) => {
            const sId = typeof d.source === 'object' ? d.source.id : d.source;
            const tId = typeof d.target === 'object' ? d.target.id : d.target;
            return newEdgeKeys.has(`${sId}-${tId}`);
          })
          .transition()
          .duration(500)
          .attr("stroke", "#ff1744")
          .attr("stroke-width", 3)
          .attr("stroke-dasharray", "none");
      }, 500);
    }

    setGraphLoaded(true);
  }, [newNodes, newEdges, ringDetected]);

  useEffect(() => {
    initGraph();

    return () => {
      if (simulationRef.current) {
        simulationRef.current.stop();
      }
    };
  }, [initGraph]);

  return (
    <div className="relative">
      {/* Header with ring alert */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-300 flex items-center gap-2">
          🕸️ Fraud Ring Network
        </h3>
        {ringDetected && (
          <div className="flex items-center gap-2 px-4 py-2 rounded-xl bg-red-500/15 border border-red-500/30 animate-pulse-ring">
            <span className="text-red-400 font-bold text-sm">
              ⚠ FRAUD RING DETECTED
            </span>
            {ringId && (
              <span className="text-red-400/70 text-xs font-mono">{ringId}</span>
            )}
          </div>
        )}
      </div>

      {/* Graph container */}
      <div ref={containerRef} className="graph-container relative" style={{ minHeight: 550 }}>
        <svg ref={svgRef} className="w-full" />

        {/* Tooltip */}
        {tooltip.visible && tooltip.data && (
          <div
            className="node-tooltip"
            style={{ left: tooltip.x, top: tooltip.y }}
          >
            <div className="flex items-center gap-2 mb-1">
              <div
                className="w-3 h-3 rounded-full"
                style={{
                  backgroundColor: NODE_COLORS[tooltip.data.type] || "#666",
                }}
              />
              <span className="font-semibold text-sm">
                {NODE_LABELS[tooltip.data.type] || tooltip.data.type}
              </span>
            </div>
            <div className="text-xs text-gray-400 space-y-0.5">
              <p>ID: {tooltip.data.id}</p>
              <p>Claims: {tooltip.data.claim_count || 0}</p>
              {tooltip.data.risk_score > 0 && (
                <p>Risk: {Math.round(tooltip.data.risk_score)}</p>
              )}
            </div>
          </div>
        )}

        {/* Legend */}
        <div className="absolute top-3 right-3 bg-black/60 backdrop-blur-sm rounded-xl p-3 border border-white/10">
          <p className="text-[10px] text-gray-500 mb-2 font-semibold uppercase tracking-wider">
            Node Types
          </p>
          {Object.entries(NODE_COLORS).map(([type, color]) => (
            <div key={type} className="flex items-center gap-2 mb-1">
              <div
                className="w-2.5 h-2.5 rounded-full"
                style={{ backgroundColor: color }}
              />
              <span className="text-[11px] text-gray-400 capitalize">
                {type.replace("_", " ")}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Side panel */}
      {sidePanel && (
        <div
          className="fixed top-0 right-0 w-80 h-full glass-card rounded-none border-l border-white/10 z-50 animate-slide-in-right overflow-y-auto"
          style={{ animation: "slideInFromRight 0.3s ease-out" }}
        >
          <div className="p-6">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-bold text-gray-200">Entity Details</h3>
              <button
                onClick={() => setSidePanel(null)}
                className="text-gray-500 hover:text-gray-300 text-xl"
              >
                ✕
              </button>
            </div>

            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <div
                  className="w-12 h-12 rounded-xl flex items-center justify-center"
                  style={{
                    backgroundColor: `${NODE_COLORS[sidePanel.type] || "#666"}20`,
                    border: `2px solid ${NODE_COLORS[sidePanel.type] || "#666"}40`,
                  }}
                >
                  <div
                    className="w-4 h-4 rounded-full"
                    style={{
                      backgroundColor: NODE_COLORS[sidePanel.type] || "#666",
                    }}
                  />
                </div>
                <div>
                  <p className="font-semibold text-gray-200 capitalize">
                    {NODE_LABELS[sidePanel.type] || sidePanel.type}
                  </p>
                  <p className="text-xs text-gray-500 font-mono">{sidePanel.id}</p>
                </div>
              </div>

              <div className="space-y-3 pt-2">
                <DetailRow label="Label" value={sidePanel.label || "N/A"} />
                <DetailRow label="Claim Count" value={sidePanel.claim_count || 0} />
                <DetailRow
                  label="Risk Score"
                  value={
                    sidePanel.risk_score
                      ? `${Math.round(sidePanel.risk_score)}/100`
                      : "N/A"
                  }
                />
                <DetailRow label="Type" value={sidePanel.type} />
              </div>
            </div>
          </div>
        </div>
      )}

      <style jsx>{`
        @keyframes slideInFromRight {
          from { transform: translateX(100%); opacity: 0; }
          to { transform: translateX(0); opacity: 1; }
        }
      `}</style>
    </div>
  );
}

function DetailRow({ label, value }: { label: string; value: any }) {
  return (
    <div className="flex justify-between items-center py-2 border-b border-white/5">
      <span className="text-xs text-gray-500">{label}</span>
      <span className="text-sm text-gray-300 font-medium">{String(value)}</span>
    </div>
  );
}

"use client";

import { useEffect, useState, useRef, useCallback, useMemo } from "react";
import { ZoomIn, ZoomOut, RotateCcw, Network, Info, Activity } from "lucide-react";
import { useTheme } from "next-themes";
import "vis-network/styles/vis-network.css";
import { StatusPlaceholder } from "./StatusPlaceholder";

// ─── Types & Constants ────────────────────────────────────────────────────────

interface GraphNode {
  id: string;
  label: string;
  type: string;
  properties: Record<string, unknown>;
}

interface GraphEdge {
  id: string;
  source: string;
  target: string;
  label: string;
}

interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

// VIP Color Palette (matched to previous styles but optimized for vis-network groups)
const TYPE_COLORS: Record<string, string> = {
  owl__Class: "#818cf8",
  owl__ObjectProperty: "#fbbf24",
  owl__DatatypeProperty: "#34d399",
  owl__AnnotationProperty: "#22d3ee",
  owl__Restriction: "#f472b6",
  owl__NamedIndividual: "#a78bfa",
  rdfs__Class: "#818cf8",
  rdfs__Property: "#fbbf24",
  Equipment: "#6366f1",
  ConnectionPoint: "#f59e0b",
  System: "#8b5cf6",
  Sensor: "#06b6d4",
  Zone: "#ec4899",
  Function: "#f97316", // Orange
  Connection: "#d946ef", // Fuchsia
  Property: "#34d399", // Emerald
};

const DEFAULT_COLOR = "#64748b";

function getNodeColor(type: string): string {
  if (TYPE_COLORS[type]) return TYPE_COLORS[type];
  for (const [key, color] of Object.entries(TYPE_COLORS)) {
    if (type.includes(key)) return color;
  }
  return DEFAULT_COLOR;
}

function getNodeShape(type: string, label: string): "dot" | "square" | "triangle" | "triangleDown" | "diamond" | "star" | "box" {
  const t = type.toLowerCase();
  const l = label.toLowerCase();
  
  if (t.includes("sensor") || t.includes("equipment")) return "square";
  if (t.includes("system")) return "box";
  if (t.includes("function") || t.includes("producer")) return "star";
  if (t.includes("connectionpoint")) {
    if (l.includes("inlet") || l.includes("input")) return "triangle";
    if (l.includes("outlet") || l.includes("output")) return "triangleDown";
    return "triangle";
  }
  if (t.includes("connection")) return "diamond";
  if (t.includes("property")) return "dot";
  
  return "dot";
}

function getNodeSize(type: string): number {
  const t = type.toLowerCase();
  if (t.includes("system")) return 40;
  if (t.includes("equipment") || t.includes("sensor")) return 20;
  return 15;
}

function generateTooltip(node: GraphNode): string {
  const props = node.properties || {};
  let tooltip = `Label : ${node.label}\n=======\nURI : ${node.id}\nTypes: ${node.type}`;
  
  const entries = Object.entries(props).filter(([k]) => k !== 'uri' && k !== 'label');
  if (entries.length > 0) {
    tooltip += "\n=======";
    entries.forEach(([k, v]) => {
      tooltip += `\n  - ${k} : ${v}`;
    });
  }
  return tooltip;
}

// ─── Main Component ───────────────────────────────────────────────────────────

export function GraphWindow() {
  const containerRef = useRef<HTMLDivElement>(null);
  const networkRef = useRef<any>(null);
  const { theme } = useTheme();
  
  const [data, setData] = useState<GraphData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeNode, setActiveNode] = useState<string | null>(null);
  const [stabilizationProgress, setStabilizationProgress] = useState<{current: number, total: number} | null>(null);
  const [searchQuery, setSearchQuery] = useState("");

  // Fetch data
  useEffect(() => {
    let cancelled = false;
    fetch("/api/graph")
      .then((r) => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json() as Promise<GraphData>; })
      .then((json) => { if (!cancelled) { setData(json); setLoading(false); } })
      .catch((err: Error) => { if (!cancelled) { setError(err.message); setLoading(false); } });
    return () => { cancelled = true; };
  }, []);

  // Initialize Network
  useEffect(() => {
    if (!data || !containerRef.current) return;

    // We import vis-network dynamically or assume it's available via npm
    // Using vis-network directly as it was installed
    const vis = require("vis-network/standalone");

    const visNodes = data.nodes.map(n => ({
      id: n.id,
      label: n.label,
      title: generateTooltip(n),
      shape: getNodeShape(n.type, n.label),
      size: getNodeSize(n.type),
      color: {
        background: getNodeColor(n.type),
        border: getNodeColor(n.type),
        highlight: {
          background: getNodeColor(n.type),
          border: "#ffffff"
        }
      },
      font: {
        color: theme === "dark" ? "#e2e8f0" : "#1e293b",
        face: "Outfit, Inter, system-ui",
        size: 14,
        strokeWidth: theme === "dark" ? 0 : 2,
        strokeColor: "#ffffff"
      },
      originalColor: getNodeColor(n.type),
      originalLabel: n.label
    }));

    const visEdges = data.edges.map(e => {
      // Logic to match ontology.html dashed styles
      const label = e.label.toLowerCase();
      const isDashed = label.includes("isdeltaquantity") || 
                       label.includes("modulation") || 
                       label.includes("amps") || 
                       label.includes("volts") || 
                       label.includes("fluid") || 
                       label.includes("water") || 
                       label.includes("steam") ||
                       label.includes("air");
      const isContains = label.includes("contains");

      return {
        id: e.id,
        from: e.source,
        to: e.target,
        label: e.label,
        font: {
          align: "top",
          size: 10,
          color: theme === "dark" ? "#94a3b8" : "#64748b"
        },
        color: {
          color: theme === "dark" ? "rgba(255, 255, 255, 0.2)" : "rgba(0, 0, 0, 0.15)",
          highlight: theme === "dark" ? "#818cf8" : "#4f46e5"
        },
        arrows: {
          to: { enabled: true, scaleFactor: 0.5 }
        },
        dashes: isDashed ? [5, 5] : false,
        width: isContains ? 8 : 1
      };
    });

    const networkData = {
      nodes: new vis.DataSet(visNodes),
      edges: new vis.DataSet(visEdges)
    };

    const options = {
      autoResize: true,
      edges: {
        smooth: {
          enabled: true,
          type: "dynamic",
          roundness: 0.5
        }
      },
      interaction: {
        hover: true,
        tooltipDelay: 200,
        hideEdgesOnDrag: false,
        dragNodes: true,
        navigationButtons: false
      },
      physics: {
        enabled: true,
        stabilization: {
          enabled: true,
          iterations: 1000,
          updateInterval: 50,
          fit: true
        },
        barnesHut: {
          gravitationalConstant: -12000,
          centralGravity: 0.3,
          springLength: 100,
          springConstant: 0.02,
          damping: 0.09,
          avoidOverlap: 0.1
        }
      }
    };

    const network = new vis.Network(containerRef.current, networkData, options);
    networkRef.current = network;

    // Neighbourhood Highlight Logic (ported from ontology.html)
    let highlightActive = false;

    network.on("selectNode", (params: any) => {
      const nodes = networkData.nodes;
      const allNodes = nodes.get({ returnType: "Object" }) as any;
      
      if (params.nodes.length > 0) {
        highlightActive = true;
        const selectedNode = params.nodes[0];
        setActiveNode(selectedNode);

        // Highlight additive
        const connectedNodes = network.getConnectedNodes(selectedNode) as string[];
        const neighbors = new Set(connectedNodes);

        for (let nodeId in allNodes) {
          const isSelected = nodeId === selectedNode;
          const isNeighbor = neighbors.has(nodeId);

          if (isSelected) {
            allNodes[nodeId].color = {
              background: allNodes[nodeId].originalColor,
              border: "#ffffff"
            };
            allNodes[nodeId].borderWidth = 4;
            allNodes[nodeId].shadow = { enabled: true, color: "rgba(99, 102, 241, 0.8)", size: 10 };
          } else if (isNeighbor) {
            allNodes[nodeId].color = {
              background: allNodes[nodeId].originalColor,
              border: theme === "dark" ? "#ffffff" : "#000000"
            };
            allNodes[nodeId].borderWidth = 2;
          } else {
            // Very subtle dimming instead of hard removal
            allNodes[nodeId].color = {
              background: allNodes[nodeId].originalColor,
              border: allNodes[nodeId].originalColor,
              opacity: 0.3 // Vis.js supports opacity in some versions or via rgba
            };
            allNodes[nodeId].font = { color: theme === "dark" ? "rgba(226, 232, 240, 0.2)" : "rgba(30, 41, 59, 0.2)" };
          }
        }
        nodes.update(Object.values(allNodes));
      } else {
        if (highlightActive) {
          // Reset
          for (let nodeId in allNodes) {
             allNodes[nodeId].color = {
               background: allNodes[nodeId].originalColor,
               border: allNodes[nodeId].originalColor
             };
             allNodes[nodeId].borderWidth = 1;
             allNodes[nodeId].shadow = { enabled: false };
             allNodes[nodeId].font = { color: theme === "dark" ? "#e2e8f0" : "#1e293b" };
          }
          nodes.update(Object.values(allNodes));
          highlightActive = false;
        }
        setActiveNode(null);
      }
    });

    network.on("deselectNode", () => {
      // Handled by selectNode with empty array
    });

    network.on("stabilizationProgress", (params: {iterations: number, total: number}) => {
      setStabilizationProgress({ current: params.iterations, total: params.total });
    });

    network.on("stabilizationIterationsDone", () => {
      setStabilizationProgress(null);
      network.fit();
    });

    return () => {
      if (networkRef.current) {
        networkRef.current.destroy();
      }
    };
  }, [data, theme]);

  // Toolbar Actions
  const handleZoomIn = () => networkRef.current?.moveTo({ scale: networkRef.current.getScale() * 1.2 });
  const handleZoomOut = () => networkRef.current?.moveTo({ scale: networkRef.current.getScale() / 1.2 });
  const handleReset = () => {
    networkRef.current?.fit();
    setActiveNode(null);
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery || !networkRef.current || !data) return;
    
    const matchedNode = data.nodes.find(n => 
      n.label.toLowerCase().includes(searchQuery.toLowerCase()) || 
      n.id.toLowerCase().includes(searchQuery.toLowerCase())
    );

    if (matchedNode) {
      networkRef.current.selectNodes([matchedNode.id]);
      networkRef.current.focus(matchedNode.id, {
        scale: 1.0,
        animation: { duration: 1000, easingFunction: "easeInOutQuad" }
      });
      setActiveNode(matchedNode.id);
    }
  };

  if (loading) return <div className="w-full h-full flex items-center justify-center"><StatusPlaceholder icon={Network} title="LOADING GRAPH" subtitle="Fetching nodes and relationships from Neo4j..." /></div>;
  if (error) return <div className="w-full h-full flex items-center justify-center"><StatusPlaceholder icon={Network} title="GRAPH UNAVAILABLE" subtitle="Could not connect to the graph API. Ensure Neo4j is running." /></div>;
  if (!data || data.nodes.length === 0) return <div className="w-full h-full flex items-center justify-center"><StatusPlaceholder icon={Network} title="NO GRAPH DATA" subtitle="Run 'Load TTL to Neo4j' from the agent to import the current ontology" /></div>;

  return (
    <div className="relative w-full h-full bg-[radial-gradient(circle_at_center,var(--accent)/[0.03]_0%,transparent_70%)] overflow-hidden">
      {/* Vis Container */}
      <div ref={containerRef} className="w-full h-full" />

      {/* Toolbar */}
      <div className="absolute top-6 left-6 z-20 flex items-center gap-3 p-2 rounded-2xl border border-[var(--muted-foreground)]/10 bg-[var(--background)]/60 backdrop-blur-xl shadow-[0_15px_30px_rgba(0,0,0,0.05)]">
        <form onSubmit={handleSearch} className="flex items-center pl-2">
          <input 
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search graph..."
            className="w-40 px-3 py-1.5 bg-[var(--muted)]/20 border border-white/5 rounded-xl text-[11px] font-bold focus:outline-none focus:ring-1 focus:ring-[var(--primary)]/50 transition-all placeholder:text-[var(--muted-foreground)]/40"
          />
        </form>
        <div className="w-[1px] h-6 bg-[var(--muted-foreground)]/10 mx-1" />
        <div className="flex items-center gap-1">
          <button 
            className="p-2 rounded-xl text-sm transition-all duration-300 flex items-center justify-center border border-[var(--muted-foreground)]/10 text-[var(--muted-foreground)] hover:text-[var(--accent)] hover:bg-[var(--accent)]/5 hover:border-[var(--accent)]/20 shadow-sm active:scale-90 group"
            onClick={handleZoomIn}
            title="Zoom In"
          >
            <ZoomIn size={18} className="group-hover:scale-110 transition-transform" />
          </button>
          <button 
            className="p-2 rounded-xl text-sm transition-all duration-300 flex items-center justify-center border border-[var(--muted-foreground)]/10 text-[var(--muted-foreground)] hover:text-[var(--accent)] hover:bg-[var(--accent)]/5 hover:border-[var(--accent)]/20 shadow-sm active:scale-90 group"
            onClick={handleZoomOut}
            title="Zoom Out"
          >
            <ZoomOut size={18} className="group-hover:scale-110 transition-transform" />
          </button>
          <button 
            className="p-2 rounded-xl text-sm transition-all duration-300 flex items-center justify-center border border-[var(--muted-foreground)]/10 text-[var(--muted-foreground)] hover:text-[var(--accent)] hover:bg-[var(--accent)]/5 hover:border-[var(--accent)]/20 shadow-sm active:scale-90 group"
            onClick={handleReset}
            title="Reset View"
          >
            <RotateCcw size={18} className="group-hover:rotate-[-45deg] transition-transform" />
          </button>
        </div>
      </div>

      {/* Status Info (Optional overlays) */}
      <div className="absolute top-6 right-6 z-10 hidden md:block select-none pointer-events-none">
        <div className="px-4 py-2 rounded-full bg-[var(--background)]/40 backdrop-blur-md border border-[var(--foreground)]/5 flex items-center gap-3">
          <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          <span className="text-[10px] font-black uppercase tracking-widest text-[var(--muted-foreground)]">Live Physics Active</span>
        </div>
      </div>

      {/* Stabilization Overlay */}
      {stabilizationProgress && (
        <div className="absolute inset-0 z-50 flex flex-col items-center justify-center bg-[var(--background)]/80 backdrop-blur-md">
          <div className="p-8 rounded-3xl border border-[var(--primary)]/20 bg-[var(--card)] shadow-2xl flex flex-col items-center gap-6 max-w-sm w-full mx-4">
            <div className="relative w-20 h-20">
              <div className="absolute inset-0 border-4 border-[var(--primary)]/10 rounded-full" />
              <div 
                className="absolute inset-0 border-4 border-[var(--primary)] rounded-full border-t-transparent animate-spin" 
                style={{ animationDuration: '2s' }}
              />
              <div className="absolute inset-0 flex items-center justify-center">
                <Activity className="w-8 h-8 text-[var(--primary)] animate-pulse" />
              </div>
            </div>
            <div className="text-center space-y-2">
              <h3 className="text-xl font-bold bg-gradient-to-br from-[var(--foreground)] to-[var(--muted-foreground)] bg-clip-text text-transparent">
                Stabilizing Graph
              </h3>
              <p className="text-sm text-[var(--muted-foreground)] font-medium">
                Optimizing layout coordinates...
              </p>
            </div>
            <div className="w-full bg-[var(--muted)]/30 h-1.5 rounded-full overflow-hidden border border-white/5">
              <div 
                className="h-full bg-gradient-to-r from-[#6366f1] to-[#8b5cf6] transition-all duration-300 ease-out shadow-[0_0_10px_rgba(99,102,241,0.5)]"
                style={{ width: `${(stabilizationProgress.current / stabilizationProgress.total) * 100}%` }}
              />
            </div>
            <span className="text-[10px] font-black tracking-widest uppercase text-[var(--muted-foreground)] opacity-50">
              Iteration {stabilizationProgress.current} / {stabilizationProgress.total}
            </span>
          </div>
        </div>
      )}

      {/* Details Card (Reusing InfoCard logic but for vis-network) */}
      {activeNode && (
        <NodeInfoCard nodes={data.nodes} activeNodeId={activeNode} />
      )}

      {/* Legend Overlay */}
      <div className="absolute bottom-6 left-6 z-10 p-4 rounded-2xl border border-[var(--muted-foreground)]/10 bg-[var(--background)]/60 backdrop-blur-xl shadow-lg select-none pointer-events-none">
        <h5 className="text-[10px] font-black uppercase tracking-widest text-[var(--muted-foreground)] mb-3">Graph Legend</h5>
        <div className="flex flex-col gap-2.5">
          <div className="flex items-center gap-3">
            <div className="w-3 h-3 bg-[#6366f1] rounded-sm" /> 
            <span className="text-[10px] font-bold text-[var(--foreground)] uppercase">Equipment / Sensor</span>
          </div>
          <div className="flex items-center gap-3">
            <div className="w-4 h-2 bg-[#8b5cf6] rounded-none" /> 
            <span className="text-[10px] font-bold text-[var(--foreground)] uppercase">System Container</span>
          </div>
          <div className="flex items-center gap-3">
            <div className="w-0 h-0 border-l-[6px] border-l-transparent border-r-[6px] border-r-transparent border-b-[10px] border-b-[#f59e0b]" /> 
            <span className="text-[10px] font-bold text-[var(--foreground)] uppercase">Inlet Point</span>
          </div>
          <div className="flex items-center gap-3">
            <div className="w-0 h-0 border-l-[6px] border-l-transparent border-r-[6px] border-r-transparent border-t-[10px] border-t-[#f59e0b]" /> 
            <span className="text-[10px] font-bold text-[var(--foreground)] uppercase">Outlet Point</span>
          </div>
          <div className="flex items-center gap-3">
            <div className="w-3 h-3 bg-[#34d399] rounded-full" /> 
            <span className="text-[10px] font-bold text-[var(--foreground)] uppercase">Property / Observation</span>
          </div>
        </div>
      </div>
    </div>
  );
}

function NodeInfoCard({ nodes, activeNodeId }: { nodes: GraphNode[], activeNodeId: string }) {
  const node = nodes.find(n => n.id === activeNodeId);
  if (!node) return null;

  const type = node.type;
  const uri = (node.properties?.uri as string) ?? node.id;
  
  return (
    <div className="absolute bottom-6 right-6 z-20 w-[340px] animate-in slide-in-from-right-8 duration-500">
      <div className="p-6 rounded-2xl border border-[var(--accent)]/30 bg-[var(--background)]/80 backdrop-blur-xl shadow-[0_20px_50px_rgba(0,0,0,0.2)] overflow-hidden group">
        <div 
          className="absolute -top-12 -right-12 w-24 h-24 rounded-full blur-3xl opacity-20 pointer-events-none group-hover:opacity-40 transition-opacity duration-700"
          style={{ backgroundColor: getNodeColor(type) }}
        />
        
        <div className="flex items-start justify-between gap-3 mb-5 relative z-10">
          <div className="flex-1 min-w-0">
            <h4 className="text-[10px] font-black uppercase tracking-[0.3em] text-[var(--muted-foreground)] mb-1">
              Active Selection
            </h4>
            <span className="text-lg font-bold text-[var(--foreground)] truncate block leading-tight">
              {node.label}
            </span>
          </div>
          <span
            className="text-[10px] font-bold uppercase tracking-[0.2em] shrink-0 px-3 py-1 rounded-full border border-current"
            style={{ backgroundColor: `${getNodeColor(type)}15`, color: getNodeColor(type), borderColor: `${getNodeColor(type)}30` }}
          >
            {type.split("__").pop()?.replace(/_/g, " ") ?? type}
          </span>
        </div>

        <div className="space-y-4 relative z-10">
          <div className="flex flex-col gap-1">
            <span className="text-[10px] font-bold text-[var(--muted-foreground)] uppercase tracking-wider flex items-center gap-1.5">
              <Info size={10} /> URI
            </span>
            <span className="text-xs font-mono text-[var(--foreground)] bg-[var(--foreground)]/5 p-2 rounded-lg border border-[var(--foreground)]/5 truncate">
              {uri}
            </span>
          </div>

          {Object.entries(node.properties).length > 0 && (
            <div className="flex flex-col gap-1 border-t border-[var(--foreground)]/5 pt-4 mt-2">
              <span className="text-[10px] font-bold text-[var(--muted-foreground)] uppercase tracking-wider mb-2">Properties</span>
              <div className="max-h-[150px] overflow-y-auto pr-2 custom-scrollbar">
                {Object.entries(node.properties).filter(([k]) => k !== 'uri' && k !== 'label').map(([k, v]) => (
                  <div key={k} className="flex justify-between items-baseline mb-1 gap-4">
                    <span className="text-[10px] font-medium text-[var(--muted-foreground)] capitalize">{k.replace(/_/g, " ")}</span>
                    <span className="text-[11px] font-mono text-[var(--foreground)] text-right">{String(v)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

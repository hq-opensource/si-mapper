"use client";

import React, { useEffect, useState, useRef, useCallback } from "react";
import { ZoomIn, ZoomOut, RotateCcw, Network, Info, Activity, X } from "lucide-react";
import { useTheme } from "next-themes";
import "vis-network/styles/vis-network.css";
import { StatusPlaceholder } from "./StatusPlaceholder";
import { useWorkspace } from "@/context/WorkspaceContext";

// ─── Types & Constants ────────────────────────────────────────────────────────

interface GraphNode {
  id: string;
  label: string;
  type: string;
  allLabels: string[];
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

// ─── Search Highlight Constants ───────────────────────────────────────────────
const SEARCH_HIGHLIGHT_DURATION = 2000;
const SEARCH_HIGHLIGHT_START_FACTOR = 10;
const SEARCH_HIGHLIGHT_FINAL_FACTOR = 3.5;
const SEARCH_HIGHLIGHT_COLOR = "rgba(255, 215, 0, 0.5)";
const SEARCH_DEBOUNCE_DELAY = 300;
const SEARCH_MIN_CHARS = 2;

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
  const labelsList = (node.allLabels ?? [node.type]).join(", ");
  let tooltip = `Label : ${node.label}\n=======\nURI : ${node.id}\nTypes: ${labelsList}`;
  
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
  const { activeSystem } = useWorkspace();

  const [data, setData] = useState<GraphData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeNode, setActiveNode] = useState<string | null>(null);
  const [stabilizationProgress, setStabilizationProgress] = useState<{current: number, total: number} | null>(null);
  const [searchQuery, setSearchQuery] = useState("");

  // Refs so toolbar handlers can trigger highlight/reset without needing the selectNode event
  // (vis-network's selectNodes() does NOT fire selectNode events)
  const highlightNodeRef = useRef<((nodeId: string) => void) | null>(null);
  const resetHighlightRef = useRef<(() => void) | null>(null);

  // Search highlight animation state
  const searchHighlightRef = useRef<{ nodes: Array<{ nodeId: string; nodeSize: number }>; startTime: number } | null>(null);
  const searchAnimRafRef = useRef<number | null>(null);
  const searchDebounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const nodeSizeMapRef = useRef<Map<string, number>>(new Map());

  const cancelDebounce = useCallback(() => {
    if (searchDebounceRef.current !== null) {
      clearTimeout(searchDebounceRef.current);
      searchDebounceRef.current = null;
    }
  }, []);

  const clearSearchHighlight = useCallback(() => {
    searchHighlightRef.current = null;
    if (searchAnimRafRef.current !== null) {
      cancelAnimationFrame(searchAnimRafRef.current);
      searchAnimRafRef.current = null;
    }
    networkRef.current?.redraw();
  }, []);

  const startSearchHighlight = useCallback((nodeIds: string[]) => {
    const nodes = nodeIds.map(nodeId => ({ nodeId, nodeSize: nodeSizeMapRef.current.get(nodeId) ?? 15 }));
    searchHighlightRef.current = { nodes, startTime: performance.now() };
    if (searchAnimRafRef.current !== null) {
      cancelAnimationFrame(searchAnimRafRef.current);
      searchAnimRafRef.current = null;
    }
    const animate = () => {
      if (!searchHighlightRef.current) return;
      networkRef.current?.redraw();
      const elapsed = performance.now() - searchHighlightRef.current.startTime;
      if (elapsed < SEARCH_HIGHLIGHT_DURATION) {
        searchAnimRafRef.current = requestAnimationFrame(animate);
      } else {
        searchAnimRafRef.current = null;
        networkRef.current?.redraw(); // settle at final state
      }
    };
    searchAnimRafRef.current = requestAnimationFrame(animate);
  }, [SEARCH_HIGHLIGHT_DURATION]);

  // Fetch data — re-runs whenever the active system changes
  useEffect(() => {
    let cancelled = false;
    const db = encodeURIComponent(activeSystem?.neo4j_db_name ?? 'neo4j');
    const ns = encodeURIComponent(activeSystem?.id ?? '');
    setData(null);
    setLoading(true);
    setError(null);
    fetch(`/api/graph?db=${db}&ns=${ns}`)
      .then((r) => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json() as Promise<GraphData>; })
      .then((json) => { if (!cancelled) { setData(json); setLoading(false); } })
      .catch((err: Error) => { if (!cancelled) { setError(err.message); setLoading(false); } });
    return () => { cancelled = true; };
  }, [activeSystem?.id]);

  // Initialize Network
  useEffect(() => {
    if (!data || !containerRef.current) return;

    // We import vis-network dynamically or assume it's available via npm
    // Using vis-network directly as it was installed
    const vis = require("vis-network/standalone");

    // Cancel any in-flight search animation from a previous render
    if (searchAnimRafRef.current !== null) {
      cancelAnimationFrame(searchAnimRafRef.current);
      searchAnimRafRef.current = null;
    }
    searchHighlightRef.current = null;

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

    // Populate node size map for the search highlight animation
    nodeSizeMapRef.current.clear();
    visNodes.forEach(n => nodeSizeMapRef.current.set(n.id as string, n.size as number));

    const visEdges = data.edges.map(e => {
      // Logic to match ontology.html styles
      const label = e.label.toLowerCase();
      // Dashed for flows, properties, and measures (bob, scratch, qudt, etc.)
      const isMeasurement = label.includes(":") && (
        label.includes("bob:") || 
        label.includes("scratch:") || 
        label.includes("qudt:") ||
        label.includes("modulation") ||
        label.includes("volts") ||
        label.includes("amps") ||
        label.includes("pressure") ||
        label.includes("temp") ||
        label.includes("freq") ||
        label.includes("speed")
      );
      
      const isContains = label.includes("contains");

      return {
        id: e.id,
        from: e.source,
        to: e.target,
        label: e.label,
        font: {
          align: "top",
          size: 10,
          color: theme === "dark" ? "#94a3b8" : "#64748b",
          strokeWidth: 0
        },
        color: {
          inherit: "from",
          opacity: 0.6
        },
        arrows: {
          to: { enabled: true, scaleFactor: 0.5 }
        },
        dashes: isMeasurement ? [5, 5] : false,
        width: isContains ? 6 : 1.5,
        selectionWidth: 3
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
          enabled: false, // Show live movements instead of pre-calculating
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

    // Search result highlight: yellow circles drawn behind all matched nodes
    network.on("beforeDrawing", (ctx: CanvasRenderingContext2D) => {
      const highlight = searchHighlightRef.current;
      if (!highlight) return;

      const elapsed = Math.min(performance.now() - highlight.startTime, SEARCH_HIGHLIGHT_DURATION);
      const t = elapsed / SEARCH_HIGHLIGHT_DURATION;
      const eased = 1 - Math.pow(1 - t, 3);

      const nodeIds = highlight.nodes.map(n => n.nodeId);
      const positions = network.getPositions(nodeIds);

      for (const { nodeId, nodeSize } of highlight.nodes) {
        const pos = positions[nodeId];
        if (!pos) continue;

        const startRadius = nodeSize * SEARCH_HIGHLIGHT_START_FACTOR;
        const finalRadius = nodeSize * SEARCH_HIGHLIGHT_FINAL_FACTOR;

        // Ease-out cubic: fast initial shrink, settles gently at final size
        const radius = startRadius + (finalRadius - startRadius) * eased;

        ctx.save();
        ctx.beginPath();
        ctx.arc(pos.x, pos.y, radius, 0, 2 * Math.PI);
        ctx.fillStyle = SEARCH_HIGHLIGHT_COLOR;
        ctx.fill();
        ctx.restore();
      }
    });

    // Neighbourhood Highlight Logic
    let highlightActive = false;

    // Store as refs so handleSearch / handleReset can call them directly
    // (vis-network's selectNodes() does NOT fire the selectNode event)
    highlightNodeRef.current = (selectedNode: string) => {
      const nodes = networkData.nodes;
      const allNodes = nodes.get({ returnType: "Object" }) as any;
      highlightActive = true;
      const connectedNodes = network.getConnectedNodes(selectedNode) as string[];
      const neighbors = new Set(connectedNodes);
      for (let nodeId in allNodes) {
        const isSelected = nodeId === selectedNode;
        const isNeighbor = neighbors.has(nodeId);
        if (isSelected) {
          allNodes[nodeId].color = { background: allNodes[nodeId].originalColor, border: "#ffffff" };
          allNodes[nodeId].borderWidth = 4;
          allNodes[nodeId].shadow = { enabled: true, color: "rgba(99, 102, 241, 0.8)", size: 10 };
        } else if (isNeighbor) {
          allNodes[nodeId].color = { background: allNodes[nodeId].originalColor, border: theme === "dark" ? "#ffffff" : "#000000" };
          allNodes[nodeId].borderWidth = 2;
        } else {
          allNodes[nodeId].color = { background: allNodes[nodeId].originalColor, border: allNodes[nodeId].originalColor, opacity: 0.3 };
          allNodes[nodeId].font = { color: theme === "dark" ? "rgba(226, 232, 240, 0.2)" : "rgba(30, 41, 59, 0.2)" };
        }
      }
      nodes.update(Object.values(allNodes));
    };

    resetHighlightRef.current = () => {
      if (!highlightActive) return;
      const nodes = networkData.nodes;
      const allNodes = nodes.get({ returnType: "Object" }) as any;
      for (let nodeId in allNodes) {
        allNodes[nodeId].color = { background: allNodes[nodeId].originalColor, border: allNodes[nodeId].originalColor };
        allNodes[nodeId].borderWidth = 1;
        allNodes[nodeId].shadow = { enabled: false };
        allNodes[nodeId].font = { color: theme === "dark" ? "#e2e8f0" : "#1e293b" };
      }
      nodes.update(Object.values(allNodes));
      highlightActive = false;
    };

    network.on("selectNode", (params: any) => {
      if (params.nodes.length > 0) {
        const selectedNode = params.nodes[0];
        setActiveNode(selectedNode);
        highlightNodeRef.current?.(selectedNode);
      } else {
        resetHighlightRef.current?.();
        setActiveNode(null);
      }
    });

    network.on("stabilizationProgress", (params: {iterations: number, total: number}) => {
      setStabilizationProgress({ current: params.iterations, total: params.total });
    });

    network.on("stabilizationIterationsDone", () => {
      setStabilizationProgress(null);
      network.fit();
    });

    return () => {
      if (searchAnimRafRef.current !== null) {
        cancelAnimationFrame(searchAnimRafRef.current);
        searchAnimRafRef.current = null;
      }
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
    resetHighlightRef.current?.();
    clearSearchHighlight();
    setActiveNode(null);
    setSearchQuery("");
  };

  // Accepts the query string directly — never relies on the React state value
  // (avoids stale closure when onKeyDown fires before the state re-render completes)
  const doSearch = (query: string) => {
    if (!query.trim() || !networkRef.current || !data) return;
    const lq = query.toLowerCase();
    const matchedNodes = data.nodes.filter(n =>
      n.label.toLowerCase().includes(lq) ||
      n.id.toLowerCase().includes(lq) ||
      n.allLabels.some(l => l.toLowerCase().includes(lq))
    );
    if (matchedNodes.length > 0) {
      startSearchHighlight(matchedNodes.map(n => n.id));
    } else {
      clearSearchHighlight();
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
        <div className="flex items-center pl-2">
          {stabilizationProgress ? (
            <Activity className="w-4 h-4 text-[var(--primary)] animate-spin mr-2" />
          ) : (
            <Network className="w-4 h-4 text-[var(--muted-foreground)] mr-2" />
          )}
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => {
              const val = e.target.value;
              setSearchQuery(val);
              cancelDebounce();
              if (val.length < SEARCH_MIN_CHARS) {
                clearSearchHighlight();
              } else {
                searchDebounceRef.current = setTimeout(() => {
                  searchDebounceRef.current = null;
                  doSearch(val);
                }, SEARCH_DEBOUNCE_DELAY);
              }
            }}
            onKeyDown={(e) => {
              e.stopPropagation(); // prevent vis-network from intercepting keys
              if (e.key === "Enter") {
                cancelDebounce();
                doSearch((e.target as HTMLInputElement).value);
              }
              if (e.key === "Escape") {
                cancelDebounce();
                setSearchQuery("");
                clearSearchHighlight();
              }
            }}
            onPointerDown={(e) => e.stopPropagation()}
            placeholder={stabilizationProgress ? `Stabilizing (${stabilizationProgress.current})...` : "Search graph..."}
            className="w-40 px-1 py-1.5 bg-transparent border-none rounded-xl text-[11px] font-bold focus:outline-none transition-all placeholder:text-[var(--muted-foreground)]/40"
          />
        </div>
        <div className="w-[1px] h-6 bg-[var(--muted-foreground)]/10 mx-1" />
        <div className="flex items-center gap-1">
          <ToolbarButton onClick={handleZoomIn} title="Zoom In">
            <ZoomIn size={18} className="group-hover:scale-110 transition-transform" />
          </ToolbarButton>
          <ToolbarButton onClick={handleZoomOut} title="Zoom Out">
            <ZoomOut size={18} className="group-hover:scale-110 transition-transform" />
          </ToolbarButton>
          <ToolbarButton onClick={handleReset} title="Reset View">
            <RotateCcw size={18} className="group-hover:rotate-[-45deg] transition-transform" />
          </ToolbarButton>
        </div>
      </div>

      {/* Status Info (Optional overlays) */}
      <div className="absolute top-6 right-6 z-10 hidden md:block select-none pointer-events-none">
        <div className="px-4 py-2 rounded-full bg-[var(--background)]/40 backdrop-blur-md border border-[var(--foreground)]/5 flex items-center gap-3">
          <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          <span className="text-[10px] font-black uppercase tracking-widest text-[var(--muted-foreground)]">Live Physics Active</span>
        </div>
      </div>

      {/* Stabilization Overlay removed in favor of toolbar indicator */}

      {/* Details Card (Reusing InfoCard logic but for vis-network) */}
      {activeNode && (
        <NodeInfoCard nodes={data.nodes} activeNodeId={activeNode} onClose={() => {
          networkRef.current?.selectNodes([]);
          resetHighlightRef.current?.();
          setActiveNode(null);
        }} onLabelClick={(label) => {
          setSearchQuery(label);
          doSearch(label);
        }} />
      )}

      {/* Universal Legend (Bottom Center) */}
      <div className="absolute bottom-6 left-1/2 -translate-x-1/2 z-10 p-4 rounded-2xl border border-[var(--muted-foreground)]/10 bg-[var(--background)]/60 backdrop-blur-xl shadow-lg select-none pointer-events-none w-max max-w-[90vw]">
        <div className="grid grid-cols-4 grid-rows-2 gap-x-8 gap-y-3">
          {/* Column 1: Equipment & System */}
          <div className="flex items-center gap-3">
            <div className="w-3 h-3 bg-[#6366f1] rounded-sm" /> 
            <span className="text-[10px] font-bold tracking-wider text-[var(--foreground)] uppercase">Equipment / Sensor</span>
          </div>
          <div className="flex items-center gap-3">
            <div className="w-4 h-2 bg-[#8b5cf6] rounded-none" /> 
            <span className="text-[10px] font-bold tracking-wider text-[var(--foreground)] uppercase">System Container</span>
          </div>

          {/* Column 2: Points */}
          <div className="flex items-center gap-3">
            <div className="w-0 h-0 border-l-[5px] border-l-transparent border-r-[5px] border-r-transparent border-b-[9px] border-b-[#f59e0b]" /> 
            <span className="text-[10px] font-bold tracking-wider text-[var(--foreground)] uppercase">Inlet Point</span>
          </div>
          <div className="flex items-center gap-3">
            <div className="w-0 h-0 border-l-[5px] border-l-transparent border-r-[5px] border-r-transparent border-t-[9px] border-t-[#f59e0b]" /> 
            <span className="text-[10px] font-bold tracking-wider text-[var(--foreground)] uppercase">Outlet Point</span>
          </div>

          {/* Column 3: Properties & Metadata */}
          <div className="flex items-center gap-3">
            <div className="w-3 h-3 bg-[#34d399] rounded-full" /> 
            <span className="text-[10px] font-bold tracking-wider text-[var(--foreground)] uppercase">Property / Observation</span>
          </div>
          <div className="flex items-center gap-3">
            <div className="w-3 h-3 bg-[#64748b] rounded-full" /> 
            <span className="text-[10px] font-bold tracking-wider text-[var(--foreground)] uppercase">Definition / Metadata</span>
          </div>

          {/* Column 4: Edges */}
          <div className="flex items-center gap-3">
            <div className="w-6 h-[2.5px] bg-[var(--muted-foreground)]/40" /> 
            <span className="text-[10px] font-bold tracking-wider text-[var(--foreground)] uppercase">Standard Link</span>
          </div>
          <div className="flex items-center gap-3">
            <div className="w-6 h-0 border-t border-dashed border-[var(--muted-foreground)]/50" /> 
            <span className="text-[10px] font-bold tracking-wider text-[var(--foreground)] uppercase">Flow / Property</span>
          </div>
        </div>
      </div>
    </div>
  );
}

function ToolbarButton({ onClick, title, children }: { onClick: () => void; title: string; children: React.ReactNode }) {
  return (
    <button
      className="p-2 rounded-xl text-sm transition-all duration-300 flex items-center justify-center border border-[var(--muted-foreground)]/10 text-[var(--muted-foreground)] hover:text-[var(--accent)] hover:bg-[var(--accent)]/5 hover:border-[var(--accent)]/20 shadow-sm active:scale-90 group"
      onClick={onClick}
      title={title}
    >
      {children}
    </button>
  );
}

function NodeInfoCard({ nodes, activeNodeId, onClose, onLabelClick }: { nodes: GraphNode[], activeNodeId: string, onClose: () => void, onLabelClick: (label: string) => void }) {
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
          <div className="flex items-center gap-2 shrink-0">
          <span
            className="text-[10px] font-bold uppercase tracking-[0.2em] shrink-0 px-3 py-1 rounded-full border border-current"
            style={{ backgroundColor: `${getNodeColor(type)}15`, color: getNodeColor(type), borderColor: `${getNodeColor(type)}30` }}
          >
            {type.split("__").pop()?.replace(/_/g, " ") ?? type}
          </span>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-[var(--muted-foreground)] hover:text-[var(--foreground)] hover:bg-[var(--foreground)]/10 transition-all duration-200 active:scale-90"
            title="Close"
          >
            <X size={14} />
          </button>
          </div>
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

          {node.allLabels && node.allLabels.length > 0 && (
            <div className="flex flex-col gap-1">
              <span className="text-[10px] font-bold text-[var(--muted-foreground)] uppercase tracking-wider">Labels</span>
              <div className="flex flex-wrap gap-1">
                {node.allLabels.map((l) => (
                  <button
                    key={l}
                    onClick={() => onLabelClick(l)}
                    title={`Search for others like ${l}`}
                    className="text-[10px] font-mono px-2 py-0.5 rounded bg-[var(--foreground)]/5 border border-[var(--foreground)]/10 text-[var(--foreground)] cursor-pointer transition-all duration-150 hover:bg-[var(--accent)]/15 hover:border-[var(--accent)]/40 hover:text-[var(--accent)]"
                  >
                    {l}
                  </button>
                ))}
              </div>
            </div>
          )}

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

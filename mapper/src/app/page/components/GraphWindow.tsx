"use client";

import { SigmaContainer, useLoadGraph, useSigma, useRegisterEvents } from "@react-sigma/core";
import { useWorkerLayoutForceAtlas2 } from "@react-sigma/layout-forceatlas2";
import { MultiDirectedGraph } from "graphology";
import "@react-sigma/core/lib/style.css";
import { useEffect, useState, useCallback, useMemo } from "react";
import { ZoomIn, ZoomOut, RotateCcw, Network, Info, Activity } from "lucide-react";
import { StatusPlaceholder } from "./StatusPlaceholder";

// ─── Types ────────────────────────────────────────────────────────────────────

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

// ─── VIP Color Palette ────────────────────────────────────────────────────────

// High-end, vibrant colors that pop in both light and dark modes
const TYPE_COLORS: Record<string, string> = {
  // OWL/Ontology concepts - Neon & Glowy tones
  owl__Class: "#818cf8", // Electric Indigo
  owl__ObjectProperty: "#fbbf24", // Vibrant Amber
  owl__DatatypeProperty: "#34d399", // Neon Emerald
  owl__AnnotationProperty: "#22d3ee", // Bright Cyan
  owl__Restriction: "#f472b6", // Soft Neon Pink
  owl__NamedIndividual: "#a78bfa", // Electric Violet
  
  // RDFS
  rdfs__Class: "#818cf8",
  rdfs__Property: "#fbbf24",
  
  // HVAC / Building specific (VIP styles)
  Equipment: "#6366f1", // Deep Indigo
  ConnectionPoint: "#f59e0b", // Gold Amber
  System: "#8b5cf6", // Purple Aura
  Sensor: "#06b6d4", // Cyber Cyan
  Zone: "#ec4899", // Rose Pink
};

const TYPE_LABELS: Record<string, string> = {
  owl__Class: "OWL Class",
  owl__ObjectProperty: "Object Property",
  owl__DatatypeProperty: "Datatype Property",
  owl__AnnotationProperty: "Annotation",
  owl__Restriction: "Restriction",
  owl__NamedIndividual: "Individual",
  rdfs__Class: "RDFS Class",
  rdfs__Property: "RDFS Property",
  Resource: "Resource",
};

const DEFAULT_COLOR = "#64748b";

function getNodeColor(type: string): string {
  if (TYPE_COLORS[type]) return TYPE_COLORS[type];
  for (const [key, color] of Object.entries(TYPE_COLORS)) {
    if (type.includes(key)) return color;
  }
  return DEFAULT_COLOR;
}

function friendlyType(type: string): string {
  return TYPE_LABELS[type] ?? type.replace("__", ": ").replace(/_/g, " ");
}

// ─── GraphLoader: builds graph and runs dynamic FA2 layout ───────────────

function GraphLoader({ nodes, edges }: { nodes: GraphNode[]; edges: GraphEdge[] }) {
  const loadGraph = useLoadGraph();
  const { start, stop } = useWorkerLayoutForceAtlas2({
    settings: {
      gravity: 0.01, // Very low constant gravity to keep it centered
      scalingRatio: 10, // Adjusted for LinLog mode
      linLogMode: true, // Key for distinct clustering in knowledge graphs
      outboundAttractionDistribution: true, // Pushes hubs to center, others to periphery
      barnesHutOptimize: true,
      barnesHutTheta: 0.5,
      slowDown: 2, 
      adjustSizes: true,
    }
  });

  useEffect(() => {
    if (nodes.length === 0) return;

    const graph = new MultiDirectedGraph();

    // Add nodes with Organic Scattering
    // We scatter them in a wide space so they can find their clusters naturally
    nodes.forEach((n) => {
      graph.addNode(n.id, {
        label: n.label,
        size: 5,
        color: getNodeColor(n.type),
        x: (Math.random() - 0.5) * 1000,
        y: (Math.random() - 0.5) * 1000,
        nodeType: n.type,
        properties: n.properties,
      });
    });

    // Add edges
    edges.forEach((e) => {
      try {
        graph.addEdgeWithKey(e.id, e.source, e.target, {
          label: e.label,
          type: "arrow",
          size: 1,
          color: "rgba(148, 163, 184, 0.4)", // Muted link color
        });
      } catch {
        // skip edges referencing missing nodes
      }
    });

    // Degree-based node sizing with better range
    graph.forEachNode((key) => {
      const deg = graph.degree(key);
      graph.setNodeAttribute(key, "size", Math.max(6, Math.min(22, Math.log(deg + 1) * 10)));
    });

    loadGraph(graph);
    
    // Start layout animation
    start();
    
    // Stop after 3 seconds to preserve CPU
    const timer = setTimeout(() => stop(), 3000);
    return () => {
      clearTimeout(timer);
      stop();
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [nodes, edges, loadGraph]);

  return null;
}

// ─── GraphEvents ──────────────────────────────────────────────────────────────

function GraphEvents({ onActiveNode }: { onActiveNode: (nodeId: string | null) => void }) {
  const sigma = useSigma();
  const registerEvents = useRegisterEvents();
  const [hoveredNode, setHoveredNode] = useState<string | null>(null);
  const [clickedNode, setClickedNode] = useState<string | null>(null);

  useEffect(() => {
    registerEvents({
      enterNode: ({ node }) => setHoveredNode(node),
      leaveNode: () => setHoveredNode(null),
      clickNode: ({ node }) => setClickedNode((prev) => (prev === node ? null : node)),
      clickStage: () => { setClickedNode(null); setHoveredNode(null); },
    });
  }, [registerEvents]);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") { setClickedNode(null); setHoveredNode(null); }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);

  useEffect(() => {
    onActiveNode(clickedNode ?? hoveredNode);
  }, [clickedNode, hoveredNode, onActiveNode]);

  useEffect(() => {
    const activeNode = clickedNode ?? hoveredNode;
    if (!activeNode) {
      sigma.setSetting("nodeReducer", null);
      sigma.setSetting("edgeReducer", null);
      return;
    }

    const neighbors = new Set(sigma.getGraph().neighbors(activeNode));

    sigma.setSetting("nodeReducer", (node: string, data: Record<string, unknown>) => {
      if (node === activeNode) return { 
        ...data, 
        highlighted: true, 
        size: (data.size as number) * 1.8,
        color: "#6366f1", // Highlight with accent color
        zIndex: 999 
      };
      if (neighbors.has(node)) return {
        ...data,
        highlighted: true,
        size: (data.size as number) * 1.2
      };
      return { ...data, color: "rgba(100,116,139,0.15)", size: (data.size as number) * 0.6, label: "" };
    });

    sigma.setSetting("edgeReducer", (edge: string, data: Record<string, unknown>) => {
      const src = sigma.getGraph().source(edge);
      const tgt = sigma.getGraph().target(edge);
      if (src === activeNode || tgt === activeNode) return {
        ...data,
        color: "#6366f1", // Accent color for active paths
        size: 3,
        zIndex: 1
      };
      return { ...data, color: "rgba(100,116,139,0.04)" };
    });
  }, [hoveredNode, clickedNode, sigma]);

  return null;
}

// ─── NodeInfoCard ─────────────────────────────────────────────────────────────

function NodeInfoCardInner({ activeNode }: { activeNode: string | null }) {
  const sigma = useSigma();
  if (!activeNode) return null;

  const graph = sigma.getGraph();
  const attrs = graph.getNodeAttributes(activeNode) as {
    label?: string;
    nodeType?: string;
    properties?: Record<string, unknown>;
  };

  const label = attrs.label ?? activeNode;
  const type = attrs.nodeType ?? "Resource";
  const degree = graph.degree(activeNode);
  const uri = (attrs.properties?.uri as string) ?? activeNode;
  const namespace = uri.includes("#") ? uri.split("#")[0].split("/").pop() : uri.split("/").slice(-2, -1)[0];

  return (
    <div className="absolute bottom-6 right-6 z-20 w-[340px] animate-in slide-in-from-right-8 duration-500">
      <div className="p-6 rounded-2xl border border-[var(--accent)]/30 bg-[var(--background)]/80 backdrop-blur-xl shadow-[0_20px_50px_rgba(0,0,0,0.2)] overflow-hidden group">
        {/* Decorative background glow */}
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
              {label}
            </span>
          </div>
          <span
            className="text-[10px] font-bold uppercase tracking-[0.2em] shrink-0 px-3 py-1 rounded-full border border-current"
            style={{ backgroundColor: `${getNodeColor(type)}15`, color: getNodeColor(type), borderColor: `${getNodeColor(type)}30` }}
          >
            {friendlyType(type)}
          </span>
        </div>

        <div className="space-y-4 relative z-10">
          {namespace && (
            <div className="flex flex-col gap-1">
              <span className="text-[10px] font-bold text-[var(--muted-foreground)] uppercase tracking-wider flex items-center gap-1.5">
                <Info size={10} /> Namespace
              </span>
              <span className="text-xs font-mono text-[var(--foreground)] bg-[var(--foreground)]/5 p-2 rounded-lg border border-[var(--foreground)]/5 truncate">
                {namespace}
              </span>
            </div>
          )}
          
          <div className="flex gap-8">
            <div className="flex flex-col gap-1">
              <span className="text-[10px] font-bold text-[var(--muted-foreground)] uppercase tracking-wider flex items-center gap-1.5">
                <Activity size={10} /> Degree
              </span>
              <span className="text-xl font-black text-[var(--foreground)]">{degree}</span>
            </div>
          </div>

          <div className="flex flex-col gap-1 border-t border-[var(--foreground)]/5 pt-4 mt-2">
            <span className="text-[10px] font-bold text-[var(--muted-foreground)] uppercase tracking-wider">Resource URI</span>
            <span className="text-xs font-mono text-[var(--foreground)] opacity-50 break-all select-all hover:opacity-100 transition-opacity duration-300">
              {uri}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Toolbar ──────────────────────────────────────────────────────────────────

function ToolbarInner() {
  const sigma = useSigma();
  const btn = "p-3 rounded-xl text-sm transition-all duration-300 flex items-center justify-center border border-[var(--muted-foreground)]/10 text-[var(--muted-foreground)] hover:text-[var(--accent)] hover:bg-[var(--accent)]/5 hover:border-[var(--accent)]/20 shadow-sm active:scale-90 group";

  return (
    <div className="absolute top-6 left-6 z-20 flex flex-col gap-2 p-2 rounded-2xl border border-[var(--muted-foreground)]/10 bg-[var(--background)]/60 backdrop-blur-xl shadow-[0_15px_30px_rgba(0,0,0,0.05)]">
      <button className={btn} onClick={() => sigma.getCamera().animatedZoom()} aria-label="Zoom in" title="Zoom In">
        <ZoomIn size={18} className="group-hover:scale-110 transition-transform" />
      </button>
      <button className={btn} onClick={() => sigma.getCamera().animatedUnzoom()} aria-label="Zoom out" title="Zoom Out">
        <ZoomOut size={18} className="group-hover:scale-110 transition-transform" />
      </button>
      <div className="h-[1px] mx-2 bg-[var(--muted-foreground)]/10 my-1" />
      <button className={btn} onClick={() => sigma.getCamera().animatedReset()} aria-label="Reset view" title="Reset View">
        <RotateCcw size={18} className="group-hover:rotate-[-45deg] transition-transform" />
      </button>
    </div>
  );
}

// ─── SigmaContent ─────────────────────────────────────────────────────────────

function SigmaContent({ nodes, edges }: { nodes: GraphNode[]; edges: GraphEdge[] }) {
  const [activeNode, setActiveNode] = useState<string | null>(null);
  const handleActiveNode = useCallback((id: string | null) => setActiveNode(id), []);

  return (
    <>
      <GraphLoader nodes={nodes} edges={edges} />
      <GraphEvents onActiveNode={handleActiveNode} />
      <ToolbarInner />
      <NodeInfoCardInner activeNode={activeNode} />
    </>
  );
}

// ─── GraphWindow ──────────────────────────────────────────────────────────────

export function GraphWindow() {
  const [data, setData] = useState<GraphData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetch("/api/graph")
      .then((r) => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json() as Promise<GraphData>; })
      .then((json) => { if (!cancelled) { setData(json); setLoading(false); } })
      .catch((err: Error) => { if (!cancelled) { setError(err.message); setLoading(false); } });
    return () => { cancelled = true; };
  }, []);

  // Resolve theme colors for Sigma
  const [themeColors, setThemeColors] = useState({ foreground: "#94a3b8" });

  useEffect(() => {
    const updateColors = () => {
      const style = getComputedStyle(document.documentElement);
      const foreground = style.getPropertyValue('--muted-foreground').trim() || "#94a3b8";
      setThemeColors({ foreground });
    };

    updateColors();
    // Observe theme class changes
    const observer = new MutationObserver(updateColors);
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] });
    return () => observer.disconnect();
  }, []);

  if (loading) return <div className="w-full h-full flex items-center justify-center"><StatusPlaceholder icon={Network} title="LOADING GRAPH" subtitle="Fetching nodes and relationships from Neo4j..." /></div>;
  if (error) return <div className="w-full h-full flex items-center justify-center"><StatusPlaceholder icon={Network} title="GRAPH UNAVAILABLE" subtitle="Could not connect to the graph API. Ensure Neo4j is running." /></div>;
  if (!data || data.nodes.length === 0) return <div className="w-full h-full flex items-center justify-center"><StatusPlaceholder icon={Network} title="NO GRAPH DATA" subtitle="Run 'Load TTL to Neo4j' from the agent to import the current ontology" /></div>;

  return (
    <div className="relative w-full h-full bg-[radial-gradient(circle_at_center,var(--accent)/[0.03]_0%,transparent_70%)]">
      <SigmaContainer
        graph={MultiDirectedGraph}
        style={{ height: "100%", width: "100%" }}
        settings={{
          renderEdgeLabels: true,
          defaultEdgeType: "arrow",
          labelFont: "Outfit, Inter, system-ui",
          labelSize: 13,
          labelWeight: "600",
          labelColor: { color: themeColors.foreground },
          edgeLabelFont: "Outfit, Inter, system-ui",
          edgeLabelSize: 9,
          edgeLabelWeight: "500",
          zoomToSizeRatioFunction: (x: number) => x,
          itemSizesReference: "screen", // Ensure radius is in pixels, not graph units
          zIndex: true,
        }}
      >
        <SigmaContent nodes={data.nodes} edges={data.edges} />
      </SigmaContainer>
    </div>
  );
}

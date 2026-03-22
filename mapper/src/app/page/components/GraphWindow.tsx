"use client";

import { SigmaContainer, useLoadGraph, useSigma, useRegisterEvents } from "@react-sigma/core";
import forceAtlas2 from "graphology-layout-forceatlas2";
import { MultiDirectedGraph } from "graphology";
import "@react-sigma/core/lib/style.css";
import { useEffect, useState, useCallback } from "react";
import { ZoomIn, ZoomOut, RotateCcw, Network } from "lucide-react";
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

// ─── Color Palette ────────────────────────────────────────────────────────────

const TYPE_COLORS: Record<string, string> = {
  // OWL concepts
  owl__Class: "#4f46e5",
  owl__ObjectProperty: "#f59e0b",
  owl__DatatypeProperty: "#10b981",
  owl__AnnotationProperty: "#06b6d4",
  owl__Restriction: "#ec4899",
  owl__NamedIndividual: "#8b5cf6",
  // RDFS
  rdfs__Class: "#4f46e5",
  rdfs__Property: "#f59e0b",
  // ASHRAE 223P instances (if present in data)
  Equipment: "#4f46e5",
  ConnectionPoint: "#f59e0b",
  System: "#8b5cf6",
  Sensor: "#06b6d4",
  Zone: "#ec4899",
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

// ─── GraphLoader: builds graph and runs synchronous FA2 layout ───────────────

function GraphLoader({ nodes, edges }: { nodes: GraphNode[]; edges: GraphEdge[] }) {
  const loadGraph = useLoadGraph();

  useEffect(() => {
    if (nodes.length === 0) return;

    const graph = new MultiDirectedGraph();

    // Add nodes with random seed positions
    nodes.forEach((n) => {
      graph.addNode(n.id, {
        label: n.label,
        size: 6,
        color: getNodeColor(n.type),
        x: Math.random() * 100,
        y: Math.random() * 100,
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
        });
      } catch {
        // skip edges referencing missing nodes
      }
    });

    // Degree-based node sizing
    graph.forEachNode((key) => {
      const deg = graph.degree(key);
      graph.setNodeAttribute(key, "size", Math.max(4, Math.log(deg + 1) * 8));
    });

    // Run ForceAtlas2 synchronously — graph loads pre-positioned, no animation needed
    forceAtlas2.assign(graph, {
      iterations: 2000,
      settings: {
        gravity: 0.2,
        scalingRatio: 30,
        barnesHutOptimize: true,
        barnesHutTheta: 0.5,
        slowDown: 1,
        adjustSizes: true,
      },
    });

    loadGraph(graph);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [nodes, edges]);

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
      if (node === activeNode) return { ...data, highlighted: true, size: (data.size as number) * 1.5 };
      if (neighbors.has(node)) return data;
      return { ...data, color: "rgba(100,116,139,0.25)", size: (data.size as number) * 0.7 };
    });

    sigma.setSetting("edgeReducer", (edge: string, data: Record<string, unknown>) => {
      const src = sigma.getGraph().source(edge);
      const tgt = sigma.getGraph().target(edge);
      if (src === activeNode || tgt === activeNode) return data;
      return { ...data, color: "rgba(100,116,139,0.08)" };
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
    <div className="absolute bottom-4 right-4 z-20 w-[300px]">
      <div className="p-4 rounded-xl border border-[var(--accent)]/20 bg-[var(--background)]/90 backdrop-blur-md shadow-[0_8px_30px_rgb(0,0,0,0.12)]">
        <div className="flex items-start justify-between gap-2 mb-3">
          <span className="text-sm font-bold text-[var(--foreground)] truncate flex-1">{label}</span>
          <span
            className="text-[10px] font-bold uppercase tracking-[0.25em] shrink-0 px-2 py-0.5 rounded-full"
            style={{ backgroundColor: `${getNodeColor(type)}22`, color: getNodeColor(type) }}
          >
            {friendlyType(type)}
          </span>
        </div>

        <div className="border-t border-[var(--muted-foreground)]/10 mb-3" />

        <div className="space-y-2 text-sm">
          {namespace && (
            <div className="flex gap-2">
              <span className="text-[var(--muted-foreground)] text-xs w-24 shrink-0 pt-0.5">Namespace</span>
              <span className="text-[var(--foreground)] font-mono text-xs break-all">{namespace}</span>
            </div>
          )}
          <div className="flex gap-2">
            <span className="text-[var(--muted-foreground)] text-xs w-24 shrink-0 pt-0.5">Connections</span>
            <span className="text-[var(--foreground)]">{degree}</span>
          </div>
          <div className="flex gap-2">
            <span className="text-[var(--muted-foreground)] text-xs w-24 shrink-0 pt-0.5">URI</span>
            <span className="text-[var(--foreground)] font-mono text-[11px] break-all opacity-70">{uri}</span>
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Toolbar ──────────────────────────────────────────────────────────────────

function ToolbarInner() {
  const sigma = useSigma();
  const btn = "p-2 rounded-lg text-sm transition-all duration-200 flex items-center gap-2 border border-transparent text-[var(--muted-foreground)] hover:text-[var(--foreground)] hover:bg-[var(--foreground)]/5";

  return (
    <div className="absolute top-4 left-4 z-20 flex flex-col gap-1 p-2 rounded-xl border border-[var(--muted-foreground)]/20 bg-[var(--background)]/80 backdrop-blur-md shadow-[0_8px_30px_rgb(0,0,0,0.04)]">
      <button className={btn} onClick={() => sigma.getCamera().animatedZoom()} aria-label="Zoom in" title="Zoom In">
        <ZoomIn size={16} />
      </button>
      <button className={btn} onClick={() => sigma.getCamera().animatedUnzoom()} aria-label="Zoom out" title="Zoom Out">
        <ZoomOut size={16} />
      </button>
      <button className={btn} onClick={() => sigma.getCamera().animatedReset()} aria-label="Reset view" title="Reset View">
        <RotateCcw size={16} />
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

  if (loading) return <div className="w-full h-full flex items-center justify-center"><StatusPlaceholder icon={Network} title="LOADING GRAPH" subtitle="Fetching nodes and relationships from Neo4j..." /></div>;
  if (error) return <div className="w-full h-full flex items-center justify-center"><StatusPlaceholder icon={Network} title="GRAPH UNAVAILABLE" subtitle="Could not connect to the graph API. Ensure Neo4j is running." /></div>;
  if (!data || data.nodes.length === 0) return <div className="w-full h-full flex items-center justify-center"><StatusPlaceholder icon={Network} title="NO GRAPH DATA" subtitle="Run 'Load TTL to Neo4j' from the agent to import the current ontology" /></div>;

  return (
    <div className="relative w-full h-full">
      <SigmaContainer
        graph={MultiDirectedGraph}
        style={{ height: "100%", width: "100%" }}
        settings={{
          renderEdgeLabels: true,
          defaultEdgeType: "arrow",
          labelFont: "Outfit, Inter, system-ui",
          labelSize: 12,
          labelWeight: "700",
          labelColor: { color: "#94a3b8" },
          edgeLabelFont: "Outfit, Inter, system-ui",
          edgeLabelSize: 10,
          edgeLabelWeight: "400",
          zoomToSizeRatioFunction: (x: number) => x,
          itemSizesReference: "positions",
        }}
      >
        <SigmaContent nodes={data.nodes} edges={data.edges} />
      </SigmaContainer>
    </div>
  );
}

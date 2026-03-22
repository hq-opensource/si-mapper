"use client";

import { SigmaContainer, useLoadGraph, useSigma, useRegisterEvents } from "@react-sigma/core";
import { useWorkerLayoutForceAtlas2 } from "@react-sigma/layout-forceatlas2";
import { MultiDirectedGraph } from "graphology";
import "@react-sigma/core/lib/style.css";
import { useEffect, useState, useCallback } from "react";
import { ZoomIn, ZoomOut, RotateCcw, Play, Pause, Network } from "lucide-react";
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

// ─── RDF Type Color Palette ───────────────────────────────────────────────────

const TYPE_COLORS: Record<string, string> = {
  Equipment: "#4f46e5",
  Fan: "#4f46e5",
  Pump: "#4f46e5",
  Coil: "#4f46e5",
  Humidifier: "#4f46e5",
  Duct: "#10b981",
  Pipe: "#10b981",
  ConnectionPoint: "#f59e0b",
  InletConnectionPoint: "#f59e0b",
  OutletConnectionPoint: "#f59e0b",
  BidirectionalConnectionPoint: "#f59e0b",
  System: "#8b5cf6",
  Subsystem: "#8b5cf6",
  Sensor: "#06b6d4",
  Actuator: "#06b6d4",
  Zone: "#ec4899",
  Space: "#ec4899",
};

const DEFAULT_COLOR = "#64748b";

function getNodeColor(type: string): string {
  if (TYPE_COLORS[type]) return TYPE_COLORS[type];
  for (const [key, color] of Object.entries(TYPE_COLORS)) {
    if (type.includes(key)) return color;
  }
  return DEFAULT_COLOR;
}

// ─── GraphLoader: child of SigmaContainer ────────────────────────────────────

interface GraphLoaderProps {
  nodes: GraphNode[];
  edges: GraphEdge[];
  onLayoutChange: (isRunning: boolean) => void;
  onLayoutReady: (controls: { start: () => void; stop: () => void }) => void;
}

function GraphLoader({ nodes, edges, onLayoutChange, onLayoutReady }: GraphLoaderProps) {
  const loadGraph = useLoadGraph();
  const { start, stop, isRunning } = useWorkerLayoutForceAtlas2({
    settings: {
      gravity: 1,
      scalingRatio: 10,
      barnesHutOptimize: true,
      barnesHutTheta: 0.5,
      slowDown: 5,
      adjustSizes: true,
    },
  });

  // Expose controls to parent
  useEffect(() => {
    onLayoutReady({ start, stop });
  }, [start, stop, onLayoutReady]);

  // Keep parent in sync with isRunning state
  useEffect(() => {
    onLayoutChange(isRunning);
  }, [isRunning, onLayoutChange]);

  useEffect(() => {
    if (nodes.length === 0) return;

    const graph = new MultiDirectedGraph();

    // First pass: add all nodes with default size
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

    // Add edges (skip edges referencing missing nodes)
    edges.forEach((e) => {
      try {
        graph.addEdgeWithKey(e.id, e.source, e.target, {
          label: e.label,
          type: "arrow",
        });
      } catch {
        // Skip edges that reference nodes not in the graph
      }
    });

    // Second pass: update sizes based on actual degree
    graph.forEachNode((nodeKey) => {
      const deg = graph.degree(nodeKey);
      graph.setNodeAttribute(nodeKey, "size", Math.max(4, Math.log(deg + 1) * 8));
    });

    loadGraph(graph);
    start();

    // Auto-stop ForceAtlas2 after 5 seconds
    const timer = setTimeout(() => stop(), 5000);
    return () => clearTimeout(timer);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [nodes, edges]);

  return null;
}

// ─── GraphEvents: registers hover/click reducers ─────────────────────────────

interface GraphEventsProps {
  onActiveNode: (nodeId: string | null) => void;
}

function GraphEvents({ onActiveNode }: GraphEventsProps) {
  const sigma = useSigma();
  const registerEvents = useRegisterEvents();
  const [hoveredNode, setHoveredNode] = useState<string | null>(null);
  const [clickedNode, setClickedNode] = useState<string | null>(null);

  // Register sigma events
  useEffect(() => {
    registerEvents({
      enterNode: ({ node }) => setHoveredNode(node),
      leaveNode: () => {
        setHoveredNode((prev) => {
          // Only clear hover if not locked by click
          void prev;
          return null;
        });
      },
      clickNode: ({ node }) =>
        setClickedNode((prev) => (prev === node ? null : node)),
      clickStage: () => {
        setClickedNode(null);
        setHoveredNode(null);
      },
    });
  }, [registerEvents]);

  // Escape key clears click lock
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setClickedNode(null);
        setHoveredNode(null);
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);

  // Notify parent of active node for NodeInfoCard
  useEffect(() => {
    onActiveNode(clickedNode ?? hoveredNode);
  }, [clickedNode, hoveredNode, onActiveNode]);

  // Dynamic reducers via sigma.setSetting — avoids stale closure on SigmaContainer props
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
      return { ...data, color: "rgba(100,116,139,0.4)", size: (data.size as number) * 0.6 };
    });

    sigma.setSetting("edgeReducer", (edge: string, data: Record<string, unknown>) => {
      const src = sigma.getGraph().source(edge);
      const tgt = sigma.getGraph().target(edge);
      if (src === activeNode || tgt === activeNode) return data;
      return { ...data, color: "rgba(100,116,139,0.15)" };
    });
  }, [hoveredNode, clickedNode, sigma]);

  return null;
}

// ─── NodeInfoCard ─────────────────────────────────────────────────────────────

interface NodeInfoCardProps {
  sigma: ReturnType<typeof useSigma>;
  nodeId: string;
}

function NodeInfoCard({ sigma, nodeId }: NodeInfoCardProps) {
  const graph = sigma.getGraph();
  const attrs = graph.getNodeAttributes(nodeId) as {
    label?: string;
    nodeType?: string;
    properties?: Record<string, unknown>;
  };

  const label = attrs.label ?? nodeId;
  const nodeType = attrs.nodeType ?? "Resource";
  const degree = graph.degree(nodeId);
  const uri = (attrs.properties?.uri as string) ?? nodeId;

  return (
    <div className="absolute bottom-4 right-4 z-20 w-[280px]">
      <div className="p-4 rounded-xl border border-[var(--accent)]/20 bg-[var(--background)]/90 backdrop-blur-md shadow-[0_8px_30px_rgb(0,0,0,0.12)] transition-opacity duration-200 translate-y-0">
        {/* Header */}
        <div className="flex items-start justify-between gap-2 mb-1">
          <span className="text-sm font-bold text-[var(--foreground)] truncate flex-1">{label}</span>
          <span className="text-[10px] font-bold uppercase tracking-[0.3em] text-[var(--accent)] opacity-80 shrink-0">
            {nodeType}
          </span>
        </div>

        <div className="border-t border-[var(--muted-foreground)]/10 my-3" />

        {/* Property rows */}
        <div className="space-y-2">
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.2em] text-[var(--muted-foreground)] opacity-60">URI</p>
            <p className="text-sm font-normal text-[var(--foreground)] break-all">{uri}</p>
          </div>
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.2em] text-[var(--muted-foreground)] opacity-60">TYPE</p>
            <p className="text-sm font-normal text-[var(--foreground)]">{nodeType}</p>
          </div>
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.2em] text-[var(--muted-foreground)] opacity-60">
              CONNECTIONS
            </p>
            <p className="text-sm font-normal text-[var(--foreground)]">{degree}</p>
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── ToolbarInner: inside SigmaContainer for sigma access ────────────────────

interface ToolbarInnerProps {
  isRunning: boolean;
  layoutControls: { start: () => void; stop: () => void } | null;
}

function ToolbarInner({ isRunning, layoutControls }: ToolbarInnerProps) {
  const sigma = useSigma();

  const handleZoomIn = useCallback(() => {
    sigma.getCamera().animatedZoom();
  }, [sigma]);

  const handleZoomOut = useCallback(() => {
    sigma.getCamera().animatedUnzoom();
  }, [sigma]);

  const handleReset = useCallback(() => {
    sigma.getCamera().animatedReset();
  }, [sigma]);

  const handleToggleLayout = useCallback(() => {
    if (!layoutControls) return;
    if (isRunning) {
      layoutControls.stop();
    } else {
      layoutControls.start();
    }
  }, [isRunning, layoutControls]);

  const btnBase =
    "px-3 py-2 rounded-lg text-sm font-bold transition-all duration-300 flex items-center gap-2 border border-transparent text-[var(--muted-foreground)] hover:text-[var(--foreground)] hover:bg-[var(--foreground)]/5";
  const btnActive =
    "text-[var(--accent)] bg-[var(--accent)]/15 border-[var(--accent)]/10 shadow-sm";

  return (
    <div className="absolute top-4 left-4 z-20 flex flex-col gap-2 p-2 rounded-xl border border-[var(--muted-foreground)]/20 bg-[var(--background)]/80 backdrop-blur-md shadow-[0_8px_30px_rgb(0,0,0,0.04)]">
      <button
        className={btnBase}
        onClick={handleZoomIn}
        aria-label="Zoom in"
        title="Zoom In"
      >
        <ZoomIn size={16} />
      </button>
      <button
        className={btnBase}
        onClick={handleZoomOut}
        aria-label="Zoom out"
        title="Zoom Out"
      >
        <ZoomOut size={16} />
      </button>
      <button
        className={btnBase}
        onClick={handleReset}
        aria-label="Reset layout"
        title="Reset Layout"
      >
        <RotateCcw size={16} />
      </button>
      <button
        className={`${btnBase} ${isRunning ? btnActive : ""}`}
        onClick={handleToggleLayout}
        aria-label={isRunning ? "Pause layout" : "Run layout"}
        title={isRunning ? "Pause Layout" : "Run Layout"}
      >
        {isRunning ? <Pause size={16} /> : <Play size={16} />}
      </button>
    </div>
  );
}

// ─── NodeInfoCardInner: inside SigmaContainer for sigma access ───────────────

interface NodeInfoCardInnerProps {
  activeNode: string | null;
}

function NodeInfoCardInner({ activeNode }: NodeInfoCardInnerProps) {
  const sigma = useSigma();
  if (!activeNode) return null;
  return <NodeInfoCard sigma={sigma} nodeId={activeNode} />;
}

// ─── SigmaContent: combines all inner components ─────────────────────────────

interface SigmaContentProps {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

function SigmaContent({ nodes, edges }: SigmaContentProps) {
  const [isRunning, setIsRunning] = useState(false);
  const [layoutControls, setLayoutControls] = useState<{
    start: () => void;
    stop: () => void;
  } | null>(null);
  const [activeNode, setActiveNode] = useState<string | null>(null);

  const handleLayoutChange = useCallback((running: boolean) => {
    setIsRunning(running);
  }, []);

  const handleLayoutReady = useCallback(
    (controls: { start: () => void; stop: () => void }) => {
      setLayoutControls(controls);
    },
    []
  );

  const handleActiveNode = useCallback((nodeId: string | null) => {
    setActiveNode(nodeId);
  }, []);

  return (
    <>
      <GraphLoader
        nodes={nodes}
        edges={edges}
        onLayoutChange={handleLayoutChange}
        onLayoutReady={handleLayoutReady}
      />
      <GraphEvents onActiveNode={handleActiveNode} />
      <ToolbarInner isRunning={isRunning} layoutControls={layoutControls} />
      <NodeInfoCardInner activeNode={activeNode} />
    </>
  );
}

// ─── GraphWindow: top-level exported component ───────────────────────────────

export function GraphWindow() {
  const [data, setData] = useState<GraphData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    setLoading(true);
    setError(null);

    fetch("/api/graph")
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json() as Promise<GraphData>;
      })
      .then((json) => {
        if (!cancelled) {
          setData(json);
          setLoading(false);
        }
      })
      .catch((err: Error) => {
        if (!cancelled) {
          setError(err.message);
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

  // Loading state
  if (loading) {
    return (
      <div className="relative w-full h-full flex items-center justify-center">
        <StatusPlaceholder
          icon={Network}
          title="LOADING GRAPH"
          subtitle="Fetching nodes and relationships from Neo4j..."
        />
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="relative w-full h-full flex items-center justify-center">
        <StatusPlaceholder
          icon={Network}
          title="GRAPH UNAVAILABLE"
          subtitle="Could not connect to the graph API. Ensure Neo4j is running."
        />
      </div>
    );
  }

  // Empty state
  if (!data || data.nodes.length === 0) {
    return (
      <div className="relative w-full h-full flex items-center justify-center">
        <StatusPlaceholder
          icon={Network}
          title="NO GRAPH DATA"
          subtitle="Run 'Load TTL to Neo4j' from the agent to import the current ontology"
        />
      </div>
    );
  }

  // Graph canvas
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
          edgeLabelWeight: "700",
          zoomToSizeRatioFunction: (x: number) => x,
          itemSizesReference: "positions",
        }}
      >
        <SigmaContent nodes={data.nodes} edges={data.edges} />
      </SigmaContainer>
    </div>
  );
}

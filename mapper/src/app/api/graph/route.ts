import { NextResponse } from "next/server";
import neo4j, { Driver } from "neo4j-driver";

// Module-level singleton with dev-safe global cache (prevents connection pool
// exhaustion on Next.js hot reload). See RESEARCH.md Pitfall 6.
const globalWithDriver = global as typeof global & { _neo4jDriver?: Driver };
if (!globalWithDriver._neo4jDriver) {
  globalWithDriver._neo4jDriver = neo4j.driver(
    process.env.NEO4J_BOLT_URI ?? "bolt://localhost:7687",
    neo4j.auth.basic(
      process.env.NEO4J_USER ?? "neo4j",
      process.env.NEO4J_PASSWORD ?? "neo4j_password"
    )
  );
}
const driver = globalWithDriver._neo4jDriver;

/**
 * Extract the local name from an RDF URI by stripping the namespace.
 * Handles both `#` and `/` separators. Falls back to full URI or "Resource".
 */
function localName(uri: string | null | undefined): string {
  if (!uri) return "Resource";
  const hash = uri.lastIndexOf("#");
  const slash = uri.lastIndexOf("/");
  const pos = Math.max(hash, slash);
  return pos >= 0 ? uri.slice(pos + 1) : uri;
}

const EXCLUDED_LABELS = ["resource", "equipment", "connectable", "controller"];

/**
 * Choose the best display label for a node.
 * Uses rdfsLabel when present; otherwise picks the longest Neo4j label that
 * is not excluded (case-insensitive): not 'Resource', 'Equipement',
 * 'Connectable', 'Controller', or any string containing 'property'.
 * Falls back to localName(uri) if no suitable label is found.
 */
function chooseLabel(
  rdfsLabel: string | undefined,
  labels: string[],
  uri: string
): string {
  if (rdfsLabel) return rdfsLabel;

  const candidates = labels.filter((l) => {
    const lower = l.toLowerCase();
    return (
      !EXCLUDED_LABELS.includes(lower) &&
      !lower.includes("property")
    );
  });

  if (candidates.length === 0) return labels[0] ?? localName(uri);

  return candidates.reduce((best, l) => (l.length > best.length ? l : best));
}

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const graphBackend = (process.env.GRAPH_BACKEND ?? "neo4j_single").trim().toLowerCase();

  // In neo4j_single and neo4j_prefix modes the entire graph lives in the
  // single "neo4j" database; ignore any ?db= param for the DB name.
  const db =
    graphBackend === "neo4j_single" || graphBackend === "neo4j_prefix"
      ? "neo4j"
      : (searchParams.get("db") ?? "neo4j");

  // In neo4j_prefix mode the frontend passes ?ns=<system_id> and all
  // Cypher queries are filtered to that namespace.
  const ns = graphBackend === "neo4j_prefix"
    ? (searchParams.get("ns") ?? null)
    : null;

  try {
    // Node query — filtered by system namespace when in prefix mode
    const nodeQuery = ns
      ? "MATCH (n {_graph_ns_system: $ns}) RETURN coalesce(n.uri, toString(id(n))) AS uri, labels(n) AS labels, properties(n) AS props"
      : "MATCH (n) RETURN coalesce(n.uri, toString(id(n))) AS uri, labels(n) AS labels, properties(n) AS props";

    const { records: nodeRecords } = await driver.executeQuery(
      nodeQuery,
      ns ? { ns } : {},
      { database: db }
    );

    // Edge query — filtered by system namespace when in prefix mode
    const edgeQuery = ns
      ? "MATCH (a {_graph_ns_system: $ns})-[r]->(b {_graph_ns_system: $ns}) RETURN coalesce(a.uri, toString(id(a))) AS source, coalesce(b.uri, toString(id(b))) AS target, type(r) AS label, coalesce(r.uri, toString(id(r))) AS id"
      : "MATCH (a)-[r]->(b) RETURN coalesce(a.uri, toString(id(a))) AS source, coalesce(b.uri, toString(id(b))) AS target, type(r) AS label, coalesce(r.uri, toString(id(r))) AS id";

    const { records: edgeRecords } = await driver.executeQuery(
      edgeQuery,
      ns ? { ns } : {},
      { database: db }
    );

    const nodes = nodeRecords.map((r) => {
      const props = r.get("props") as Record<string, unknown>;
      const labels = (r.get("labels") as string[]) ?? [];
      const uri = r.get("uri") as string;

      const rdfsLabel = props["rdfs__label"] as string | undefined;
      const label = chooseLabel(rdfsLabel, labels, uri);

      return {
        id: uri,
        label,
        type: labels.find((l) => l !== "Resource") ?? "Resource",
        allLabels: labels,
        properties: props,
      };
    });

    const edges = edgeRecords.map((r, i) => ({
      id: (r.get("id") as string) ?? `edge-${i}`,
      source: r.get("source") as string,
      target: r.get("target") as string,
      label: r.get("label") as string,
    }));

    return NextResponse.json({ nodes, edges });
  } catch (e) {
    console.error("[/api/graph] Neo4j query failed:", e);
    return NextResponse.json(
      { error: String(e) },
      { status: 500 }
    );
  }
}

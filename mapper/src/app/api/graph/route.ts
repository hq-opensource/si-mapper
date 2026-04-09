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

export async function GET() {
  try {
    // Query all nodes — use coalesce for blank nodes that may lack uri
    const { records: nodeRecords } = await driver.executeQuery(
      "MATCH (n) RETURN coalesce(n.uri, toString(id(n))) AS uri, labels(n) AS labels, properties(n) AS props",
      {},
      { database: "neo4j" }
    );

    // Query all relationships
    const { records: edgeRecords } = await driver.executeQuery(
      "MATCH (a)-[r]->(b) RETURN coalesce(a.uri, toString(id(a))) AS source, coalesce(b.uri, toString(id(b))) AS target, type(r) AS label, coalesce(r.uri, toString(id(r))) AS id",
      {},
      { database: "neo4j" }
    );

    const GENERIC_LABELS = new Set(["Resource", "owl__Class", "owl__NamedIndividual", "owl__Ontology"]);
    const nodes = nodeRecords.map((r) => {
      const props = r.get("props") as Record<string, unknown>;
      const labels = (r.get("labels") as string[]) ?? [];
      const uri = r.get("uri") as string;

      const rdfsLabel = props["rdfs__label"] as string | undefined;
      const classLabel = labels.find((l) => !GENERIC_LABELS.has(l) && !l.startsWith("n10s"));
      const label = rdfsLabel ?? classLabel ?? localName(uri);

      return {
        id: uri,
        label,
        type: labels.find((l) => l !== "Resource") ?? "Resource",
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

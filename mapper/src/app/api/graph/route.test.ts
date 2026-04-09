// Mock neo4j-driver at module level before any imports.
// The factory runs in Jest's hoisted scope — we expose the mock via globalThis
// to avoid the temporal dead zone when the module singleton is created at import.
jest.mock("neo4j-driver", () => {
  // Inline the mock fn so it is created within the hoisted factory scope
  const execQuery = jest.fn();
  // Expose via module-level ref for per-test control
  (globalThis as Record<string, unknown>).__neo4jMockExecuteQuery = execQuery;
  return {
    __esModule: true,
    default: {
      driver: () => ({ executeQuery: execQuery }),
      auth: { basic: () => ({}) },
    },
  };
});

import { GET } from "./route";

// Retrieve the mock exposed via globalThis (set inside the factory above)
function getExecMock(): jest.Mock {
  return (globalThis as Record<string, unknown>)
    .__neo4jMockExecuteQuery as jest.Mock;
}

// Helper to create mock records with .get() method
function mockRecord(data: Record<string, unknown>) {
  return { get: (key: string) => data[key] };
}

describe("GET /api/graph", () => {
  beforeEach(() => {
    getExecMock().mockReset();
  });

  test("returns nodes and edges on success", async () => {
    const exec = getExecMock();

    // First call: nodes query
    exec.mockResolvedValueOnce({
      records: [
        mockRecord({
          uri: "http://example.org/Fan-SF1",
          labels: ["Equipment"],
          props: { uri: "http://example.org/Fan-SF1" },
        }),
      ],
    });
    // Second call: edges query
    exec.mockResolvedValueOnce({
      records: [
        mockRecord({
          id: "edge-0",
          source: "http://example.org/Fan-SF1",
          target: "http://example.org/Duct-1",
          label: "connectedTo",
        }),
      ],
    });

    const response = await GET(new Request('http://localhost/api/graph?db=neo4j'));
    const body = await response.json();

    expect(response.status).toBe(200);
    expect(body.nodes).toHaveLength(1);
    expect(body.nodes[0]).toEqual({
      id: "http://example.org/Fan-SF1",
      label: "Fan-SF1",
      type: "Equipment",
      properties: { uri: "http://example.org/Fan-SF1" },
    });
    expect(body.edges).toHaveLength(1);
    expect(body.edges[0]).toEqual({
      id: "edge-0",
      source: "http://example.org/Fan-SF1",
      target: "http://example.org/Duct-1",
      label: "connectedTo",
    });
  });

  test("returns 500 when Neo4j is unreachable", async () => {
    const exec = getExecMock();
    exec.mockRejectedValueOnce(new Error("ServiceUnavailable"));

    const response = await GET(new Request('http://localhost/api/graph?db=neo4j'));
    const body = await response.json();

    expect(response.status).toBe(500);
    expect(body.error).toContain("ServiceUnavailable");
  });
});


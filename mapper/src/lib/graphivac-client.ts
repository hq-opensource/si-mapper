/**
 * graphivac-client.ts
 * ──────────────────────────────────────────────────────────────────────────────
 * Thin client for the Graphivac REST API.  Server-side only — never import
 * from a client component.
 *
 * Graphivac API (Swagger 2.0, base path /api/v1):
 *   POST   /api/v1/orgs/:org/projects            body: { "project-name": string }
 *   DELETE /api/v1/orgs/:org/projects/:proj
 *   GET    /api/v1/orgs/:org/projects/:proj/grids
 *   POST   /api/v1/orgs/:org/projects/:proj/grids body: { title?: string, ... }
 *   DELETE /api/v1/orgs/:org/projects/:proj/grids/:grid
 *
 * All functions read GRAPHIVAC_BASE_URL and GRAPHIVAC_ORG_ID from process.env
 * at call time.  Callers never supply org_id.
 */

// ── Internal helpers ──────────────────────────────────────────────────────────

function getEnv(): { baseUrl: string; orgId: string } {
  const baseUrl = process.env.GRAPHIVAC_BASE_URL;
  const orgId = process.env.GRAPHIVAC_ORG_ID;
  if (!baseUrl) throw new Error('GRAPHIVAC_BASE_URL environment variable is not set.');
  if (!orgId) throw new Error('GRAPHIVAC_ORG_ID environment variable is not set.');
  return { baseUrl: baseUrl.replace(/\/$/, ''), orgId };
}

async function graphivacFetch(
  method: string,
  path: string,
  body?: Record<string, unknown>
): Promise<Response> {
  const { baseUrl } = getEnv();
  const url = `${baseUrl}${path}`;

  const res = await fetch(url, {
    method,
    headers: { 'Content-Type': 'application/json' },
    ...(body !== undefined ? { body: JSON.stringify(body) } : {}),
  });

  return res;
}

// ── Public interfaces ─────────────────────────────────────────────────────────

export interface GraphivacProjectSummary {
  id: string;   // e.g. "P-j8QIvTGH7p"
  title: string;
}

export interface GraphivacGridSummary {
  id: string;   // e.g. "G-LAiRS3mgp6"
  title: string;
}

// ── Graphivac Project operations ──────────────────────────────────────────────

/**
 * Create a new Graphivac Project within the deployment's organisation.
 * @param title — display name (typically the SI-Mapper project name)
 * @returns the new Graphivac project id
 */
export async function createGraphivacProject(title: string): Promise<string> {
  const { orgId } = getEnv();
  const res = await graphivacFetch('POST', `/api/v1/orgs/${orgId}/projects`, {
    'project-name': title,
  });

  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(
      `Graphivac createProject failed: ${res.status} ${res.statusText} — ${text}`
    );
  }

  const data = await res.json();
  const id: string = data?.id ?? data?.['project-id'] ?? data?.projectId;
  if (!id) {
    throw new Error(
      `Graphivac createProject: could not extract id from response: ${JSON.stringify(data)}`
    );
  }
  return id;
}

/**
 * Delete a Graphivac Project (and all its grids).
 * Resolves normally if the project is already gone (idempotent / 404 is no-op).
 */
export async function deleteGraphivacProject(projectId: string): Promise<void> {
  const { orgId } = getEnv();
  const res = await graphivacFetch('DELETE', `/api/v1/orgs/${orgId}/projects/${projectId}`);

  if (!res.ok && res.status !== 404) {
    const text = await res.text().catch(() => '');
    throw new Error(
      `Graphivac deleteProject failed: ${res.status} ${res.statusText} — ${text}`
    );
  }
}

// ── Graphivac Grid operations ─────────────────────────────────────────────────

/**
 * List all grids in a Graphivac Project.
 */
export async function listGrids(graphivacProjectId: string): Promise<GraphivacGridSummary[]> {
  const { orgId } = getEnv();
  const res = await graphivacFetch('GET', `/api/v1/orgs/${orgId}/projects/${graphivacProjectId}/grids`);

  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(
      `Graphivac listGrids failed: ${res.status} ${res.statusText} — ${text}`
    );
  }

  const data = await res.json();
  // The API may return an array directly or wrap it in a field.
  const list = Array.isArray(data) ? data : (data?.grids ?? data?.items ?? []);
  return list as GraphivacGridSummary[];
}

/**
 * Create a new Graphivac Grid inside a Graphivac Project.
 * @param graphivacProjectId — the Graphivac Project to create the grid in
 * @param title — display name (typically the SI-Mapper system name)
 * @returns the new grid id
 */
export async function createGrid(graphivacProjectId: string, title: string): Promise<string> {
  const { orgId } = getEnv();
  const res = await graphivacFetch(
    'POST',
    `/api/v1/orgs/${orgId}/projects/${graphivacProjectId}/grids`,
    { title }
  );

  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(
      `Graphivac createGrid failed: ${res.status} ${res.statusText} — ${text}`
    );
  }

  const data = await res.json();
  const id: string = data?.id ?? data?.['grid-id'] ?? data?.gridId;
  if (!id) {
    throw new Error(
      `Graphivac createGrid: could not extract id from response: ${JSON.stringify(data)}`
    );
  }
  return id;
}

/**
 * Delete a Graphivac Grid.
 * Resolves normally if the grid is already gone (idempotent / 404 is no-op).
 */
export async function deleteGrid(graphivacProjectId: string, gridId: string): Promise<void> {
  const { orgId } = getEnv();
  const res = await graphivacFetch(
    'DELETE',
    `/api/v1/orgs/${orgId}/projects/${graphivacProjectId}/grids/${gridId}`
  );

  if (!res.ok && res.status !== 404) {
    const text = await res.text().catch(() => '');
    throw new Error(
      `Graphivac deleteGrid failed: ${res.status} ${res.statusText} — ${text}`
    );
  }
}


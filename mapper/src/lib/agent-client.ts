/**
 * agent-client.ts
 * ─────────────────────────────────────────────────────────────────────────────
 * Thin client for communicating with the Python agent backend via the
 * Next.js proxy routes (browser → /api/agent/... → AGENT_BACKEND_URL).
 */

import type { Project, System, SessionRef } from '@/types';

/**
 * Push the complete workspace context to the agent backend.
 *
 * This is the **single** function the UI calls whenever the active project,
 * system, or session changes.  The agent always receives the full state —
 * never a partial update.
 *
 * Fire-and-notify: errors are logged but never thrown so a transient backend
 * failure never blocks UI navigation.
 */
export async function updateAgentWorkspaceState(
  project: Project,
  system: System,
  session: SessionRef,
): Promise<void> {
  try {
    const res = await fetch('/api/agent/state', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        active_project: {
          id: project.id,
          folder_path: project.folder_path,
          name: project.name,
          graphivac_project_id: project.graphivac_project_id,
        },
        active_system: {
          id: system.id,
          folder_path: system.folder_path,
          name: system.name,
          graphivac_grid_id: system.graphivac_grid_id,
          ai_model_name: system.ai_model_name,
        },
        active_session: {
          id: session.session_id,
          name: session.session_name,
        },
      }),
    });
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      console.warn('[updateAgentWorkspaceState] Agent responded with error:', data);
    }
  } catch (err) {
    console.warn('[updateAgentWorkspaceState] Could not reach agent backend:', err);
  }
}

/**
 * Persist the chosen session as `active_session_id` on the system (system.json).
 * Uses the system PATCH endpoint — fire-and-forget, never throws.
 */
export async function markSessionActive(
  projectId: string,
  systemId: string,
  sessionId: string,
): Promise<void> {
  try {
    await fetch(`/api/projects/${projectId}/systems/${systemId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ active_session_id: sessionId }),
    });
  } catch (err) {
    console.warn('[markSessionActive] Failed:', err);
  }
}

/**
 * Create a new agent session for a given project/system and make it active.
 * Returns the created SessionRef or null on failure.
 */
export async function createAgentSession(
  projectId: string,
  systemId: string,
  sessionName?: string,
): Promise<{ session_id: string; session_name: string; created_at: string } | null> {
  try {
    const res = await fetch(`/api/projects/${projectId}/systems/${systemId}/sessions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(sessionName ? { session_name: sessionName } : {}),
    });
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      console.warn('[createAgentSession] Error:', data);
      return null;
    }
    return await res.json();
  } catch (err) {
    console.warn('[createAgentSession] Could not reach backend:', err);
    return null;
  }
}

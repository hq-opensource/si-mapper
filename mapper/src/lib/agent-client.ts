/**
 * agent-client.ts
 * ─────────────────────────────────────────────────────────────────────────────
 * Thin client for communicating with the Python agent backend via the
 * Next.js proxy routes (browser → /api/agent/... → AGENT_BACKEND_URL).
 */

/**
 * Notify the agent backend to switch its active LLM model.
 *
 * Fire-and-notify: errors are logged but never thrown — a model-swap failure
 * must not crash the UI or block navigation.
 *
 * @param modelName  LiteLLM-compatible model string, e.g. "gemini-2.0-flash"
 */
export async function notifyAgentModel(modelName: string): Promise<void> {
  if (!modelName?.trim()) return;
  try {
    const res = await fetch('/api/agent/model', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ model_name: modelName.trim() }),
    });
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      console.warn('[notifyAgentModel] Agent responded with error:', data);
    }
  } catch (err) {
    console.warn('[notifyAgentModel] Could not reach agent backend:', err);
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

/**
 * Restore a saved agent session (make it the active session on the agent).
 * Returns { session_id, session_name } or null on failure.
 */
export async function restoreAgentSession(
  projectId: string,
  systemId: string,
  sessionId: string,
): Promise<{ session_id: string; session_name: string } | null> {
  try {
    const res = await fetch(
      `/api/projects/${projectId}/systems/${systemId}/sessions/${sessionId}/restore`,
      { method: 'POST' },
    );
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      console.warn('[restoreAgentSession] Error:', data);
      return null;
    }
    return await res.json();
  } catch (err) {
    console.warn('[restoreAgentSession] Could not reach backend:', err);
    return null;
  }
}



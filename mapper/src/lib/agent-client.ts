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


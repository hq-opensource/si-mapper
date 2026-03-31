/**
 * POST /api/agent/state
 * ─────────────────────────────────────────────────────────────────────────────
 * Server-side proxy that forwards the complete workspace state to the agent.
 *
 * This is the single entry-point for any workspace context change that the UI
 * needs to communicate to the agent (project switch, system switch, session
 * switch, model edit…).  The client always sends the FULL state — never a
 * partial update.
 *
 * Request body:
 *   {
 *     "active_project": { id, folder_path, name, graphivac_project_id },
 *     "active_system":  { id, folder_path, name, graphivac_grid_id, ai_model_name },
 *     "active_session": { id, name }
 *   }
 *
 * Response (from agent):
 *   { status, session_id, session_name, project_id, system_id, model }
 */

import { NextRequest, NextResponse } from 'next/server';

const AGENT_BASE_URL = (process.env.AGENT_BACKEND_URL ?? 'http://127.0.0.1:8001').replace(/\/$/, '');

export async function POST(req: NextRequest): Promise<NextResponse> {
  let body: unknown;
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: 'Invalid JSON body.' }, { status: 400 });
  }

  const payload = body as Record<string, unknown>;
  if (!payload?.active_project || !payload?.active_system || !payload?.active_session) {
    return NextResponse.json(
      { error: 'active_project, active_system, and active_session are all required.' },
      { status: 400 },
    );
  }

  try {
    const agentRes = await fetch(`${AGENT_BASE_URL}/workspace/state`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const data = await agentRes.json().catch(() => ({}));
    return NextResponse.json(data, { status: agentRes.status });
  } catch (err) {
    console.error('[POST /api/agent/state] Failed to reach agent backend:', err);
    return NextResponse.json({ error: 'Agent backend unreachable.' }, { status: 502 });
  }
}

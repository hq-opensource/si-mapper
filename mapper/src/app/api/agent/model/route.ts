/**
 * POST /api/agent/model
 * ─────────────────────────────────────────────────────────────────────────────
 * Server-side proxy that forwards a model-swap request to the agent backend.
 *
 * Browser clients cannot reach AGENT_BACKEND_URL directly (container DNS /
 * internal network), so this route acts as the bridge.
 *
 * Request body: { "model_name": "<litellm-model-string>" }
 * Response: the agent's JSON response  →  { status, model, session_id }
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

  const modelName = (body as Record<string, unknown>)?.model_name;
  if (typeof modelName !== 'string' || !modelName.trim()) {
    return NextResponse.json({ error: 'model_name is required.' }, { status: 400 });
  }

  // The FastAPI endpoint reads model_name from the query string.
  const agentUrl = `${AGENT_BASE_URL}/model?model_name=${encodeURIComponent(modelName.trim())}`;

  try {
    const agentRes = await fetch(agentUrl, { method: 'POST' });
    const data = await agentRes.json().catch(() => ({}));
    return NextResponse.json(data, { status: agentRes.status });
  } catch (err) {
    console.error('[POST /api/agent/model] Failed to reach agent backend:', err);
    return NextResponse.json({ error: 'Agent backend unreachable.' }, { status: 502 });
  }
}


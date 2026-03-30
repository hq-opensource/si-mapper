/**
 * POST /api/projects/[id]/systems/[sysId]/sessions/[sessionId]/restore
 *
 * Restores a saved session — tells the agent to make this the active session.
 * No system.json write needed (SessionRef already exists in the sessions array).
 */

import { NextRequest, NextResponse } from 'next/server';
import { getProject, getSystem } from '@/lib/projects';

const AGENT_BASE_URL = (process.env.AGENT_BACKEND_URL ?? 'http://127.0.0.1:8001').replace(/\/$/, '');

type Params = { params: Promise<{ id: string; sysId: string; sessionId: string }> };

export async function POST(_req: NextRequest, { params }: Params): Promise<NextResponse> {
  const { id, sysId, sessionId } = await params;

  const project = await getProject(id);
  if (!project) return NextResponse.json({ error: 'Project not found.' }, { status: 404 });

  const system = await getSystem(project.folder_path, sysId);
  if (!system) return NextResponse.json({ error: 'System not found.' }, { status: 404 });

  const sessionRef = (system.sessions ?? []).find(s => s.session_id === sessionId);
  if (!sessionRef) return NextResponse.json({ error: 'Session not found in system.' }, { status: 404 });

  // Call agent to restore the session
  try {
    const agentRes = await fetch(`${AGENT_BASE_URL}/sessions/${sessionId}/restore`, { method: 'POST' });
    if (!agentRes.ok) {
      const err = await agentRes.json().catch(() => ({}));
      console.error(`[POST .../sessions/${sessionId}/restore] Agent error:`, err);
      return NextResponse.json({ error: 'Agent failed to restore session.', details: err }, { status: 502 });
    }
    const data = await agentRes.json();
    return NextResponse.json(data, { status: 200 });
  } catch (err) {
    console.error(`[POST .../sessions/${sessionId}/restore] Agent unreachable:`, err);
    return NextResponse.json({ error: 'Agent backend unreachable.' }, { status: 502 });
  }
}


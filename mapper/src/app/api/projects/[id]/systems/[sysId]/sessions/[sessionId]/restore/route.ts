/**
 * POST /api/projects/[id]/systems/[sysId]/sessions/[sessionId]/restore
 *
 * Restores a saved session — pushes the full workspace context (project,
 * system, session) to the agent via POST /workspace/state so the agent
 * activates this session with complete context.
 *
 * No system.json write needed (SessionRef already exists in sessions array).
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

  // Push full workspace context to the agent — single unified endpoint
  try {
    const agentRes = await fetch(`${AGENT_BASE_URL}/workspace/state`, {
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
          id: sessionRef.session_id,
          name: sessionRef.session_name,
        },
      }),
    });
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

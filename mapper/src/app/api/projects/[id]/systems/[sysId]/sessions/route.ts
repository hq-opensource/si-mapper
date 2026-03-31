/**
 * GET  /api/projects/[id]/systems/[sysId]/sessions  — list sessions for a system
 * POST /api/projects/[id]/systems/[sysId]/sessions  — create a new session
 *
 * Session creation calls POST /workspace/state with no session ID.
 * The agent generates the ID, creates the session with full context, and
 * returns the new ID.  This route then saves the SessionRef to system.json.
 */

import { NextRequest, NextResponse } from 'next/server';
import { z } from 'zod';
import { getProject, getSystem, writeSystem } from '@/lib/projects';
import type { SessionRef } from '@/lib/projects';

const AGENT_BASE_URL = (process.env.AGENT_BACKEND_URL ?? 'http://127.0.0.1:8001').replace(/\/$/, '');

const CreateSessionSchema = z.object({
  session_name: z.string().optional(),
});

type Params = { params: Promise<{ id: string; sysId: string }> };

// ── GET ───────────────────────────────────────────────────────────────────────

export async function GET(_req: NextRequest, { params }: Params): Promise<NextResponse> {
  const { id, sysId } = await params;
  const project = await getProject(id);
  if (!project) return NextResponse.json({ error: 'Project not found.' }, { status: 404 });
  const system = await getSystem(project.folder_path, sysId);
  if (!system) return NextResponse.json({ error: 'System not found.' }, { status: 404 });
  return NextResponse.json(system.sessions ?? [], { status: 200 });
}

// ── POST ──────────────────────────────────────────────────────────────────────

export async function POST(req: NextRequest, { params }: Params): Promise<NextResponse> {
  const { id, sysId } = await params;

  const project = await getProject(id);
  if (!project) return NextResponse.json({ error: 'Project not found.' }, { status: 404 });
  const system = await getSystem(project.folder_path, sysId);
  if (!system) return NextResponse.json({ error: 'System not found.' }, { status: 404 });

  let body: unknown = {};
  try { body = await req.json(); } catch { /* empty body is fine */ }

  const parsed = CreateSessionSchema.safeParse(body);
  const now = new Date();
  const defaultName = `Session ${now.toISOString().slice(0, 16).replace('T', ' ')}`;
  const sessionName = parsed.success && parsed.data.session_name?.trim()
    ? parsed.data.session_name.trim()
    : defaultName;

  // Send full context to the agent with an empty session ID.
  // The agent creates the session, assigns the ID, and returns it.
  let sessionId: string;
  try {
    const agentRes = await fetch(`${AGENT_BASE_URL}/workspace/state`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        active_project: {
          id:                   project.id,
          folder_path:          project.folder_path,
          name:                 project.name,
          graphivac_project_id: project.graphivac_project_id,
        },
        active_system: {
          id:               system.id,
          folder_path:      system.folder_path,
          name:             system.name,
          graphivac_grid_id: system.graphivac_grid_id,
          ai_model_name:    system.ai_model_name,
        },
        active_session: {
          id:   '',          // empty → agent creates and returns the new ID
          name: sessionName,
        },
      }),
    });
    if (!agentRes.ok) {
      const err = await agentRes.json().catch(() => ({}));
      console.error('[POST /api/.../sessions] Agent error:', err);
      return NextResponse.json({ error: 'Agent failed to create session.', details: err }, { status: 502 });
    }
    const data = await agentRes.json();
    sessionId = data.session_id;
  } catch (err) {
    console.error('[POST /api/.../sessions] Agent unreachable:', err);
    return NextResponse.json({ error: 'Agent backend unreachable.' }, { status: 502 });
  }

  // Persist the new SessionRef into system.json.
  const ref: SessionRef = {
    session_id:   sessionId,
    session_name: sessionName,
    created_at:   now.toISOString(),
  };
  await writeSystem(project.folder_path, {
    ...system,
    active_session_id: sessionId,
    sessions: [ref, ...(system.sessions ?? [])],
  });

  return NextResponse.json(ref, { status: 201 });
}

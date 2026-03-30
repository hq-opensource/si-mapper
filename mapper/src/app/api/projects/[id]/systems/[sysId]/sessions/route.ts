/**
 * GET  /api/projects/[id]/systems/[sysId]/sessions  — list sessions for a system
 * POST /api/projects/[id]/systems/[sysId]/sessions  — create a new session
 *
 * Coordinates the agent backend (SQLite) and system.json atomically.
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

// ── GET /api/projects/[id]/systems/[sysId]/sessions ───────────────────────────

export async function GET(_req: NextRequest, { params }: Params): Promise<NextResponse> {
  const { id, sysId } = await params;

  const project = await getProject(id);
  if (!project) return NextResponse.json({ error: 'Project not found.' }, { status: 404 });

  const system = await getSystem(project.folder_path, sysId);
  if (!system) return NextResponse.json({ error: 'System not found.' }, { status: 404 });

  return NextResponse.json(system.sessions ?? [], { status: 200 });
}

// ── POST /api/projects/[id]/systems/[sysId]/sessions ──────────────────────────

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

  // 1. Call agent to create a new session in SQLite
  let sessionId: string;
  let actualName: string;
  try {
    const agentRes = await fetch(`${AGENT_BASE_URL}/sessions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_name: sessionName,
        system_id: system.id,
        project_id: project.id,
      }),
    });
    if (!agentRes.ok) {
      const err = await agentRes.json().catch(() => ({}));
      console.error('[POST /api/.../sessions] Agent error:', err);
      return NextResponse.json({ error: 'Agent failed to create session.', details: err }, { status: 502 });
    }
    const data = await agentRes.json();
    sessionId = data.session_id;
    actualName = data.session_name || sessionName;
  } catch (err) {
    console.error('[POST /api/.../sessions] Agent unreachable:', err);
    return NextResponse.json({ error: 'Agent backend unreachable.' }, { status: 502 });
  }

  // 2. Prepend SessionRef to system.json; mark it as the active session.
  const ref: SessionRef = {
    session_id: sessionId,
    session_name: actualName,
    created_at: now.toISOString(),
  };
  const updatedSystem = {
    ...system,
    active_session_id: sessionId,           // newly created session becomes active
    sessions: [ref, ...(system.sessions ?? [])],
  };
  await writeSystem(project.folder_path, updatedSystem);

  return NextResponse.json(ref, { status: 201 });
}




/**
 * DELETE /api/projects/[id]/systems/[sysId]/sessions/[sessionId]  — delete a session
 * PATCH  /api/projects/[id]/systems/[sysId]/sessions/[sessionId]  — rename / mark active
 */

import { NextRequest, NextResponse } from 'next/server';
import { z } from 'zod';
import { getProject, getSystem, writeSystem } from '@/lib/projects';

const AGENT_BASE_URL = (process.env.AGENT_BACKEND_URL ?? 'http://127.0.0.1:8001').replace(/\/$/, '');

const PatchSessionSchema = z.object({
  session_name: z.string().min(1).optional(),
});

type Params = { params: Promise<{ id: string; sysId: string; sessionId: string }> };

// ── DELETE ────────────────────────────────────────────────────────────────────

export async function DELETE(_req: NextRequest, { params }: Params): Promise<NextResponse> {
  const { id, sysId, sessionId } = await params;

  const project = await getProject(id);
  if (!project) return NextResponse.json({ error: 'Project not found.' }, { status: 404 });

  const system = await getSystem(project.folder_path, sysId);
  if (!system) return NextResponse.json({ error: 'System not found.' }, { status: 404 });

  // Best-effort: delete from agent SQLite
  try {
    await fetch(`${AGENT_BASE_URL}/sessions/${sessionId}`, { method: 'DELETE' });
  } catch (err) {
    console.warn(`[DELETE .../sessions/${sessionId}] Agent call failed:`, err);
  }

  // Remove SessionRef from system.json
  const updatedSystem = {
    ...system,
    sessions: (system.sessions ?? []).filter(s => s.session_id !== sessionId),
  };
  await writeSystem(project.folder_path, updatedSystem);

  return new NextResponse(null, { status: 204 });
}

// ── PATCH ─────────────────────────────────────────────────────────────────────

export async function PATCH(req: NextRequest, { params }: Params): Promise<NextResponse> {
  const { id, sysId, sessionId } = await params;

  const project = await getProject(id);
  if (!project) return NextResponse.json({ error: 'Project not found.' }, { status: 404 });

  const system = await getSystem(project.folder_path, sysId);
  if (!system) return NextResponse.json({ error: 'System not found.' }, { status: 404 });

  let body: unknown;
  try { body = await req.json(); } catch {
    return NextResponse.json({ error: 'Invalid JSON body.' }, { status: 400 });
  }

  const parsed = PatchSessionSchema.safeParse(body);
  if (!parsed.success) {
    return NextResponse.json({ error: 'Validation failed.', details: parsed.error.flatten() }, { status: 400 });
  }

  const { session_name } = parsed.data;
  let updatedSessions = system.sessions ?? [];

  // ── Rename ───────────────────────────────────────────────────────────────
  if (session_name !== undefined) {
    // Best-effort: sync rename to agent SQLite
    try {
      await fetch(`${AGENT_BASE_URL}/sessions/${sessionId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_name }),
      });
    } catch (err) {
      console.warn(`[PATCH .../sessions/${sessionId}] Agent rename failed:`, err);
    }
    updatedSessions = updatedSessions.map(s =>
      s.session_id === sessionId ? { ...s, session_name } : s
    );
  }

  const updatedSystem = { ...system, sessions: updatedSessions };
  await writeSystem(project.folder_path, updatedSystem);

  const updated = updatedSessions.find(s => s.session_id === sessionId);
  return NextResponse.json(updated ?? { session_id: sessionId, session_name: session_name ?? '', created_at: '' }, { status: 200 });
}




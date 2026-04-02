/**
 * GET    /api/projects/[id]/systems/[sysId]  — get a single system
 * PATCH  /api/projects/[id]/systems/[sysId]  — update system metadata
 * DELETE /api/projects/[id]/systems/[sysId]  — delete system (folder + Graphivac Grid)
 */

import { NextRequest, NextResponse } from 'next/server';
import { z } from 'zod';
import {
  deleteSystemFromDisk,
  getProject,
  getSystem,
  writeSystem,
} from '@/lib/projects';
import { deleteGrid } from '@/lib/graphivac-client';

// ── Zod schema ────────────────────────────────────────────────────────────────

const SessionSchema = z.object({
  id: z.string(),
  name: z.string(),
  created_at: z.string(),
});

const PatchSystemSchema = z.object({
  name: z.string().min(1).optional(),
  ai_model_name: z.string().min(1).optional(),
  thread_id: z.string().optional(),
  sessions: z.array(SessionSchema).optional(),
});

// ── Shared helper ─────────────────────────────────────────────────────────────

type Params = { params: Promise<{ id: string; sysId: string }> };

// ── GET /api/projects/[id]/systems/[sysId] ────────────────────────────────────

export async function GET(_req: NextRequest, { params }: Params): Promise<NextResponse> {
  const { id, sysId } = await params;

  const project = await getProject(id);
  if (!project) {
    return NextResponse.json({ error: 'Project not found.' }, { status: 404 });
  }

  const system = await getSystem(project.folder_path, sysId);
  if (!system) {
    return NextResponse.json({ error: 'System not found.' }, { status: 404 });
  }

  return NextResponse.json(system, { status: 200 });
}

// ── PATCH /api/projects/[id]/systems/[sysId] ──────────────────────────────────

export async function PATCH(req: NextRequest, { params }: Params): Promise<NextResponse> {
  const { id, sysId } = await params;

  const project = await getProject(id);
  if (!project) {
    return NextResponse.json({ error: 'Project not found.' }, { status: 404 });
  }

  const system = await getSystem(project.folder_path, sysId);
  if (!system) {
    return NextResponse.json({ error: 'System not found.' }, { status: 404 });
  }

  let body: unknown;
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: 'Invalid JSON body.' }, { status: 400 });
  }

  const parsed = PatchSystemSchema.safeParse(body);
  if (!parsed.success) {
    return NextResponse.json(
      { error: 'Validation failed.', details: parsed.error.flatten() },
      { status: 400 }
    );
  }

  // Merge only mutable fields — id, folder_path, graphivac_grid_id, created_at are immutable.
  const updated = {
    ...system,
    ...(parsed.data.name !== undefined ? { name: parsed.data.name } : {}),
    ...(parsed.data.ai_model_name !== undefined ? { ai_model_name: parsed.data.ai_model_name } : {}),
    ...(parsed.data.thread_id !== undefined ? { thread_id: parsed.data.thread_id } : {}),
    ...(parsed.data.sessions !== undefined ? { sessions: parsed.data.sessions } : {}),
  };

  try {
    await writeSystem(project.folder_path, updated);
    const fresh = await getSystem(project.folder_path, sysId);
    return NextResponse.json(fresh, { status: 200 });
  } catch (err) {
    console.error(`[PATCH /api/projects/${id}/systems/${sysId}]`, err);
    return NextResponse.json({ error: 'Failed to update system.' }, { status: 500 });
  }
}

// ── DELETE /api/projects/[id]/systems/[sysId] ─────────────────────────────────

export async function DELETE(_req: NextRequest, { params }: Params): Promise<NextResponse> {
  const { id, sysId } = await params;

  const project = await getProject(id);
  if (!project) {
    return NextResponse.json({ error: 'Project not found.' }, { status: 404 });
  }

  const system = await getSystem(project.folder_path, sysId);
  if (!system) {
    return NextResponse.json({ error: 'System not found.' }, { status: 404 });
  }

  // 1. Delete the Graphivac Grid (best-effort).
  try {
    await deleteGrid(project.graphivac_project_id, system.graphivac_grid_id);
  } catch (err) {
    console.error(
      `[DELETE /api/projects/${id}/systems/${sysId}] deleteGrid(${system.graphivac_grid_id}) failed:`,
      err
    );
  }

  // 2. Remove the system subfolder from disk.
  try {
    await deleteSystemFromDisk(project.folder_path, system.folder_path);
  } catch (err) {
    console.error(`[DELETE /api/projects/${id}/systems/${sysId}] deleteSystemFromDisk failed:`, err);
    return NextResponse.json({ error: 'Failed to delete system folder.' }, { status: 500 });
  }

  return new NextResponse(null, { status: 204 });
}


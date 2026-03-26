/**
 * GET    /api/projects/[id]  — get a single project
 * PATCH  /api/projects/[id]  — update project metadata
 * DELETE /api/projects/[id]  — delete project (all systems + folder + Graphivac Project)
 */

import { NextRequest, NextResponse } from 'next/server';
import { z } from 'zod';
import {
  deleteProjectFromDisk,
  getProject,
  listSystems,
  writeProject,
} from '@/lib/projects';
import { deleteGraphivacProject, deleteGrid } from '@/lib/graphivac-client';

// ── Zod schema ────────────────────────────────────────────────────────────────

const PatchProjectSchema = z.object({
  name: z.string().min(1).optional(),
});

// ── Shared helper ─────────────────────────────────────────────────────────────

type Params = { params: Promise<{ id: string }> };

// ── GET /api/projects/[id] ────────────────────────────────────────────────────

export async function GET(_req: NextRequest, { params }: Params): Promise<NextResponse> {
  const { id } = await params;
  try {
    const project = await getProject(id);
    if (!project) {
      return NextResponse.json({ error: 'Project not found.' }, { status: 404 });
    }
    return NextResponse.json(project, { status: 200 });
  } catch (err) {
    console.error(`[GET /api/projects/${id}]`, err);
    return NextResponse.json({ error: 'Failed to read project.' }, { status: 500 });
  }
}

// ── PATCH /api/projects/[id] ──────────────────────────────────────────────────

export async function PATCH(req: NextRequest, { params }: Params): Promise<NextResponse> {
  const { id } = await params;

  const project = await getProject(id);
  if (!project) {
    return NextResponse.json({ error: 'Project not found.' }, { status: 404 });
  }

  let body: unknown;
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: 'Invalid JSON body.' }, { status: 400 });
  }

  const parsed = PatchProjectSchema.safeParse(body);
  if (!parsed.success) {
    return NextResponse.json(
      { error: 'Validation failed.', details: parsed.error.flatten() },
      { status: 400 }
    );
  }

  // Merge only mutable fields — id, folder_path, graphivac_project_id, created_at are immutable.
  const updated = {
    ...project,
    ...(parsed.data.name !== undefined ? { name: parsed.data.name } : {}),
  };

  try {
    await writeProject(updated);
    const fresh = await getProject(id);
    return NextResponse.json(fresh, { status: 200 });
  } catch (err) {
    console.error(`[PATCH /api/projects/${id}]`, err);
    return NextResponse.json({ error: 'Failed to update project.' }, { status: 500 });
  }
}

// ── DELETE /api/projects/[id] ─────────────────────────────────────────────────

export async function DELETE(_req: NextRequest, { params }: Params): Promise<NextResponse> {
  const { id } = await params;

  const project = await getProject(id);
  if (!project) {
    return NextResponse.json({ error: 'Project not found.' }, { status: 404 });
  }

  // 1. Delete each system's Graphivac Grid (best-effort).
  try {
    const systems = await listSystems(project.folder_path);
    for (const system of systems) {
      try {
        await deleteGrid(project.graphivac_project_id, system.graphivac_grid_id);
      } catch (err) {
        console.error(
          `[DELETE /api/projects/${id}] deleteGrid(${system.graphivac_grid_id}) failed:`,
          err
        );
      }
    }
  } catch (err) {
    console.error(`[DELETE /api/projects/${id}] listSystems failed:`, err);
  }

  // 2. Delete the Graphivac Project (best-effort).
  try {
    await deleteGraphivacProject(project.graphivac_project_id);
  } catch (err) {
    console.error(
      `[DELETE /api/projects/${id}] deleteGraphivacProject(${project.graphivac_project_id}) failed:`,
      err
    );
  }

  // 3. Remove the entire project folder from disk.
  try {
    await deleteProjectFromDisk(project.folder_path);
  } catch (err) {
    console.error(`[DELETE /api/projects/${id}] deleteProjectFromDisk failed:`, err);
    return NextResponse.json({ error: 'Failed to delete project folder.' }, { status: 500 });
  }

  return new NextResponse(null, { status: 204 });
}


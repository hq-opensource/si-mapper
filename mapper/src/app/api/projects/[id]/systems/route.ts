/**
 * GET  /api/projects/[id]/systems  — list all systems within a project
 * POST /api/projects/[id]/systems  — create a new system within a project
 */

import { NextRequest, NextResponse } from 'next/server';
import { z } from 'zod';
import { createSystemOnDisk, getProject, listSystems } from '@/lib/projects';
import { createGrid } from '@/lib/graphivac-client';

// ── Zod schema ────────────────────────────────────────────────────────────────

const CreateSystemSchema = z.object({
  name: z.string().min(1, 'name is required'),
});

// ── Shared helper ─────────────────────────────────────────────────────────────

type Params = { params: Promise<{ id: string }> };

// ── GET /api/projects/[id]/systems ────────────────────────────────────────────

export async function GET(_req: NextRequest, { params }: Params): Promise<NextResponse> {
  const { id } = await params;

  const project = await getProject(id);
  if (!project) {
    return NextResponse.json({ error: 'Project not found.' }, { status: 404 });
  }

  try {
    const systems = await listSystems(project.folder_path);
    return NextResponse.json(systems, { status: 200 });
  } catch (err) {
    console.error(`[GET /api/projects/${id}/systems]`, err);
    return NextResponse.json({ error: 'Failed to list systems.' }, { status: 500 });
  }
}

// ── POST /api/projects/[id]/systems ───────────────────────────────────────────

export async function POST(req: NextRequest, { params }: Params): Promise<NextResponse> {
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

  const parsed = CreateSystemSchema.safeParse(body);
  if (!parsed.success) {
    return NextResponse.json(
      { error: 'Validation failed.', details: parsed.error.flatten() },
      { status: 400 }
    );
  }

  const { name } = parsed.data;

  // 1. Create Graphivac Grid — fail early if this fails.
  let graphivac_grid_id: string;
  try {
    graphivac_grid_id = await createGrid(project.graphivac_project_id, name);
  } catch (err) {
    console.error(`[POST /api/projects/${id}/systems] Graphivac createGrid failed:`, err);
    return NextResponse.json(
      { error: 'Failed to create Graphivac grid.', details: String(err) },
      { status: 502 }
    );
  }

  // 2. Create system on disk — only reached if Graphivac succeeded.
  try {
    const system = await createSystemOnDisk(project.folder_path, {
      name,
      graphivac_grid_id,
    });
    return NextResponse.json(system, { status: 201 });
  } catch (err) {
    console.error(`[POST /api/projects/${id}/systems] Disk creation failed:`, err);
    return NextResponse.json({ error: 'Failed to create system on disk.' }, { status: 500 });
  }
}


/**
 * GET  /api/projects  — list all projects
 * POST /api/projects  — create a new project
 */

import { NextRequest, NextResponse } from 'next/server';
import { z } from 'zod';
import { createProjectOnDisk, listProjects } from '@/lib/projects';
import { createGraphivacProject } from '@/lib/graphivac-client';

// ── Zod schema ────────────────────────────────────────────────────────────────

const CreateProjectSchema = z.object({
  name: z.string().min(1, 'name is required'),
});

// ── GET /api/projects ─────────────────────────────────────────────────────────

export async function GET(): Promise<NextResponse> {
  try {
    const projects = await listProjects();
    return NextResponse.json(projects, { status: 200 });
  } catch (err) {
    console.error('[GET /api/projects]', err);
    return NextResponse.json({ error: 'Failed to list projects.' }, { status: 500 });
  }
}

// ── POST /api/projects ────────────────────────────────────────────────────────

export async function POST(req: NextRequest): Promise<NextResponse> {
  let body: unknown;
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: 'Invalid JSON body.' }, { status: 400 });
  }

  const parsed = CreateProjectSchema.safeParse(body);
  if (!parsed.success) {
    return NextResponse.json(
      { error: 'Validation failed.', details: parsed.error.flatten() },
      { status: 400 }
    );
  }

  const { name } = parsed.data;

  // 1. Create Graphivac Project — fail early if this fails.
  let graphivac_project_id: string;
  try {
    graphivac_project_id = await createGraphivacProject(name);
  } catch (err) {
    console.error('[POST /api/projects] Graphivac createProject failed:', err);
    return NextResponse.json(
      { error: 'Failed to create Graphivac project.', details: String(err) },
      { status: 502 }
    );
  }

  // 2. Create on disk — only reached if Graphivac succeeded.
  try {
    const project = await createProjectOnDisk({ name, graphivac_project_id });
    return NextResponse.json(project, { status: 201 });
  } catch (err) {
    console.error('[POST /api/projects] Disk creation failed:', err);
    return NextResponse.json({ error: 'Failed to create project on disk.' }, { status: 500 });
  }
}


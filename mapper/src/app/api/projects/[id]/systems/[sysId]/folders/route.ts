/**
 * GET  /api/projects/[id]/systems/[sysId]/folders  — list subdirectories
 * POST /api/projects/[id]/systems/[sysId]/folders  — create a subdirectory
 */

import fs from 'fs/promises';
import path from 'path';
import { NextRequest, NextResponse } from 'next/server';
import { z } from 'zod';
import { getProject, getSystem, systemDir } from '@/lib/projects';

// ── Shared helper ─────────────────────────────────────────────────────────────

type Params = { params: Promise<{ id: string; sysId: string }> };

async function resolveSystemFolder(
  id: string,
  sysId: string,
): Promise<{ folder: string } | NextResponse> {
  const project = await getProject(id);
  if (!project) return NextResponse.json({ error: 'Project not found.' }, { status: 404 });

  const system = await getSystem(project.folder_path, sysId);
  if (!system) return NextResponse.json({ error: 'System not found.' }, { status: 404 });

  return { folder: systemDir(project.folder_path, system.folder_path) };
}

/** Allow only simple, safe directory names (no path separators, no dot-only names). */
export function isSafeFolderName(name: string): boolean {
  return (
    name.length > 0 &&
    name.length <= 100 &&
    !name.includes('/') &&
    !name.includes('\\') &&
    /^[a-zA-Z0-9._\- ]+$/.test(name) &&
    name !== '.' &&
    name !== '..'
  );
}

// ── GET /api/projects/[id]/systems/[sysId]/folders ────────────────────────────

export async function GET(_req: NextRequest, { params }: Params): Promise<NextResponse> {
  const { id, sysId } = await params;

  const resolved = await resolveSystemFolder(id, sysId);
  if (resolved instanceof NextResponse) return resolved;
  const { folder } = resolved;

  try {
    const entries = await fs.readdir(folder, { withFileTypes: true });
    const folders = await Promise.all(
      entries
        .filter((e) => e.isDirectory())
        .map(async (e) => {
          const dirPath = path.join(folder, e.name);
          const subEntries = await fs.readdir(dirPath, { withFileTypes: true });
          const fileCount = subEntries.filter((s) => s.isFile()).length;
          const stat = await fs.stat(dirPath);
          return {
            name: e.name,
            file_count: fileCount,
            created_at: stat.birthtime.toISOString(),
          };
        }),
    );
    return NextResponse.json(folders, { status: 200 });
  } catch (err) {
    console.error(`[GET /api/projects/${id}/systems/${sysId}/folders]`, err);
    return NextResponse.json({ error: 'Failed to list folders.' }, { status: 500 });
  }
}

// ── POST /api/projects/[id]/systems/[sysId]/folders ───────────────────────────

const CreateFolderSchema = z.object({
  name: z.string().min(1, 'name is required'),
});

export async function POST(req: NextRequest, { params }: Params): Promise<NextResponse> {
  const { id, sysId } = await params;

  const resolved = await resolveSystemFolder(id, sysId);
  if (resolved instanceof NextResponse) return resolved;
  const { folder } = resolved;

  let body: unknown;
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: 'Invalid JSON body.' }, { status: 400 });
  }

  const parsed = CreateFolderSchema.safeParse(body);
  if (!parsed.success) {
    return NextResponse.json(
      { error: 'Validation failed.', details: parsed.error.flatten() },
      { status: 400 },
    );
  }

  const { name } = parsed.data;
  if (!isSafeFolderName(name)) {
    return NextResponse.json(
      { error: `Invalid folder name: "${name}". Use letters, numbers, spaces, dots, dashes and underscores only.` },
      { status: 400 },
    );
  }

  const targetDir = path.join(folder, name);

  // Path traversal guard (belt-and-suspenders after isSafeFolderName).
  if (!targetDir.startsWith(folder + path.sep)) {
    return NextResponse.json({ error: 'Invalid folder name.' }, { status: 400 });
  }

  // Conflict check.
  try {
    await fs.access(targetDir);
    return NextResponse.json(
      { error: `Folder "${name}" already exists.` },
      { status: 409 },
    );
  } catch {
    // Doesn't exist — proceed.
  }

  try {
    await fs.mkdir(targetDir);
    return NextResponse.json({ name, file_count: 0 }, { status: 201 });
  } catch (err) {
    console.error(`[POST /api/projects/${id}/systems/${sysId}/folders]`, err);
    return NextResponse.json({ error: 'Failed to create folder.' }, { status: 500 });
  }
}


/**
 * PATCH  /api/projects/[id]/systems/[sysId]/folders/[folderName]  — rename a subfolder
 * DELETE /api/projects/[id]/systems/[sysId]/folders/[folderName]  — delete a subfolder (recursive)
 */

import fs from 'fs/promises';
import path from 'path';
import { NextRequest, NextResponse } from 'next/server';
import { z } from 'zod';
import { getProject, getSystem, systemDir } from '@/lib/projects';
import { isSafeFolderName } from '../route';

type Params = { params: Promise<{ id: string; sysId: string; folderName: string }> };

/** Resolve and guard a folder path inside a system directory. */
async function resolveFolder(
  id: string,
  sysId: string,
  folderName: string,
): Promise<{ sysFolder: string; targetDir: string } | NextResponse> {
  const project = await getProject(id);
  if (!project) return NextResponse.json({ error: 'Project not found.' }, { status: 404 });

  const system = await getSystem(project.folder_path, sysId);
  if (!system) return NextResponse.json({ error: 'System not found.' }, { status: 404 });

  const sysFolder = systemDir(project.folder_path, system.folder_path);
  const decoded = decodeURIComponent(folderName);

  if (!isSafeFolderName(decoded)) {
    return NextResponse.json({ error: 'Invalid folder name.' }, { status: 400 });
  }

  const targetDir = path.resolve(sysFolder, decoded);

  // Path traversal guard.
  if (!targetDir.startsWith(sysFolder + path.sep)) {
    return NextResponse.json({ error: 'Invalid folder name.' }, { status: 400 });
  }

  return { sysFolder, targetDir };
}

// ── PATCH /api/projects/[id]/systems/[sysId]/folders/[folderName] ─────────────

const RenameFolderSchema = z.object({
  name: z.string().min(1, 'name is required'),
});

export async function PATCH(req: NextRequest, { params }: Params): Promise<NextResponse> {
  const { id, sysId, folderName } = await params;

  const resolved = await resolveFolder(id, sysId, folderName);
  if (resolved instanceof NextResponse) return resolved;
  const { sysFolder, targetDir } = resolved;

  // Verify source exists and is a directory.
  try {
    const stat = await fs.stat(targetDir);
    if (!stat.isDirectory()) {
      return NextResponse.json({ error: 'Not a folder.' }, { status: 400 });
    }
  } catch {
    return NextResponse.json({ error: 'Folder not found.' }, { status: 404 });
  }

  let body: unknown;
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: 'Invalid JSON body.' }, { status: 400 });
  }

  const parsed = RenameFolderSchema.safeParse(body);
  if (!parsed.success) {
    return NextResponse.json(
      { error: 'Validation failed.', details: parsed.error.flatten() },
      { status: 400 },
    );
  }

  const newName = parsed.data.name.trim();
  if (!isSafeFolderName(newName)) {
    return NextResponse.json({ error: 'Invalid folder name.' }, { status: 400 });
  }

  const destDir = path.join(sysFolder, newName);

  // Conflict check.
  try {
    await fs.access(destDir);
    return NextResponse.json(
      { error: `Folder "${newName}" already exists.` },
      { status: 409 },
    );
  } catch {
    // Destination doesn't exist — proceed.
  }

  try {
    await fs.rename(targetDir, destDir);
    // Return the updated file count.
    const subEntries = await fs.readdir(destDir, { withFileTypes: true });
    const fileCount = subEntries.filter((e) => e.isFile()).length;
    return NextResponse.json({ name: newName, file_count: fileCount }, { status: 200 });
  } catch (err) {
    console.error(`[PATCH /api/projects/${id}/systems/${sysId}/folders/${folderName}]`, err);
    return NextResponse.json({ error: 'Failed to rename folder.' }, { status: 500 });
  }
}

// ── DELETE /api/projects/[id]/systems/[sysId]/folders/[folderName] ────────────

export async function DELETE(_req: NextRequest, { params }: Params): Promise<NextResponse> {
  const { id, sysId, folderName } = await params;

  const resolved = await resolveFolder(id, sysId, folderName);
  if (resolved instanceof NextResponse) return resolved;
  const { targetDir } = resolved;

  // Verify source exists and is a directory.
  try {
    const stat = await fs.stat(targetDir);
    if (!stat.isDirectory()) {
      return NextResponse.json({ error: 'Not a folder.' }, { status: 400 });
    }
  } catch {
    return NextResponse.json({ error: 'Folder not found.' }, { status: 404 });
  }

  try {
    await fs.rm(targetDir, { recursive: true, force: true });
    return new NextResponse(null, { status: 204 });
  } catch (err) {
    console.error(`[DELETE /api/projects/${id}/systems/${sysId}/folders/${folderName}]`, err);
    return NextResponse.json({ error: 'Failed to delete folder.' }, { status: 500 });
  }
}


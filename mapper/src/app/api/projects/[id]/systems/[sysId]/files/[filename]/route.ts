/**
 * DELETE /api/projects/[id]/systems/[sysId]/files/[filename]            — delete a file from root
 * DELETE /api/projects/[id]/systems/[sysId]/files/[filename]?subfolder=X — delete a file from a subfolder
 *
 * The optional `subfolder` query param must be a single path component (no separators).
 * Path traversal is rejected with 400.
 */

import fs from 'fs/promises';
import path from 'path';
import { NextRequest, NextResponse } from 'next/server';
import { getProject, getSystem, systemDir } from '@/lib/projects';

type Params = { params: Promise<{ id: string; sysId: string; filename: string }> };

/** Resolve an optional subfolder, with path traversal protection. Returns null if invalid. */
function resolveSubfolder(sysFolder: string, subfolder: string): string | null {
  if (!subfolder) return sysFolder;
  if (subfolder.includes('/') || subfolder.includes('\\')) return null;
  const resolved = path.resolve(sysFolder, subfolder);
  if (!resolved.startsWith(sysFolder + path.sep)) return null;
  return resolved;
}

export async function DELETE(req: NextRequest, { params }: Params): Promise<NextResponse> {
  const { id, sysId, filename } = await params;

  // 1. Verify project and system exist.
  const project = await getProject(id);
  if (!project) {
    return NextResponse.json({ error: 'Project not found.' }, { status: 404 });
  }

  const system = await getSystem(project.folder_path, sysId);
  if (!system) {
    return NextResponse.json({ error: 'System not found.' }, { status: 404 });
  }

  const sysFolder = systemDir(project.folder_path, system.folder_path);

  // 2. Resolve optional subfolder.
  const subfolder = new URL(req.url).searchParams.get('subfolder') ?? '';
  const targetFolder = resolveSubfolder(sysFolder, subfolder);
  if (!targetFolder) {
    return NextResponse.json({ error: 'Invalid subfolder.' }, { status: 400 });
  }

  // 3. Decode and resolve the file path — guard against path traversal.
  const decodedFilename = decodeURIComponent(filename);
  const resolvedFile = path.resolve(targetFolder, decodedFilename);

  if (!resolvedFile.startsWith(targetFolder + path.sep) && resolvedFile !== targetFolder) {
    return NextResponse.json(
      { error: 'Invalid filename: path escapes the target folder.' },
      { status: 400 },
    );
  }

  // 4. Delete the file.
  try {
    await fs.unlink(resolvedFile);
  } catch (err: unknown) {
    if ((err as NodeJS.ErrnoException).code === 'ENOENT') {
      return NextResponse.json({ error: 'File not found.' }, { status: 404 });
    }
    console.error(`[DELETE /api/projects/${id}/systems/${sysId}/files/${filename}]`, err);
    return NextResponse.json({ error: 'Failed to delete file.' }, { status: 500 });
  }

  return new NextResponse(null, { status: 204 });
}


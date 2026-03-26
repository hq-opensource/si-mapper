/**
 * DELETE /api/projects/[id]/systems/[sysId]/files/[filename]
 * Permanently deletes a single file from the system's folder.
 */

import fs from 'fs/promises';
import path from 'path';
import { NextRequest, NextResponse } from 'next/server';
import { getProject, getSystem, systemDir } from '@/lib/projects';

type Params = { params: Promise<{ id: string; sysId: string; filename: string }> };

export async function DELETE(_req: NextRequest, { params }: Params): Promise<NextResponse> {
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

  const folder = systemDir(project.folder_path, system.folder_path);

  // 2. Decode and resolve the file path — guard against path traversal.
  const decodedFilename = decodeURIComponent(filename);
  const resolvedFile = path.resolve(folder, decodedFilename);

  if (!resolvedFile.startsWith(folder + path.sep) && resolvedFile !== folder) {
    return NextResponse.json(
      { error: 'Invalid filename: path escapes the system folder.' },
      { status: 400 }
    );
  }

  // 3. Delete the file.
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


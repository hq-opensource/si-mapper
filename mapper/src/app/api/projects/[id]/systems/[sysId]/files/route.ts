/**
 * GET  /api/projects/[id]/systems/[sysId]/files  — list files in a system's folder
 * POST /api/projects/[id]/systems/[sysId]/files  — upload files into a system's folder
 */

import fs from 'fs/promises';
import path from 'path';
import { NextRequest, NextResponse } from 'next/server';
import { getProject, getSystem, systemDir } from '@/lib/projects';

// ── Shared helper ─────────────────────────────────────────────────────────────

type Params = { params: Promise<{ id: string; sysId: string }> };

async function resolveSystemFolder(
  id: string,
  sysId: string
): Promise<
  | { project: Awaited<ReturnType<typeof getProject>>; system: Awaited<ReturnType<typeof getSystem>>; folder: string }
  | NextResponse
> {
  const project = await getProject(id);
  if (!project) return NextResponse.json({ error: 'Project not found.' }, { status: 404 });

  const system = await getSystem(project.folder_path, sysId);
  if (!system) return NextResponse.json({ error: 'System not found.' }, { status: 404 });

  const folder = systemDir(project.folder_path, system.folder_path);
  return { project, system, folder };
}

// ── GET /api/projects/[id]/systems/[sysId]/files ──────────────────────────────

export async function GET(_req: NextRequest, { params }: Params): Promise<NextResponse> {
  const { id, sysId } = await params;

  const resolved = await resolveSystemFolder(id, sysId);
  if (resolved instanceof NextResponse) return resolved;
  const { folder } = resolved;

  try {
    const entries = await fs.readdir(folder, { withFileTypes: true });
    const files = await Promise.all(
      entries
        .filter((e) => e.isFile())
        .map(async (e) => {
          const filePath = path.join(folder, e.name);
          const stat = await fs.stat(filePath);
          return {
            name: e.name,
            size: stat.size,
            modified_at: stat.mtime.toISOString(),
            url: `/api/projects/${id}/systems/${sysId}/files/${encodeURIComponent(e.name)}`,
          };
        })
    );
    return NextResponse.json(files, { status: 200 });
  } catch (err) {
    console.error(`[GET /api/projects/${id}/systems/${sysId}/files]`, err);
    return NextResponse.json({ error: 'Failed to list files.' }, { status: 500 });
  }
}

// ── POST /api/projects/[id]/systems/[sysId]/files ────────────────────────────

export async function POST(req: NextRequest, { params }: Params): Promise<NextResponse> {
  const { id, sysId } = await params;

  const resolved = await resolveSystemFolder(id, sysId);
  if (resolved instanceof NextResponse) return resolved;
  const { folder } = resolved;

  let formData: FormData;
  try {
    formData = await req.formData();
  } catch {
    return NextResponse.json({ error: 'Failed to parse multipart form data.' }, { status: 400 });
  }

  const overwrite = formData.get('overwrite') === 'true';
  const fileEntries = formData.getAll('files') as File[];

  if (!fileEntries.length) {
    return NextResponse.json({ error: 'No files provided in the request.' }, { status: 400 });
  }

  const uploaded: { name: string; size: number; url: string }[] = [];

  for (const file of fileEntries) {
    // Sanitise filename — strip path components.
    const safeName = path.basename(file.name).replace(/[^a-zA-Z0-9._\- ]/g, '_');
    const dest = path.join(folder, safeName);

    // Path traversal guard.
    if (!dest.startsWith(folder + path.sep) && dest !== folder) {
      return NextResponse.json(
        { error: `Invalid filename: "${file.name}".` },
        { status: 400 }
      );
    }

    // Conflict check.
    if (!overwrite) {
      try {
        await fs.access(dest);
        // File exists.
        return NextResponse.json(
          { error: `File already exists: "${safeName}". Set overwrite=true to replace it.` },
          { status: 409 }
        );
      } catch {
        // File does not exist — continue.
      }
    }

    const buffer = Buffer.from(await file.arrayBuffer());
    await fs.writeFile(dest, buffer);

    uploaded.push({
      name: safeName,
      size: buffer.byteLength,
      url: `/api/projects/${id}/systems/${sysId}/files/${encodeURIComponent(safeName)}`,
    });
  }

  return NextResponse.json({ uploaded }, { status: 200 });
}



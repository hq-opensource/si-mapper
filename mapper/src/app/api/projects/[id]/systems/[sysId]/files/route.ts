/**
 * GET  /api/projects/[id]/systems/[sysId]/files           — list files in a system's folder (root)
 * GET  /api/projects/[id]/systems/[sysId]/files?subfolder=X — list files in a subfolder
 * POST /api/projects/[id]/systems/[sysId]/files           — upload files into a system's folder (root)
 * POST /api/projects/[id]/systems/[sysId]/files?subfolder=X — upload files into a subfolder
 *
 * The optional `subfolder` query param must be a single path component (no separators).
 * Path traversal is rejected with 400.
 */

import fs from 'fs/promises';
import path from 'path';
import { NextRequest, NextResponse } from 'next/server';
import { getProject, getSystem, systemDir } from '@/lib/projects';

/** Internal metadata files that must never be exposed to the user. */
const HIDDEN_FILES = new Set(['system.json', 'project.json']);

/** Resolve an optional subfolder relative to sysFolder, with path traversal protection.
 *  Returns null if the subfolder param is invalid or escapes the system root. */
function resolveSubfolder(sysFolder: string, subfolder: string): string | null {
  if (!subfolder) return sysFolder;
  // Reject any separators — only single-level names allowed.
  if (subfolder.includes('/') || subfolder.includes('\\')) return null;
  const resolved = path.resolve(sysFolder, subfolder);
  if (!resolved.startsWith(sysFolder + path.sep)) return null;
  return resolved;
}

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

export async function GET(req: NextRequest, { params }: Params): Promise<NextResponse> {
  const { id, sysId } = await params;

  const resolved = await resolveSystemFolder(id, sysId);
  if (resolved instanceof NextResponse) return resolved;
  const { folder } = resolved;

  const subfolder = new URL(req.url).searchParams.get('subfolder') ?? '';
  const targetFolder = resolveSubfolder(folder, subfolder);
  if (!targetFolder) {
    return NextResponse.json({ error: 'Invalid subfolder.' }, { status: 400 });
  }

  try {
    const entries = await fs.readdir(targetFolder, { withFileTypes: true });
    const files = await Promise.all(
      entries
        .filter((e) => e.isFile() && !HIDDEN_FILES.has(e.name))
        .map(async (e) => {
          const filePath = path.join(targetFolder, e.name);
          const stat = await fs.stat(filePath);
          const fileUrl = subfolder
            ? `/api/projects/${id}/systems/${sysId}/files/${encodeURIComponent(e.name)}?subfolder=${encodeURIComponent(subfolder)}`
            : `/api/projects/${id}/systems/${sysId}/files/${encodeURIComponent(e.name)}`;
          return {
            name: e.name,
            size: stat.size,
            modified_at: stat.mtime.toISOString(),
            url: fileUrl,
          };
        }),
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
  const subfolderRaw = formData.get('subfolder');
  const subfolder = typeof subfolderRaw === 'string' ? subfolderRaw : '';

  const targetFolder = resolveSubfolder(folder, subfolder);
  if (!targetFolder) {
    return NextResponse.json({ error: 'Invalid subfolder.' }, { status: 400 });
  }

  // Ensure the target folder exists (it must already exist — we don't auto-create).
  try {
    await fs.access(targetFolder);
  } catch {
    return NextResponse.json(
      { error: `Subfolder "${subfolder}" does not exist. Create it first.` },
      { status: 404 },
    );
  }

  const fileEntries = formData.getAll('files') as File[];

  if (!fileEntries.length) {
    return NextResponse.json({ error: 'No files provided in the request.' }, { status: 400 });
  }

  const uploaded: { name: string; size: number; url: string }[] = [];

  for (const file of fileEntries) {
    // Sanitise filename — strip path components.
    const safeName = path.basename(file.name).replace(/[^a-zA-Z0-9._\- ]/g, '_');
    const dest = path.join(targetFolder, safeName);

    // Path traversal guard.
    if (!dest.startsWith(targetFolder + path.sep) && dest !== targetFolder) {
      return NextResponse.json(
        { error: `Invalid filename: "${file.name}".` },
        { status: 400 },
      );
    }

    // Conflict check.
    if (!overwrite) {
      try {
        await fs.access(dest);
        // File exists.
        return NextResponse.json(
          { error: `File already exists: "${safeName}". Set overwrite=true to replace it.` },
          { status: 409 },
        );
      } catch {
        // File does not exist — continue.
      }
    }

    const buffer = Buffer.from(await file.arrayBuffer());
    await fs.writeFile(dest, buffer);

    const fileUrl = subfolder
      ? `/api/projects/${id}/systems/${sysId}/files/${encodeURIComponent(safeName)}?subfolder=${encodeURIComponent(subfolder)}`
      : `/api/projects/${id}/systems/${sysId}/files/${encodeURIComponent(safeName)}`;

    uploaded.push({ name: safeName, size: buffer.byteLength, url: fileUrl });
  }

  return NextResponse.json({ uploaded }, { status: 200 });
}

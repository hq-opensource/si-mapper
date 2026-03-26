import { NextResponse } from 'next/server';
import { readFile, stat } from 'fs/promises';
import path from 'path';

function getProjectsFolder(): string {
  return process.env.PROJECTS_FOLDER
    ? path.resolve(process.env.PROJECTS_FOLDER)
    : path.join(process.cwd(), 'uploads');
}

function isUnder(parent: string, child: string): boolean {
  return child === parent || child.startsWith(parent + path.sep);
}

export async function GET(request: Request) {
    try {
        const { searchParams } = new URL(request.url);
        const id = searchParams.get('id');
        const projectParam = searchParams.get('project');
        const systemParam = searchParams.get('system');

        if (!id) return NextResponse.json({ error: 'ID required' }, { status: 400 });

        const PROJECTS_FOLDER = getProjectsFolder();

        // Resolve effective root (same scoping logic as /api/files GET)
        let effectiveRoot = PROJECTS_FOLDER;

        if (projectParam) {
            const projectPath = path.resolve(PROJECTS_FOLDER, projectParam);
            if (!isUnder(PROJECTS_FOLDER, projectPath)) {
                return NextResponse.json({ error: 'Invalid project path' }, { status: 400 });
            }
            effectiveRoot = projectPath;
        }

        if (systemParam) {
            const systemPath = path.resolve(effectiveRoot, systemParam);
            if (!isUnder(effectiveRoot, systemPath)) {
                return NextResponse.json({ error: 'Invalid system path' }, { status: 400 });
            }
            effectiveRoot = systemPath;
        }

        const targetPath = path.resolve(effectiveRoot, id.replace(/^\//, ''));
        if (!isUnder(PROJECTS_FOLDER, targetPath)) {
            return NextResponse.json({ error: 'Invalid path' }, { status: 400 });
        }

        const stats = await stat(targetPath);

        if (stats.isDirectory()) {
            return NextResponse.json({ error: 'Cannot view a directory' }, { status: 400 });
        }

        const buffer = await readFile(targetPath);
        const ext = path.extname(targetPath).toLowerCase();
        
        let contentType = 'application/octet-stream';
        if (ext === '.jpg' || ext === '.jpeg') contentType = 'image/jpeg';
        else if (ext === '.png') contentType = 'image/png';
        else if (ext === '.gif') contentType = 'image/gif';
        else if (ext === '.pdf') contentType = 'application/pdf';
        else if (ext === '.txt') contentType = 'text/plain';
        else if (ext === '.json') contentType = 'application/json';
        else if (ext === '.csv') contentType = 'text/csv';
        else if (ext === '.py' || ext === '.ttl' || ext === '.md') contentType = 'text/plain; charset=utf-8';

        return new Response(buffer, {
            headers: {
                'Content-Type': contentType,
                'Content-Length': buffer.length.toString(),
            },
        });

    } catch (error) {
        console.error('View error:', error);
        return NextResponse.json({ error: 'Failed to read file' }, { status: 500 });
    }
}


import { NextResponse } from 'next/server';
import { readFile, stat } from 'fs/promises';
import path from 'path';

const UPLOADS_DIR = path.join(process.cwd(), 'uploads');

const validatePath = (requestedPath: string | null) => {
    const targetPath = requestedPath ? path.resolve(UPLOADS_DIR, requestedPath.replace(/^\//, '')) : UPLOADS_DIR;
    if (!targetPath.startsWith(UPLOADS_DIR)) {
        throw new Error('Invalid path');
    }
    return targetPath;
};

export async function GET(request: Request) {
    try {
        const { searchParams } = new URL(request.url);
        const id = searchParams.get('id');

        if (!id) return NextResponse.json({ error: 'ID required' }, { status: 400 });

        const targetPath = validatePath(id);
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

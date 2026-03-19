import { NextResponse } from 'next/server';
import { readdir, stat } from 'fs/promises';
import path from 'path';

const UPLOADS_DIR = path.join(process.cwd(), 'uploads');

// Helper to validate paths
const validatePath = (requestedPath: string | null) => {
    const targetPath = requestedPath ? path.resolve(UPLOADS_DIR, requestedPath.replace(/^\//, '')) : UPLOADS_DIR;
    if (!targetPath.startsWith(UPLOADS_DIR)) {
        throw new Error('Invalid path');
    }
    return targetPath;
};

const getTree = async (dir: string): Promise<any[]> => {
    try {
        const entries = await readdir(dir, { withFileTypes: true });
        const files = await Promise.all(entries.map(async (entry) => {
            const fullPath = path.join(dir, entry.name);
            const stats = await stat(fullPath);
            const relativePath = path.relative(UPLOADS_DIR, fullPath);
            const id = `/${relativePath}`;
            
            // pId should be "/" if the parent is UPLOADS_DIR
            const parentRelPath = path.relative(UPLOADS_DIR, dir);
            const pId = parentRelPath === "" ? "/" : `/${parentRelPath}`;

            const item: any = {
                id,
                pId,
                name: entry.name,
                value: entry.name,
                size: stats.size,
                date: new Date(stats.mtime).getTime() / 1000,
                type: entry.isDirectory() ? 'folder' : 'file',
                open: false
            };

            if (entry.isDirectory()) {
                const subTree = await getTree(fullPath);
                return [item, ...subTree];
            }
            return [item];
        }));
        return files.flat();
    } catch (e) {
        console.error("Tree error:", e);
        return [];
    }
};

// GET: List files in a directory
export async function GET(request: Request) {
    try {
        const { searchParams } = new URL(request.url);
        const id = searchParams.get('id'); 
        const tree = searchParams.get('tree') === 'true';

        if (tree) {
            const items = await getTree(UPLOADS_DIR);
            return NextResponse.json(items);
        }

        const targetPath = validatePath(id);
        const entries = await readdir(targetPath, { withFileTypes: true });

        const files = await Promise.all(entries.map(async (entry) => {
            const fullPath = path.join(targetPath, entry.name);
            const stats = await stat(fullPath);
            const relativePath = path.relative(UPLOADS_DIR, fullPath);
            
            const parentRelPath = path.relative(UPLOADS_DIR, targetPath);
            const pId = parentRelPath === "" ? "/" : `/${parentRelPath}`;

            return {
                id: `/${relativePath}`,
                pId,
                name: entry.name,
                value: entry.name,
                size: stats.size,
                date: new Date(stats.mtime).getTime() / 1000,
                type: entry.isDirectory() ? 'folder' : 'file',
                open: false
            };
        }));

        return NextResponse.json(files);
    } catch (error) {
        console.error('GET error:', error);
        return NextResponse.json({ error: 'Failed to list files' }, { status: 500 });
    }
}
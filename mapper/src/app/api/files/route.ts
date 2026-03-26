import { NextResponse } from 'next/server';
import { readdir, stat } from 'fs/promises';
import path from 'path';

/** Returns PROJECTS_FOLDER evaluated at call time (testable via env var). */
function getProjectsFolder(): string {
  return process.env.PROJECTS_FOLDER
    ? path.resolve(process.env.PROJECTS_FOLDER)
    : path.join(process.cwd(), 'uploads');
}

/** True when `child` is equal to `parent` or is nested beneath it. */
function isUnder(parent: string, child: string): boolean {
  return child === parent || child.startsWith(parent + path.sep);
}

// Helper to validate paths against a given root
const validatePath = (requestedPath: string | null, root: string) => {
    const targetPath = requestedPath
      ? path.resolve(root, requestedPath.replace(/^\//, ''))
      : root;
    if (!isUnder(root, targetPath)) {
        throw new Error('Invalid path');
    }
    return targetPath;
};

const getTree = async (dir: string, rootDir: string): Promise<any[]> => {
    try {
        const entries = await readdir(dir, { withFileTypes: true });
        const files = await Promise.all(entries.map(async (entry) => {
            const fullPath = path.join(dir, entry.name);
            const stats = await stat(fullPath);
            const relativePath = path.relative(rootDir, fullPath);
            const id = `/${relativePath.split(path.sep).join('/')}`;

            const parentRelPath = path.relative(rootDir, dir);
            const pId = parentRelPath === "" ? "/" : `/${parentRelPath.split(path.sep).join('/')}`;

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
                const subTree = await getTree(fullPath, rootDir);
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
        const projectParam = searchParams.get('project');
        const systemParam = searchParams.get('system');

        const PROJECTS_FOLDER = getProjectsFolder();

        // Resolve the effective root (optionally scoped to project/system)
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

        if (tree) {
            const items = await getTree(effectiveRoot, effectiveRoot);
            return NextResponse.json(items);
        }

        const targetPath = validatePath(id, effectiveRoot);
        const entries = await readdir(targetPath, { withFileTypes: true });

        const files = await Promise.all(entries.map(async (entry) => {
            const fullPath = path.join(targetPath, entry.name);
            const stats = await stat(fullPath);
            const relativePath = path.relative(effectiveRoot, fullPath);

            const parentRelPath = path.relative(effectiveRoot, targetPath);
            const pId = parentRelPath === "" ? "/" : `/${parentRelPath.split(path.sep).join('/')}`;

            return {
                id: `/${relativePath.split(path.sep).join('/')}`,
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
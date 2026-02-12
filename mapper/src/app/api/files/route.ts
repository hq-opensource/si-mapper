import { NextResponse } from 'next/server';
import { readdir, stat, mkdir, rmdir, unlink, rename } from 'fs/promises';
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

// GET: List files in a directory
export async function GET(request: Request) {
    try {
        const { searchParams } = new URL(request.url);
        const id = searchParams.get('id'); // ID represents the path for lazy loading
        const targetPath = validatePath(id);

        const entries = await readdir(targetPath, { withFileTypes: true });

        const files = await Promise.all(entries.map(async (entry) => {
            const fullPath = path.join(targetPath, entry.name);
            const stats = await stat(fullPath);
            const relativePath = path.relative(UPLOADS_DIR, fullPath);

            // Returning consistent file structure
            return {
                id: `/${relativePath}`, // Path as ID
                name: entry.name,
                size: stats.size,
                date: new Date(stats.mtime).getTime() / 1000, // Unix timestamp in seconds
                type: entry.isDirectory() ? 'folder' : 'file',
                open: false // For folders
            };
        }));

        return NextResponse.json(files);
    } catch (error) {
        console.error('GET error:', error);
        return NextResponse.json({ error: 'Failed to list files' }, { status: 500 });
    }
}

// POST: Create Folder
export async function POST(request: Request) {
    try {
        const createParams = await request.formData();
        const parent = createParams.get('target') as string || '/'; // Parent folder ID
        const name = createParams.get('name') as string;

        if (!name) return NextResponse.json({ error: 'Name required' }, { status: 400 });

        const parentPath = validatePath(parent);
        const newFolderPath = path.join(parentPath, name);

        // Ensure we don't overwrite
        try {
            await stat(newFolderPath);
            return NextResponse.json({ error: 'Folder already exists' }, { status: 400 });
        } catch (e) {
            // Good, it doesn't exist
        }

        await mkdir(newFolderPath);

        // Return the new folder object
        const stats = await stat(newFolderPath);
        const relativePath = path.relative(UPLOADS_DIR, newFolderPath);

        return NextResponse.json({
            id: `/${relativePath}`,
            name: name,
            size: stats.size,
            date: new Date(stats.mtime).getTime() / 1000,
            type: 'folder',
            open: false
        });

    } catch (error) {
        console.error('POST error:', error);
        return NextResponse.json({ error: 'Failed to create folder' }, { status: 500 });
    }
}

// DELETE: Remove files/folders
export async function DELETE(request: Request) {
    try {
        // Expects form data with "ids"
        const formData = await request.formData();
        const ids = formData.get('ids');

        if (!ids) return NextResponse.json({ error: 'No IDs provided' }, { status: 400 });

        const idList = ids.toString().split(',').filter(Boolean);

        for (const id of idList) {
            const itemPath = validatePath(id);
            const stats = await stat(itemPath);
            if (stats.isDirectory()) {
                await rmdir(itemPath, { recursive: true });
            } else {
                await unlink(itemPath);
            }
        }

        return NextResponse.json({ status: 'success' });
    } catch (error) {
        console.error('DELETE error:', error);
        return NextResponse.json({ error: 'Failed to delete items' }, { status: 500 });
    }
}

// PUT: Rename items
export async function PUT(request: Request) {
    try {
        const formData = await request.formData();
        const id = formData.get('id') as string;
        const value = formData.get('value') as string; // New name

        if (!id || !value) return NextResponse.json({ error: 'Invalid parameters' }, { status: 400 });

        const oldPath = validatePath(id);
        const dir = path.dirname(oldPath);
        const newPath = path.join(dir, value);

        // Check local collision in same dir
        // Security check: ensure newPath is still within UPLOADS_DIR (dirname ensures this if oldPath was valid, but checking doesn't hurt)
        if (!newPath.startsWith(UPLOADS_DIR)) throw new Error("Invalid destination");

        await rename(oldPath, newPath);

        return NextResponse.json({ status: 'success' });

    } catch (error) {
        console.error('PUT error:', error);
        return NextResponse.json({ error: 'Failed to rename item' }, { status: 500 });
    }
}
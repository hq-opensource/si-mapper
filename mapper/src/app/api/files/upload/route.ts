import { NextResponse } from 'next/server';
import { writeFile, mkdir } from 'fs/promises';
import path from 'path';

const UPLOADS_DIR = path.join(process.cwd(), 'uploads');

const validatePath = (requestedPath: string | null) => {
    const targetPath = requestedPath ? path.resolve(UPLOADS_DIR, requestedPath.replace(/^\//, '')) : UPLOADS_DIR;
    if (!targetPath.startsWith(UPLOADS_DIR)) {
        throw new Error('Invalid path');
    }
    return targetPath;
};

export async function POST(request: Request) {
    try {
        const formData = await request.formData();
        const file = formData.get('file') as File;
        const targetId = formData.get('target') as string || '/';

        if (!file) {
            return NextResponse.json({ error: 'No file provided' }, { status: 400 });
        }

        const buffer = Buffer.from(await file.arrayBuffer());
        const targetPath = validatePath(targetId);

        // Ensure directory exists (just in case)
        await mkdir(targetPath, { recursive: true });

        const filePath = path.join(targetPath, file.name);

        // Check collision or overwrite? We might handle conflict checks or we just overwrite.
        // For now, overwrite.

        await writeFile(filePath, buffer);

        return NextResponse.json({ status: 'success' });

    } catch (error) {
        console.error('Upload error:', error);
        return NextResponse.json({ error: 'Upload failed' }, { status: 500 });
    }
}

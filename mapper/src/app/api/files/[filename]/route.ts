import { NextResponse } from 'next/server';
import { unlink, access, constants, rmdir } from 'fs/promises';
import path from 'path';

export async function DELETE(request: Request, { params }: { params: Promise<{ filename: string }> }) {
    try {
        const { filename } = await params;
        if (!filename) {
            return NextResponse.json({ error: 'Filename is required.' }, { status: 400 });
        }

        const uploadDir = path.join(process.cwd(), 'uploads');
        const filePath = path.join(uploadDir, filename);

        // Check if file exists before attempting to delete
        try {
            await access(filePath, constants.F_OK);
        } catch (err: unknown) {
            if ((err as NodeJS.ErrnoException).code === 'ENOENT') {
                return NextResponse.json({ error: `File '${filename}' not found.` }, { status: 404 });
            }
            throw err; // Re-throw other errors
        }

        try {
            await unlink(filePath);
        } catch (error: unknown) {
            if ((error as NodeJS.ErrnoException).code === 'EISDIR') {
                await rmdir(filePath, { recursive: true });
            } else {
                throw error;
            }
        }

        return NextResponse.json({ message: `File '${filename}' deleted successfully.` }, { status: 200 });

    } catch (error) {
        console.error('Error deleting file:', error);
        return NextResponse.json({ error: 'Failed to delete file.' }, { status: 500 });
    }
}
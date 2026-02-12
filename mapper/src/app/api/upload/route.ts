import { NextResponse } from 'next/server';
import { writeFile, mkdir, access, constants } from 'fs/promises';
import path from 'path';

export async function POST(request: Request) {
    try {
        const formData = await request.formData();
        const files = formData.getAll('files') as File[]; // 'files' is the field name from the frontend

        if (!files || files.length === 0) {
            return NextResponse.json({ error: 'No files uploaded.' }, { status: 400 });
        }

        const uploadDir = path.join(process.cwd(), 'uploads'); // Corrected path
        await mkdir(uploadDir, { recursive: true }); // Ensure the uploads directory exists

        const uploadedFileDetails = [];

        const overwrite = formData.get('overwrite') === 'true';

        for (const file of files) {
            const buffer = Buffer.from(await file.arrayBuffer());
            const fileName = file.name.replace(/\s/g, '_'); // Use original file name, replace spaces
            const filePath = path.join(uploadDir, fileName);

            // Check if file already exists, unless overwrite is true
            if (!overwrite) {
                try {
                    await access(filePath, constants.F_OK);
                    // If access succeeds, file exists and overwrite is false
                    return NextResponse.json({ error: `File '${fileName}' already exists.` }, { status: 409 });
                } catch (err: unknown) {
                    if ((err as NodeJS.ErrnoException).code !== 'ENOENT') { // ENOENT means file does not exist, which is fine
                        throw err; // Re-throw other errors
                    }
                }
            }

            await writeFile(filePath, buffer);

            uploadedFileDetails.push({
                name: file.name,
                uniqueName: fileName, // Use original file name as uniqueName
                size: file.size,
                type: file.type,
                url: `/uploads/${fileName}` // URL to access the file
            });
        }

        return NextResponse.json({
            message: 'Files uploaded successfully',
            files: uploadedFileDetails
        }, { status: 200 });

    } catch (error) {
        console.error('Error uploading files:', error);
        return NextResponse.json({ error: 'Failed to upload files.' }, { status: 500 });
    }
}
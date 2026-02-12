export interface UploadedFile {
    id: string;
    name: string;
    uniqueName: string; // Add uniqueName from backend
    type: string;
    size: number;
    uploadedAt: Date;
    url: string;
    thumbnailUrl?: string;
}

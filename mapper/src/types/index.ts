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

/**
 * Project — mirrors lib/projects.ts#Project.
 * Defined here so client components can import it without bundling server-only fs modules.
 */
export interface Project {
    id: string;
    name: string;
    folder_path: string;
    graphivac_project_id: string;
    created_at: string;
    updated_at: string;
}

/**
 * System — mirrors lib/projects.ts#System.
 * Defined here so client components can import it without bundling server-only fs modules.
 */
export interface System {
    id: string;
    name: string;
    folder_path: string;
    graphivac_grid_id: string;
    ai_model_name: string;
    created_at: string;
    updated_at: string;
}

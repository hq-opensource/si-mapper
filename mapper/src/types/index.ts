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

/** Lightweight reference to an ADK session stored in the agent's SQLite DB. */
export interface SessionRef {
    /** ADK session ID — matches Session.id in SqliteSessionService. */
    session_id: string;
    /** User-facing name, e.g. "Session 2026-03-30 14:05". */
    session_name: string;
    /** ISO 8601. Set once at creation. */
    created_at: string;
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
    /** Ordered list of agent sessions associated with this system. Latest first. */
    sessions: SessionRef[];
    /**
     * session_id of the session that was last actively selected.
     * Used on page load / F5 to restore the correct session without localStorage.
     * Falls back to the latest session by created_at when absent.
     */
    active_session_id?: string;
}

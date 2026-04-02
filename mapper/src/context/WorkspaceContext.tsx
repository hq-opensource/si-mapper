"use client";

/**
 * WorkspaceContext
 * ─────────────────────────────────────────────────────────────────────────────
 * Tracks the currently active project and system across the entire app.
 * State is persisted to localStorage under the keys:
 *   - "active-project-id"
 *   - "active-system-id"
 *
 * On mount the context:
 *   1. Fetches GET /api/projects
 *   2. Resolves the active project (stored ID → object, or first, or null)
 *   3. Fetches GET /api/projects/[id]/systems for the active project
 *   4. Resolves the active system (stored ID → object, or first, or null)
 */

import React, {
  createContext,
  useContext,
  useState,
  useCallback,
  useEffect,
  useRef,
  ReactNode,
} from 'react';
import type { Project, System } from '@/types';

// ── Context interface ─────────────────────────────────────────────────────────

interface WorkspaceContextValue {
  /** The currently active project, or null if none exist. */
  activeProject: Project | null;
  /** The currently active system within the active project, or null. */
  activeSystem: System | null;
  /** All available projects. */
  projects: Project[];
  /** All systems within the active project. */
  systems: System[];
  /** Switch the active project. Refreshes system list. Persists to localStorage. */
  setActiveProject: (project: Project) => Promise<void>;
  /** Switch the active system. Persists to localStorage. */
  setActiveSystem: (system: System) => void;
  /** Merge a partial update into the active system (local state only). */
  updateActiveSystem: (patch: Partial<System>) => void;
  /** Refresh the project list from the API. Auto-switches if active was deleted. */
  refreshProjects: () => Promise<void>;
  /** Refresh the system list for the active project. Auto-switches if active was deleted. */
  refreshSystems: () => Promise<void>;
  /** True while the initial project or system list is loading. */
  isLoading: boolean;
}

const WorkspaceContext = createContext<WorkspaceContextValue | undefined>(undefined);

export function useWorkspace(): WorkspaceContextValue {
  const ctx = useContext(WorkspaceContext);
  if (!ctx) {
    throw new Error('useWorkspace must be used within a WorkspaceProvider');
  }
  return ctx;
}

// ── Provider ──────────────────────────────────────────────────────────────────

export function WorkspaceProvider({ children }: { children: ReactNode }) {
  const [projects, setProjects] = useState<Project[]>([]);
  const [systems, setSystems] = useState<System[]>([]);
  const [activeProject, setActiveProjectState] = useState<Project | null>(null);
  const [activeSystem, setActiveSystemState] = useState<System | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Refs to avoid stale closures in stable callbacks
  const activeProjectRef = useRef<Project | null>(null);
  const activeSystemRef = useRef<System | null>(null);
  activeProjectRef.current = activeProject;
  activeSystemRef.current = activeSystem;

  // ── refreshProjects ─────────────────────────────────────────────────────────

  const refreshProjects = useCallback(async () => {
    try {
      const res = await fetch('/api/projects');
      if (!res.ok) return;
      const list: Project[] = await res.json();
      setProjects(list);

      const current = activeProjectRef.current;
      if (!current) return;

      const stillExists = list.find(p => p.id === current.id);
      if (stillExists) return; // Active project still alive — no action needed

      // Active project was deleted — switch to first or clear
      if (list.length > 0) {
        const next = list[0];
        setActiveProjectState(next);
        localStorage.setItem('active-project-id', next.id);
        localStorage.removeItem('active-system-id');
        setActiveSystemState(null);
        // Fetch systems for next project
        const sysRes = await fetch(`/api/projects/${next.id}/systems`);
        if (sysRes.ok) {
          const sysList: System[] = await sysRes.json();
          setSystems(sysList);
          if (sysList.length > 0) {
            setActiveSystemState(sysList[0]);
            localStorage.setItem('active-system-id', sysList[0].id);
          }
        }
      } else {
        // No projects left
        setActiveProjectState(null);
        setSystems([]);
        setActiveSystemState(null);
        localStorage.removeItem('active-project-id');
        localStorage.removeItem('active-system-id');
      }
    } catch (err) {
      console.error('[WorkspaceContext] refreshProjects:', err);
    }
  }, []); // Stable — uses refs

  // ── refreshSystems ──────────────────────────────────────────────────────────

  const refreshSystems = useCallback(async () => {
    const proj = activeProjectRef.current;
    if (!proj) {
      setSystems([]);
      setActiveSystemState(null);
      return;
    }
    try {
      const res = await fetch(`/api/projects/${proj.id}/systems`);
      if (!res.ok) return;
      const list: System[] = await res.json();
      setSystems(list);

      const current = activeSystemRef.current;
      if (!current) {
        if (list.length > 0) {
          setActiveSystemState(list[0]);
          localStorage.setItem('active-system-id', list[0].id);
        }
        return;
      }

      const stillExists = list.find(s => s.id === current.id);
      if (stillExists) return; // Active system still alive

      // Active system was deleted
      if (list.length > 0) {
        setActiveSystemState(list[0]);
        localStorage.setItem('active-system-id', list[0].id);
      } else {
        setActiveSystemState(null);
        localStorage.removeItem('active-system-id');
      }
    } catch (err) {
      console.error('[WorkspaceContext] refreshSystems:', err);
    }
  }, []); // Stable — uses refs

  // ── setActiveProject ────────────────────────────────────────────────────────

  const setActiveProject = useCallback(async (project: Project) => {
    setActiveProjectState(project);
    localStorage.setItem('active-project-id', project.id);
    localStorage.removeItem('active-system-id');
    setActiveSystemState(null);
    setSystems([]);
    try {
      const res = await fetch(`/api/projects/${project.id}/systems`);
      if (!res.ok) return;
      const list: System[] = await res.json();
      setSystems(list);
      if (list.length > 0) {
        setActiveSystemState(list[0]);
        localStorage.setItem('active-system-id', list[0].id);
      }
    } catch (err) {
      console.error('[WorkspaceContext] setActiveProject fetch systems:', err);
    }
  }, []);

  // ── setActiveSystem ─────────────────────────────────────────────────────────

  const setActiveSystem = useCallback((system: System) => {
    setActiveSystemState(system);
    localStorage.setItem('active-system-id', system.id);
  }, []);

  // ── updateActiveSystem ──────────────────────────────────────────────────────

  const updateActiveSystem = useCallback((patch: Partial<System>) => {
    setActiveSystemState(prev => (prev ? { ...prev, ...patch } : prev));
    setSystems(prev =>
      prev.map(s => (s.id === activeSystemRef.current?.id ? { ...s, ...patch } : s))
    );
  }, []);

  // ── Bootstrap on mount ──────────────────────────────────────────────────────

  useEffect(() => {
    async function bootstrap() {
      setIsLoading(true);
      try {
        const res = await fetch('/api/projects');
        if (!res.ok) throw new Error('Failed to fetch projects');
        const projectList: Project[] = await res.json();
        setProjects(projectList);

        if (projectList.length === 0) return;

        const savedProjectId = localStorage.getItem('active-project-id');
        const project = projectList.find(p => p.id === savedProjectId) ?? projectList[0];
        setActiveProjectState(project);
        localStorage.setItem('active-project-id', project.id);

        const sysRes = await fetch(`/api/projects/${project.id}/systems`);
        if (!sysRes.ok) return;
        const sysList: System[] = await sysRes.json();
        setSystems(sysList);

        if (sysList.length > 0) {
          const savedSystemId = localStorage.getItem('active-system-id');
          const system = sysList.find(s => s.id === savedSystemId) ?? sysList[0];
          setActiveSystemState(system);
          localStorage.setItem('active-system-id', system.id);
        }
      } catch (err) {
        console.error('[WorkspaceContext] bootstrap error:', err);
      } finally {
        setIsLoading(false);
      }
    }
    bootstrap();
  }, []);

  // ── Render ──────────────────────────────────────────────────────────────────

  return (
    <WorkspaceContext.Provider
      value={{
        activeProject,
        activeSystem,
        projects,
        systems,
        setActiveProject,
        setActiveSystem,
        updateActiveSystem,
        refreshProjects,
        refreshSystems,
        isLoading,
      }}
    >
      {children}
    </WorkspaceContext.Provider>
  );
}


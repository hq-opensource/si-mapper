"use client";

/**
 * WorkspaceContext
 * ─────────────────────────────────────────────────────────────────────────────
 * Tracks the currently active project, system, and session across the app.
 * Project and system are persisted to localStorage:
 *   - "active-project-id"
 *   - "active-system-id"
 *
 * Active session is NOT stored in localStorage — system.json is the source of
 * truth. On mount / F5, resolveSession reads the `is_active: true` flag from
 * system.sessions. If none is marked, the latest-created session is used and
 * immediately persisted. If no sessions exist at all, one is auto-created.
 *
 * On mount the context:
 *   1. Fetches GET /api/projects
 *   2. Resolves the active project (stored ID → object, or first, or null)
 *   3. Fetches GET /api/projects/[id]/systems for the active project
 *   4. Resolves the active system (stored ID → object, or first, or null)
 *   5. Resolves the active session via resolveSession (see above)
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
import type { Project, System, SessionRef } from '@/types';
import { notifyAgentModel, createAgentSession, restoreAgentSession, markSessionActive } from '@/lib/agent-client';

// ── Context interface ─────────────────────────────────────────────────────────

interface WorkspaceContextValue {
  activeProject: Project | null;
  activeSystem: System | null;
  /** The currently active agent session, or null if no system is active. */
  activeSession: SessionRef | null;
  /** All available projects. */
  projects: Project[];
  /** All systems within the active project. */
  systems: System[];
  /** Switch the active project. Refreshes system list. Persists to localStorage. */
  setActiveProject: (project: Project) => Promise<void>;
  /** Switch the active system. Persists to localStorage. */
  setActiveSystem: (system: System) => Promise<void>;
  /** Switch to a different session. Calls restore on the agent and updates state. */
  setActiveSession: (session: SessionRef) => Promise<void>;
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
  if (!ctx) throw new Error('useWorkspace must be used within a WorkspaceProvider');
  return ctx;
}

// ── Provider ──────────────────────────────────────────────────────────────────

export function WorkspaceProvider({ children }: { children: ReactNode }) {
  const [projects, setProjects] = useState<Project[]>([]);
  const [systems, setSystems] = useState<System[]>([]);
  const [activeProject, setActiveProjectState] = useState<Project | null>(null);
  const [activeSystem, setActiveSystemState] = useState<System | null>(null);
  const [activeSession, setActiveSessionState] = useState<SessionRef | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Refs to avoid stale closures in stable callbacks
  const activeProjectRef = useRef<Project | null>(null);
  const activeSystemRef = useRef<System | null>(null);
  const activeSessionRef = useRef<SessionRef | null>(null);
  activeProjectRef.current = activeProject;
  activeSystemRef.current = activeSystem;
  activeSessionRef.current = activeSession;

  // ── Internal: resolve/auto-create session for a system ────────────────────

  /**
   * Resolve the active session for a system using this priority order:
   *   1. system.active_session_id  (top-level field in system.json — survives F5)
   *   2. The latest session by `created_at` (and persist it as active_session_id)
   *   3. Auto-create a new session if the system has none at all
   */
  const resolveSession = useCallback(async (system: System, project: Project): Promise<SessionRef | null> => {
    const sessions = system.sessions ?? [];

    if (sessions.length > 0) {
      // 1. Honour the persisted active_session_id field
      const activeId = system.active_session_id;
      let chosen = (activeId ? sessions.find(s => s.session_id === activeId) : null) ?? null;

      if (!chosen) {
        // 2. Fall back to the latest session by created_at
        chosen = [...sessions].sort(
          (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
        )[0];
        // Persist the choice so the next F5 finds it immediately
        markSessionActive(project.id, system.id, chosen.session_id);
      }

      // Restore the session in the agent (best-effort)
      restoreAgentSession(project.id, system.id, chosen.session_id).catch(() => {});
      return chosen;
    }

    // 3. No sessions at all — auto-create a default one
    const ref = await createAgentSession(project.id, system.id);
    if (!ref) return null;

    // Reload the system so the new session (with active_session_id set) is reflected
    try {
      const res = await fetch(`/api/projects/${project.id}/systems`);
      if (res.ok) {
        const list: System[] = await res.json();
        setSystems(list);
        const fresh = list.find(s => s.id === system.id);
        if (fresh) setActiveSystemState(fresh);
      }
    } catch { /* ignore */ }

    return ref;
  }, []);

  // ── refreshProjects ────────────────────────────────────────────────────────

  const refreshProjects = useCallback(async () => {
    try {
      const res = await fetch('/api/projects');
      if (!res.ok) return;
      const list: Project[] = await res.json();
      setProjects(list);

      const current = activeProjectRef.current;
      if (!current) return;

      const stillExists = list.find(p => p.id === current.id);
      if (stillExists) return;

      if (list.length > 0) {
        const next = list[0];
        setActiveProjectState(next);
        localStorage.setItem('active-project-id', next.id);
        localStorage.removeItem('active-system-id');
        setActiveSystemState(null);
        setActiveSessionState(null);
        const sysRes = await fetch(`/api/projects/${next.id}/systems`);
        if (sysRes.ok) {
          const sysList: System[] = await sysRes.json();
          setSystems(sysList);
          if (sysList.length > 0) {
            const sys = sysList[0];
            setActiveSystemState(sys);
            localStorage.setItem('active-system-id', sys.id);
            const session = await resolveSession(sys, next);
            if (session) setActiveSessionState(session);
          }
        }
      } else {
        setActiveProjectState(null);
        setSystems([]);
        setActiveSystemState(null);
        setActiveSessionState(null);
        localStorage.removeItem('active-project-id');
        localStorage.removeItem('active-system-id');
      }
    } catch (err) {
      console.error('[WorkspaceContext] refreshProjects:', err);
    }
  }, [resolveSession]);

  // ── refreshSystems ─────────────────────────────────────────────────────────

  const refreshSystems = useCallback(async () => {
    const proj = activeProjectRef.current;
    if (!proj) { setSystems([]); setActiveSystemState(null); return; }
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

      // Refresh the current system object (it may have new/updated sessions)
      const fresh = list.find(s => s.id === current.id);
      if (fresh) {
        setActiveSystemState(fresh);
        const currentSession = activeSessionRef.current;
        if (currentSession) {
          const stillExists = (fresh.sessions ?? []).find(s => s.session_id === currentSession.session_id);
          if (stillExists) {
            setActiveSessionState(stillExists);
          } else if (fresh.sessions?.length > 0) {
            const session = await resolveSession(fresh, proj);
            if (session) setActiveSessionState(session);
          }
        } else {
          const session = await resolveSession(fresh, proj);
          if (session) setActiveSessionState(session);
        }
      } else {
        if (list.length > 0) {
          setActiveSystemState(list[0]);
          localStorage.setItem('active-system-id', list[0].id);
          const session = await resolveSession(list[0], proj);
          if (session) setActiveSessionState(session);
        } else {
          setActiveSystemState(null);
          setActiveSessionState(null);
          localStorage.removeItem('active-system-id');
        }
      }
    } catch (err) {
      console.error('[WorkspaceContext] refreshSystems:', err);
    }
  }, [resolveSession]);

  // ── setActiveProject ───────────────────────────────────────────────────────

  const setActiveProject = useCallback(async (project: Project) => {
    // Read saved system ID before we clear it, so we can restore it if the
    // system happens to belong to the newly selected project.
    const savedSystemId = localStorage.getItem('active-system-id');

    setActiveProjectState(project);
    localStorage.setItem('active-project-id', project.id);
    localStorage.removeItem('active-system-id');
    setActiveSystemState(null);
    setActiveSessionState(null);
    setSystems([]);
    try {
      const res = await fetch(`/api/projects/${project.id}/systems`);
      if (!res.ok) return;
      const list: System[] = await res.json();
      setSystems(list);
      if (list.length > 0) {
        // Prefer the previously active system if it exists in this project;
        // otherwise fall back to the first system.
        const sys = list.find(s => s.id === savedSystemId) ?? list[0];
        setActiveSystemState(sys);
        localStorage.setItem('active-system-id', sys.id);
        notifyAgentModel(sys.ai_model_name);
        const session = await resolveSession(sys, project);
        if (session) setActiveSessionState(session);
      }
    } catch (err) {
      console.error('[WorkspaceContext] setActiveProject fetch systems:', err);
    }
  }, [resolveSession]);

  // ── setActiveSystem ────────────────────────────────────────────────────────

  const setActiveSystem = useCallback(async (system: System) => {
    setActiveSystemState(system); // optimistic — update UI immediately
    localStorage.setItem('active-system-id', system.id);
    notifyAgentModel(system.ai_model_name);
    const proj = activeProjectRef.current;
    if (!proj) return;

    // Fetch fresh system from disk to guarantee we use the latest active_session_id.
    // The in-memory object may be stale if setActiveSession was called after the
    // systems list was last loaded.
    let freshSystem = system;
    try {
      const res = await fetch(`/api/projects/${proj.id}/systems/${system.id}`);
      if (res.ok) {
        freshSystem = await res.json();
        setActiveSystemState(freshSystem);
        setSystems(prev => prev.map(s => s.id === freshSystem.id ? freshSystem : s));
      }
    } catch { /* fall back to in-memory system */ }

    const session = await resolveSession(freshSystem, proj);
    if (session) setActiveSessionState(session);
  }, [resolveSession]);

  // ── setActiveSession ───────────────────────────────────────────────────────

  const setActiveSession = useCallback(async (session: SessionRef) => {
    setActiveSessionState(session);
    const proj = activeProjectRef.current;
    const sys = activeSystemRef.current;
    if (!proj || !sys) return;

    // Keep in-memory systems state in sync so that switching systems and
    // coming back restores the correct session (avoids stale active_session_id).
    setSystems(prev => prev.map(s =>
      s.id === sys.id ? { ...s, active_session_id: session.session_id } : s
    ));

    // Persist is_active in system.json — this survives F5
    markSessionActive(proj.id, sys.id, session.session_id);

    // Restore the session context in the agent
    restoreAgentSession(proj.id, sys.id, session.session_id).catch(err =>
      console.warn('[WorkspaceContext] restoreAgentSession failed:', err)
    );
  }, []);

  // ── Bootstrap on mount ─────────────────────────────────────────────────────

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
        if (sysList.length === 0) return;

        const savedSystemId = localStorage.getItem('active-system-id');
        const system = sysList.find(s => s.id === savedSystemId) ?? sysList[0];
        setActiveSystemState(system);
        localStorage.setItem('active-system-id', system.id);
        notifyAgentModel(system.ai_model_name);

        const session = await resolveSession(system, project);
        if (session) setActiveSessionState(session);
      } catch (err) {
        console.error('[WorkspaceContext] bootstrap error:', err);
      } finally {
        setIsLoading(false);
      }
    }
    bootstrap();
  // resolveSession is stable (useCallback with no deps that change)
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ── Render ��────────────────────────────────────────────────────────────────

  return (
    <WorkspaceContext.Provider
      value={{
        activeProject,
        activeSystem,
        activeSession,
        projects,
        systems,
        setActiveProject,
        setActiveSystem,
        setActiveSession,
        refreshProjects,
        refreshSystems,
        isLoading,
      }}
    >
      {children}
    </WorkspaceContext.Provider>
  );
}


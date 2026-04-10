"use client";

import { useCopilotAction, useCoAgent, useCopilotContext } from "@copilotkit/react-core";
import { useState, useEffect, useRef, useMemo } from "react";
import { AlertTriangle, X } from "lucide-react";
import { SplitSidebar } from "@/components/SplitSidebar";
import { YourMainContent, type ActiveTab } from "@/app/page/components/YourMainContent";
import { ThoughtsProvider, useThoughts, type Thought, type ToolCall, type AgentEvent } from "@/context/ThoughtsContext";
import { useWorkspace } from "@/context/WorkspaceContext";
import { useAgentPolling } from "@/hooks/useAgentPolling";
import {
  EXCLUDED_SYNC_KEYS,
  FILTERED_STATE_KEY_PREFIXES,
  ACTIVE_TURN_STATUSES,
} from "@/constants/agentState";
import type { System, Session } from "@/types";

type AgentState = {
  status: string;
  current_step: string;
  observed_steps: string[];
  data: Record<string, unknown>;
  active_agent?: string;
  thoughts?: Thought[];
  tool_calls?: ToolCall[];
  events?: AgentEvent[];
  active_project?: {
    id: string;
    name: string;
    folder_path: string;
    graphivac_project_id: string;
  } | null;
  active_system?: {
    id: string;
    name: string;
    folder_path: string;
    graphivac_grid_id: string;
    neo4j_db_name: string;
  } | null;
};

// Internal component to handle syncing to context
function StateSyncer({ pooledState, agentState }: { pooledState: AgentState | null, agentState: AgentState }) {
  const { syncThoughts, syncToolCalls, syncEvents, syncData } = useThoughts();

  useEffect(() => {
    const combinedEvents = [
      ...(agentState.events || []),
      ...(pooledState?.events || [])
    ];
    const combinedThoughts = [
      ...(agentState.thoughts || []),
      ...(pooledState?.thoughts || [])
    ];
    const combinedToolCalls = [
      ...(agentState.tool_calls || []),
      ...(pooledState?.tool_calls || [])
    ];
    if (combinedThoughts.length > 0) syncThoughts(combinedThoughts);
    if (combinedToolCalls.length > 0) syncToolCalls(combinedToolCalls);
    if (combinedEvents.length > 0) syncEvents(combinedEvents);

    // adkData = ADK nested dict, copilotData = CopilotKit nested dict
    const pooledRest = pooledState ? Object.fromEntries(
      Object.entries(pooledState).filter(([key]) =>
        !FILTERED_STATE_KEY_PREFIXES.some(p => key.startsWith(p)) &&
        !(EXCLUDED_SYNC_KEYS as readonly string[]).includes(key)
      )
    ) : {};

    const agentRest = Object.fromEntries(
      Object.entries(agentState).filter(([key]) =>
        !FILTERED_STATE_KEY_PREFIXES.some(p => key.startsWith(p)) &&
        !(EXCLUDED_SYNC_KEYS as readonly string[]).includes(key)
      )
    );

    const customData: Record<string, unknown> = { ...agentRest, ...pooledRest };

    // pooledState.data → adkData, agentState.data → copilotData
    if (pooledState?.data && Object.keys(pooledState.data).length > 0)
      customData.adkData = pooledState.data;

    if (agentState.data && Object.keys(agentState.data).length > 0)
      customData.copilotData = agentState.data;

    if (Object.keys(customData).length > 0) {
      // Pass snapshot so stale keys are pruned automatically
      syncData(customData, Object.keys(customData));
    }
  }, [pooledState, agentState, syncThoughts, syncToolCalls, syncEvents, syncData]);

  return null;
}

export default function CopilotKitPage() {
  const [themeColor, setThemeColor] = useState("#6366f1");
  const [isEditMode, setIsEditMode] = useState(false);
  // Lifted above ThoughtsProvider so tab selection survives session switches (key remount).
  const [activeTab, setActiveTab] = useState<ActiveTab>('view');
  const { activeProject, activeSystem, updateActiveSystem } = useWorkspace();
  const { threadId, setThreadId } = useCopilotContext();

  // Use `running` from useCoAgent as the canonical "turn active" flag
  const { state: agentState, setState: setAgentState, running: isCopilotTurnActive } = useCoAgent<AgentState>({name: "my_agent"});

  // Two-speed polling: slow when agent is at rest, fast during active turns
  const pollingConfig = useMemo(() => ({
    baseUrl: process.env.NEXT_PUBLIC_AGENT_BACKEND_URL ?? "http://localhost:8001",
    interval: (agentState.status === "idle" || agentState.status === "complete")
      ? 5_000
      : 2_000,
  }), [agentState.status]);

  const { pooledState, error: pollingError } = useAgentPolling<AgentState>(pollingConfig);

  // Track whether the user manually dismissed the banner so it doesn't flicker back
  const [bannerDismissed, setBannerDismissed] = useState(false);

  // Re-show the banner whenever a new error appears
  useEffect(() => {
    if (pollingError) setBannerDismissed(false);
  }, [pollingError]);

  const showErrorBanner = !!pollingError && !bannerDismissed;

  // Prefer `running` flag; fall back to status vocabulary check
  const isActiveTurn = isCopilotTurnActive ??
    (ACTIVE_TURN_STATUSES as readonly string[]).includes(agentState.status);

  // combinedState with explicit ownership rules
  const combinedState = {
    ...agentState,
    ...(pooledState || {}),
    // Lifecycle keys: CopilotKit stream wins during active turns; poll wins at rest
    status:       isActiveTurn ? agentState.status       : (pooledState?.status       ?? agentState.status),
    current_step: isActiveTurn ? agentState.current_step : (pooledState?.current_step ?? agentState.current_step),
    active_agent: isActiveTurn ? agentState.active_agent : (pooledState?.active_agent ?? agentState.active_agent),
    // Frontend is always authoritative for workspace selection
    active_project: activeProject ? {
        id: activeProject.id,
        name: activeProject.name,
        folder_path: activeProject.folder_path,
        graphivac_project_id: activeProject.graphivac_project_id,
      } : null,
    active_system: activeSystem ? {
        id: activeSystem.id,
        name: activeSystem.name,
        folder_path: activeSystem.folder_path,
        graphivac_grid_id: activeSystem.graphivac_grid_id,
        neo4j_db_name: activeSystem.neo4j_db_name
      } : null,
  } as AgentState;

  // Keep a ref so the effect always sees the latest agent state without
  // triggering extra re-runs.
  const agentStateRef = useRef<AgentState>(agentState);
  agentStateRef.current = agentState;
  // Sync active project / system into the CopilotKit agent state whenever
  // the workspace selection changes.
  useEffect(() => {
    setAgentState({
      ...agentState,
      active_project: activeProject ? {
        id: activeProject.id,
        name: activeProject.name,
        folder_path: activeProject.folder_path,
        graphivac_project_id: activeProject.graphivac_project_id,
      } : null,
      active_system: activeSystem ? {
        id: activeSystem.id,
        name: activeSystem.name,
        folder_path: activeSystem.folder_path,
        graphivac_grid_id: activeSystem.graphivac_grid_id,
        neo4j_db_name: activeSystem.neo4j_db_name,
      } : null,
    });
  }, [activeSystem]); // Re-stamp after CopilotKit resets agentState on thread switch

  // ── PATCH: guard against CopilotKit stream wiping active_system ──────────────
  // CopilotKit can re-hydrate agent state from a stale Agent-session snapshot,
  // emitting null / undefined / {} for `active_system` (and `active_project`).
  // Whenever that happens, immediately re-stamp the CopilotKit state with the
  // workspace values that the frontend owns authoritatively.
  // Refs capture the latest workspace selection so the effect only needs to run
  // when `agentState.active_system` changes — NOT when the workspace changes.
  const activeProjectPatchRef = useRef(activeProject);
  activeProjectPatchRef.current = activeProject;
  const activeSystemPatchRef = useRef(activeSystem);
  activeSystemPatchRef.current = activeSystem;

  useEffect(() => {
    const sys = agentState.active_system;
    const isBlank = !sys || Object.keys(sys as object).length === 0;
    if (!isBlank) return; // active_system is valid — nothing to fix

    const proj = activeProjectPatchRef.current;
    const wsSystem = activeSystemPatchRef.current;
    if (!proj && !wsSystem) return; // no workspace selected yet — nothing to restore

    setAgentState(prev => ({
      ...prev,
      active_project: proj
        ? {
            id: proj.id,
            name: proj.name,
            folder_path: proj.folder_path,
            graphivac_project_id: proj.graphivac_project_id,
          }
        : null,
      active_system: wsSystem
        ? {
            id: wsSystem.id,
            name: wsSystem.name,
            folder_path: wsSystem.folder_path,
            graphivac_grid_id: wsSystem.graphivac_grid_id,
            neo4j_db_name: wsSystem.neo4j_db_name,
          }
        : null,
    }) as AgentState);
    console.info('[page] CopilotKit stream wiped active_system, restoring from workspace:', { 'project': proj?.id, 'system': wsSystem?.id });
  }, [agentState.active_system]); // eslint-disable-line react-hooks/exhaustive-deps
  // ── END PATCH ─────────────────────────────────────────────────────────────

  useCopilotAction({
    name: "setThemeColor",
    parameters: [{
      name: "themeColor",
      description: "The theme color to set. Make sure to pick nice colors.",
      required: true,
    }],
    handler({ themeColor }) {
      setThemeColor(themeColor);
    },
  });

  // Receives a threadId (from the dropdown or backend) and applies it
  const useSession = (newId: string) => {
    setThreadId(newId);
  }

  // ── Shared PATCH helper ───────────────────────────────────────────────────
  const patchSystem = (projectId: string, systemId: string, body: object) =>
    fetch(`/api/projects/${projectId}/systems/${systemId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    }).then(res => res.ok ? res.json() as Promise<System> : Promise.reject(res.statusText));

  // ── Shared: create a session, persist it, and activate it ───────────────
  const addSession = (name: string, existingSessions: Session[]) => {
    if (!activeProject || !activeSystem) return;
    const newSession: Session = { id: crypto.randomUUID(), name, created_at: new Date().toISOString() };
    patchSystem(activeProject.id, activeSystem.id, { sessions: [...existingSessions, newSession], thread_id: newSession.id })
      .then(updated => {
        updateActiveSystem({ sessions: updated.sessions, thread_id: updated.thread_id });
        setThreadId(newSession.id);
      })
      .catch(err => console.error('[page] Failed to create session:', err));
  };

  // Auto-create a timestamped session (used on first load or after last session is removed)
  const createAutoSession = (existingSessions: Session[] = []) => {
    const pad = (n: number) => String(n).padStart(2, '0');
    const now = new Date();
    const autoName = `New Session [${now.getFullYear()}/${pad(now.getMonth() + 1)}/${pad(now.getDate())} ${pad(now.getHours())}:${pad(now.getMinutes())}:${pad(now.getSeconds())}]`;
    addSession(autoName, existingSessions);
  };

  // Creates a named session (called from the "New session" dialog)
  const handleNewSession = (sessionName: string) => {
    addSession(sessionName, activeSystem?.sessions ?? []);
  };

  // Removes a session from system.json, then selects the next one (or auto-creates)
  const handleRemoveSession = (sessionId: string) => {
    if (!activeProject || !activeSystem) return;
    const remaining = (activeSystem.sessions ?? []).filter(s => s.id !== sessionId);
    if (remaining.length > 0) {
      // Pick the session that was after the removed one, otherwise the last one
      const removedIndex = (activeSystem.sessions ?? []).findIndex(s => s.id === sessionId);
      const nextSession = remaining[removedIndex] ?? remaining[remaining.length - 1];
      patchSystem(activeProject.id, activeSystem.id, { sessions: remaining, thread_id: nextSession.id })
        .then(updated => {
          updateActiveSystem({ sessions: updated.sessions, thread_id: updated.thread_id });
          setThreadId(nextSession.id);
        })
        .catch(err => console.error('[page] Failed to remove session:', err));
    } else {
      // No sessions left — remove from disk first, then auto-create
      patchSystem(activeProject.id, activeSystem.id, { sessions: [], thread_id: '' })
        .then(updated => {
          updateActiveSystem({ sessions: updated.sessions ?? [], thread_id: updated.thread_id });
          createAutoSession([]);
        })
        .catch(err => console.error('[page] Failed to remove last session:', err));
    }
  };

  // Load / initialise the session when the active system changes
  const prevSystemIdRef = useRef<string | null>(null);
  useEffect(() => {
    if (!activeSystem || !activeProject) return;
    if (activeSystem.id === prevSystemIdRef.current) return;
    prevSystemIdRef.current = activeSystem.id;

    // ── Case 1: system already has an active thread_id ──────────────────────
    if (activeSystem.thread_id) {
      setThreadId(activeSystem.thread_id);
      return;
    }

    // ── Case 2: no thread_id but sessions exist → activate the first one ────
    if (activeSystem.sessions && activeSystem.sessions.length > 0) {
      const first = activeSystem.sessions[0];
      setThreadId(first.id);
      patchSystem(activeProject.id, activeSystem.id, { thread_id: first.id })
        .then(updated => updateActiveSystem({ thread_id: updated.thread_id }))
        .catch(err => console.error('[page] Failed to persist first session as thread_id:', err));
      return;
    }

    // ── Case 3: no sessions at all → auto-create a timestamped one ──────────
    createAutoSession([]);
  }, [activeSystem, activeProject, setThreadId, updateActiveSystem]); // eslint-disable-line react-hooks/exhaustive-deps

  // Persist the active threadId to system.json whenever it changes
  const isMountedRef = useRef(false);
  useEffect(() => {
    if (!isMountedRef.current) { isMountedRef.current = true; return; }
    if (!activeProject || !activeSystem || !threadId) return;
    // Skip if already in sync
    if (activeSystem.thread_id === threadId) return;

    fetch(`/api/projects/${activeProject.id}/systems/${activeSystem.id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ thread_id: threadId }),
    })
      .then(res => res.ok ? res.json() as Promise<System> : Promise.reject(res.statusText))
      .then(updated => updateActiveSystem({ thread_id: updated.thread_id }))
      .catch(err => console.error('[page] Failed to save threadId to system.json:', err));
  }, [threadId]); // eslint-disable-line react-hooks/exhaustive-deps

  // Chat is disabled until both an active project and an active system are selected
  const isWorkspaceReady = !!activeProject && !!activeSystem;

  return (
    <main className="flex h-screen" style={{ "--copilot-kit-primary-color": themeColor, "--accent": themeColor } as React.CSSProperties}>
      {/* key={threadId} forces full unmount/remount on session switch,
           resetting all four context slices (thoughts, toolCalls, events, data) */}
      <ThoughtsProvider key={threadId} currentAgentName={combinedState.active_agent || "SI-MAPPER"}>
        <StateSyncer pooledState={pooledState} agentState={agentState} />
        <SplitSidebar
          isEditMode={isEditMode}
          toggleEditMode={() => setIsEditMode(!isEditMode)}
          disabled={!isWorkspaceReady}
        />
        <div className="flex-grow min-w-0 overflow-hidden">
          <YourMainContent
            agentState={combinedState}
            onUseSession={useSession}
            onNewSession={handleNewSession}
            onRemoveSession={handleRemoveSession}
            threadId={threadId}
            sessions={activeSystem?.sessions ?? []}
            activeTab={activeTab}
            onTabChange={setActiveTab}
          />
        </div>
      </ThoughtsProvider>

      {/* Warning banner — shown when the agent backend is unreachable */}
      {showErrorBanner && (
        <div className="fixed bottom-0 left-0 right-0 z-[9999] flex items-center gap-3 px-5 py-3 bg-amber-500/95 backdrop-blur-sm text-amber-950 shadow-[0_-4px_24px_rgba(0,0,0,0.15)] animate-in slide-in-from-bottom-2 duration-300">
          <AlertTriangle size={16} className="shrink-0" />
          <div className="flex-1 min-w-0">
            <span className="font-bold text-sm">Agent backend unreachable</span>
            <span className="text-sm font-medium opacity-80 ml-2">— State panel may show stale data</span>
            <span className="text-sm font-medium opacity-80 ml-2">::&nbsp;&nbsp;&nbsp;{pollingError}</span>
          </div>
          <button
            onClick={() => setBannerDismissed(true)}
            aria-label="Dismiss warning"
            className="shrink-0 p-1 rounded-lg hover:bg-amber-600/30 transition-colors"
          >
            <X size={14} />
          </button>
        </div>
      )}
    </main>
  );
}

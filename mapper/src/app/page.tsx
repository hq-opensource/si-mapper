"use client";

import { useCopilotAction, useCoAgent, useCopilotContext } from "@copilotkit/react-core";
import { useState, useEffect, useRef, useMemo } from "react";
import { SplitSidebar } from "@/components/SplitSidebar";
import { YourMainContent } from "@/app/page/components/YourMainContent";
import { ThoughtsProvider, useThoughts, type Thought, type ToolCall, type AgentEvent } from "@/context/ThoughtsContext";
import { useWorkspace } from "@/context/WorkspaceContext";
import { useAgentPolling } from "@/hooks/useAgentPolling";
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
    ai_model_name: string;
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

    const { data } = pooledState || {};
    const adkData = agentState.data;

    const excludedKeys = ['status', 'current_step', 'observed_steps', 'active_agent', 'thoughts', 'tool_calls', 'events', 'data', 'active_project', 'active_system'];

    const pooledRest = pooledState ? Object.fromEntries(
      Object.entries(pooledState).filter(([key]) => !key.startsWith('EXIT_') && !excludedKeys.includes(key))
    ) : {};

    const agentRest = Object.fromEntries(
      Object.entries(agentState).filter(([key]) => !key.startsWith('EXIT_') && !excludedKeys.includes(key))
    );

    const customData: Record<string, unknown> = { ...agentRest, ...pooledRest };

    if (data && Object.keys(data).length > 0) customData.data = data;
    if (adkData && Object.keys(adkData).length > 0) customData.adkData = adkData;

    if (Object.keys(customData).length > 0) {
      syncData(customData);
    }
  }, [pooledState, agentState, syncThoughts, syncToolCalls, syncEvents, syncData]);


  return null;
}

export default function CopilotKitPage() {
  const [themeColor, setThemeColor] = useState("#6366f1");
  const [isEditMode, setIsEditMode] = useState(false);
  const { activeProject, activeSystem, updateActiveSystem } = useWorkspace();

  const pollingConfig = useMemo(() => ({
    baseUrl: process.env.NEXT_PUBLIC_AGENT_BACKEND_URL ?? "http://localhost:8001",
    interval: 2000
  }), []);

  const { pooledState } = useAgentPolling<AgentState>(pollingConfig);

  const { state: agentState, setState: setAgentState } = useCoAgent<AgentState>({
    name: "my_agent",
    initialState: {
      status: "idle",
      current_step: "",
      observed_steps: [],
      data: {},
      active_project: null,
      active_system: null,
    },
  });

  // Keep refs so effects always see the latest values without triggering loops.
  const agentStateRef = useRef<AgentState>(agentState);
  agentStateRef.current = agentState;

  // Stabilize setAgentState via a ref — CopilotKit does NOT guarantee a stable
  // function reference across renders, so including it in a useEffect dependency
  // array causes an infinite loop (effect fires → state updates → new ref →
  // effect fires again…). Accessing it through a ref breaks that cycle.
  const setAgentStateRef = useRef(setAgentState);
  setAgentStateRef.current = setAgentState;

  // Sync active project / system into the CopilotKit agent state whenever
  // the workspace selection changes.
  useEffect(() => {
    setAgentStateRef.current({
      ...agentStateRef.current,
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
        ai_model_name: activeSystem.ai_model_name,
      } : null,
    });
  }, [activeProject, activeSystem]); // setAgentState intentionally omitted — accessed via ref above

  const combinedState = {
    ...agentState,
    ...(pooledState || {}),
    status: pooledState?.status || agentState.status,
    current_step: pooledState?.current_step || agentState.current_step,
    active_agent: pooledState?.active_agent || agentState.active_agent,
  } as AgentState;

  useEffect(() => {
    if (pooledState) {
      console.log("DEBUG: Pooled State Update:", pooledState);
    }
  }, [pooledState]);

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

  const { threadId, setThreadId } = useCopilotContext();

  // Receives a threadId (from the dropdown or backend) and applies it
  const useSession = (newId: string) => {
    setThreadId(newId);
  }

  // Creates a named session, persists it to system.json, and activates it
  const handleNewSession = (sessionName: string) => {
    if (!activeProject || !activeSystem) return;
    const newSession: Session = {
      id: crypto.randomUUID(),
      name: sessionName,
      created_at: new Date().toISOString(),
    };
    const updatedSessions = [...(activeSystem.sessions ?? []), newSession];
    // Persist both the new sessions list and the new thread_id
    fetch(`/api/projects/${activeProject.id}/systems/${activeSystem.id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ sessions: updatedSessions, thread_id: newSession.id }),
    })
      .then(res => res.ok ? res.json() as Promise<System> : Promise.reject(res.statusText))
      .then(updated => {
        updateActiveSystem({ sessions: updated.sessions, thread_id: updated.thread_id });
        setThreadId(newSession.id);
      })
      .catch(err => console.error('[page] Failed to create session:', err));
  };

  // Load / initialise the session when the active system changes
  const prevSystemIdRef = useRef<string | null>(null);
  useEffect(() => {
    if (!activeSystem || !activeProject) return;
    if (activeSystem.id === prevSystemIdRef.current) return;
    prevSystemIdRef.current = activeSystem.id;

    const patchUrl = `/api/projects/${activeProject.id}/systems/${activeSystem.id}`;
    const patch = (body: object) =>
      fetch(patchUrl, { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })
        .then(res => res.ok ? res.json() as Promise<System> : Promise.reject(res.statusText));

    // ── Case 1: system already has an active thread_id ──────────────────────
    if (activeSystem.thread_id) {
      setThreadId(activeSystem.thread_id);
      return;
    }

    // ── Case 2: no thread_id but sessions exist → activate the first one ────
    if (activeSystem.sessions && activeSystem.sessions.length > 0) {
      const first = activeSystem.sessions[0];
      setThreadId(first.id);
      patch({ thread_id: first.id })
        .then(updated => updateActiveSystem({ thread_id: updated.thread_id }))
        .catch(err => console.error('[page] Failed to persist first session as thread_id:', err));
      return;
    }

    // ── Case 3: no sessions at all → auto-create a timestamped one ──────────
    const pad = (n: number) => String(n).padStart(2, '0');
    const now = new Date();
    const autoName = `New Session [${now.getFullYear()}/${pad(now.getMonth() + 1)}/${pad(now.getDate())} ${pad(now.getHours())}:${pad(now.getMinutes())}:${pad(now.getSeconds())}]`;
    const newSession: Session = { id: crypto.randomUUID(), name: autoName, created_at: now.toISOString() };
    patch({ sessions: [newSession], thread_id: newSession.id })
      .then(updated => {
        updateActiveSystem({ sessions: updated.sessions, thread_id: updated.thread_id });
        setThreadId(newSession.id);
      })
      .catch(err => console.error('[page] Failed to auto-create session:', err));
  }, [activeSystem, activeProject, setThreadId, updateActiveSystem]);

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
      <ThoughtsProvider currentAgentName={combinedState.active_agent || "SI-MAPPER"}>
        <StateSyncer pooledState={pooledState} agentState={agentState} />
        <SplitSidebar
          isEditMode={isEditMode}
          toggleEditMode={() => setIsEditMode(!isEditMode)}
          disabled={!isWorkspaceReady}
        />
        <div className="flex-grow min-w-0 overflow-hidden">
          <YourMainContent
            isEditMode={isEditMode}
            agentState={combinedState}
            onUseSession={useSession}
            onNewSession={handleNewSession}
            threadId={threadId}
            sessions={activeSystem?.sessions ?? []}
          />
        </div>
      </ThoughtsProvider>
    </main>
  );
}


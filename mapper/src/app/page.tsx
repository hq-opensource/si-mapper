"use client";

import { useCopilotAction, useCoAgent } from "@copilotkit/react-core";
import { useState, useEffect, useRef, useMemo } from "react";
import { SplitSidebar } from "@/components/SplitSidebar";
import { YourMainContent } from "@/app/page/components/YourMainContent";
import { ThoughtsProvider, useThoughts, type Thought, type ToolCall, type AgentEvent } from "@/context/ThoughtsContext";
import { useWorkspace } from "@/context/WorkspaceContext";
import { useAgentPolling } from "@/hooks/useAgentPolling";

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
  const { syncThoughts, syncToolCalls, syncEvents, syncData, clearAll } = useThoughts();
  const { activeSession } = useWorkspace();

  // Clear all accumulated UI state whenever the active session changes
  const prevSessionIdRef = useRef<string | null>(null);
  useEffect(() => {
    const currentId = activeSession?.session_id ?? null;
    if (prevSessionIdRef.current !== null && prevSessionIdRef.current !== currentId) {
      clearAll();
    }
    prevSessionIdRef.current = currentId;
  }, [activeSession?.session_id, clearAll]);

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

    // Forward status and active agent explicitly — they are stripped from
    // agentRest/pooledRest by excludedKeys but the Performance tab needs them.
    customData.agentStatus = pooledState?.status || agentState.status || 'idle';
    customData.activeAgent = pooledState?.active_agent || agentState.active_agent || null;

    if (Object.keys(customData).length > 0) {
      syncData(customData);
    }
  }, [pooledState, agentState, syncThoughts, syncToolCalls, syncEvents, syncData]);


  return null;
}

export default function CopilotKitPage() {
  const [themeColor, setThemeColor] = useState("#6366f1");
  const [isEditMode, setIsEditMode] = useState(false);
  const { activeProject, activeSystem, activeSession } = useWorkspace();

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
          />
        </div>
      </ThoughtsProvider>
    </main>
  );
}


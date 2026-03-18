"use client";

import { useCopilotAction, useCoAgent } from "@copilotkit/react-core";
import { useState, useEffect, useMemo } from "react";
import { SplitSidebar } from "@/components/SplitSidebar";
import { YourMainContent } from "@/app/page/components/YourMainContent";
import { ThoughtsProvider, useThoughts, type Thought, type ToolCall, type AgentEvent, type AgentTask } from "@/context/ThoughtsContext";
import { useAgentPolling } from "@/hooks/useAgentPolling";

type AgentState = {
  status: string;
  current_step: string;
  observed_steps: string[];
  data: Record<string, unknown>;
  active_agent?: string;
  tasks?: AgentTask[];
  plan?: string;
  thoughts?: Thought[];
  tool_calls?: ToolCall[];
  events?: AgentEvent[];
};

// Internal component to handle syncing to context
function StateSyncer({ pooledState, agentState }: { pooledState: AgentState | null, agentState: AgentState }) {
  const { syncThoughts, syncToolCalls, syncEvents, syncTasks, syncData } = useThoughts();

  useEffect(() => {
    // 1. Merge sources (prioritize streaming agentState for real-time thoughts)
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
    const combinedTasks = pooledState?.tasks || agentState.tasks;

    if (combinedThoughts.length > 0) syncThoughts(combinedThoughts);
    if (combinedToolCalls.length > 0) syncToolCalls(combinedToolCalls);
    if (combinedEvents.length > 0) syncEvents(combinedEvents);
    if (combinedTasks && combinedTasks.length > 0) syncTasks(combinedTasks);

    // 2. Sync Custom Data
    const { data } = pooledState || {};
    const adkData = agentState.data;

    const excludedKeys = ['status', 'current_step', 'observed_steps', 'active_agent', 'tasks', 'plan', 'thoughts', 'tool_calls', 'events', 'data'];
    
    // Filter rest from both sources
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
  }, [pooledState, agentState, syncThoughts, syncToolCalls, syncEvents, syncTasks, syncData]);

  return null;
}

export default function CopilotKitPage() {
  const [themeColor, setThemeColor] = useState("#6366f1");
  const [isEditMode, setIsEditMode] = useState(false);

  // 1. Polling Agent State (Backup/Sub-agent visibility)
  // We use 8001 as seen in api/copilotkit/route.ts
  const pollingConfig = useMemo(() => ({
    baseUrl: "http://localhost:8001",
    interval: 2000
  }), []);

  const { pooledState } = useAgentPolling<AgentState>(pollingConfig);

  // 2. Co-Agent State (Primary/Streaming)
  const { state: agentState } = useCoAgent<AgentState>({
    name: "my_agent", // This matches the runtime config
    initialState: {
      status: "idle",
      current_step: "",
      observed_steps: [],
      data: {},
    },
  });

  // 🤖 Combined State
  // We prioritize pooledState for tasks and plan if they are more complete
  const combinedState = {
    ...agentState,
    ...(pooledState || {}),
    // Explicitly merge lists if they exist in pooled state
    tasks: pooledState?.tasks || agentState.tasks,
    plan: pooledState?.plan || agentState.plan,
    status: pooledState?.status || agentState.status,
    current_step: pooledState?.current_step || agentState.current_step,
    active_agent: pooledState?.active_agent || agentState.active_agent,
  } as AgentState;

  // Log state changes
  useEffect(() => {
    if (pooledState) {
      console.log("DEBUG: Pooled State Update:", pooledState);
    }
  }, [pooledState]);

  // 🪁 Frontend Actions
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

  return (
    <main className="flex h-screen" style={{ "--copilot-kit-primary-color": themeColor, "--accent": themeColor } as React.CSSProperties}>
      <ThoughtsProvider currentAgentName={combinedState.active_agent || "SI-MAPPER"}>
        <StateSyncer pooledState={pooledState} agentState={agentState} />
        <SplitSidebar isEditMode={isEditMode} toggleEditMode={() => setIsEditMode(!isEditMode)} />
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

"use client";

import { useCopilotAction } from "@copilotkit/react-core";
import { useState, useEffect, useMemo } from "react";
import { SplitSidebar } from "@/components/SplitSidebar";
import { YourMainContent } from "@/app/page/components/YourMainContent";
import { ThoughtsProvider, useThoughts } from "@/context/ThoughtsContext";
import { useAgentPolling } from "@/hooks/useAgentPolling";
import { type AgentState } from "@/app/page/components/AgentStateOverlay";

// Stable module-level constant — never causes re-renders
const DEFAULT_AGENT_STATE: AgentState = {
  status: "idle",
  current_step: "",
  observed_steps: [],
  data: {} as Record<string, unknown>,
};

// Internal component to handle syncing pooledState to ThoughtsContext
function StateSyncer({ pooledState }: { pooledState: AgentState | null }) {
  const { syncThoughts, syncToolCalls, syncEvents, syncData } = useThoughts();

  useEffect(() => {
    if (!pooledState) return;

    // Sync array fields
    const thoughts = pooledState.thoughts as Array<Record<string, unknown>> | undefined;
    const toolCalls = pooledState.tool_calls as Array<Record<string, unknown>> | undefined;
    const events = pooledState.events as Array<Record<string, unknown>> | undefined;

    if (thoughts?.length) syncThoughts(thoughts as never[]);
    if (toolCalls?.length) syncToolCalls(toolCalls as never[]);
    if (events?.length) syncEvents(events as never[]);

    // Sync custom data (everything except known scalar/array keys)
    const excludedKeys = ['status', 'current_step', 'observed_steps', 'active_agent', 'thoughts', 'tool_calls', 'events', 'data'];
    const pooledRest = Object.fromEntries(
      Object.entries(pooledState).filter(([key]) => !key.startsWith('EXIT_') && !excludedKeys.includes(key))
    );

    const customData: Record<string, unknown> = { ...pooledRest };
    const data = pooledState.data as Record<string, unknown> | undefined;
    if (data && Object.keys(data).length > 0) customData.data = data;

    if (Object.keys(customData).length > 0) {
      syncData(customData);
    }
  }, [pooledState, syncThoughts, syncToolCalls, syncEvents, syncData]);

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

  // Combined State — polling is the sole source of truth
  const combinedState: AgentState = pooledState ?? DEFAULT_AGENT_STATE;


  // Frontend Actions
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
        <StateSyncer pooledState={pooledState} />
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

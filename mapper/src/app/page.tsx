"use client";

import { useCopilotAction, useCoAgent } from "@copilotkit/react-core";
import { useState, useEffect, useMemo, useRef } from "react";
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

interface StateSyncerProps {
  pooledState: AgentState | null;
  agentStateRef: React.RefObject<AgentState>;
  // Primitive version key derived from streaming content lengths — changes only
  // when new items arrive, NOT on every render. Breaks the reference-churn loop.
  streamingVersion: string;
}

function syncStateToContext(
  source: AgentState,
  syncThoughts: (t: never[]) => void,
  syncToolCalls: (t: never[]) => void,
  syncEvents: (t: never[]) => void,
  syncData: (d: Record<string, unknown>) => void,
) {
  const thoughts = source.thoughts as Array<Record<string, unknown>> | undefined;
  const toolCalls = source.tool_calls as Array<Record<string, unknown>> | undefined;
  const events = source.events as Array<Record<string, unknown>> | undefined;

  if (thoughts?.length) syncThoughts(thoughts as never[]);
  if (toolCalls?.length) syncToolCalls(toolCalls as never[]);
  if (events?.length) syncEvents(events as never[]);

  const excludedKeys = ['status', 'current_step', 'observed_steps', 'active_agent', 'thoughts', 'tool_calls', 'events', 'data'];
  const rest = Object.fromEntries(
    Object.entries(source).filter(([key]) => !key.startsWith('EXIT_') && !excludedKeys.includes(key))
  );
  const customData: Record<string, unknown> = { ...rest };
  const data = source.data as Record<string, unknown> | undefined;
  if (data && Object.keys(data).length > 0) customData.data = data;
  if (Object.keys(customData).length > 0) syncData(customData);
}

// Internal component to handle syncing both data sources into ThoughtsContext.
// Two separate effects with different trigger conditions:
//   1. streamingVersion — fires when new thoughts/events/tool_calls arrive via streaming.
//      Uses agentStateRef (not agentState directly) so the object reference churn from
//      CopilotKit re-renders doesn't re-trigger the effect. Breaks the render loop.
//   2. pooledState — fires every 2s from polling, fills in sub-agent data.
function StateSyncer({ pooledState, agentStateRef, streamingVersion }: StateSyncerProps) {
  const { syncThoughts, syncToolCalls, syncEvents, syncData } = useThoughts();

  // Effect 1: streaming data — triggered by content changes, not reference churn
  useEffect(() => {
    const streaming = agentStateRef.current;
    if (!streaming) return;
    syncStateToContext(streaming, syncThoughts, syncToolCalls, syncEvents, syncData);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [streamingVersion, syncThoughts, syncToolCalls, syncEvents, syncData]);

  // Effect 2: polling data — fills gaps (sub-agents, fallback when streaming idle)
  useEffect(() => {
    if (!pooledState) return;
    syncStateToContext(pooledState, syncThoughts, syncToolCalls, syncEvents, syncData);
  }, [pooledState, syncThoughts, syncToolCalls, syncEvents, syncData]);

  return null;
}

export default function CopilotKitPage() {
  const [themeColor, setThemeColor] = useState("#6366f1");
  const [isEditMode, setIsEditMode] = useState(false);

  // 1. Streaming Agent State via CopilotKit (primary — delivers events/thoughts in real-time)
  const { state: agentState } = useCoAgent<AgentState>({
    name: "my_agent",
    initialState: DEFAULT_AGENT_STATE,
  });

  // Ref holds latest streaming state so StateSyncer can read it inside effects
  // without agentState being a dep (which would fire on every CopilotKit re-render).
  const agentStateRef = useRef<AgentState>(agentState);
  agentStateRef.current = agentState;

  // Stable primitive derived from streaming content — changes only when new items
  // arrive, not on every render. Passed to StateSyncer as a safe effect dependency.
  const streamingVersion = `${(agentState.thoughts as unknown[])?.length ?? 0}-${(agentState.tool_calls as unknown[])?.length ?? 0}-${(agentState.events as unknown[])?.length ?? 0}`;

  // 2. Polling Agent State (backup — sub-agent visibility, 2s cadence)
  const pollingConfig = useMemo(() => ({
    baseUrl: "http://localhost:8001",
    interval: 2000
  }), []);

  const { pooledState } = useAgentPolling<AgentState>(pollingConfig);

  // Combined State — streaming takes priority, polling as fallback
  const combinedState: AgentState = agentState.status !== "idle"
    ? agentState
    : (pooledState ?? DEFAULT_AGENT_STATE);

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
        <StateSyncer pooledState={pooledState} agentStateRef={agentStateRef} streamingVersion={streamingVersion} />
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

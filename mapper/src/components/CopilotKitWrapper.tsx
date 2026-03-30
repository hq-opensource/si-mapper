"use client";

/**
 * CopilotKitWrapper
 * ─────────────────────────────────────────────────────────────────────────────
 * Client component that sits between WorkspaceProvider and CopilotKit.
 *
 * It reads `activeSession.session_id` from WorkspaceContext and passes it as
 * `threadId` to CopilotKit. This makes CopilotKit send that ID as the
 * `thread_id` in every AG-UI message to the agent backend.
 *
 * On the agent side, `SessionManager._find_session_by_thread_id` scans SQLite
 * for a session whose `_ag_ui_thread_id` state key equals the incoming
 * `thread_id`. Because we store `_ag_ui_thread_id = session_id` when creating
 * sessions (in `bootstrap_session`), the manager finds and reuses the correct
 * session — including its full event history — instead of creating a blank one.
 *
 * Layout hierarchy (must stay this way):
 *   WorkspaceProvider           ← reads/writes active session to localStorage
 *     CopilotKitWrapper        ← reads activeSession, feeds threadId to CopilotKit
 *       CopilotKit             ← sends threadId with every agent request
 *         {children}
 */

import { CopilotKit } from "@copilotkit/react-core";
import { useWorkspace } from "@/context/WorkspaceContext";
import type { ReactNode } from "react";

const AGENT_RUNTIME_URL = "/api/copilotkit";
const AGENT_NAME = "my_agent";

export function CopilotKitWrapper({ children }: { children: ReactNode }) {
  const { activeSession } = useWorkspace();

  return (
    <CopilotKit
      runtimeUrl={AGENT_RUNTIME_URL}
      agent={AGENT_NAME}
      threadId={activeSession?.session_id}
    >
      {children}
    </CopilotKit>
  );
}


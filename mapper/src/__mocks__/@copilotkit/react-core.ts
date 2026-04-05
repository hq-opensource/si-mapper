/**
 * Manual module mock for @copilotkit/react-core.
 *
 * CopilotKit has no test mode and requires a live WebSocket runtime.
 * This mock exposes mutable refs that tests can update to drive component
 * behaviour without network or socket dependencies.
 *
 * Usage in tests:
 *   import { __setThreadId, __setRunning, __setAgentState } from '@copilotkit/react-core';
 *   __setThreadId('session-2');
 */

let _threadId = 'default-thread';
let _running = false;
let _agentState: Record<string, unknown> = {
    status: 'idle',
    current_step: '',
    observed_steps: [],
    data: {},
    active_project: null,
    active_system: null,
};
const _setAgentStateFn = jest.fn((s: Record<string, unknown>) => { _agentState = s; });

export const __setThreadId  = (id: string) => { _threadId = id; };
export const __setRunning   = (r: boolean) => { _running = r; };
export const __setAgentState = (s: Record<string, unknown>) => { _agentState = s; };

export const useCopilotContext = jest.fn(() => ({
    threadId: _threadId,
    setThreadId: jest.fn((id: string) => { _threadId = id; }),
}));

export const useCoAgent = jest.fn(() => ({
    state: _agentState,
    setState: _setAgentStateFn,
    running: _running,
}));

export const useCopilotAction = jest.fn();
export const CopilotKit = ({ children }: { children: React.ReactNode }) => children;


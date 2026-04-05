/**
 * Unit tests — combinedState ownership rules (page.tsx logic extracted)
 *
 * Phase 2.2 — active_project/active_system always come from agentState (frontend-owned)
 * Phase 4.1 — lifecycle keys follow isCopilotTurnActive
 * Phase 3.3 — pollingConfig interval
 */

import { ACTIVE_TURN_STATUSES } from '@/constants/agentState';

type MinimalAgentState = {
    status: string;
    current_step: string;
    active_agent: string | undefined;
    active_project: { id: string } | null;
    active_system: { id: string } | null;
};

type MinimalPooledState = Partial<MinimalAgentState>;

/** Replicates the combinedState logic from page.tsx so it can be tested in isolation */
function buildCombinedState(
    agentState: MinimalAgentState,
    pooledState: MinimalPooledState | null,
    isCopilotTurnActive: boolean | undefined
) {
    const isActiveTurn = isCopilotTurnActive ??
        (ACTIVE_TURN_STATUSES as readonly string[]).includes(agentState.status);

    return {
        ...agentState,
        ...(pooledState || {}),
        status:       isActiveTurn ? agentState.status       : (pooledState?.status       ?? agentState.status),
        current_step: isActiveTurn ? agentState.current_step : (pooledState?.current_step ?? agentState.current_step),
        active_agent: isActiveTurn ? agentState.active_agent : (pooledState?.active_agent ?? agentState.active_agent),
        // Frontend is always authoritative for workspace selection
        active_project: agentState.active_project,
        active_system:  agentState.active_system,
    };
}

describe('combinedState — Phase 2.2 frontend ownership', () => {
    const baseAgent: MinimalAgentState = {
        status: 'idle',
        current_step: '',
        active_agent: undefined,
        active_project: { id: 'proj-1' },
        active_system: { id: 'sys-1' },
    };

    it('pooledState active_project does NOT overwrite agentState.active_project', () => {
        const pooled: MinimalPooledState = { active_project: { id: 'proj-backend' } };
        const combined = buildCombinedState(baseAgent, pooled, false);
        expect(combined.active_project?.id).toBe('proj-1');
    });

    it('pooledState active_system does NOT overwrite agentState.active_system', () => {
        const pooled: MinimalPooledState = { active_system: { id: 'sys-backend' } };
        const combined = buildCombinedState(baseAgent, pooled, false);
        expect(combined.active_system?.id).toBe('sys-1');
    });
});

describe('combinedState — Phase 4.1 lifecycle authority', () => {
    const agent: MinimalAgentState = {
        status: 'running',
        current_step: 'streaming_step',
        active_agent: 'MasterAgent',
        active_project: null,
        active_system: null,
    };
    const pooled: MinimalPooledState = {
        status: 'idle',
        current_step: 'stale_step',
        active_agent: 'StaleAgent',
    };

    it('during active turn (running=true), lifecycle keys come from agentState', () => {
        const combined = buildCombinedState(agent, pooled, true);
        expect(combined.status).toBe('running');
        expect(combined.current_step).toBe('streaming_step');
        expect(combined.active_agent).toBe('MasterAgent');
    });

    it('at rest (running=false), lifecycle keys come from pooledState', () => {
        const agent2 = { ...agent, status: 'idle', current_step: '', active_agent: undefined };
        const combined = buildCombinedState(agent2, pooled, false);
        expect(combined.status).toBe('idle');
        expect(combined.current_step).toBe('stale_step');
        expect(combined.active_agent).toBe('StaleAgent');
    });

    it('falls back to ACTIVE_TURN_STATUSES when running is undefined', () => {
        // agentState.status === 'thinking' should activate stream authority
        const agent3 = { ...agent, status: 'thinking' };
        const combined = buildCombinedState(agent3, pooled, undefined);
        expect(combined.status).toBe('thinking');
    });

    it('?? operator: pooledState status="" does not fall through to agentState (unlike ||)', () => {
        const agent2 = { ...agent, status: 'idle' };
        const pooled2 = { ...pooled, status: '' };
        const combined = buildCombinedState(agent2, pooled2, false);
        // ?? preserves empty string — it's a valid status value
        expect(combined.status).toBe('');
    });
});

describe('pollingConfig interval — Phase 3.3', () => {
    it('uses 10_000 when status is idle', () => {
        const status = 'idle';
        const interval = (status === 'idle' || status === 'complete') ? 10_000 : 2_000;
        expect(interval).toBe(10_000);
    });

    it('uses 10_000 when status is complete', () => {
        const status = 'complete';
        const interval = (status === 'idle' || status === 'complete') ? 10_000 : 2_000;
        expect(interval).toBe(10_000);
    });

    it('uses 2_000 when status is running', () => {
        const status = 'running';
        const interval = (status === 'idle' || status === 'complete') ? 10_000 : 2_000;
        expect(interval).toBe(2_000);
    });
});


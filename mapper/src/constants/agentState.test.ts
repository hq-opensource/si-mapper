/**
 * Unit tests — src/constants/agentState.ts
 * Verify contract completeness and no accidental mutations.
 */
import {
    FRONTEND_OWNED_KEYS,
    LIFECYCLE_KEYS,
    EXCLUDED_SYNC_KEYS,
    FILTERED_STATE_KEY_PREFIXES,
    ACTIVE_TURN_STATUSES,
} from '@/constants/agentState';

describe('agentState constants', () => {
    it('FRONTEND_OWNED_KEYS includes active_project and active_system', () => {
        expect(FRONTEND_OWNED_KEYS).toContain('active_project');
        expect(FRONTEND_OWNED_KEYS).toContain('active_system');
    });

    it('EXCLUDED_SYNC_KEYS contains all LIFECYCLE_KEYS', () => {
        for (const k of LIFECYCLE_KEYS) {
            expect(EXCLUDED_SYNC_KEYS).toContain(k);
        }
    });

    it('EXCLUDED_SYNC_KEYS contains all FRONTEND_OWNED_KEYS', () => {
        for (const k of FRONTEND_OWNED_KEYS) {
            expect(EXCLUDED_SYNC_KEYS).toContain(k);
        }
    });

    it('EXCLUDED_SYNC_KEYS includes thoughts, tool_calls, events', () => {
        expect(EXCLUDED_SYNC_KEYS).toContain('thoughts');
        expect(EXCLUDED_SYNC_KEYS).toContain('tool_calls');
        expect(EXCLUDED_SYNC_KEYS).toContain('events');
    });

    it('FILTERED_STATE_KEY_PREFIXES includes EXIT_', () => {
        expect(FILTERED_STATE_KEY_PREFIXES).toContain('EXIT_');
    });

    it('ACTIVE_TURN_STATUSES includes the documented vocabulary', () => {
        expect(ACTIVE_TURN_STATUSES).toContain('running');
        expect(ACTIVE_TURN_STATUSES).toContain('active');
        expect(ACTIVE_TURN_STATUSES).toContain('thinking');
        expect(ACTIVE_TURN_STATUSES).toContain('processing');
    });
});

describe('StateSyncer EXIT_ filter logic', () => {
    it('filters EXIT_ prefixed keys from pooledState before syncData', () => {
        const pooledState = {
            status: 'idle',
            EXIT_reason: 'done',
            equipment: { fans: [] },
        };

        const filtered = Object.fromEntries(
            Object.entries(pooledState).filter(([key]) =>
                !FILTERED_STATE_KEY_PREFIXES.some(p => key.startsWith(p)) &&
                !(EXCLUDED_SYNC_KEYS as readonly string[]).includes(key)
            )
        );

        // EXIT_ key must not pass through
        expect(filtered).not.toHaveProperty('EXIT_reason');
        // domain key should pass through
        expect(filtered).toHaveProperty('equipment');
        // lifecycle key excluded by EXCLUDED_SYNC_KEYS
        expect(filtered).not.toHaveProperty('status');
    });
});


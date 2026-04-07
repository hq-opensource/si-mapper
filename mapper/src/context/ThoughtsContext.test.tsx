/**
 * @jest-environment jsdom
 *
 * Unit tests — src/context/ThoughtsContext.tsx
 * Phase 4.2 — syncData snapshot-prune
 * Phase 4.3 — deepEqual prevents phantom re-renders
 */
import React from 'react';
import { renderHook, act } from '@testing-library/react';
import { ThoughtsProvider, useThoughts, type Thought } from '@/context/ThoughtsContext';

const wrapper = ({ children }: { children: React.ReactNode }) => (
    <ThoughtsProvider currentAgentName="test-agent">{children}</ThoughtsProvider>
);

describe('syncData — Phase 4.2 snapshot-prune', () => {
    it('removes keys absent from the snapshot on the next call', () => {
        const { result } = renderHook(() => useThoughts(), { wrapper });

        // Seed two keys
        act(() => {
            result.current.syncData({ alpha: 1, beta: 2 });
        });
        expect(result.current.data).toMatchObject({ alpha: 1, beta: 2 });

        // Call again with only 'alpha' in snapshot — 'beta' must be pruned
        act(() => {
            result.current.syncData({ alpha: 1 }, ['alpha']);
        });
        expect(result.current.data).toHaveProperty('alpha', 1);
        expect(result.current.data).not.toHaveProperty('beta');
    });

    it('does NOT prune when no snapshot is provided', () => {
        const { result } = renderHook(() => useThoughts(), { wrapper });

        act(() => {
            result.current.syncData({ alpha: 1, beta: 2 });
        });
        act(() => {
            result.current.syncData({ alpha: 1 }); // no snapshot
        });
        expect(result.current.data).toHaveProperty('beta', 2); // still there
    });

    it('does not trigger a re-render when data is unchanged (deepEqual guard)', () => {
        const { result } = renderHook(() => useThoughts(), { wrapper });

        act(() => {
            result.current.syncData({ x: { y: 1 } });
        });

        const snapshot1 = result.current.data;

        // Same content, different object reference
        act(() => {
            result.current.syncData({ x: { y: 1 } });
        });

        // deepEqual should prevent a new state reference from being created
        expect(result.current.data).toBe(snapshot1);
    });
});

describe('syncThoughts — Phase 4.3 deepEqual', () => {
    it('does not mutate state when thoughts are structurally identical', () => {
        const { result } = renderHook(() => useThoughts(), { wrapper });
        const thought: Thought = {
            id: 'chat:abc',
            content: 'hello',
            agentName: 'agent',
            timestamp: 1000,
        };

        act(() => {
            result.current.syncThoughts([thought]);
        });

        const snapshot1 = result.current.thoughts;

        act(() => {
            // Same content, freshly constructed object
            result.current.syncThoughts([{ ...thought }]);
        });

        expect(result.current.thoughts).toBe(snapshot1);
    });
});



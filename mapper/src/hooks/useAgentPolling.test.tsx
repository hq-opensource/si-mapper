/**
 * @jest-environment jsdom
 *
 * Unit + integration tests — src/hooks/useAgentPolling.ts
 *
 * pooledState is null immediately after threadId changes
 * Late responses from prior session do not overwrite current state
 * After 3 consecutive errors, fetchSessionInfo is re-invoked
 *
 * Uses jest.fn() to mock global.fetch — avoids MSW's ESM/pnpm incompatibilities.
 */

import { renderHook, act, waitFor } from '@testing-library/react';
import { useAgentPolling } from '@/hooks/useAgentPolling';

// ─── CopilotKit mock ─────────────────────────────────────────────────────────
// We manage threadId externally so we can simulate session switches.
let _mockThreadId = 'thread-1';
const mockSetThreadId = jest.fn((id: string) => { _mockThreadId = id; });

jest.mock('@copilotkit/react-core', () => ({
    useCopilotContext: () => ({
        threadId: _mockThreadId,
        setThreadId: mockSetThreadId,
    }),
}));

// ─── fetch mock helpers ───────────────────────────────────────────────────────

function makeFetchMock(
    sessionInfoData = { app_name: 'si_mapper', user_id: 'demo_user' },
    sessionStateData: Record<string, unknown> | 'error' | 'pending' = { status: 'idle' }
) {
    return jest.fn().mockImplementation((url: string, init?: RequestInit) => {
        // Respect AbortSignal
        if (init?.signal?.aborted) {
            return Promise.reject(Object.assign(new Error('AbortError'), { name: 'AbortError' }));
        }

        if (String(url).includes('/session_info')) {
            return Promise.resolve({
                ok: true,
                json: () => Promise.resolve(sessionInfoData),
            } as Response);
        }

        if (String(url).includes('/session_state')) {
            if (sessionStateData === 'error') {
                return Promise.resolve({ ok: false, status: 500, statusText: 'Internal Server Error' } as Response);
            }
            if (sessionStateData === 'pending') {
                return new Promise(() => {}); // never resolves (simulate slow/hanging request)
            }
            return Promise.resolve({
                ok: true,
                json: () => Promise.resolve(sessionStateData),
            } as Response);
        }

        return Promise.reject(new Error(`Unexpected fetch call: ${url}`));
    });
}

const config = { baseUrl: 'http://localhost:8001', interval: 200 };

beforeEach(() => {
    _mockThreadId = 'thread-1';
    jest.useFakeTimers({ doNotFake: ['nextTick', 'setImmediate', 'queueMicrotask'] });
});

afterEach(() => {
    jest.useRealTimers();
    jest.restoreAllMocks();
});

// ── pooledState cleared immediately on threadId change ────────────────────

describe('pooledState → null on threadId change', () => {
    it('sets pooledState to null before next poll after threadId changes', async () => {
        global.fetch = makeFetchMock(
            { app_name: 'si_mapper', user_id: 'demo_user' },
            { status: 'from-thread-1' }
        );

        const { result, rerender } = renderHook(() => {
            // useAgentPolling calls useCopilotContext internally
            return useAgentPolling(config);
        });

        // Let session_info + first poll complete
        await act(async () => {
            jest.advanceTimersByTime(300);
            await Promise.resolve();
        });
        await waitFor(() => expect((result.current.pooledState as Record<string, unknown>)?.status).toBe('from-thread-1'));

        // Switch threadId
        act(() => { _mockThreadId = 'thread-2'; });
        rerender();

        // pooledState must be null immediately (before next poll)
        expect(result.current.pooledState).toBeNull();
    });
});

// ── Abort: late response does not land after threadId change ─────────────

describe('Abort in-flight fetch on threadId change', () => {
    it('a pending fetch for session A does not update state after switch to session B', async () => {
        let capturedSignalA: AbortSignal | undefined;

        global.fetch = jest.fn().mockImplementation((url: string, init?: RequestInit) => {
            if (String(url).includes('/session_info')) {
                return Promise.resolve({ ok: true, json: () => Promise.resolve({ app_name: 'si_mapper', user_id: 'demo_user' }) } as Response);
            }
            if (String(url).includes('/session_state')) {
                // Capture the signal from the first poll attempt for thread-1
                if (!capturedSignalA) {
                    capturedSignalA = init?.signal;
                }
                // Return a never-resolving promise to simulate slow response
                return new Promise((resolve, reject) => {
                    // If aborted, reject with AbortError
                    init?.signal?.addEventListener('abort', () => {
                        reject(Object.assign(new Error('AbortError'), { name: 'AbortError' }));
                    });
                });
            }
            return Promise.reject(new Error(`Unhandled: ${url}`));
        });

        const { result, rerender } = renderHook(() => useAgentPolling(config));

        // Wait for session_info to load
        await act(async () => {
            jest.advanceTimersByTime(50);
            await Promise.resolve();
        });
        await waitFor(() => expect(result.current.sessionInfo).not.toBeNull());

        // Kick off a poll (it will hang)
        await act(async () => {
            jest.advanceTimersByTime(config.interval);
            await Promise.resolve();
        });

        // Switch session — should abort the hanging request
        act(() => { _mockThreadId = 'thread-2'; });
        rerender();

        // The first signal must be aborted
        await waitFor(() => expect(capturedSignalA?.aborted).toBe(true));

        // State stays null
        expect(result.current.pooledState).toBeNull();
    });
});

// ── sessionInfo re-fetched after 3 consecutive errors ────────────────────

describe('sessionInfo refresh after SESSION_INFO_ERROR_THRESHOLD errors', () => {
    it('calls /session_info again after 3 consecutive poll failures', async () => {
        let sessionInfoCallCount = 0;

        global.fetch = jest.fn().mockImplementation((url: string) => {
            if (String(url).includes('/session_info')) {
                sessionInfoCallCount++;
                return Promise.resolve({ ok: true, json: () => Promise.resolve({ app_name: 'si_mapper', user_id: 'demo_user' }) } as Response);
            }
            if (String(url).includes('/session_state')) {
                return Promise.resolve({ ok: false, status: 503, statusText: 'Service Unavailable' } as Response);
            }
            return Promise.reject(new Error(`Unhandled: ${url}`));
        });

        const { result } = renderHook(() => useAgentPolling(config));

        // Wait for initial session_info fetch
        await act(async () => {
            jest.advanceTimersByTime(50);
            await Promise.resolve();
        });
        await waitFor(() => expect(result.current.sessionInfo).not.toBeNull());
        const initialInfoCount = sessionInfoCallCount;

        // Trigger 3+ poll failures
        for (let i = 0; i < 4; i++) {
            await act(async () => {
                jest.advanceTimersByTime(config.interval);
                await Promise.resolve();
            });
        }

        // After 3 errors, session_info must have been re-fetched
        await waitFor(() => expect(sessionInfoCallCount).toBeGreaterThan(initialInfoCount));
    });
});

// ── Recovery after backend offline on startup ────────────────────────────

describe('Backend offline on startup recovery', () => {
    it('resumes polling once the backend becomes available after the initial failure', async () => {
        let backendOnline = false;

        global.fetch = jest.fn().mockImplementation((url: string, init?: RequestInit) => {
            if (init?.signal?.aborted) {
                return Promise.reject(Object.assign(new Error('AbortError'), { name: 'AbortError' }));
            }
            if (String(url).includes('/session_info')) {
                if (!backendOnline) {
                    return Promise.reject(new Error('fetch failed'));
                }
                return Promise.resolve({ ok: true, json: () => Promise.resolve({ app_name: 'si_mapper', user_id: 'demo_user' }) } as Response);
            }
            if (String(url).includes('/session_state')) {
                return Promise.resolve({ ok: true, json: () => Promise.resolve({ status: 'running' }) } as Response);
            }
            return Promise.reject(new Error(`Unhandled: ${url}`));
        });

        const { result } = renderHook(() => useAgentPolling(config));

        // Backend is offline — initial fetch fails, sessionInfo stays null.
        await act(async () => {
            jest.advanceTimersByTime(50);
            await Promise.resolve();
        });
        expect(result.current.sessionInfo).toBeNull();

        // A couple of retry ticks pass — still offline.
        await act(async () => {
            jest.advanceTimersByTime(config.interval * 2);
            await Promise.resolve();
        });
        expect(result.current.sessionInfo).toBeNull();

        // Backend comes back online.
        backendOnline = true;

        // The next retry tick should fetch sessionInfo and kick off polling.
        await act(async () => {
            jest.advanceTimersByTime(config.interval);
            await Promise.resolve();
        });
        await waitFor(() => expect(result.current.sessionInfo).not.toBeNull());
        await waitFor(() => expect((result.current.pooledState as Record<string, unknown>)?.status).toBe('running'));
    });
});

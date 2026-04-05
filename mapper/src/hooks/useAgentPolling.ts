import { useState, useEffect, useRef, useCallback } from 'react';
import { useCopilotContext } from '@copilotkit/react-core';
import { deepEqual } from '@/utils/deepEqual';

export interface PollingConfig {
    baseUrl: string;
    /** Polling interval in ms. Changes take effect on the next tick. */
    interval?: number;
    /** Set to false to suspend all polling (used for tab visibility pause). */
    enabled?: boolean;
}

/**
 * SessionInfo returned by /session_info.
 * session_id is intentionally absent — polling is driven by threadId from CopilotKit.
 */
export interface SessionInfo {
    app_name: string;
    user_id: string;
}

/** How many poll ticks between automatic sessionInfo re-fetches. */
const SESSION_INFO_REFRESH_TICKS = 15;
/** How many consecutive errors before forcing a sessionInfo re-fetch. */
const SESSION_INFO_ERROR_THRESHOLD = 3;

export function useAgentPolling<T = unknown>(config: PollingConfig) {
    const { baseUrl, interval = 3500, enabled = true } = config;
    const { threadId } = useCopilotContext();

    // Ref so the polling closure always reads the latest threadId
    // without restarting the interval on every change.
    const threadIdRef = useRef(threadId);
    useEffect(() => {
        threadIdRef.current = threadId;
    }, [threadId]);

    const [sessionInfo, setSessionInfo] = useState<SessionInfo | null>(null);
    const [pooledState, setPooledState] = useState<T | null>(null);
    const [error, setError] = useState<string | null>(null);
    // Internal flag — pause polling when browser tab is hidden.
    const [tabVisible, setTabVisible] = useState(true);

    // ── Clear stale state immediately on session switch ──────────
    useEffect(() => {
        setPooledState(null);
    }, [threadId]);

    // ── Pause polling when tab is hidden ─────────────────────────
    useEffect(() => {
        const handleVisibility = () => {
            setTabVisible(!document.hidden);
        };
        document.addEventListener('visibilitychange', handleVisibility);
        return () => document.removeEventListener('visibilitychange', handleVisibility);
    }, []);

    const isPollingActive = enabled && tabVisible;

    // ── Session Info fetch ────────────────────────────────────────
    const fetchSessionInfo = useCallback(async (signal?: AbortSignal) => {
        try {
            const response = await fetch(`${baseUrl}/session_info`, { signal });
            if (!response.ok) {
                setError(`Failed to fetch session info: ${response.statusText}`);
                return;
            }
            const data: SessionInfo = await response.json();
            setSessionInfo(prev => deepEqual(prev, data) ? prev : data);
        } catch (err: unknown) {
            if ((err as Error).name === 'AbortError') return;
            setError(`Network error fetching session info: ${err instanceof Error ? err.message : String(err)}`);
        }
    }, [baseUrl]);

    // ── Fetch session info (immediate + retry until available) ───────
    // Runs whenever polling is active and sessionInfo is missing.
    // Fires once immediately, then keeps retrying on the polling interval
    // so recovery is automatic if the backend was offline at startup.
    // Clears itself as soon as sessionInfo is obtained (sessionInfo dep).
    useEffect(() => {
        if (!isPollingActive || sessionInfo !== null) return;

        const controller = new AbortController();
        fetchSessionInfo(controller.signal);

        const retryTimer = setInterval(() => {
            fetchSessionInfo(controller.signal);
        }, interval);

        return () => {
            clearInterval(retryTimer);
            controller.abort();
        };
    }, [isPollingActive, sessionInfo, fetchSessionInfo, interval]);

    // ── Main polling loop with AbortController ────────────────────
    useEffect(() => {
        if (!isPollingActive || !sessionInfo) return;

        let isMounted = true;
        let pollCount = 0;
        let consecutiveErrors = 0;
        // AbortController for the currently in-flight request.
        let activeController: AbortController | null = null;

        const poll = async () => {
            // Refresh session info periodically or after repeated errors.
            if (pollCount % SESSION_INFO_REFRESH_TICKS === 0 || consecutiveErrors >= SESSION_INFO_ERROR_THRESHOLD) {
                if (pollCount > 0 || consecutiveErrors >= SESSION_INFO_ERROR_THRESHOLD) {
                    await fetchSessionInfo();
                }
            }
            pollCount++;

            // Abort any previous in-flight request before starting a new one.
            activeController?.abort();
            activeController = new AbortController();

            try {
                const params = new URLSearchParams({
                    request_session_id: threadIdRef.current as string,
                    app_name: sessionInfo.app_name,
                    user_id: sessionInfo.user_id,
                });

                const response = await fetch(
                    `${baseUrl}/session_state?${params.toString()}`,
                    { signal: activeController.signal }
                );

                if (response.ok && isMounted) {
                    const data = await response.json();
                    setPooledState((prev: T | null) => deepEqual(prev, data) ? prev : data);
                    setError(null);
                    consecutiveErrors = 0;
                } else if (!response.ok) {
                    // Non-2xx counts as a consecutive error (same path as network failure below)
                    consecutiveErrors++;
                    if (isMounted) {
                        setError(`Polling error: HTTP ${response.status}: ${response.statusText}`);
                    }
                }
            } catch (err: unknown) {
                // AbortError is expected (interval tick / threadId change); stay silent.
                if ((err as Error).name === 'AbortError') return;
                consecutiveErrors++;
                if (isMounted) {
                    setError(`Polling error: ${err instanceof Error ? err.message : String(err)}`);
                }
            }
        };

        const timer = setInterval(poll, interval);
        poll(); // Initial poll immediately

        return () => {
            isMounted = false;
            clearInterval(timer);
            activeController?.abort();
        };
    }, [baseUrl, interval, isPollingActive, sessionInfo, fetchSessionInfo]);

    return { pooledState, sessionInfo, error, threadId };
}

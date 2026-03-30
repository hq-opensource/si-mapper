import { useState, useEffect, useRef } from 'react';
import { useWorkspace } from '@/context/WorkspaceContext';

export interface PollingConfig {
    baseUrl: string;
    interval?: number;
    enabled?: boolean;
}

export function useAgentPolling<T = unknown>(config: PollingConfig) {
    const { baseUrl, interval = 2000, enabled = true } = config;
    const { activeSession } = useWorkspace();
    const [pooledState, setPooledState] = useState<T | null>(null);
    const [error, setError] = useState<string | null>(null);

    // Keep a ref to the latest activeSession so the polling closure always sees
    // the most recent value without restarting the interval on every session change.
    const activeSessionRef = useRef(activeSession);
    activeSessionRef.current = activeSession;

    // Expose a minimal sessionInfo shape for backward compat with consumers
    const sessionInfo = activeSession
        ? { session_id: activeSession.session_id, app_name: 'si_mapper', user_id: 'demo_user' }
        : null;

    // Poll Session State whenever activeSession or baseUrl changes
    useEffect(() => {
        if (!enabled || !activeSessionRef.current) return;

        let isMounted = true;
        const poll = async () => {
            const session = activeSessionRef.current;
            if (!session) return;
            try {
                const params = new URLSearchParams({
                    request_session_id: session.session_id,
                    app_name: 'si_mapper',
                    user_id: 'demo_user',
                });

                const response = await fetch(`${baseUrl}/session_state?${params.toString()}`);
                if (response.ok) {
                    const data = await response.json();
                    if (isMounted) {
                        setPooledState((prev: T | null) => {
                            if (JSON.stringify(prev) === JSON.stringify(data)) return prev;
                            return data;
                        });
                        setError(null);
                    }
                }
            } catch (err: unknown) {
                console.warn("Polling error:", err);
            }
        };

        const timer = setInterval(poll, interval);
        poll(); // Initial poll

        return () => {
            isMounted = false;
            clearInterval(timer);
        };
    }, [baseUrl, interval, enabled, activeSession?.session_id]);

    return { pooledState, sessionInfo, error };
}

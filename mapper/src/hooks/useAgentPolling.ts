
import { useState, useEffect } from 'react';

export interface PollingConfig {
    baseUrl: string;
    interval?: number;
    enabled?: boolean;
}

export function useAgentPolling<T = unknown>(config: PollingConfig) {
    const { baseUrl, interval = 2000, enabled = true } = config;
    const [sessionInfo, setSessionInfo] = useState<{ session_id: string; app_name: string; user_id: string } | null>(null);
    const [pooledState, setPooledState] = useState<T | null>(null);
    const [error, setError] = useState<string | null>(null);

    // 1. Fetch Session Info once
    useEffect(() => {
        if (!enabled) return;

        let isMounted = true;
        const fetchInfo = async () => {
            try {
                const response = await fetch(`${baseUrl}/session_info`);
                if (response.ok) {
                    const data = await response.json();
                    if (isMounted) {
                        setSessionInfo(prev => {
                            // Deep equality check to avoid unnecessary re-renders
                            if (prev &&
                                prev.session_id === data.session_id &&
                                prev.app_name === data.app_name &&
                                prev.user_id === data.user_id) {
                                return prev;
                            }
                            return data;
                        });
                    }
                } else {
                    setError(`Failed to fetch session info: ${response.statusText}`);
                }
            } catch (err: unknown) {
                setError(`Network error fetching session info: ${err instanceof Error ? err.message : String(err)}`);
            }
        };

        fetchInfo();
        return () => { isMounted = false; };
    }, [baseUrl, enabled]);

    // 2. Poll Session State
    useEffect(() => {
        if (!enabled || !sessionInfo) return;

        let isMounted = true;
        const poll = async () => {
            try {
                const params = new URLSearchParams({
                    request_session_id: sessionInfo.session_id as string,
                    app_name: sessionInfo.app_name as string,
                    user_id: sessionInfo.user_id as string,
                });

                const response = await fetch(`${baseUrl}/session_state?${params.toString()}`);
                if (response.ok) {
                    const data = await response.json();
                    if (isMounted) {
                        setPooledState((prev: T | null) => {
                            // Simple stringify comparison for deep check of state
                            if (JSON.stringify(prev) === JSON.stringify(data)) {
                                return prev;
                            }
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
    }, [baseUrl, interval, enabled, sessionInfo]);

    return { pooledState, sessionInfo, error };
}

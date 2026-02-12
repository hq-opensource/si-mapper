
import { useState, useEffect, useCallback } from 'react';

export interface PollingConfig {
    baseUrl: string;
    interval?: number;
    enabled?: boolean;
}

export function useAgentPolling(config: PollingConfig) {
    const { baseUrl, interval = 2000, enabled = true } = config;
    const [sessionInfo, setSessionInfo] = useState<{ session_id: string; app_name: string; user_id: string } | null>(null);
    const [pooledState, setPooledState] = useState<any>(null);
    const [error, setError] = useState<string | null>(null);

    // 1. Fetch Session Info once
    useEffect(() => {
        if (!enabled) return;

        const fetchInfo = async () => {
            try {
                const response = await fetch(`${baseUrl}/session_info`);
                if (response.ok) {
                    const data = await response.json();
                    setSessionInfo(data);
                } else {
                    setError(`Failed to fetch session info: ${response.statusText}`);
                }
            } catch (err: any) {
                setError(`Network error fetching session info: ${err.message}`);
            }
        };

        fetchInfo();
    }, [baseUrl, enabled]);

    // 2. Poll Session State
    useEffect(() => {
        if (!enabled || !sessionInfo) return;

        const poll = async () => {
            try {
                const params = new URLSearchParams({
                    request_session_id: sessionInfo.session_id,
                    app_name: sessionInfo.app_name,
                    user_id: sessionInfo.user_id,
                });

                const response = await fetch(`${baseUrl}/session_state?${params.toString()}`);
                if (response.ok) {
                    const data = await response.json();
                    setPooledState(data);
                    setError(null);
                }
            } catch (err: any) {
                console.warn("Polling error:", err);
                // We don't set error state here to avoid UI flickering on transient network issues
            }
        };

        const timer = setInterval(poll, interval);
        poll(); // Initial poll

        return () => clearInterval(timer);
    }, [baseUrl, interval, enabled, sessionInfo]);

    return { pooledState, sessionInfo, error };
}

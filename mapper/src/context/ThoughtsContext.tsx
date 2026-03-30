"use client";

import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';

export interface Thought {
    id: string; // Unique ID for the thought stream (e.g. message ID)
    content: string;
    agentName: string;
    timestamp: number;
}

export interface ToolCall {
    id: string;
    content: string;
    agentName: string;
    timestamp: number;
}

export interface AgentEvent {
    id: string;
    timestamp: number;
    agent_name: string;
    event_type: string;
    content: string;
    metadata: Record<string, unknown>;
    trace_id?: string;
}

interface ThoughtsContextType {
    thoughts: Thought[];
    addThought: (id: string, content: string, agentName?: string) => void;
    syncThoughts: (newThoughts: Thought[]) => void;
    toolCalls: ToolCall[];
    addToolCall: (id: string, content: string, agentName?: string) => void;
    syncToolCalls: (newToolCalls: ToolCall[]) => void;
    events: AgentEvent[];
    syncEvents: (newEvents: AgentEvent[]) => void;
    data: Record<string, unknown>;
    syncData: (newData: Record<string, unknown>) => void;
    /** Clear all accumulated state (thoughts, tool calls, events, data). Call on session switch. */
    clearAll: () => void;
}

const ThoughtsContext = createContext<ThoughtsContextType | undefined>(undefined);

export function useThoughts() {
    const context = useContext(ThoughtsContext);
    if (!context) {
        throw new Error('useThoughts must be used within a ThoughtsProvider');
    }
    return context;
}

interface ThoughtsProviderProps {
    children: ReactNode;
    currentAgentName: string;
}

export function ThoughtsProvider({ children, currentAgentName }: ThoughtsProviderProps) {
    const [thoughts, setThoughts] = useState<Thought[]>([]);
    const [toolCalls, setToolCalls] = useState<ToolCall[]>([]);
    const [events, setEvents] = useState<AgentEvent[]>([]);
    const [data, setData] = useState<Record<string, unknown>>({});

    const addThought = useCallback((id: string, content: string, agentName?: string) => {
        setThoughts(prev => {
            const existingIndex = prev.findIndex(t => t.id === id);

            if (existingIndex >= 0) {
                const updated = [...prev];
                if (updated[existingIndex].content !== content) {
                    updated[existingIndex] = {
                        ...updated[existingIndex],
                        content
                    };
                }
                return updated;
            } else {
                return [...prev, {
                    id,
                    content,
                    agentName: agentName || currentAgentName || "System",
                    timestamp: Date.now()
                }];
            }
        });
    }, [currentAgentName]);

    const syncThoughts = useCallback((newThoughts: Thought[]) => {
        const thoughtsArray = (Array.isArray(newThoughts)
            ? newThoughts
            : Object.values(newThoughts)) as Thought[];

        setThoughts(prev => {
            let changed = false;
            const merged = [...prev];
            thoughtsArray.forEach(nt => {
                const idx = merged.findIndex(t => t.id === nt.id);
                if (idx >= 0) {
                    if (JSON.stringify(merged[idx]) !== JSON.stringify(nt)) {
                        merged[idx] = nt;
                        changed = true;
                    }
                } else {
                    merged.push(nt);
                    changed = true;
                }
            });
            if (!changed) return prev;
            return merged.sort((a, b) => a.timestamp - b.timestamp);
        });
    }, []);

    const addToolCall = useCallback((id: string, content: string, agent_name?: string) => {
        setToolCalls(prev => {
            const existingIndex = prev.findIndex(t => t.id === id);

            if (existingIndex >= 0) {
                const updated = [...prev];
                if (updated[existingIndex].content !== content) {
                    updated[existingIndex] = {
                        ...updated[existingIndex],
                        content
                    };
                }
                return updated;
            } else {
                return [...prev, {
                    id,
                    content,
                    agentName: agent_name || currentAgentName || "System",
                    timestamp: Date.now()
                }];
            }
        });
    }, [currentAgentName]);

    const syncToolCalls = useCallback((newToolCalls: ToolCall[]) => {
        const callsArray = (Array.isArray(newToolCalls)
            ? newToolCalls
            : Object.values(newToolCalls)) as ToolCall[];

        setToolCalls(prev => {
            let changed = false;
            const merged = [...prev];
            callsArray.forEach(nc => {
                const idx = merged.findIndex(c => c.id === nc.id);
                if (idx >= 0) {
                    if (JSON.stringify(merged[idx]) !== JSON.stringify(nc)) {
                        merged[idx] = nc;
                        changed = true;
                    }
                } else {
                    merged.push(nc);
                    changed = true;
                }
            });
            if (!changed) return prev;
            return merged.sort((a, b) => a.timestamp - b.timestamp);
        });
    }, []);

    const syncEvents = useCallback((newEvents: AgentEvent[]) => {
        const eventsArray = (Array.isArray(newEvents)
            ? newEvents
            : Object.values(newEvents)) as AgentEvent[];

        setEvents(prev => {
            let changed = false;
            const merged = [...prev];
            eventsArray.forEach(ne => {
                const idx = merged.findIndex(e =>
                    (ne.trace_id && e.trace_id === ne.trace_id) || (e.id === ne.id)
                );

                if (idx >= 0) {
                    if (JSON.stringify(merged[idx]) !== JSON.stringify(ne)) {
                        merged[idx] = ne;
                        changed = true;
                    }
                } else {
                    merged.push(ne);
                    changed = true;
                }
            });
            if (!changed) return prev;
            return merged.sort((a, b) => a.timestamp - b.timestamp);
        });
    }, []);

    const syncData = useCallback((newData: Record<string, unknown>) => {
        setData(prev => {
            const hasChange = Object.entries(newData).some(([key, value]) => {
                return JSON.stringify(prev[key]) !== JSON.stringify(value);
            });
            if (!hasChange) return prev;
            return { ...prev, ...newData };
        });
    }, []);

    const clearAll = useCallback(() => {
        setThoughts([]);
        setToolCalls([]);
        setEvents([]);
        setData({});
    }, []);

    return (
        <ThoughtsContext.Provider value={{
            thoughts, addThought, syncThoughts,
            toolCalls, addToolCall, syncToolCalls,
            events, syncEvents,
            data, syncData,
            clearAll,
        }}>
            {children}
        </ThoughtsContext.Provider>
    );
}


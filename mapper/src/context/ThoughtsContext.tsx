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
    metadata: Record<string, any>;
    trace_id?: string;
}

export interface AgentTask {
    id: string;
    agent_name: string;
    description: string;
    status: 'pending' | 'processing' | 'working' | 'verification_ready' | 'verified' | 'failed';
    category?: string;
    priority?: number;
    retry_count: number;
    created_at?: string;
    updated_at?: string;
    metadata?: any;
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
    tasks: AgentTask[];
    syncTasks: (newTasks: AgentTask[]) => void;
    data: Record<string, any>;
    syncData: (newData: Record<string, any>) => void;
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
    const [tasks, setTasks] = useState<AgentTask[]>([]);
    const [data, setData] = useState<Record<string, any>>({});

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
            const merged = [...prev];
            thoughtsArray.forEach(nt => {
                const idx = merged.findIndex(t => t.id === nt.id);
                if (idx >= 0) {
                    merged[idx] = nt;
                } else {
                    merged.push(nt);
                }
            });
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
            const merged = [...prev];
            callsArray.forEach(nc => {
                const idx = merged.findIndex(c => c.id === nc.id);
                if (idx >= 0) {
                    merged[idx] = nc;
                } else {
                    merged.push(nc);
                }
            });
            return merged.sort((a, b) => a.timestamp - b.timestamp);
        });
    }, []);

    const syncEvents = useCallback((newEvents: AgentEvent[]) => {
        const eventsArray = (Array.isArray(newEvents)
            ? newEvents
            : Object.values(newEvents)) as AgentEvent[];

        setEvents(prev => {
            const merged = [...prev];
            eventsArray.forEach(ne => {
                // Deduplicate by trace_id if present, otherwise by id
                const idx = merged.findIndex(e =>
                    (ne.trace_id && e.trace_id === ne.trace_id) || (e.id === ne.id)
                );

                if (idx >= 0) {
                    merged[idx] = ne;
                } else {
                    merged.push(ne);
                }
            });
            return merged.sort((a, b) => a.timestamp - b.timestamp);
        });
    }, []);

    const syncTasks = useCallback((newTasks: AgentTask[]) => {
        const tasksArray = (Array.isArray(newTasks)
            ? newTasks
            : Object.values(newTasks)) as AgentTask[];

        setTasks(prev => {
            const merged = [...prev];
            tasksArray.forEach(nt => {
                const idx = merged.findIndex(t => t.id === nt.id);
                if (idx >= 0) {
                    merged[idx] = { ...merged[idx], ...nt };
                } else {
                    merged.push(nt);
                }
            });
            return [...merged]; // Keep order from backend for tasks
        });
    }, []);

    const syncData = useCallback((newData: Record<string, any>) => {
        setData(prev => ({ ...prev, ...newData }));
    }, []);

    return (
        <ThoughtsContext.Provider value={{
            thoughts, addThought, syncThoughts,
            toolCalls, addToolCall, syncToolCalls,
            events, syncEvents,
            tasks, syncTasks,
            data, syncData
        }}>
            {children}
        </ThoughtsContext.Provider>
    );
}


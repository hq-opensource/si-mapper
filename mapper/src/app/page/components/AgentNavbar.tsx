"use client";

import { Eye, Edit3, BarChart2, Brain, Folder, Wrench, Database, Package } from "lucide-react";
import { AgentState } from "./AgentStateOverlay";
import { useState, useEffect } from "react";
import { useThoughts } from "@/context/ThoughtsContext";
import { formatAgentName } from "@/lib/utils";

interface AgentNavbarProps {
    agentState: AgentState;
    activeTab: 'thoughts' | 'files' | 'view' | 'edit' | 'graph' | 'debug' | 'tools' | 'state' | 'performance' | 'artifacts';
    onTabChange: (tab: 'thoughts' | 'files' | 'view' | 'edit' | 'graph' | 'debug' | 'tools' | 'state' | 'performance' | 'artifacts') => void;
}

export function AgentNavbar({ activeTab, onTabChange, agentState }: AgentNavbarProps) {

    // Derived state for the status indicator
    // const isActive = agentState?.status && agentState.status !== 'idle';
    // const agentName = agentState?.active_agent || 'Agent';
    // const status = agentState?.status || 'Idle';

    const navItems = [
        { id: 'view', label: 'View', icon: Eye },
        { id: 'edit', label: 'Edit', icon: Edit3 },
        { id: 'graph', label: 'Graph', icon: BarChart2 },
        { id: 'thoughts', label: 'Thoughts', icon: Brain },
        { id: 'state', label: 'State', icon: Database },
        { id: 'tools', label: 'Tools', icon: Wrench },
        { id: 'performance', label: 'Performance', icon: BarChart2 },
        { id: 'artifacts', label: 'Artifacts', icon: Package },
        { id: 'files', label: 'Files', icon: Folder },
        { id: 'debug', label: 'Debug', icon: BarChart2 },
    ] as const;

    const { events, data } = useThoughts();

    const [hasNewThoughts, setHasNewThoughts] = useState(false);
    const [hasNewTools, setHasNewTools] = useState(false);
    const [hasNewState, setHasNewState] = useState(false);
    const [hasNewPerformance, setHasNewPerformance] = useState(false);
    const [hasNewArtifacts, setHasNewArtifacts] = useState(false);
    const [lastEventCount, setLastEventCount] = useState(0);
    const [lastDataHash, setLastDataHash] = useState("");

    // Track new events (Thoughts/Tools)
    useEffect(() => {
        if (events.length > lastEventCount) {
            const newEvents = events.slice(lastEventCount);

            const hasThoughts = newEvents.some(e => e.event_type === 'BRAINSTORM' || e.event_type === 'DELEGATION');
            const hasTools = newEvents.some(e => e.event_type === 'ACTION_TRIGGER' || e.event_type === 'ACTION_RESULT' || e.event_type === 'STATE_MUTATION');
            const hasPerf = newEvents.some(e => e.metadata?.latency_s !== undefined);

            if (activeTab !== 'thoughts' && hasThoughts) setHasNewThoughts(true);
            if (activeTab !== 'tools' && hasTools) setHasNewTools(true);
            if (activeTab !== 'performance' && hasPerf) setHasNewPerformance(true);

            const hasArtifacts = newEvents.some(e => e.event_type === 'ARTIFACT');
            if (activeTab !== 'artifacts' && hasArtifacts) setHasNewArtifacts(true);

            setLastEventCount(events.length);
        }
    }, [events, activeTab, lastEventCount]);

    // Track new state data
    useEffect(() => {
        const currentHash = JSON.stringify(data);
        if (currentHash !== "{}" && currentHash !== lastDataHash) {
            if (activeTab !== 'state') {
                setHasNewState(true);
            }
            setLastDataHash(currentHash);
        }
    }, [data, lastDataHash, activeTab]);

    // Reset markers when visiting tabs
    useEffect(() => {
        if (activeTab === 'thoughts') setHasNewThoughts(false);
        if (activeTab === 'tools') setHasNewTools(false);
        if (activeTab === 'state') setHasNewState(false);
        if (activeTab === 'performance') setHasNewPerformance(false);
        if (activeTab === 'artifacts') setHasNewArtifacts(false);
    }, [activeTab]);




    return (
        <div className="absolute top-0 left-1/2 -translate-x-1/2 h-24 flex items-center z-30">
            <div className="
                flex items-center gap-1 p-1.5
                rounded-2xl border border-[var(--muted-foreground)]/20
                shadow-[0_8px_30px_rgb(0,0,0,0.04)]
            "
                style={{ backgroundColor: 'var(--background)' }}>

                {/* Status indicator (Left side of nav) */}
                <div className="flex items-center gap-3 px-4 py-1.5 border-r border-[var(--muted-foreground)]/20 mr-1">
                    <div className="relative flex h-2 w-2">
                        {agentState?.status && agentState.status !== 'idle' && (
                            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-[var(--accent)] opacity-75"></span>
                        )}
                        <span className="relative inline-flex h-2 w-2 rounded-full bg-[var(--accent)]"></span>
                    </div>
                    <div className="w-32 flex items-center overflow-hidden">
                        <span className="text-[12px] font-black uppercase tracking-widest truncate text-[var(--foreground)]">
                            {agentState.active_agent ? formatAgentName(agentState.active_agent) : 'SI-MAPPER'}
                        </span>
                    </div>
                </div>

                {/* Navigation Items */}
                {navItems.map((item) => {
                    const isNew =
                        (item.id === 'thoughts' && hasNewThoughts) ||
                        (item.id === 'state' && hasNewState) ||
                        (item.id === 'performance' && hasNewPerformance) ||
                        (item.id === 'artifacts' && hasNewArtifacts) ||
                        (item.id === 'tools' && hasNewTools);

                    return (
                        <button
                            key={item.id}
                            onClick={() => onTabChange(item.id)}
                            className={`
                            relative px-4 py-2 rounded-xl text-sm font-bold transition-all duration-300
                            flex items-center gap-2 border border-transparent
                            ${activeTab === item.id
                                    ? 'text-[var(--accent)] bg-[var(--accent)]/15 border-[var(--accent)]/10 shadow-sm'
                                    : 'text-[var(--muted-foreground)] hover:text-[var(--foreground)] hover:bg-[var(--foreground)]/5'
                                }
                        `}
                        >
                            <span className={`relative z-10 ${isNew ? 'animate-soft-glow text-[var(--accent)]' : ''}`}>
                                {item.label}
                            </span>
                        </button>
                    );
                })}
            </div>
        </div>
    );
}

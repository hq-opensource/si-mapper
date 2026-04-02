"use client";

import { Eye, Edit3, BarChart2, Brain, Folder, Wrench, Database, Package, Code2, ChevronDown, Plus, X } from "lucide-react";
import { AgentState } from "./AgentStateOverlay";
import { useState, useEffect, useRef } from "react";
import { useThoughts } from "@/context/ThoughtsContext";
import { formatAgentName } from "@/lib/utils";
import { ProjectSelector } from "@/components/ProjectSelector";
import { SystemSelector } from "@/components/SystemSelector";
import { PromptDialog } from "@/components/PromptDialog";
import type { Session } from "@/types";

// ── SessionDropdown ───────────────────────────────────────────────────────────

function SessionDropdown({
    threadId,
    sessions,
    onUseSession,
    onNewSession,
    onRemoveSession,
}: {
    threadId?: string | null;
    sessions: Session[];
    onUseSession: (id: string) => void;
    onNewSession: (name: string) => void;
    onRemoveSession: (id: string) => void;
}) {
    const [isOpen, setIsOpen] = useState(false);
    const [isDialogOpen, setIsDialogOpen] = useState(false);
    const ref = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const handler = (e: MouseEvent) => {
            if (ref.current && !ref.current.contains(e.target as Node)) setIsOpen(false);
        };
        document.addEventListener('mousedown', handler);
        return () => document.removeEventListener('mousedown', handler);
    }, []);

    const activeSession = sessions.find(s => s.id === threadId);
    const activeLabel = activeSession?.name ?? (threadId ? `${threadId.slice(0, 8)}…` : 'Session');

    const handleCreate = (name: string) => {
        onNewSession(name);
        setIsOpen(false);
    };

    return (
        <>
            <div className="relative ml-2" ref={ref}>
                <button
                    onClick={() => setIsOpen(o => !o)}
                    className="h-8 flex items-center gap-1.5 rounded-lg border border-[var(--muted-foreground)]/20 px-2 text-xs font-semibold text-[var(--foreground)] transition-colors hover:border-[var(--accent)]"
                    title={threadId ?? 'No session'}
                >
                    <span className="max-w-[8rem] truncate">{activeLabel}</span>
                    <ChevronDown
                        size={10}
                        className={`flex-shrink-0 transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`}
                    />
                </button>

                {isOpen && (
                    <div className="absolute left-0 top-full mt-1 w-72 bg-[var(--background)] border border-[var(--muted-foreground)]/20 rounded-2xl shadow-2xl z-[200] overflow-hidden">
                        <div className="max-h-48 overflow-y-auto py-1.5">
                            {sessions.length === 0 ? (
                                <p className="px-4 py-3 text-xs text-[var(--muted-foreground)]">No sessions yet.</p>
                            ) : (
                                sessions.map(session => (
                                    <div
                                        key={session.id}
                                        onClick={() => { onUseSession(session.id); setIsOpen(false); }}
                                        className={`flex items-center px-4 py-2 cursor-pointer hover:bg-[var(--foreground)]/5 transition-colors group/session
                                            ${threadId === session.id ? 'text-[var(--accent)]' : 'text-[var(--foreground)]'}`}
                                    >
                                        <div className="flex flex-col flex-1 min-w-0">
                                            <span className="flex items-center gap-1.5 text-xs font-semibold">
                                                {threadId === session.id && (
                                                    <span className="flex-shrink-0 w-1.5 h-1.5 rounded-full bg-[var(--accent)]" />
                                                )}
                                                {session.name}
                                            </span>
                                            <span className="text-[10px] text-[var(--muted-foreground)] font-mono truncate mt-0.5">
                                                {session.id}
                                            </span>
                                        </div>
                                        <button
                                            onClick={(e) => { e.stopPropagation(); onRemoveSession(session.id); setIsOpen(false); }}
                                            className="flex-shrink-0 ml-2 p-1 rounded-md opacity-0 group-hover/session:opacity-100 hover:bg-red-500/10 hover:text-red-500 transition-all"
                                            title="Remove session"
                                        >
                                            <X size={10} />
                                        </button>
                                    </div>
                                ))
                            )}
                        </div>
                        <div className="border-t border-[var(--muted-foreground)]/20 p-1.5">
                            <button
                                onClick={() => { setIsOpen(false); setIsDialogOpen(true); }}
                                className="w-full flex items-center gap-2 px-3 py-2 text-xs text-[var(--foreground)] rounded-xl hover:bg-[var(--foreground)]/5 transition-colors"
                            >
                                <Plus size={12} className="text-[var(--accent)]" />
                                <span>New session</span>
                            </button>
                        </div>
                    </div>
                )}
            </div>

            <PromptDialog
                isOpen={isDialogOpen}
                onClose={() => setIsDialogOpen(false)}
                onConfirm={handleCreate}
                title="New Session"
                description="Give this conversation session a name."
                placeholder="e.g. Initial mapping"
                confirmText="Create"
            />
        </>
    );
}

// ── AgentNavbar ───────────────────────────────────────────────────────────────

interface AgentNavbarProps {
    agentState: AgentState;
    activeTab: 'thoughts' | 'files' | 'view' | 'edit' | 'graph' | 'debug' | 'tools' | 'state' | 'performance' | 'artifacts' | 'python' | 'ttl';
    onTabChange: (tab: 'thoughts' | 'files' | 'view' | 'edit' | 'graph' | 'debug' | 'tools' | 'state' | 'performance' | 'artifacts' | 'python' | 'ttl') => void;
    onUseSession: (sessionId: string) => void;
    onNewSession: (name: string) => void;
    onRemoveSession: (sessionId: string) => void;
    threadId?: string | null;
    sessions: Session[];
}

export function AgentNavbar({ activeTab, onTabChange, agentState, onUseSession, onNewSession, onRemoveSession, threadId, sessions }: AgentNavbarProps) {

    const navItems = [
        { id: 'view', label: 'View', icon: Eye },
        { id: 'edit', label: 'Edit', icon: Edit3 },
        { id: 'graph', label: 'Graph', icon: BarChart2 },
        { id: 'thoughts', label: 'Thoughts', icon: Brain },
        { id: 'state', label: 'State', icon: Database },
        { id: 'tools', label: 'Tools', icon: Wrench },
        { id: 'performance', label: 'Performance', icon: BarChart2 },
        { id: 'artifacts', label: 'Artifacts', icon: Package },
        { id: 'python', label: 'Python', icon: Code2 },
        { id: 'ttl', label: 'TTL', icon: Database },
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
            const hasArtifacts = newEvents.some(e => e.event_type === 'ARTIFACT');
            if (activeTab !== 'thoughts' && hasThoughts) setHasNewThoughts(true);
            if (activeTab !== 'tools' && hasTools) setHasNewTools(true);
            if (activeTab !== 'performance' && hasPerf) setHasNewPerformance(true);
            if (activeTab !== 'artifacts' && hasArtifacts) setHasNewArtifacts(true);
            setLastEventCount(events.length);
        }
    }, [events, activeTab, lastEventCount]);

    // Track new state data
    useEffect(() => {
        const currentHash = JSON.stringify(data);
        if (currentHash !== "{}" && currentHash !== lastDataHash) {
            if (activeTab !== 'state') setHasNewState(true);
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

                {/* Status indicator */}
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

                {/* Workspace selectors */}
                <div className="flex items-center gap-1 px-3 py-1 border-r border-[var(--muted-foreground)]/20 mr-1">
                    <ProjectSelector />
                    <span className="text-[var(--muted-foreground)]/40 text-xs select-none px-0.5">/</span>
                    <SystemSelector />
                    <SessionDropdown
                        threadId={threadId}
                        sessions={sessions}
                        onUseSession={onUseSession}
                        onNewSession={onNewSession}
                        onRemoveSession={onRemoveSession}
                    />
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

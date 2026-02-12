"use client";

import { CheckCircle2, Circle, Clock, Loader2, AlertTriangle, RefreshCw, FileText, ListTodo, ChevronRight } from "lucide-react";
import { useState, useEffect } from "react";
import { Markdown } from "@copilotkit/react-ui";

export interface Task {
    id: string | number;
    description: string;
    status: "pending" | "processing" | "working" | "verification_ready" | "verified" | "failed";
    agent_name: string;
    retry_count?: number;
}

export interface AgentState {
    status: string;
    current_step: string;
    observed_steps: string[];
    active_agent?: string;
    tasks?: Task[];
    plan?: string;
    [key: string]: unknown;
}

interface AgentStateOverlayProps {
    agentState: AgentState;
}

export function AgentStateOverlay({ agentState }: AgentStateOverlayProps) {
    const [activeTab, setActiveTab] = useState<'status' | 'plan'>('status');
    const [isExpanded, setIsExpanded] = useState(true);
    const [hasNewPlan, setHasNewPlan] = useState(false);

    // Auto-focus plan tab when a new plan arrives
    useEffect(() => {
        if (agentState.plan && agentState.active_agent === 'PlanLlmAgent') {
            setHasNewPlan(true);
            setActiveTab('plan');
            setIsExpanded(true);
        }
    }, [agentState.plan, agentState.active_agent]);

    // Clear "New" badge when plan tab is visited
    useEffect(() => {
        if (activeTab === 'plan') {
            setHasNewPlan(false);
        }
    }, [activeTab]);

    // Format plan content with emojis and better styling
    const formatPlanContent = (content: string) => {
        if (!content) return "";
        return content
            .replace(/\[NEW\]/g, '✨ **NEW**')
            .replace(/\[MODIFY\]/g, '🔨 **MODIFY**')
            .replace(/\[REMOVE\]/g, '🗑️ **REMOVE**')
            .replace(/\[IMPORTANT\]/g, '⚠️ **IMPORTANT**')
            .replace(/\[NOTE\]/g, '📝 **NOTE**')
            .replace(/\[INFO\]/g, 'ℹ️ **INFO**');
    };

    if (!agentState || agentState.status === "idle") {
        return null;
    }

    return (
        <div className="absolute top-6 right-6 z-20 flex sm:flex-col lg:flex-row items-start lg:items-center gap-2">

            {/* Sidebar Control / Tray */}
            {/* Only show if we decide to have a collapsed state, for now let's just make the main box collapsible or have a side-strip */}

            <div className={`
                flex flex-col overflow-hidden rounded-2xl border border-[var(--muted-foreground)]/20 shadow-[0_8px_32px_0_rgba(31,38,135,0.15)] transition-all duration-300 ease-in-out
                ${isExpanded ? 'w-96' : 'w-16'}
           `}
                style={{ backgroundColor: 'var(--background)' }}
            >
                {/* Header - Always visible (in some form) */}
                <div
                    className="bg-gradient-to-r from-indigo-600 to-violet-600 cursor-pointer"
                    onClick={() => setIsExpanded(!isExpanded)}
                >
                    <div className="p-4 flex items-center justify-between">
                        {isExpanded ? (
                            <>
                                <div className="flex items-center gap-2">
                                    <div className="relative flex h-2 w-2">
                                        <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-white opacity-75"></span>
                                        <span className="relative inline-flex h-2 w-2 rounded-full bg-white"></span>
                                    </div>
                                    <h3 className="text-[10px] font-bold tracking-widest text-white uppercase opacity-90 truncate max-w-[120px]">
                                        {agentState.active_agent || "Agent"}
                                    </h3>
                                </div>
                                <div className="flex items-center gap-2">
                                    <span className="rounded-full bg-white/20 px-2.5 py-0.5 text-[10px] font-black text-white uppercase backdrop-blur-sm">
                                        {agentState.status}
                                    </span>
                                    <ChevronRight size={14} className="text-white/70" />
                                </div>
                            </>
                        ) : (
                            <div className="flex flex-col items-center gap-4 w-full">
                                <div className="relative flex h-2 w-2">
                                    <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-white opacity-75"></span>
                                    <span className="relative inline-flex h-2 w-2 rounded-full bg-white"></span>
                                </div>
                                {/* Vertical Text for collapsed state could go here if needed */}
                            </div>
                        )}
                    </div>

                    {/* Collapsed Status Indicator */}
                    {!isExpanded && (
                        <div className="pb-4 flex flex-col items-center gap-2">
                            <div className={`p-2 rounded-lg ${activeTab === 'status' ? 'bg-white/20 text-white' : 'text-indigo-100 hover:bg-white/10'}`} onClick={(e) => { e.stopPropagation(); setActiveTab('status'); setIsExpanded(true); }}>
                                <ListTodo size={16} />
                            </div>
                            <div className={`p-2 rounded-lg relative ${activeTab === 'plan' ? 'bg-white/20 text-white' : 'text-indigo-100 hover:bg-white/10'}`} onClick={(e) => { e.stopPropagation(); setActiveTab('plan'); setIsExpanded(true); }}>
                                <FileText size={16} />
                                {hasNewPlan && <span className="absolute top-1 right-1 h-2 w-2 rounded-full bg-amber-400 border border-indigo-600"></span>}
                            </div>
                        </div>
                    )}
                </div>

                {/* Expanded Content */}
                {isExpanded && (
                    <div className="flex flex-col h-[600px]"> {/* Fixed height when expanded */}
                        {/* Tabs */}
                        <div className="flex border-b border-white/10 bg-indigo-600/5">
                            <button
                                onClick={() => setActiveTab('status')}
                                className={`flex-1 py-3 text-[10px] font-bold uppercase tracking-wider transition-colors flex items-center justify-center gap-2
                                    ${activeTab === 'status'
                                        ? 'text-[var(--accent)] bg-white/10 border-b-2 border-white'
                                        : 'text-[var(--muted-foreground)] hover:text-white hover:bg-white/10'
                                    }`}
                            >
                                <ListTodo size={14} />
                                Status & Tasks
                            </button>
                            <button
                                onClick={() => setActiveTab('plan')}
                                className={`flex-1 py-3 text-[10px] font-bold uppercase tracking-wider transition-colors flex items-center justify-center gap-2 relative
                                    ${activeTab === 'plan'
                                        ? 'text-[var(--accent)] bg-white/10 border-b-2 border-white'
                                        : 'text-[var(--muted-foreground)] hover:text-white hover:bg-white/10'
                                    }`}
                            >
                                <FileText size={14} />
                                Current Plan
                                {hasNewPlan && <span className="flex h-2 w-2 relative -top-1 -right-1">
                                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75"></span>
                                    <span className="relative inline-flex rounded-full h-2 w-2 bg-amber-500"></span>
                                </span>}
                            </button>
                        </div>

                        {/* Content Area */}
                        <div className="flex-1 overflow-hidden flex flex-col relative" style={{ backgroundColor: 'var(--background)' }}>
                            {activeTab === 'status' ? (
                                <>
                                    {/* Current Step / Status Header */}
                                    <div className="p-4 border-b border-[var(--muted-foreground)]/20 shrink-0" style={{ backgroundColor: 'var(--background)' }}>
                                        <p className="text-[10px] font-bold text-[var(--accent)] uppercase tracking-wider mb-1">Current Activity</p>
                                        <div className="p-3 rounded-xl border border-[var(--muted-foreground)]/20 shadow-sm" style={{ backgroundColor: 'var(--card-foreground)', color: 'var(--background)' }}>
                                            <p className="text-sm font-bold leading-snug">
                                                {agentState.current_step || "Synchronizing state..."}
                                            </p>
                                        </div>
                                    </div>

                                    {/* Task List */}
                                    <div className="flex-1 overflow-y-auto p-4 space-y-3 scrollbar-thin scrollbar-thumb-slate-300 scrollbar-track-transparent">
                                        <p className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] flex items-center gap-2 mb-2">
                                            <span className="h-px w-4 bg-slate-300"></span>
                                            Execution Queue
                                        </p>

                                        {agentState.tasks?.map((task) => (
                                            <div
                                                key={task.id}
                                                className={`group flex items-start gap-3 rounded-xl border p-3 transition-all ${task.status === 'working' || task.status === 'processing'
                                                    ? 'border-[var(--accent)] shadow-md translate-x-1'
                                                    : 'border-[var(--muted-foreground)]/20 hover:border-[var(--muted-foreground)]/40'
                                                    }`}
                                                style={{ backgroundColor: 'var(--background)' }}
                                            >
                                                <div className={`mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full ${task.status === 'verified' ? 'text-green-500 bg-green-50' :
                                                    task.status === 'failed' ? 'text-red-500 bg-red-50' :
                                                        (task.status === 'working' || task.status === 'processing') ? 'text-indigo-600 bg-indigo-50' :
                                                            'text-slate-400 bg-slate-100'
                                                    }`}>
                                                    {task.status === 'verified' && <CheckCircle2 size={12} strokeWidth={3} />}
                                                    {task.status === 'failed' && <AlertTriangle size={12} strokeWidth={3} />}
                                                    {(task.status === 'working' || task.status === 'processing') && <Loader2 size={12} className="animate-spin" strokeWidth={3} />}
                                                    {task.status === 'pending' && <Circle size={12} strokeWidth={3} />}
                                                    {task.status === 'verification_ready' && <Clock size={12} strokeWidth={3} />}
                                                </div>

                                                <div className="flex-1 min-w-0">
                                                    <div className="flex items-center justify-between gap-2 mb-0.5">
                                                        <span className="text-[10px] font-bold text-[var(--muted-foreground)] uppercase tracking-wider">
                                                            {task.agent_name || "System"}
                                                        </span>
                                                        {task.retry_count !== undefined && task.retry_count > 0 && (
                                                            <span className="flex items-center gap-1 text-[9px] font-bold text-amber-600 bg-amber-50 px-1.5 py-0.5 rounded-full">
                                                                <RefreshCw size={8} /> Retry #{task.retry_count}
                                                            </span>
                                                        )}
                                                    </div>
                                                    <p className="text-xs font-medium text-[var(--foreground)] leading-relaxed">
                                                        {task.description}
                                                    </p>
                                                </div>
                                            </div>
                                        ))}

                                        {(!agentState.tasks || agentState.tasks.length === 0) && (
                                            <div className="text-center py-10 flex flex-col items-center gap-3 opacity-60">
                                                <div className="p-3 rounded-full bg-slate-100 text-slate-400">
                                                    <ListTodo size={24} strokeWidth={1.5} />
                                                </div>
                                                <div>
                                                    <p className="text-slate-500 text-xs font-bold uppercase tracking-widest">No Active Tasks</p>
                                                    <p className="text-[10px] text-slate-400 mt-1">Agent is planning or idle</p>
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                </>
                            ) : (
                                <div className="flex-1 flex flex-col min-h-0" style={{ backgroundColor: 'var(--background)' }}>
                                    {/* Plan Content */}
                                    {agentState.plan ? (
                                        <div className="flex-1 overflow-y-auto p-5 scrollbar-thin scrollbar-thumb-slate-300 scrollbar-track-transparent bg-white">
                                            <div className="prose prose-sm max-w-none 
                                                prose-headings:font-bold prose-headings:text-slate-900 
                                                prose-p:text-slate-800 prose-p:leading-relaxed
                                                prose-li:text-slate-800 prose-li:marker:text-slate-500
                                                prose-strong:text-indigo-700 prose-strong:font-extrabold
                                                prose-hr:border-slate-200
                                                prose-pre:bg-slate-900 prose-pre:text-slate-50
                                            ">
                                                <Markdown content={formatPlanContent(agentState.plan)} />
                                            </div>
                                        </div>
                                    ) : (
                                        <div className="flex-1 flex flex-col items-center justify-center text-center p-8 opacity-60">
                                            <div className="p-3 rounded-full bg-indigo-50 text-indigo-300 mb-3">
                                                <FileText size={32} strokeWidth={1.5} />
                                            </div>
                                            <p className="text-slate-500 text-xs font-bold uppercase tracking-widest">No Plan Available</p>
                                            <p className="text-[10px] text-slate-400 mt-1 max-w-[200px]">The agent has not generated a formal implementation plan yet.</p>
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>

                        {/* Footer */}
                        <div className="px-4 py-2 border-t border-indigo-100 bg-white/80 shrink-0">
                            <div className="flex items-center justify-between text-[9px] font-black text-slate-400 uppercase tracking-widest">
                                <span>Status: {agentState.status === 'idle' ? 'Standby' : 'Active'}</span>
                                <div className="flex gap-1.5">
                                    <span className="h-1 w-1 rounded-full bg-slate-300"></span>
                                    <span className="h-1 w-1 rounded-full bg-slate-300"></span>
                                    <span className={`h-1 w-1 rounded-full ${agentState.status !== 'idle' ? 'bg-indigo-500 animate-pulse' : 'bg-slate-300'}`}></span>
                                </div>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}

"use client";

import React, { useRef, useEffect, useState } from 'react';
import { useThoughts } from '../../../context/ThoughtsContext';
import { ListTodo, CheckCircle2, AlertTriangle, Loader2, Circle, Clock, RefreshCw, Eye } from 'lucide-react';
import { SharedPageContainer } from './SharedPageContainer';
import { StatusPlaceholder } from './StatusPlaceholder';
import { formatAgentName } from '@/lib/utils';

export function TasksWindow() {
    const { tasks } = useThoughts();
    const bottomRef = useRef<HTMLDivElement>(null);
    const containerRef = useRef<HTMLDivElement>(null);
    const [isHovering, setIsHovering] = useState(false);

    // Auto-scroll logic refined for streaming stability
    useEffect(() => {
        if (isHovering) return;
        if (bottomRef.current && tasks.length > 0) {
            bottomRef.current.scrollIntoView({ behavior: 'auto', block: 'end' });
        }
    }, [tasks.length, isHovering]);

    const getStatusStyles = (status: string) => {
        switch (status) {
            case 'verified':
                return {
                    dot: "border-emerald-500 shadow-[0_0_15px_rgba(16,185,129,0.3)] bg-emerald-500",
                    badge: "bg-emerald-500/10 text-emerald-500 border-emerald-500/20",
                    text: "text-emerald-500/80",
                    icon: CheckCircle2
                };
            case 'failed':
                return {
                    dot: "border-rose-500 shadow-[0_0_15px_rgba(244,63,94,0.3)] bg-rose-500",
                    badge: "bg-rose-500/10 text-rose-500 border-rose-500/20",
                    text: "text-rose-500/80",
                    icon: AlertTriangle
                };
            case 'working':
            case 'processing':
                return {
                    dot: "border-indigo-500 shadow-[0_0_20px_rgba(99,102,241,0.5)] bg-indigo-500 animate-pulse",
                    badge: "bg-indigo-500/10 text-indigo-500 border-indigo-500/20",
                    text: "text-indigo-500/80",
                    icon: Loader2
                };
            case 'verification_ready':
                return {
                    dot: "border-amber-500 shadow-[0_0_15px_rgba(245,158,11,0.3)] bg-amber-500",
                    badge: "bg-amber-500/10 text-amber-500 border-amber-500/20",
                    text: "text-amber-500/80",
                    icon: Eye
                };
            default:
                return {
                    dot: "border-[var(--muted-foreground)]/30 bg-[var(--muted-foreground)]/10",
                    badge: "bg-[var(--muted-foreground)]/5 text-[var(--muted-foreground)] border-[var(--muted-foreground)]/10",
                    text: "text-[var(--muted-foreground)]/50",
                    icon: Clock
                };
        }
    };



    return (
        <SharedPageContainer
            title="Execution Queue"
            subtitle="Orchestrating Complex Multi-Agent Workflows"
            icon={ListTodo}
            containerRef={containerRef}
            onMouseEnter={() => setIsHovering(true)}
            onMouseLeave={() => setIsHovering(false)}
            fullWidth
            fullHeight
            footerContent={
                <div className="flex items-center gap-4">
                    <div className={`px-3 py-1 rounded-full text-xs font-bold tracking-wider uppercase border transition-all duration-500
                        ${isHovering
                            ? 'bg-amber-500/10 text-amber-500 border-amber-500/20'
                            : 'bg-indigo-500/10 text-indigo-500 border-indigo-500/20 shadow-[0_0_15px_rgba(99,102,241,0.1)]'}`}>
                        {isHovering ? 'Manual Override' : 'System Managed'}
                    </div>
                    <span className="text-xs font-bold text-[var(--muted-foreground)] tracking-wider uppercase opacity-50">
                        Pending: {tasks.filter(t => t.status === 'pending').length} |
                        Active: {tasks.filter(t => t.status === 'working' || t.status === 'processing').length} |
                        Total: {tasks.length}
                    </span>
                </div>
            }
        >
            {tasks.length === 0 ? (
                <StatusPlaceholder
                    icon={ListTodo}
                    title="No active tasks in queue"
                    subtitle="System is idling or awaiting mission directives"
                />
            ) : (
                <div className="space-y-12 pl-10 pt-4">
                    {tasks.map((task, idx) => {
                        const style = getStatusStyles(task.status);
                        const StatusIcon = style.icon;

                        return (
                            <div key={task.id} className="relative group animate-in fade-in slide-in-from-bottom-8 duration-700">
                                {/* Timeline line */}
                                {idx < tasks.length - 1 && (
                                    <div className="absolute -left-10 top-8 bottom-[-48px] w-px bg-gradient-to-b from-[var(--muted-foreground)]/20 via-[var(--muted-foreground)]/10 to-transparent" />
                                )}

                                {/* Status indicator dot */}
                                <div className={`absolute -left-[45px] top-1.5 h-3 w-3 rounded-full border-2 border-white dark:border-black transition-all duration-500 z-10 ${style.dot}`} />

                                <div className="flex flex-col gap-5">
                                    <div className="flex items-center justify-between">
                                        <div className="flex items-center gap-4">
                                            {/* Agent Badge */}
                                            <span className={`text-xs font-bold px-2 py-0.5 rounded shadow-sm uppercase tracking-wider transition-all duration-500 
                                                ${(task.status === 'working' || task.status === 'processing')
                                                    ? 'bg-indigo-500 text-white'
                                                    : 'bg-[var(--muted-foreground)]/10 text-[var(--muted-foreground)]'}`}>
                                                {task.agent_name ? formatAgentName(task.agent_name) : "SYSTEM"}
                                            </span>

                                            {/* Status Badge */}
                                            <span className={`text-xs font-bold px-2 py-0.5 rounded border uppercase tracking-wider flex items-center gap-1.5 ${style.badge}`}>
                                                {task.status === 'working' || task.status === 'processing' ? (
                                                    <StatusIcon size={8} className="animate-spin" />
                                                ) : (
                                                    <StatusIcon size={8} />
                                                )}
                                                {task.status.replace('_', ' ')}
                                            </span>

                                            {task.retry_count > 0 && (
                                                <span className="text-[9px] font-bold text-amber-500 bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/20 uppercase tracking-tighter flex items-center gap-1">
                                                    <RefreshCw size={8} className="animate-pulse" />
                                                    {task.retry_count} retries
                                                </span>
                                            )}
                                        </div>
                                    </div>

                                    <div className="pl-4">
                                        <p className={`text-xl font-bold tracking-tight leading-tight transition-colors duration-500 
                                            ${(task.status === 'working' || task.status === 'processing') ? 'text-[var(--foreground)]' : 'text-[var(--foreground)] opacity-60'}`}>
                                            {task.description}
                                        </p>

                                        {task.category && (
                                            <div className="mt-3 flex items-center gap-2">
                                                <span className="text-[8px] font-black uppercase text-[var(--muted-foreground)]/40 tracking-[0.2em]">Category:</span>
                                                <span className="text-[9px] font-bold text-[var(--accent)] bg-[var(--accent)]/5 px-2 py-0.5 rounded border border-[var(--accent)]/10">
                                                    {task.category}
                                                </span>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </div>
                        );
                    })}
                    <div ref={bottomRef} className="h-40" />
                </div>
            )}
        </SharedPageContainer>
    );
}

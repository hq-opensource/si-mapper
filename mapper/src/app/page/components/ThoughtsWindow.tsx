"use client";

import React, { useRef, useEffect, useState } from 'react';
import { useThoughts } from '../../../context/ThoughtsContext';
import { Markdown } from "@copilotkit/react-ui";
import { Brain } from 'lucide-react';
import { SharedPageContainer } from './SharedPageContainer';
import { StatusPlaceholder } from './StatusPlaceholder';
import { formatAgentName } from '@/lib/utils';

export function ThoughtsWindow() {
    const { events } = useThoughts();
    const bottomRef = useRef<HTMLDivElement>(null);
    const containerRef = useRef<HTMLDivElement>(null);
    const [isHovering, setIsHovering] = useState(false);

    // Filter events relevant for the thinking trace
    const traceEvents = events.filter(e =>
        e.event_type === "BRAINSTORM" ||
        e.event_type === "DELEGATION"
    );

    // Auto-scroll logic refined for streaming stability
    useEffect(() => {
        if (isHovering) return;
        if (bottomRef.current && traceEvents.length > 0) {
            bottomRef.current.scrollIntoView({ behavior: 'auto', block: 'end' });
        }
    }, [traceEvents.length, isHovering]);

    const getEventStyles = (type: string) => {
        switch (type) {
            case "DELEGATION":
                return "border-amber-500/20 bg-amber-500/5 text-amber-600 dark:text-amber-400";
            case "ACTION_TRIGGER":
                return "border-indigo-500/20 bg-indigo-500/5 text-indigo-600 dark:text-indigo-400";
            case "ACTION_RESULT":
                return "border-emerald-500/20 bg-emerald-500/5 text-emerald-600 dark:text-emerald-400";
            default:
                return "border-[var(--accent)]/20 bg-[var(--accent)]/5 text-[var(--accent)]";
        }
    };

    return (
        <SharedPageContainer
            title="Thinking Trace"
            subtitle="Professional Agent Observation Platform"
            icon={Brain}
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
                        Trace Events: {traceEvents.length}
                    </span>
                </div>
            }
        >
            {traceEvents.length === 0 ? (
                <StatusPlaceholder
                    icon={Brain}
                    title="Awaiting agent cognition"
                    subtitle="Structured observation stream will appear here"
                />
            ) : (
                <div className="space-y-16 pl-10 pt-8">
                    {traceEvents.map((event) => (
                        <div key={event.id} className="relative group animate-in fade-in slide-in-from-bottom-8 duration-700">
                            {/* Timeline line */}
                            <div className="absolute -left-10 top-0 bottom-0 w-px bg-gradient-to-b from-[var(--accent)]/40 via-[var(--muted-foreground)]/10 to-transparent" />

                            <div className="flex flex-col gap-6">
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-4">
                                        {/* Agent Badge */}
                                        <span className="text-xs font-bold text-white px-2 py-0.5 rounded bg-[var(--accent)] shadow-sm uppercase tracking-wider">
                                            {formatAgentName(event.agent_name)}
                                        </span>

                                        {/* Type Badge */}
                                        <span className={`text-xs font-bold px-2 py-0.5 rounded border uppercase tracking-wider ${getEventStyles(event.event_type)}`}>
                                            {event.event_type}
                                        </span>

                                        <span className="text-[10px] font-bold text-[var(--muted-foreground)] opacity-40 uppercase tracking-[0.2em]">
                                            {new Date(event.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                                        </span>
                                    </div>
                                </div>

                                <div className={`pl-6 border-l-2 text-[var(--foreground)] leading-loose prose prose-sm max-w-none 
                                                prose-p:text-[var(--foreground)] prose-p:opacity-90 prose-p:text-lg
                                                prose-strong:text-[var(--accent)] prose-strong:font-black
                                                ${event.event_type === 'DELEGATION' ? 'italic opacity-80 border-amber-500/30' : 'border-[var(--accent)]/10'}`}>
                                    <Markdown content={event.content} />

                                    {!!event.metadata?.pretty_args && (
                                        <pre className="mt-4 p-4 rounded-xl bg-black/5 dark:bg-white/5 border border-black/10 dark:border-white/10 overflow-x-auto text-[13px] font-mono leading-relaxed">
                                            <code className="text-[var(--foreground)]">{event.metadata.pretty_args as string}</code>
                                        </pre>
                                    )}
                                </div>
                            </div>
                        </div>
                    ))}
                    <div ref={bottomRef} className="h-40" />
                </div>
            )}
        </SharedPageContainer>
    );
}

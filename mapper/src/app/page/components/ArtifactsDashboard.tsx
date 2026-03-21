"use client";

import React, { useMemo, useRef, useEffect, useState } from 'react';
import { useThoughts, AgentEvent } from '../../../context/ThoughtsContext';
import { SharedPageContainer } from './SharedPageContainer';
import { Package, Eye, Download, AlertTriangle, RefreshCw, FileText, Image as ImageIcon, CheckCircle2 } from 'lucide-react';
import { StatusPlaceholder } from './StatusPlaceholder';
import { formatAgentName } from '@/lib/utils';

export function ArtifactsDashboard() {
    const { events } = useThoughts();
    const bottomRef = useRef<HTMLDivElement>(null);
    const containerRef = useRef<HTMLDivElement>(null);
    const [isHovering, setIsHovering] = useState(false);

    // Filter artifact events
    const artifactEvents = useMemo(() => {
        return events.filter(e => e.event_type === "ARTIFACT");
    }, [events]);

    // Current/Latest Status
    const latestEvent = artifactEvents.length > 0 ? artifactEvents[artifactEvents.length - 1] : null;
    const latestMetadata = (latestEvent?.metadata || {}) as Record<string, any>;

    // Auto-scroll logic refined for consistency
    useEffect(() => {
        if (isHovering) return;
        if (bottomRef.current && artifactEvents.length > 0) {
            bottomRef.current.scrollIntoView({ behavior: 'auto', block: 'end' });
        }
    }, [artifactEvents.length, isHovering]);

    if (artifactEvents.length === 0) {
        return (
            <SharedPageContainer title="Artifacts Control" subtitle="Artifact Injection & Context Management" icon={Package}>
                <StatusPlaceholder 
                    icon={Package} 
                    title="No artifact activity detected" 
                    subtitle="Artifact loading and visibility logs will appear here when the agent interacts with images or files." 
                />
            </SharedPageContainer>
        );
    }

    return (
        <SharedPageContainer
            title="Artifacts Control"
            subtitle="Artifact Injection & Context Management"
            icon={Package}
            containerRef={containerRef}
            fullWidth
            fullHeight
            onMouseEnter={() => setIsHovering(true)}
            onMouseLeave={() => setIsHovering(false)}
            footerContent={
                <div className="flex items-center gap-4">
                    <div className={`px-3 py-1 rounded-full text-xs font-bold tracking-wider uppercase border transition-all duration-500
                        ${isHovering
                            ? 'bg-amber-500/10 text-amber-500 border-amber-500/20'
                            : 'bg-indigo-500/10 text-indigo-500 border-indigo-500/20 shadow-[0_0_15px_rgba(99,102,241,0.1)]'}`}>
                        {isHovering ? 'Manual Override' : 'System Managed'}
                    </div>
                    <div className="px-3 py-1 rounded-full text-xs font-bold tracking-wider uppercase border bg-indigo-500/10 text-indigo-500 border-indigo-500/20">
                        Active artifacts: {String(latestMetadata.total_blobs || 0)}
                    </div>
                </div>
            }
        >
            <div className="p-8 space-y-12 h-fit">
                {/* History Section (Now Chronological for Auto-scroll) */}
                <div className="space-y-6">
                    <div className="flex items-center justify-between">
                        <h4 className="text-sm font-black text-[var(--foreground)] uppercase tracking-widest flex items-center gap-2">
                            <span className="h-1 w-6 bg-[var(--accent)] rounded-full"></span>
                            Artifact Transaction History
                        </h4>
                    </div>

                    <div className="space-y-4">
                        {artifactEvents.map((event: AgentEvent) => {
                            const meta = (event.metadata || {}) as Record<string, any>;
                            return (
                                <div key={event.id} className="bg-[var(--background)] border border-[var(--muted-foreground)]/10 rounded-2xl p-6 hover:border-[var(--accent)]/30 transition-all group">
                                    <div className="flex items-start justify-between">
                                        <div className="flex items-center gap-4">
                                            <div className={`p-3 rounded-xl ${
                                                meta.load_artifacts ? 'bg-indigo-500/10 text-indigo-500' : 
                                                meta.reinjection ? 'bg-amber-500/10 text-amber-500' :
                                                'bg-[var(--accent)]/10 text-[var(--accent)]'
                                            }`}>
                                                {meta.load_artifacts ? <Download size={24} /> : 
                                                meta.reinjection ? <RefreshCw size={24} /> :
                                                <ImageIcon size={24} />}
                                            </div>
                                            <div>
                                                <div className="flex items-center gap-3 mb-1">
                                                    <span className="text-xs font-black text-white px-2 py-0.5 rounded bg-[var(--accent)] uppercase tracking-wider">
                                                        {formatAgentName(event.agent_name)}
                                                    </span>
                                                    <span className="text-[10px] font-bold text-[var(--muted-foreground)] uppercase tracking-widest">
                                                        {new Date(event.timestamp).toLocaleTimeString()}
                                                    </span>
                                                </div>
                                                <h3 className="text-lg font-black text-[var(--foreground)]">
                                                    {String(event.content)}
                                                </h3>
                                            </div>
                                        </div>
                                        
                                        {meta.total_blobs !== undefined && (
                                            <div className="flex flex-col items-end">
                                                <div className="text-2xl font-black text-indigo-500">{String(meta.total_blobs)}</div>
                                                <div className="text-[10px] font-bold text-[var(--muted-foreground)] uppercase tracking-widest">Blobs Visible</div>
                                            </div>
                                        )}
                                    </div>

                                    {/* Details List */}
                                    <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4">
                                        {/* Left side: Blob details */}
                                        {(meta.inline_blobs || meta.tool_response_blobs) && (
                                            <div className="space-y-2">
                                                <div className="text-[10px] font-black uppercase text-[var(--muted-foreground)] tracking-widest">Visibility Details</div>
                                                <div className="bg-black/5 dark:bg-white/5 rounded-xl p-4 font-mono text-[11px] space-y-1 max-h-40 overflow-y-auto custom-scrollbar">
                                                    {Array.isArray(meta.inline_blobs) && (meta.inline_blobs as any[]).map((b: any, idx: number) => (
                                                        <div key={`inline-${idx}`} className="flex items-center gap-2 text-indigo-500">
                                                            <ImageIcon size={10} />
                                                            {String(b)}
                                                        </div>
                                                    ))}
                                                    {Array.isArray(meta.tool_response_blobs) && (meta.tool_response_blobs as any[]).map((b: any, idx: number) => (
                                                        <div key={`tool-${idx}`} className="flex items-center gap-2 text-amber-500">
                                                            <FileText size={10} />
                                                            {String(b)}
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>
                                        )}

                                        {/* Right side: Tool context */}
                                        {Array.isArray(meta.requested_names) && (
                                            <div className="space-y-2">
                                                <div className="text-[10px] font-black uppercase text-[var(--muted-foreground)] tracking-widest">Requested Artifacts</div>
                                                <div className="bg-black/5 dark:bg-white/5 rounded-xl p-4 font-mono text-[11px] grid grid-cols-1 gap-1 max-h-40 overflow-y-auto custom-scrollbar">
                                                    {(meta.requested_names as any[]).map((name: any, idx: number) => (
                                                        <div key={`req-${idx}`} className="flex items-center gap-2 text-emerald-500">
                                                            <div className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
                                                            {String(name)}
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            );
                        })}
                        <div ref={bottomRef} className="h-40" />
                    </div>
                </div>
            </div>
        </SharedPageContainer>
    );
}

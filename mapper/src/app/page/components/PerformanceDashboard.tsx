"use client";

import React, { useMemo } from 'react';
import { useThoughts } from '../../../context/ThoughtsContext';
import { SharedPageContainer } from './SharedPageContainer';
import { Activity, Zap, Cpu, Clock, Layers, Hash } from 'lucide-react';
import { StatusPlaceholder } from './StatusPlaceholder';

export function PerformanceDashboard() {
    const { events } = useThoughts();

    // Aggregate metrics from all events
    const metricsHistory = useMemo(() => {
        return events
            .filter(e => e.metadata?.latency_s !== undefined && e.metadata?.latency_s !== null)
            .map(e => ({
                id: e.id,
                agent: e.agent_name,
                timestamp: e.timestamp,
                latency: (e.metadata.latency_s as number) || 0,
                promptTokens: (e.metadata.prompt_tokens as number) || 0,
                completionTokens: (e.metadata.completion_tokens as number) || 0,
                totalTokens: (e.metadata.total_tokens as number) || 0,
                cachedTokens: (e.metadata.cached_tokens as number) || 0,
                provider: (e.metadata.provider as string) || 'unknown'
            }));
    }, [events]);

    const totals = useMemo(() => {
        return metricsHistory.reduce((acc, curr) => ({
            totalTokens: acc.totalTokens + curr.totalTokens,
            totalPrompt: acc.totalPrompt + curr.promptTokens,
            totalCompletion: acc.totalCompletion + curr.completionTokens,
            totalCached: acc.totalCached + curr.cachedTokens,
            avgLatency: acc.avgLatency + curr.latency,
            maxLatency: Math.max(acc.maxLatency, curr.latency),
            count: acc.count + 1
        }), { totalTokens: 0, totalPrompt: 0, totalCompletion: 0, totalCached: 0, avgLatency: 0, maxLatency: 0, count: 0 });
    }, [metricsHistory]);

    const stats = [
        { label: 'Total Tokens', value: totals.totalTokens.toLocaleString(), icon: Hash, color: 'text-indigo-500' },
        { label: 'Avg Latency', value: `${(totals.avgLatency / (totals.count || 1)).toFixed(2)}s`, icon: Clock, color: 'text-amber-500' },
        { label: 'Max Latency', value: `${totals.maxLatency.toFixed(2)}s`, icon: Zap, color: 'text-rose-500' },
        { label: 'Iterations', value: totals.count, icon: Activity, color: 'text-emerald-500' },
        { label: 'Cache Hit Rate', value: totals.totalTokens > 0 ? `${((totals.totalCached / totals.totalTokens) * 100).toFixed(1)}%` : '0%', icon: Layers, color: 'text-blue-500' },
        { label: 'Output Velocity', value: totals.avgLatency > 0 ? `${(totals.totalCompletion / totals.avgLatency).toFixed(1)} t/s` : '0 t/s', icon: Cpu, color: 'text-purple-500' },
    ];

    if (metricsHistory.length === 0) {
        return (
            <SharedPageContainer title="Performance Dashboard" subtitle="Real-time Agent Telemetry & Resource Usage" icon={Activity}>
                <StatusPlaceholder 
                    icon={Activity} 
                    title="No performance data available" 
                    subtitle="Metrics will appear once the agent starts interacting with the system." 
                />
            </SharedPageContainer>
        );
    }

    return (
        <SharedPageContainer
            title="Performance Dashboard"
            subtitle="Real-time Agent Telemetry & Resource Usage"
            icon={Activity}
            fullWidth
            fullHeight
        >
            <div className="p-8 space-y-12">
                {/* Stats Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-6">
                    {stats.map((stat, i) => (
                        <div key={i} className="bg-[var(--background)] border border-[var(--muted-foreground)]/10 rounded-2xl p-6 shadow-sm hover:shadow-md transition-all group overflow-hidden relative">
                            <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:scale-110 transition-transform">
                                <stat.icon size={48} />
                            </div>
                            <div className={`p-2 rounded-lg bg-current/10 ${stat.color} w-fit mb-4`}>
                                <stat.icon size={20} />
                            </div>
                            <div className="text-2xl font-black text-[var(--foreground)] mb-1">
                                {stat.value}
                            </div>
                            <div className="text-[10px] font-bold text-[var(--muted-foreground)] uppercase tracking-widest">
                                {stat.label}
                            </div>
                        </div>
                    ))}
                </div>

                {/* History Table */}
                <div className="space-y-6">
                    <div className="flex items-center justify-between">
                        <h4 className="text-sm font-black text-[var(--foreground)] uppercase tracking-widest flex items-center gap-2">
                            <span className="h-1 w-6 bg-[var(--accent)] rounded-full"></span>
                            Recent Iterations
                        </h4>
                        <div className="text-[10px] font-bold text-[var(--muted-foreground)] uppercase tracking-widest bg-[var(--muted-foreground)]/5 px-3 py-1 rounded-full border border-[var(--muted-foreground)]/10">
                            Session Events: {metricsHistory.length}
                        </div>
                    </div>

                    <div className="overflow-hidden rounded-2xl border border-[var(--muted-foreground)]/10 bg-[var(--background)] shadow-sm">
                        <table className="w-full text-left border-collapse">
                            <thead>
                                <tr className="bg-[var(--muted-foreground)]/5">
                                    <th className="px-6 py-4 text-[10px] font-black text-[var(--muted-foreground)] uppercase tracking-widest border-b border-[var(--muted-foreground)]/10">Time</th>
                                    <th className="px-6 py-4 text-[10px] font-black text-[var(--muted-foreground)] uppercase tracking-widest border-b border-[var(--muted-foreground)]/10">Agent</th>
                                    <th className="px-6 py-4 text-[10px] font-black text-[var(--muted-foreground)] uppercase tracking-widest border-b border-[var(--muted-foreground)]/10 text-right">Prompt</th>
                                    <th className="px-6 py-4 text-[10px] font-black text-[var(--muted-foreground)] uppercase tracking-widest border-b border-[var(--muted-foreground)]/10 text-right">Output</th>
                                    <th className="px-6 py-4 text-[10px] font-black text-[var(--muted-foreground)] uppercase tracking-widest border-b border-[var(--muted-foreground)]/10 text-right">Total</th>
                                    <th className="px-6 py-4 text-[10px] font-black text-[var(--muted-foreground)] uppercase tracking-widest border-b border-[var(--muted-foreground)]/10 text-right">Latency</th>
                                    <th className="px-6 py-4 text-[10px] font-black text-[var(--muted-foreground)] uppercase tracking-widest border-b border-[var(--muted-foreground)]/10 text-center">Provider</th>
                                </tr>
                            </thead>
                            <tbody>
                                {metricsHistory.slice().reverse().map((m, i) => (
                                    <tr key={m.id} className="hover:bg-[var(--foreground)]/5 transition-colors border-b border-[var(--muted-foreground)]/5 last:border-0 group">
                                        <td className="px-6 py-4 font-mono text-[11px] text-[var(--muted-foreground)]">
                                            {new Date(m.timestamp).toLocaleTimeString()}
                                        </td>
                                        <td className="px-6 py-4">
                                            <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-[var(--accent)]/10 text-[var(--accent)] uppercase tracking-wider border border-[var(--accent)]/10">
                                                {m.agent}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 text-right tabular-nums text-xs font-medium">{m.promptTokens}</td>
                                        <td className="px-6 py-4 text-right tabular-nums text-xs font-medium text-indigo-500">{m.completionTokens}</td>
                                        <td className="px-6 py-4 text-right tabular-nums text-xs font-bold">{m.totalTokens}</td>
                                        <td className="px-6 py-4 text-right tabular-nums text-xs font-bold text-amber-500">
                                            {m.latency.toFixed(2)}s
                                        </td>
                                        <td className="px-6 py-4 text-center">
                                            <span className="text-[9px] font-black bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900 px-2 py-0.5 rounded uppercase tracking-tighter">
                                                {m.provider}
                                            </span>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </SharedPageContainer>
    );
}

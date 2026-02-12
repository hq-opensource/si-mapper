"use client";

import React from 'react';
import { useThoughts } from '../../../context/ThoughtsContext';
import { Database, Box, Info } from 'lucide-react';
import { SharedPageContainer } from './SharedPageContainer';
import { StatusPlaceholder } from './StatusPlaceholder';

export function StateWindow() {
    const { data } = useThoughts();

    const dataEntries = Object.entries(data || {});

    return (
        <SharedPageContainer
            title="Session State Variables"
            subtitle="Real-time Agent Memory Inspection"
            icon={Database}
            fullWidth
            fullHeight
        >
            {dataEntries.length === 0 ? (
                <StatusPlaceholder
                    icon={Database}
                    title="No variables tracked"
                    subtitle="State variables will appear here as the agent works"
                />
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 p-4">
                    {dataEntries.map(([key, value]) => (
                        <div
                            key={key}
                            className="bg-[var(--background)] border border-[var(--muted-foreground)]/20 rounded-2xl p-6 shadow-sm hover:shadow-md transition-shadow duration-300 group overflow-hidden relative"
                        >
                            <div className="absolute top-0 right-0 p-3 opacity-5 group-hover:opacity-10 transition-opacity">
                                <Box size={60} />
                            </div>

                            <div className="flex items-center gap-2 mb-4">
                                <div className="p-2 rounded-lg bg-[var(--accent)]/10 text-[var(--accent)]">
                                    <Database size={20} />
                                </div>
                                <h3 className="text-base font-black uppercase tracking-wider text-[var(--foreground)] truncate">
                                    {key}
                                </h3>
                            </div>

                            <div className="bg-black/5 dark:bg-white/5 rounded-xl p-4 font-mono text-[10px] sm:text-xs overflow-auto border border-black/5 dark:border-white/5 shadow-inner max-h-[500px] custom-scrollbar">
                                <pre className="text-[var(--foreground)] leading-tight whitespace-pre">
                                    {(() => {
                                        if (typeof value === 'object' && value !== null) {
                                            return JSON.stringify(value, null, 2);
                                        }
                                        if (typeof value === 'string') {
                                            const trimmed = value.trim();
                                            if ((trimmed.startsWith('{') && trimmed.endsWith('}')) || (trimmed.startsWith('[') && trimmed.endsWith(']'))) {
                                                try {
                                                    const parsed = JSON.parse(trimmed);
                                                    return JSON.stringify(parsed, null, 2);
                                                } catch {
                                                    return value;
                                                }
                                            }
                                            return value;
                                        }
                                        return String(value);
                                    })()}
                                </pre>
                            </div>

                            <div className="mt-5 flex items-center gap-2 text-xs font-bold text-[var(--muted-foreground)] uppercase tracking-tight opacity-70">
                                <Info size={12} />
                                <span>TYPE: {typeof value === 'string' && (() => { try { JSON.parse(value); return true; } catch { return false; } })() ? 'json' : typeof value}</span>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </SharedPageContainer>
    );
}

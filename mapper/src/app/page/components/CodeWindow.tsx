"use client";

import React, { useState, useEffect } from 'react';
import { useThoughts } from '../../../context/ThoughtsContext';
import { Code2 } from 'lucide-react';
import { SharedPageContainer } from './SharedPageContainer';
import { StatusPlaceholder } from './StatusPlaceholder';

interface SnapshotEntry {
    label: string;
    code: string;
    iteration: number;
    status: 'generated' | 'fix' | 'validated';
}

export function CodeWindow() {
    const { data } = useThoughts();
    const snapshots = (data?.ontology_code_snapshots ?? []) as SnapshotEntry[];
    const [selectedIdx, setSelectedIdx] = useState<number>(0);

    // Auto-advance to latest snapshot when new ones arrive
    useEffect(() => {
        if (snapshots.length > 0) {
            setSelectedIdx(snapshots.length - 1);
        }
    }, [snapshots.length]);

    return (
        <SharedPageContainer
            title="Ontology Code"
            subtitle="ASHRAE 223P Generated Source"
            icon={Code2}
            fullWidth
            fullHeight
        >
            {snapshots.length === 0 ? (
                <StatusPlaceholder
                    icon={Code2}
                    title="No ontology code generated yet"
                    subtitle="Code snapshots will appear here after ontology generation"
                />
            ) : (
                <div className="flex flex-col h-full">
                    {/* Version selector pill row */}
                    <div className="flex items-center gap-2 p-4 border-b border-[var(--muted-foreground)]/20 flex-wrap">
                        {snapshots.map((snap, idx) => (
                            <button
                                key={idx}
                                onClick={() => setSelectedIdx(idx)}
                                className={`
                                    px-3 py-1.5 rounded-lg text-xs font-bold transition-all duration-200
                                    ${selectedIdx === idx
                                        ? 'bg-[var(--accent)]/15 text-[var(--accent)] border border-[var(--accent)]/30'
                                        : 'text-[var(--muted-foreground)] hover:text-[var(--foreground)] hover:bg-[var(--foreground)]/5 border border-transparent'
                                    }
                                `}
                            >
                                {snap.label}
                                {snap.status === 'validated' && (
                                    <span className="ml-1.5 inline-block w-2 h-2 rounded-full bg-green-500" />
                                )}
                            </button>
                        ))}
                    </div>

                    {/* Code display */}
                    <div className="flex-1 overflow-auto p-4">
                        <pre className="whitespace-pre-wrap font-mono text-sm text-[var(--foreground)] leading-relaxed">
                            <code>{snapshots[selectedIdx]?.code ?? ''}</code>
                        </pre>
                    </div>
                </div>
            )}
        </SharedPageContainer>
    );
}

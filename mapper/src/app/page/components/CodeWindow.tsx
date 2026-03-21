"use client";

import React, { useState, useEffect } from 'react';
import { useThoughts } from '../../../context/ThoughtsContext';
import { Code2, Database } from 'lucide-react';
import { SharedPageContainer } from './SharedPageContainer';
import { StatusPlaceholder } from './StatusPlaceholder';

interface SnapshotEntry {
    label: string;
    code: string;
    iteration: number;
    status: 'generated' | 'fix' | 'validated';
}

interface CodeWindowProps {
    type: 'python' | 'ttl';
}

export function CodeWindow({ type }: CodeWindowProps) {
    const { data } = useThoughts();
    const snapshots = ((type === 'python' 
        ? data?.python_code_snapshots 
        : data?.ttl_code_snapshots) ?? []) as SnapshotEntry[];
    const [selectedIdx, setSelectedIdx] = useState<number>(0);

    // Auto-advance to latest snapshot when new ones arrive
    useEffect(() => {
        if (snapshots.length > 0) {
            setSelectedIdx(snapshots.length - 1);
        }
    }, [snapshots.length]);

    return (
        <SharedPageContainer
            title={type === 'python' ? "Python Source" : "Ontology TTL"}
            subtitle={type === 'python' ? "ontology.py Generation" : "ASHRAE 223P Serialized Output"}
            icon={type === 'python' ? Code2 : Database}
            fullWidth
            fullHeight
        >
            {snapshots.length === 0 ? (
                <StatusPlaceholder
                    icon={type === 'python' ? Code2 : Database}
                    title={type === 'python' ? "No Python code generated yet" : "No TTL code generated yet"}
                    subtitle={type === 'python' ? "Code snapshots will appear here during generation" : "TTL versions will appear here after validation"}
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

"use client";

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Code2, Database } from 'lucide-react';
import { SharedPageContainer } from './SharedPageContainer';
import { StatusPlaceholder } from './StatusPlaceholder';
import { useWorkspace } from '@/context/WorkspaceContext';

interface FileEntry {
    id: string;
    name: string;
    date: number; // unix timestamp in seconds
}

interface CodeWindowProps {
    type: 'python' | 'ttl';
}

const POLL_INTERVAL = 3000;
const FOLDER: Record<string, string> = { python: 'python', ttl: 'ttl' };
const EXT: Record<string, string> = { python: '.py', ttl: '.ttl' };
const LATEST: Record<string, string> = { python: 'latest_ontology.py', ttl: 'latest_ontology.ttl' };

function formatLabel(filename: string): string {
    const match = filename.match(/ontology_(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})/);
    if (!match) return filename;
    const [, year, month, day, hour, min] = match;
    const d = new Date(+year, +month - 1, +day, +hour, +min);
    return d.toLocaleString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', hour12: false });
}

export function CodeWindow({ type }: CodeWindowProps) {
    const [files, setFiles] = useState<FileEntry[]>([]);
    const [selectedId, setSelectedId] = useState<string | null>(null);
    const [content, setContent] = useState<string>('');
    const [loadingContent, setLoadingContent] = useState(false);
    const fileCountRef = useRef(0);

    const { activeProject, activeSystem } = useWorkspace();

    const buildScopeParams = useCallback(() => {
        const params = new URLSearchParams();
        if (activeProject) params.set('project', activeProject.folder_path);
        if (activeSystem) params.set('system', activeSystem.folder_path);
        return params;
    }, [activeProject, activeSystem]);

    const fetchFiles = useCallback(async () => {
        try {
            const params = buildScopeParams();
            params.set('id', FOLDER[type]);
            const res = await fetch(`/api/files?${params}`);
            if (!res.ok) return;
            const items: FileEntry[] = await res.json();
            const versioned = items
                .filter(f => f.name !== LATEST[type] && f.name.endsWith(EXT[type]))
                .sort((a, b) => a.date - b.date); // oldest → newest left to right

            if (versioned.length > fileCountRef.current && versioned.length > 0) {
                setSelectedId(versioned[versioned.length - 1].id);
            }
            fileCountRef.current = versioned.length;
            setFiles(versioned);
        } catch {
            // silent — folder may not exist yet
        }
    }, [type, buildScopeParams]);

    // Reset file list when project/system context changes
    useEffect(() => {
        setFiles([]);
        setSelectedId(null);
        setContent('');
        fileCountRef.current = 0;
    }, [activeProject?.id, activeSystem?.id]);

    useEffect(() => {
        fetchFiles();
        const timer = setInterval(fetchFiles, POLL_INTERVAL);
        return () => clearInterval(timer);
    }, [fetchFiles]);

    useEffect(() => {
        if (!selectedId) return;
        setLoadingContent(true);
        const params = buildScopeParams();
        params.set('id', selectedId);
        fetch(`/api/files/view?${params}`)
            .then(r => r.text())
            .then(text => { setContent(text); setLoadingContent(false); })
            .catch(() => setLoadingContent(false));
    }, [selectedId, buildScopeParams]);

    const icon = type === 'python' ? Code2 : Database;

    return (
        <SharedPageContainer
            title={type === 'python' ? "Python Source" : "Ontology TTL"}
            subtitle={type === 'python' ? "ontology.py Generation" : "ASHRAE 223P Serialized Output"}
            icon={icon}
            fullWidth
            fullHeight
        >
            {files.length === 0 ? (
                <StatusPlaceholder
                    icon={icon}
                    title={type === 'python' ? "No Python code generated yet" : "No TTL code generated yet"}
                    subtitle={type === 'python' ? "Code snapshots will appear here during generation" : "TTL versions will appear here after validation"}
                />
            ) : (
                <div className="flex flex-col h-full">
                    <div className="flex items-center gap-2 p-4 border-b border-[var(--muted-foreground)]/20 flex-wrap">
                        {files.map((file, idx) => {
                            const isLatest = idx === files.length - 1;
                            const isSelected = file.id === selectedId;
                            return (
                                <button
                                    key={file.id}
                                    onClick={() => setSelectedId(file.id)}
                                    className={`
                                        px-3 py-1.5 rounded-lg text-xs font-bold transition-all duration-200
                                        ${isSelected
                                            ? 'bg-[var(--accent)]/15 text-[var(--accent)] border border-[var(--accent)]/30'
                                            : 'text-[var(--muted-foreground)] hover:text-[var(--foreground)] hover:bg-[var(--foreground)]/5 border border-transparent'
                                        }
                                    `}
                                >
                                    {formatLabel(file.name)}
                                    {isLatest && (
                                        <span className="ml-1.5 inline-block w-2 h-2 rounded-full bg-green-500" />
                                    )}
                                </button>
                            );
                        })}
                    </div>

                    <div className="flex-1 overflow-auto p-4">
                        {loadingContent ? (
                            <div className="text-[var(--muted-foreground)] text-sm">Loading...</div>
                        ) : (
                            <pre className="whitespace-pre-wrap font-mono text-sm text-[var(--foreground)] leading-relaxed">
                                <code>{content}</code>
                            </pre>
                        )}
                    </div>
                </div>
            )}
        </SharedPageContainer>
    );
}

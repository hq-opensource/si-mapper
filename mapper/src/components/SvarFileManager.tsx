"use client";

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Filemanager, WillowDark } from "@svar-ui/react-filemanager";
import "@svar-ui/react-filemanager/style.css";

// Interface for my API objects
interface FileItem {
    id: string; // The path
    value: string; // The name (SVAR uses value)
    size?: number;
    date?: Date;
    type: 'file' | 'folder';
    open?: boolean;
}

export function SvarFileManager() {
    const [data, setData] = useState<FileItem[]>([]);
    const [currentPath, setCurrentPath] = useState('/');
    const apiRef = useRef<any>(null);

    const fetchFiles = useCallback(async (path: string) => {
        try {
            const response = await fetch(`/api/files?id=${encodeURIComponent(path)}`);
            if (!response.ok) throw new Error('Failed to fetch files');
            const result = await response.json();
            
            // Map the data to SVAR format
            const mappedData = result.map((item: any) => ({
                ...item,
                date: item.date ? new Date(item.date * 1000) : undefined // Convert Unix to Date object as SVAR prefers
            }));
            
            setData(mappedData);
        } catch (error) {
            console.error('Error fetching files:', error);
        }
    }, []);

    useEffect(() => {
        fetchFiles(currentPath);
    }, [currentPath, fetchFiles]);

    // Generic Action Handler
    // SVAR React File Manager uses onAction for many operations
    const handleAction = async (ev: any) => {
        const { action, id, value, item } = ev;
        console.log("SVAR Action:", action, id, value);

        switch (action) {
            case "open":
                if (item?.type === 'folder') {
                    setCurrentPath(id);
                }
                break;
            case "remove":
                const idsToRemove = Array.isArray(id) ? id.join(',') : id;
                await fetch('/api/files', {
                    method: 'DELETE',
                    body: new URLSearchParams({ ids: idsToRemove }),
                });
                fetchFiles(currentPath);
                break;
            case "create-folder":
                // Value is the folder name, currentPath is the target
                await fetch('/api/files', {
                    method: 'POST',
                    body: new URLSearchParams({ target: currentPath, name: value }),
                });
                fetchFiles(currentPath);
                break;
            case "rename":
                await fetch('/api/files', {
                    method: 'PUT',
                    body: new URLSearchParams({ id, value }),
                });
                fetchFiles(currentPath);
                break;
            case "upload-file":
                // Standard SVAR upload event usually provides the file in ev
                // If it's a manual trigger, we would handle it differently
                if (ev.files) {
                    for (const file of ev.files) {
                        const formData = new FormData();
                        formData.append('file', file);
                        formData.append('target', currentPath);
                        await fetch('/api/files/upload', {
                            method: 'POST',
                            body: formData,
                        });
                    }
                    fetchFiles(currentPath);
                }
                break;
        }
    };

    return (
        <div className="w-full h-full min-h-[500px] bg-[var(--background)] rounded-3xl border border-[var(--muted-foreground)]/10 overflow-hidden shadow-[0_30px_60px_-15px_rgba(0,0,0,0.3)] transition-all duration-700 hover:border-[var(--accent)]/30 group relative">
            {/* Glossy Overlay for Premium Look */}
            <div className="absolute inset-0 bg-gradient-to-tr from-[var(--accent)]/[0.03] to-transparent pointer-events-none z-10" />
            
            <WillowDark>
                <div className="w-full h-full p-2 bg-[#1a1c1e]"> 
                    <Filemanager 
                        data={data}
                        onAction={handleAction}
                        init={(api) => { apiRef.current = api; }}
                    />
                </div>
            </WillowDark>

            <style jsx global>{`
                /* Fine-tune SVAR styles to match project's premium aesthetic */
                .svar-filemanager {
                    border: none !important;
                    background: transparent !important;
                }
                .svar-filemanager-toolbar {
                    background: transparent !important;
                    border-bottom: 1px solid rgba(255, 255, 255, 0.05) !important;
                    padding: 0.75rem !important;
                }
                .svar-filemanager-item {
                    border-radius: 8px !important;
                    margin: 2px 0 !important;
                    transition: all 0.2s ease !important;
                }
                .svar-filemanager-item:hover {
                    background: rgba(var(--accent-rgb), 0.1) !important;
                }
                .svar-filemanager-tree {
                    border-right: 1px solid rgba(255, 255, 255, 0.05) !important;
                }
            `}</style>
        </div>
    );
}

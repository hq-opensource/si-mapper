"use client";

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Filemanager, Willow, WillowDark } from "@svar-ui/react-filemanager";
import "@svar-ui/react-filemanager/style.css";

// Interface for my API objects
interface FileItem {
    id: string; // The path
    pId?: string; // Parent ID
    value: string; // The name (SVAR uses value)
    size?: number;
    date?: Date;
    type: 'file' | 'folder';
    open?: boolean;
}

export function SvarFileManager() {
    const [data, setData] = useState<FileItem[]>([]);
    const [theme, setTheme] = useState<'light' | 'dark'>('light');
    const apiRef = useRef<any>(null);

    const fetchTree = useCallback(async () => {
        try {
            const response = await fetch(`/api/files?tree=true`);
            if (!response.ok) throw new Error('Failed to fetch tree');
            const result = await response.json();
            
            // Map the data to SVAR format
            const mappedData = result.map((item: any) => ({
                ...item,
                date: item.date ? new Date(item.date * 1000) : undefined 
            }));
            
            setData(mappedData);
        } catch (error) {
            console.error('Error fetching tree:', error);
        }
    }, []);

    useEffect(() => {
        const checkTheme = () => {
            const currentTheme = document.documentElement.classList.contains('dark') ? 'dark' : 'light';
            setTheme(currentTheme);
        };
        checkTheme();
        const observer = new MutationObserver(checkTheme);
        observer.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] });
        return () => observer.disconnect();
    }, []);

    useEffect(() => {
        fetchTree();
    }, [fetchTree]);

    // Generic Action Handler
    const handleAction = async (ev: any) => {
        const { action, id, value, item } = ev;
        console.log("SVAR Action:", action, id, value);

        switch (action) {
            case "remove":
                const idsToRemove = Array.isArray(id) ? id.join(',') : id;
                await fetch('/api/files', {
                    method: 'DELETE',
                    body: new URLSearchParams({ ids: idsToRemove }),
                });
                fetchTree();
                break;
            case "rename":
                await fetch('/api/files', {
                    method: 'PUT',
                    body: new URLSearchParams({ id, value }),
                });
                fetchTree();
                break;
            case "upload-file":
                if (ev.files) {
                    const currentPath = apiRef.current?.getState().path || '/';
                    for (const file of ev.files) {
                        const formData = new FormData();
                        formData.append('file', file);
                        formData.append('target', currentPath);
                        await fetch('/api/files/upload', {
                            method: 'POST',
                            body: formData,
                        });
                    }
                    fetchTree();
                }
                break;
        }
    };

    const ThemeProvider = theme === 'dark' ? WillowDark : Willow;

    return (
        <div className="w-full h-full flex flex-row bg-white overflow-hidden group relative">
            
            {/* Explorer Pane */}
            <div className={`flex-1 flex flex-col transition-all duration-500`}>
                <ThemeProvider>
                    <div className="w-full h-full bg-white"> 
                        <Filemanager 
                            data={data}
                            onAction={handleAction}
                            init={(api) => { 
                                apiRef.current = api;
                                // Set grid view and info panel by default
                                setTimeout(() => {
                                    api.setState({ view: "grid", info: true });
                                }, 100);
                            }}
                        />
                    </div>
                </ThemeProvider>
            </div>

            <style jsx global>{`
                /* Target the ghost uploader that shows "Choose Files" */
                .svar-uploader-input, 
                .svar-filemanager-uploader,
                input[type="file"] {
                    display: none !important;
                }
                
                /* HIDE THE TOOLBAR VIEW OPTIONS (EYE ICON AND VIEW SWITCHERS) */
                /* These are usually the last buttons on the toolbar */
                .svar-filemanager-toolbar button[title="List view"],
                .svar-filemanager-toolbar button[title="Icons view"],
                .svar-filemanager-toolbar button[title="Cards view"],
                .svar-filemanager-toolbar button[title="Show info"] {
                    display: none !important;
                }
                /* If titles are translated or different, we can also target by icon if classes exist */
                /* For SVAR, they often use these classes: */
                .svar-filemanager-v-list, 
                .svar-filemanager-v-grid, 
                .svar-filemanager-v-cards,
                .svar-filemanager-i-toggle {
                    display: none !important;
                }

                /* Ensure the Filemanager container fills the space and has a distinct look */
                .svar-filemanager {
                    border: none !important;
                    background: white !important;
                    display: flex !important;
                    flex-flow: column nowrap !important;
                    height: 100% !important;
                    width: 100% !important;
                    flex: 1 1 0% !important;
                }
                
                .svar-filemanager-toolbar {
                    background: white !important;
                    border-bottom: 1px solid rgba(0, 0, 0, 0.05) !important;
                    padding: 0.75rem 1.5rem !important;
                    color: #0f172a !important;
                }

                .svar-filemanager-body {
                    display: flex !important;
                    flex-direction: row !important;
                    flex: 1 1 auto !important;
                    height: 100% !important;
                    min-height: 0 !important;
                }

                .svar-filemanager-tree {
                    width: 280px !important;
                    min-width: 280px !important;
                    border-right: 1px solid rgba(0, 0, 0, 0.05) !important;
                    background: #f8fafc !important;
                    padding: 0 !important;
                }

                .svar-filemanager-content {
                    flex: 1 1 auto !important;
                    background: white !important;
                    display: flex !important;
                    flex-direction: column !important;
                    height: 100% !important;
                }

                .svar-filemanager-list, .svar-filemanager-grid {
                    flex: 1 1 auto !important;
                    height: 100% !important;
                    overflow-y: auto !important;
                    background: white !important;
                }

                /* Selection & Item Styling */
                .svar-filemanager-item {
                    border-radius: 8px !important;
                    transition: all 0.2s ease !important;
                }
                .svar-filemanager-item:hover {
                    background: rgba(var(--accent-rgb), 0.05) !important;
                }
                .svar-filemanager-item.svar-filemanager-selected {
                    background: rgba(var(--accent-rgb), 0.1) !important;
                    border-left: 3px solid var(--accent) !important;
                }

                /* Custom Scrollbar */
                ::-webkit-scrollbar {
                    width: 6px;
                }
                ::-webkit-scrollbar-thumb {
                    background: rgba(var(--accent-rgb), 0.1);
                    border-radius: 10px;
                }
                ::-webkit-scrollbar-thumb:hover {
                    background: rgba(var(--accent-rgb), 0.2);
                }

                .svar-filemanager-breadcrumb {
                    background: white !important;
                    padding: 0.5rem 1.5rem !important;
                }

                /* Font fixes */
                .svar-filemanager * {
                    font-family: inherit !important;
                    color: inherit;
                }

                /* Labeling the Upload functionality if needed */
                .svar-filemanager-tree::before {
                    content: "Resource Explorer";
                    display: block;
                    padding: 1.5rem 1.5rem 0.5rem 1.5rem;
                    font-size: 10px;
                    font-weight: 800;
                    text-transform: uppercase;
                    letter-spacing: 0.1em;
                    color: var(--muted-foreground);
                    opacity: 0.6;
                }

                /* Ensure SVAR's native info sidebar looks high-end */
                .svar-filemanager-info {
                    border-left: 1px solid rgba(0, 0, 0, 0.05) !important;
                    background: #f8fafc !important;
                    width: 320px !important;
                }
            `}</style>
        </div>
    );
}

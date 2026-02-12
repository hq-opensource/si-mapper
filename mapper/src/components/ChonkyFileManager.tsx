"use client";

import React, { useCallback, useEffect, useState, useMemo } from 'react';
import {
    Folder,
    ChevronRight,
    Upload,
    Trash2,
    FolderPlus,
    FileText,
    RefreshCw
} from 'lucide-react';
import { ConfirmationDialog } from './ConfirmationDialog';
import { PromptDialog } from './PromptDialog';

interface FileItem {
    id: string;
    name: string;
    size?: number;
    date?: number;
    type: 'file' | 'folder';
}

export function ChonkyFileManager() {
    const [files, setFiles] = useState<FileItem[]>([]);
    const [currentPath, setCurrentPath] = useState('/');
    const [isLoading, setIsLoading] = useState(false);
    const uploadInputRef = React.useRef<HTMLInputElement>(null);

    // Dialog state
    const [deleteDialog, setDeleteDialog] = useState<{ isOpen: boolean; id: string; name: string }>({
        isOpen: false, id: '', name: ''
    });
    const [isPromptOpen, setIsPromptOpen] = useState(false);

    const fetchFiles = useCallback(async (path: string) => {
        setIsLoading(true);
        try {
            const response = await fetch(`/api/files?id=${encodeURIComponent(path)}`);
            if (!response.ok) throw new Error('Failed to fetch files');
            const data = await response.json();
            setFiles(data);
        } catch (error) {
            console.error('Error fetching files:', error);
        } finally {
            setIsLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchFiles(currentPath);
    }, [currentPath, fetchFiles]);

    const folderChain = useMemo(() => {
        const parts = currentPath.split('/').filter(Boolean);
        const chain = [{ id: '/', name: 'Uploads' }];
        let cumulativePath = '';
        parts.forEach(part => {
            cumulativePath += `/${part}`;
            chain.push({ id: cumulativePath, name: part });
        });
        return chain;
    }, [currentPath]);

    const handleNavigate = (path: string) => {
        setCurrentPath(path);
    };

    const handleCreateFolder = async (name: string) => {
        try {
            const response = await fetch('/api/files', {
                method: 'POST',
                body: new URLSearchParams({ target: currentPath, name }),
            });
            if (response.ok) fetchFiles(currentPath);
        } catch (error) {
            console.error('Create folder error:', error);
        }
    };

    const handleDelete = async () => {
        const { id } = deleteDialog;
        try {
            const response = await fetch('/api/files', {
                method: 'DELETE',
                body: new URLSearchParams({ ids: id }),
            });
            if (response.ok) fetchFiles(currentPath);
        } catch (error) {
            console.error('Delete error:', error);
        }
    };

    const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
        const uploadedFiles = event.target.files;
        if (!uploadedFiles || uploadedFiles.length === 0) return;

        const formData = new FormData();
        formData.append('file', uploadedFiles[0]);
        formData.append('target', currentPath);

        try {
            const response = await fetch('/api/files/upload', {
                method: 'POST',
                body: formData,
            });
            if (response.ok) fetchFiles(currentPath);
        } catch (error) {
            console.error('Upload error:', error);
        }
        if (uploadInputRef.current) uploadInputRef.current.value = '';
    };

    return (
        <div className="flex flex-col h-full text-[var(--foreground)]">
            {/* Toolbar */}
            <div className="flex items-center justify-between p-4 border-b border-[var(--muted-foreground)]/10">
                <div className="flex items-center gap-2 overflow-x-auto pb-1">
                    {folderChain.map((crumb, index) => (
                        <React.Fragment key={crumb.id}>
                            <button
                                onClick={() => handleNavigate(crumb.id)}
                                className="text-sm font-medium hover:text-[var(--accent)] transition-colors whitespace-nowrap"
                            >
                                {crumb.name}
                            </button>
                            {index < folderChain.length - 1 && (
                                <ChevronRight size={14} className="text-[var(--muted-foreground)]/40 flex-shrink-0" />
                            )}
                        </React.Fragment>
                    ))}
                </div>

                <div className="flex items-center gap-2">
                    <button
                        onClick={() => setIsPromptOpen(true)}
                        className="p-2 hover:bg-[var(--muted-foreground)]/10 rounded-lg transition-colors text-[var(--muted-foreground)]"
                        title="New Folder"
                    >
                        <FolderPlus size={20} />
                    </button>
                    <button
                        onClick={() => uploadInputRef.current?.click()}
                        className="p-2 hover:bg-[var(--muted-foreground)]/10 rounded-lg transition-colors text-[var(--muted-foreground)]"
                        title="Upload File"
                    >
                        <Upload size={20} />
                    </button>
                    <button
                        onClick={() => fetchFiles(currentPath)}
                        className={`p-2 hover:bg-[var(--muted-foreground)]/10 rounded-lg transition-colors text-[var(--muted-foreground)] ${isLoading ? 'animate-spin' : ''}`}
                        title="Refresh"
                    >
                        <RefreshCw size={20} />
                    </button>
                </div>
            </div>

            <input
                type="file"
                ref={uploadInputRef}
                className="hidden"
                onChange={handleFileUpload}
            />

            {/* File List */}
            <div className="flex-1 overflow-y-auto min-h-[400px]">
                <table className="w-full text-left border-collapse">
                    <thead>
                        <tr className="border-b border-[var(--muted-foreground)]/5 text-[10px] uppercase tracking-widest text-[var(--muted-foreground)] font-bold">
                            <th className="px-6 py-3 font-semibold">Name</th>
                            <th className="px-6 py-3 font-semibold hidden md:table-cell">Size</th>
                            <th className="px-6 py-3 font-semibold hidden lg:table-cell">Modified</th>
                            <th className="px-6 py-3 font-semibold w-10"></th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-[var(--muted-foreground)]/5">
                        {files.map((file) => (
                            <tr key={file.id} className="group hover:bg-[var(--muted-foreground)]/5 transition-colors cursor-default">
                                <td className="px-6 py-4">
                                    <div
                                        className="flex items-center gap-3 cursor-pointer"
                                        onClick={() => file.type === 'folder' ? handleNavigate(file.id) : null}
                                    >
                                        {file.type === 'folder' ? (
                                            <Folder size={20} className="text-[var(--accent)] fill-[var(--accent)]/10" />
                                        ) : (
                                            <FileText size={20} className="text-[var(--muted-foreground)]" />
                                        )}
                                        <span className={`text-sm font-medium ${file.type === 'folder' ? 'hover:text-[var(--accent)]' : ''}`}>
                                            {file.name}
                                        </span>
                                    </div>
                                </td>
                                <td className="px-6 py-4 text-xs text-[var(--muted-foreground)] hidden md:table-cell">
                                    {file.type === 'file' ? `${(file.size || 0 / 1024).toFixed(1)} KB` : '--'}
                                </td>
                                <td className="px-6 py-4 text-xs text-[var(--muted-foreground)] hidden lg:table-cell">
                                    {file.date ? new Date(file.date * 1000).toLocaleDateString() : '--'}
                                </td>
                                <td className="px-6 py-4 text-right">
                                    <button
                                        onClick={() => setDeleteDialog({ isOpen: true, id: file.id, name: file.name })}
                                        className="p-1.5 opacity-0 group-hover:opacity-100 hover:text-red-500 transition-all"
                                    >
                                        <Trash2 size={16} />
                                    </button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>

                {files.length === 0 && !isLoading && (
                    <div className="flex flex-col items-center justify-center py-24 opacity-20">
                        <Folder size={64} strokeWidth={1} />
                        <p className="mt-4 font-bold uppercase tracking-widest text-sm">Empty Folder</p>
                    </div>
                )}
            </div>

            {/* Custom Dialogs */}
            <PromptDialog
                isOpen={isPromptOpen}
                onClose={() => setIsPromptOpen(false)}
                onConfirm={handleCreateFolder}
                title="Create Folder"
                description="Enter a name for the new directory."
                placeholder="Folder name..."
            />

            <ConfirmationDialog
                isOpen={deleteDialog.isOpen}
                onClose={() => setDeleteDialog({ ...deleteDialog, isOpen: false })}
                onConfirm={handleDelete}
                title="Delete Item?"
                description={`This will permanently remove "${deleteDialog.name}". This action cannot be undone.`}
                confirmText="Delete"
                type="danger"
            />
        </div>
    );
}

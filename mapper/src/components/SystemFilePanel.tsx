"use client";

/**
 * SystemFilePanel
 * File / folder manager that matches the SVAR Willow "Files" tab aesthetic:
 *   - Uniform dark-navy folder SVG icons (no rainbow)
 *   - Coloured document-shape SVG icons per file type
 *   - White cards with subtle shadow
 *   - Three-dot (⋮) dropdown for Rename / Delete
 *   - Breadcrumb "← Back to parent folder" navigation
 */

import { useState, useRef, useEffect } from 'react';
import { Upload, Plus, ArrowLeft, X, CloudUpload, MoreVertical } from 'lucide-react';
import { cn } from '@/lib/utils';
import { ConfirmationDialog } from './ConfirmationDialog';

// ── Types ─────────────────────────────────────────────────────────────────────

interface SystemFile {
  name: string;
  size: number;
  modified_at: string;
  url: string;
}

interface SystemFolder {
  name: string;
  file_count: number;
  created_at: string;
}

interface ConflictState {
  filename: string;
  resolve: (decision: 'replace' | 'skip') => void;
}

export interface SystemFilePanelProps {
  projectId: string;
  systemId: string;
  systemName: string;
  isOpen: boolean;
  onFileCountChange?: (count: number) => void;
  /** Override the outer wrapper class. Defaults to an accordion-style wrapper. */
  className?: string;
}

// ── File-type icon config ─────────────────────────────────────────────────────

const FILE_TYPE_MAP: Record<string, { color: string; label: string }> = {
  pdf:  { color: '#ef4444', label: 'PDF'  },
  jpg:  { color: '#f59e0b', label: 'JPG'  },
  jpeg: { color: '#f59e0b', label: 'JPG'  },
  png:  { color: '#3b82f6', label: 'PNG'  },
  gif:  { color: '#ec4899', label: 'GIF'  },
  svg:  { color: '#10b981', label: 'SVG'  },
  ttl:  { color: '#8b5cf6', label: 'TTL'  },
  json: { color: '#f97316', label: 'JSON' },
  csv:  { color: '#10b981', label: 'CSV'  },
  xlsx: { color: '#22c55e', label: 'XLS'  },
  xls:  { color: '#22c55e', label: 'XLS'  },
  docx: { color: '#3b82f6', label: 'DOC'  },
  doc:  { color: '#3b82f6', label: 'DOC'  },
  py:   { color: '#f59e0b', label: 'PY'   },
  ts:   { color: '#2563eb', label: 'TS'   },
  tsx:  { color: '#2563eb', label: 'TSX'  },
  js:   { color: '#eab308', label: 'JS'   },
  md:   { color: '#64748b', label: 'MD'   },
  yaml: { color: '#f97316', label: 'YML'  },
  yml:  { color: '#f97316', label: 'YML'  },
};

function getFileType(filename: string) {
  const ext = filename.split('.').pop()?.toLowerCase() ?? '';
  return FILE_TYPE_MAP[ext] ?? { color: '#94a3b8', label: (ext.toUpperCase().slice(0, 4) || 'FILE') };
}

// ── SVG Icons ─────────────────────────────────────────────────────────────────

/**
 * Folder icon matching the reference image:
 *   - Left side: perfectly straight (no rounding)
 *   - Tab: rounded top-left corner, diagonal right shoulder
 *   - Body right side: large rounded top-right and bottom-right corners
 *   - Bottom edge: straight, flush with the left
 */
function FolderSvg() {
  return (
    <svg width="68" height="56" viewBox="0 0 68 56" fill="none" aria-hidden>
      <path
        d="M0 48 V8 Q0 0 8 0 H26 L34 11 H60 Q68 11 68 19 V48 Q68 56 60 56 H8 Q0 56 0 48 Z"
        fill="#0f172a"
      />
    </svg>
  );
}

/** Coloured document shape with folded corner — one per file type */
function FileSvg({ color, label }: { color: string; label: string }) {
  return (
    <div className="relative inline-flex items-center justify-center">
      <svg width="52" height="64" viewBox="0 0 52 64" fill="none" aria-hidden>
        <path
          d="M4 0C1.791 0 0 1.791 0 4V60C0 62.209 1.791 64 4 64H48C50.209 64 52 62.209 52 60V16L36 0H4Z"
          fill={color}
        />
        <path
          d="M36 0L52 16H40C37.791 16 36 14.209 36 12V0Z"
          fill="white"
          fillOpacity="0.28"
        />
      </svg>
      {/* Extension label centered on the icon */}
      <span
        className="absolute font-black text-white select-none"
        style={{ fontSize: label.length > 3 ? 8 : 10, letterSpacing: '0.05em', marginTop: 10 }}
      >
        {label}
      </span>
    </div>
  );
}

// ── Three-dot dropdown ────────────────────────────────────────────────────────

interface MenuAction { label: string; danger?: boolean; onClick: () => void; }

function CardMenu({ actions }: { actions: MenuAction[] }) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [open]);

  return (
    <div ref={ref} className="relative flex-shrink-0">
      <button
        onClick={e => { e.stopPropagation(); setOpen(v => !v); }}
        className="p-1 rounded-md hover:bg-[var(--foreground)]/5 text-[var(--muted-foreground)] hover:text-[var(--foreground)] transition-colors"
        title="More actions"
      >
        <MoreVertical size={14} />
      </button>
      {open && (
        <div className="absolute right-0 bottom-7 z-30 min-w-[130px] bg-[var(--background)] border border-[var(--muted-foreground)]/20 rounded-xl shadow-lg overflow-hidden">
          {actions.map(a => (
            <button
              key={a.label}
              onClick={e => { e.stopPropagation(); a.onClick(); setOpen(false); }}
              className={cn(
                'w-full text-left px-4 py-2 text-xs font-semibold transition-colors',
                a.danger
                  ? 'text-red-500 hover:bg-red-500/5'
                  : 'text-[var(--foreground)] hover:bg-[var(--foreground)]/5',
              )}
            >
              {a.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Component ─────────────────────────────────────────────────────────────────

export function SystemFilePanel({
  projectId,
  systemId,
  systemName,
  isOpen,
  onFileCountChange,
  className,
}: SystemFilePanelProps) {
  const [currentFolder, setCurrentFolder] = useState<string | null>(null);
  const [files,   setFiles]   = useState<SystemFile[]>([]);
  const [folders, setFolders] = useState<SystemFolder[]>([]);
  const [isLoading,    setIsLoading]    = useState(false);
  const [isDragging,   setIsDragging]   = useState(false);
  const [isUploading,  setIsUploading]  = useState(false);
  const [showNewFolder,    setShowNewFolder]    = useState(false);
  const [newFolderName,    setNewFolderName]    = useState('');
  const [isCreatingFolder, setIsCreatingFolder] = useState(false);
  const [renamingFolder,   setRenamingFolder]   = useState<string | null>(null);
  const [renameValue,      setRenameValue]      = useState('');
  const [conflictState,  setConflictState]  = useState<ConflictState | null>(null);
  const [deletingFile,   setDeletingFile]   = useState<string | null>(null);
  const [deletingFolder, setDeletingFolder] = useState<string | null>(null);

  const fileInputRef      = useRef<HTMLInputElement>(null);
  const newFolderInputRef = useRef<HTMLInputElement>(null);
  const renameInputRef    = useRef<HTMLInputElement>(null);

  const baseUrl  = `/api/projects/${projectId}/systems/${systemId}`;
  const filesUrl = currentFolder
    ? `${baseUrl}/files?subfolder=${encodeURIComponent(currentFolder)}`
    : `${baseUrl}/files`;

  // ── Data fetching ───────────────────────────────────────────────────────────

  const refreshAll = async () => {
    setIsLoading(true);
    try {
      const filesRes = await fetch(filesUrl);
      if (filesRes.ok) {
        const data: SystemFile[] = await filesRes.json();
        setFiles(data);
        if (!currentFolder) onFileCountChange?.(data.length);
      }
      if (!currentFolder) {
        const foldersRes = await fetch(`${baseUrl}/folders`);
        if (foldersRes.ok) setFolders(await foldersRes.json());
      }
    } finally {
      setIsLoading(false);
    }
  };

  // Reset when system changes
  useEffect(() => {
    setCurrentFolder(null);
    setFiles([]);
    setFolders([]);
    setShowNewFolder(false);
    setRenamingFolder(null);
    setRenameValue('');
  }, [projectId, systemId]);

  useEffect(() => {
    if (isOpen) refreshAll();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen, currentFolder, projectId, systemId]);

  useEffect(() => {
    if (showNewFolder)  setTimeout(() => newFolderInputRef.current?.focus(), 40);
  }, [showNewFolder]);
  useEffect(() => {
    if (renamingFolder) setTimeout(() => renameInputRef.current?.focus(), 40);
  }, [renamingFolder]);

  // ── Folder CRUD ─────────────────────────────────────────────────────────────

  const handleCreateFolder = async (e: React.FormEvent) => {
    e.preventDefault();
    const name = newFolderName.trim();
    if (!name) return;
    setIsCreatingFolder(true);
    try {
      const res = await fetch(`${baseUrl}/folders`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name }),
      });
      if (res.ok) { setShowNewFolder(false); setNewFolderName(''); await refreshAll(); }
    } finally { setIsCreatingFolder(false); }
  };

  const handleRenameFolder = async (e: React.FormEvent) => {
    e.preventDefault();
    const newName = renameValue.trim();
    if (!newName || !renamingFolder) return;
    const res = await fetch(`${baseUrl}/folders/${encodeURIComponent(renamingFolder)}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: newName }),
    });
    if (res.ok) { setRenamingFolder(null); setRenameValue(''); await refreshAll(); }
  };

  const handleDeleteFolder = async (name: string) => {
    await fetch(`${baseUrl}/folders/${encodeURIComponent(name)}`, { method: 'DELETE' });
    setDeletingFolder(null);
    await refreshAll();
  };

  // ── File upload ─────────────────────────────────────────────────────────────

  const uploadSingle = async (file: File, overwrite: boolean): Promise<'ok' | 'conflict' | 'error'> => {
    const fd = new FormData();
    fd.append('files', file);
    if (overwrite) fd.append('overwrite', 'true');
    if (currentFolder) fd.append('subfolder', currentFolder);
    const res = await fetch(`${baseUrl}/files`, { method: 'POST', body: fd });
    if (res.ok) return 'ok';
    if (res.status === 409) return 'conflict';
    return 'error';
  };

  const askConflict = (filename: string): Promise<'replace' | 'skip'> =>
    new Promise(resolve => setConflictState({ filename, resolve }));

  const handleFiles = async (fileList: FileList | File[]) => {
    const arr = Array.from(fileList);
    if (!arr.length) return;
    setIsUploading(true);
    try {
      for (const file of arr) {
        let result = await uploadSingle(file, false);
        if (result === 'conflict') {
          const decision = await askConflict(file.name);
          setConflictState(null);
          if (decision === 'replace') result = await uploadSingle(file, true);
        }
      }
    } finally { setIsUploading(false); await refreshAll(); }
  };

  const handleDeleteFile = async (filename: string) => {
    const url = currentFolder
      ? `${baseUrl}/files/${encodeURIComponent(filename)}?subfolder=${encodeURIComponent(currentFolder)}`
      : `${baseUrl}/files/${encodeURIComponent(filename)}`;
    await fetch(url, { method: 'DELETE' });
    setDeletingFile(null);
    await refreshAll();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    handleFiles(e.dataTransfer.files);
  };

  // ── Render ──────────────────────────────────────────────────────────────────

  if (!isOpen) return null;

  const isAtRoot     = currentFolder === null;
  const isEmpty      = files.length === 0 && (isAtRoot ? folders.length === 0 : true);
  const wrapperClass = className ?? 'mt-2 border border-[var(--muted-foreground)]/20 rounded-2xl overflow-hidden bg-[var(--background)]';

  return (
    <div
      className={cn(wrapperClass, 'flex flex-col h-full relative')}
      onDragOver={e => { e.preventDefault(); setIsDragging(true); }}
      onDragLeave={e => { if (!e.currentTarget.contains(e.relatedTarget as Node)) setIsDragging(false); }}
      onDrop={handleDrop}
    >

      {/* ── Header ──────────────────────────────────────────────────────── */}
      <div className="flex-none bg-[var(--background)]/80 backdrop-blur-md border-b border-[var(--muted-foreground)]/10 z-10">
        <div className="px-6 pt-4 pb-3 flex items-center justify-between gap-4">
          {/* Breadcrumb */}
          <div className="flex items-center gap-2 text-sm min-w-0">
            <button
              onClick={() => setCurrentFolder(null)}
              className={cn(
                'font-semibold transition-colors flex-shrink-0',
                isAtRoot
                  ? 'text-[var(--foreground)] cursor-default'
                  : 'text-[var(--accent)] hover:underline cursor-pointer',
              )}
            >
              {systemName}
            </button>
            {!isAtRoot && (
              <>
                <span className="text-[var(--muted-foreground)] select-none">›</span>
                <span className="font-semibold text-[var(--foreground)] truncate">{currentFolder}</span>
              </>
            )}
          </div>

          {/* Actions */}
          <div className="flex items-center gap-2 flex-shrink-0">
            {isAtRoot && (
              <button
                onClick={() => { setShowNewFolder(v => !v); setNewFolderName(''); }}
                className={cn(
                  'flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all border',
                  showNewFolder
                    ? 'bg-[var(--accent)]/10 text-[var(--accent)] border-[var(--accent)]/20'
                    : 'text-[var(--muted-foreground)] hover:text-[var(--foreground)] hover:bg-[var(--foreground)]/5 border-transparent',
                )}
              >
                <Plus size={12} />
                New Folder
              </button>
            )}
            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={isUploading}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-white bg-[var(--accent)] rounded-lg hover:opacity-90 transition-opacity disabled:opacity-50"
            >
              <Upload size={12} />
              {isUploading ? 'Uploading…' : 'Upload'}
            </button>
            <input
              ref={fileInputRef}
              type="file"
              multiple
              className="hidden"
              onChange={e => e.target.files && handleFiles(e.target.files)}
              onClick={e => ((e.target as HTMLInputElement).value = '')}
            />
          </div>
        </div>
      </div>

      {/* ── Scrollable content ───────────────────────────────────────────── */}
      <div className="flex-1 overflow-y-auto bg-[var(--foreground)]/[0.015]">
        {isLoading ? (
          <div className="flex items-center justify-center py-20">
            <p className="text-xs text-[var(--muted-foreground)] animate-pulse">Loading…</p>
          </div>
        ) : (
          <div className="p-6">

            {/* Back to parent folder */}
            {!isAtRoot && (
              <button
                onClick={() => setCurrentFolder(null)}
                className="flex items-center gap-1.5 text-xs font-semibold text-[var(--accent)] hover:underline mb-5"
              >
                <ArrowLeft size={13} />
                Back to parent folder
              </button>
            )}

            {/* ── New-folder inline form ───────────────────────────────── */}
            {showNewFolder && isAtRoot && (
              <form
                onSubmit={handleCreateFolder}
                className="flex items-center gap-2 mb-4 p-3 bg-[var(--background)] border border-[var(--muted-foreground)]/20 rounded-xl shadow-sm"
              >
                <FolderSvg />
                <input
                  ref={newFolderInputRef}
                  required
                  value={newFolderName}
                  onChange={e => setNewFolderName(e.target.value)}
                  placeholder="Folder name"
                  className="flex-1 px-2.5 py-1.5 border border-[var(--muted-foreground)]/20 rounded-lg text-xs focus:outline-none focus:border-[var(--accent)] bg-[var(--background)] text-[var(--foreground)]"
                />
                <button
                  type="submit"
                  disabled={isCreatingFolder || !newFolderName.trim()}
                  className="px-3 py-1.5 text-xs font-bold text-white bg-[var(--accent)] rounded-lg hover:opacity-90 disabled:opacity-50"
                >
                  {isCreatingFolder ? '…' : 'Create'}
                </button>
                <button
                  type="button"
                  onClick={() => { setShowNewFolder(false); setNewFolderName(''); }}
                  className="p-1.5 rounded-lg hover:bg-[var(--foreground)]/5 text-[var(--muted-foreground)]"
                >
                  <X size={13} />
                </button>
              </form>
            )}

            {/* ── Folders grid (root only) ──────────────────────────── */}
            {isAtRoot && folders.length > 0 && (
              <div className="mb-6">
                <div className="flex flex-wrap gap-3">
                  {folders.map(f => {
                    /* ── Rename form card ── */
                    if (renamingFolder === f.name) {
                      return (
                        <form
                          key={f.name}
                          onSubmit={handleRenameFolder}
                          className="w-[140px] border-2 border-[var(--accent)]/30 rounded-xl bg-[var(--background)] shadow-sm p-3 flex flex-col gap-2"
                        >
                          <div className="flex justify-center py-2">
                            <FolderSvg />
                          </div>
                          <input
                            ref={renameInputRef}
                            required
                            value={renameValue}
                            onChange={e => setRenameValue(e.target.value)}
                            className="w-full px-2 py-1 border border-[var(--muted-foreground)]/20 rounded-lg text-xs focus:outline-none focus:border-[var(--accent)] bg-[var(--background)] text-[var(--foreground)]"
                          />
                          <div className="flex gap-1">
                            <button
                              type="submit"
                              disabled={!renameValue.trim()}
                              className="flex-1 py-1 text-[10px] font-bold text-white bg-[var(--accent)] rounded-lg disabled:opacity-50"
                            >
                              Save
                            </button>
                            <button
                              type="button"
                              onClick={() => setRenamingFolder(null)}
                              className="p-1 rounded-lg hover:bg-[var(--foreground)]/5 text-[var(--muted-foreground)]"
                            >
                              <X size={12} />
                            </button>
                          </div>
                        </form>
                      );
                    }

                    /* ── Normal folder card ── */
                    return (
                      <div
                        key={f.name}
                        onClick={() => setCurrentFolder(f.name)}
                        className="w-[140px] border border-[var(--muted-foreground)]/15 rounded-xl bg-[var(--background)] shadow-sm hover:shadow-md transition-shadow cursor-pointer overflow-hidden group"
                      >
                        <div className="flex items-center justify-center py-5 px-4">
                          <FolderSvg />
                        </div>
                        <div className="px-3 pb-3 flex items-end justify-between gap-1">
                          <div className="min-w-0">
                            <p className="text-[10px] font-bold text-[var(--accent)] leading-none mb-0.5">Folder</p>
                            <p className="text-xs font-semibold text-[var(--foreground)] truncate leading-tight" title={f.name}>
                              {f.name}
                            </p>
                          </div>
                          <CardMenu
                            actions={[
                              { label: 'Rename', onClick: () => { setRenamingFolder(f.name); setRenameValue(f.name); } },
                              { label: 'Delete', danger: true, onClick: () => setDeletingFolder(f.name) },
                            ]}
                          />
                        </div>
                      </div>
                    );
                  })}

                  {/* Add new folder placeholder */}
                  <button
                    onClick={() => setShowNewFolder(true)}
                    className="w-[140px] border-2 border-dashed border-[var(--muted-foreground)]/20 hover:border-[var(--accent)]/40 rounded-xl bg-transparent hover:bg-[var(--accent)]/[0.03] transition-all flex flex-col items-center justify-center gap-2 py-5 group"
                  >
                    <div className="w-9 h-9 rounded-lg bg-[var(--foreground)]/5 group-hover:bg-[var(--accent)]/10 flex items-center justify-center transition-colors">
                      <Plus size={16} className="text-[var(--muted-foreground)] group-hover:text-[var(--accent)] transition-colors" />
                    </div>
                    <p className="text-xs font-semibold text-[var(--muted-foreground)] group-hover:text-[var(--accent)] transition-colors">
                      Add new folder
                    </p>
                  </button>
                </div>
              </div>
            )}

            {/* "Add new folder" when no folders exist yet */}
            {isAtRoot && folders.length === 0 && !showNewFolder && (
              <div className="mb-6 flex flex-wrap gap-3">
                <button
                  onClick={() => setShowNewFolder(true)}
                  className="w-[140px] border-2 border-dashed border-[var(--muted-foreground)]/20 hover:border-[var(--accent)]/40 rounded-xl hover:bg-[var(--accent)]/[0.03] transition-all flex flex-col items-center justify-center gap-2 py-6 group"
                >
                  <div className="w-9 h-9 rounded-lg bg-[var(--foreground)]/5 group-hover:bg-[var(--accent)]/10 flex items-center justify-center transition-colors">
                    <Plus size={16} className="text-[var(--muted-foreground)] group-hover:text-[var(--accent)] transition-colors" />
                  </div>
                  <p className="text-xs font-semibold text-[var(--muted-foreground)] group-hover:text-[var(--accent)] transition-colors">
                    Add new folder
                  </p>
                </button>
              </div>
            )}

            {/* ── Files grid ───────────────────────────────────────────── */}
            {files.length > 0 && (
              <div className="flex flex-wrap gap-3">
                {files.map(f => {
                  const type = getFileType(f.name);
                  return (
                    <div
                      key={f.name}
                      className="w-[140px] border border-[var(--muted-foreground)]/15 rounded-xl bg-[var(--background)] shadow-sm hover:shadow-md transition-shadow overflow-hidden group"
                    >
                      <div className="flex items-center justify-center py-5 px-4">
                        <FileSvg color={type.color} label={type.label} />
                      </div>
                      <div className="px-3 pb-3 flex items-end justify-between gap-1">
                        <p
                          className="text-xs font-semibold text-[var(--foreground)] truncate leading-tight min-w-0"
                          title={f.name}
                        >
                          {f.name}
                        </p>
                        <CardMenu
                          actions={[
                            { label: 'Delete', danger: true, onClick: () => setDeletingFile(f.name) },
                          ]}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            )}

            {/* ── Empty state ───────────────────────────────────────────── */}
            {isEmpty && !showNewFolder && (
              <div className="flex flex-col items-center justify-center py-20 gap-3">
                <div className="opacity-20">
                  <FolderSvg />
                </div>
                <p className="text-sm font-semibold text-[var(--muted-foreground)]">
                  {isAtRoot ? 'No files or folders yet' : 'No files in this folder'}
                </p>
                <p className="text-xs text-[var(--muted-foreground)] opacity-70">
                  Drag & drop files here or click <strong>Upload</strong>
                  {isAtRoot && ' / Add new folder'}.
                </p>
              </div>
            )}

          </div>
        )}
      </div>

      {/* ── Drag & drop overlay ──────────────────────────────────────────── */}
      {isDragging && (
        <div className="absolute inset-0 z-20 flex flex-col items-center justify-center gap-4 bg-[var(--background)]/85 backdrop-blur-sm border-2 border-[var(--accent)]/50 rounded-[inherit] pointer-events-none">
          <div className="w-20 h-20 rounded-2xl bg-[var(--accent)]/10 border-2 border-[var(--accent)]/30 flex items-center justify-center animate-bounce">
            <CloudUpload size={36} className="text-[var(--accent)]" />
          </div>
          <p className="text-base font-black text-[var(--accent)]">
            Drop to upload{currentFolder ? ` into "${currentFolder}"` : ''}
          </p>
        </div>
      )}

      {/* ── Conflict prompt ──────────────────────────────────────────────── */}
      {conflictState && (
        <div className="fixed inset-0 z-[300] flex items-center justify-center p-4">
          <div
            className="absolute inset-0 bg-black/40 backdrop-blur-md"
            onClick={() => { conflictState.resolve('skip'); setConflictState(null); }}
          />
          <div className="relative bg-[var(--background)] border border-[var(--muted-foreground)]/20 rounded-[2rem] p-8 max-w-sm w-full shadow-2xl">
            <h3 className="text-lg font-black text-[var(--foreground)] mb-2">File already exists</h3>
            <p className="text-sm text-[var(--muted-foreground)] mb-6 leading-relaxed">
              <strong className="text-[var(--foreground)]">{conflictState.filename}</strong>{' '}
              already exists{currentFolder ? ` in "${currentFolder}"` : ''}. Replace it?
            </p>
            <div className="flex justify-end gap-3">
              <button
                onClick={() => { conflictState.resolve('skip'); setConflictState(null); }}
                className="px-5 py-2 text-sm text-[var(--muted-foreground)] rounded-xl hover:bg-[var(--foreground)]/5 transition-colors"
              >
                Skip
              </button>
              <button
                onClick={() => { conflictState.resolve('replace'); setConflictState(null); }}
                className="px-5 py-2 text-sm font-bold text-white bg-red-500 rounded-xl hover:bg-red-600 transition-colors"
              >
                Replace
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── Dialogs ──────────────────────────────────────────────────────── */}
      <ConfirmationDialog
        isOpen={!!deletingFile}
        onClose={() => setDeletingFile(null)}
        onConfirm={() => deletingFile && handleDeleteFile(deletingFile)}
        title={`Delete "${deletingFile}"?`}
        description={`This file will be permanently deleted${currentFolder ? ` from "${currentFolder}"` : ''}. This action cannot be undone.`}
        confirmText="Delete file"
        type="danger"
      />
      <ConfirmationDialog
        isOpen={!!deletingFolder}
        onClose={() => setDeletingFolder(null)}
        onConfirm={() => deletingFolder && handleDeleteFolder(deletingFolder)}
        title={`Delete folder "${deletingFolder}"?`}
        description="This will permanently delete the folder and all files inside it. This action cannot be undone."
        confirmText="Delete folder"
        type="danger"
      />
    </div>
  );
}


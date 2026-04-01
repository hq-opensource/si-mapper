"use client";

import { useState, useRef, useEffect } from 'react';
import { ChevronDown, Trash2, Plus, RotateCcw, Pencil, Clock } from 'lucide-react';
import { useWorkspace } from '@/context/WorkspaceContext';
import { ConfirmationDialog } from './ConfirmationDialog';
import { PromptDialog } from './PromptDialog';
import type { SessionRef } from '@/types';

// ── Helpers ───────────────────────────────────────────────────────────────────

function formatRelativeTime(isoDate: string): string {
  if (!isoDate) return '';
  const diff = Date.now() - new Date(isoDate).getTime();
  const mins = Math.floor(diff / 60_000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

// ── SessionSelector ───────────────────────────────────────────────────────────

export function SessionSelector() {
  const {
    activeProject,
    activeSystem,
    activeSession,
    setActiveSession,
    refreshSystems,
  } = useWorkspace();

  const [isOpen, setIsOpen] = useState(false);
  const [deletingSession, setDeletingSession] = useState<SessionRef | null>(null);
  const [renamingSession, setRenamingSession] = useState<SessionRef | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [newSessionDialogOpen, setNewSessionDialogOpen] = useState(false);
  const [newSessionDefaultName, setNewSessionDefaultName] = useState('');
  const [newSessionForced, setNewSessionForced] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const sessions = activeSystem?.sessions ?? [];
  const disabled = !activeProject || !activeSystem;

  // Close on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const handleSelect = async (session: SessionRef) => {
    setIsOpen(false);
    if (session.session_id === activeSession?.session_id) return;
    await setActiveSession(session);
  };

  const handleNewSession = () => {
    if (!activeProject || !activeSystem) return;
    const now = new Date();
    const suggested = `Session ${now.toISOString().slice(0, 16).replace('T', ' ')}`;
    setNewSessionDefaultName(suggested);
    setNewSessionForced(false);
    setIsOpen(false);
    setNewSessionDialogOpen(true);
  };

  const handleCreateSession = async (name: string) => {
    if (!activeProject || !activeSystem) return;
    setIsCreating(true);
    try {
      const res = await fetch(`/api/projects/${activeProject.id}/systems/${activeSystem.id}/sessions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_name: name }),
      });
      const newSession = res.ok ? await res.json() : null;
      await refreshSystems();
      if (newSession?.session_id) {
        await setActiveSession(newSession);
      }
    } finally {
      setIsCreating(false);
    }
  };

  const handleDelete = async (session: SessionRef) => {
    if (!activeProject || !activeSystem) return;
    const isLast = sessions.length === 1;
    await fetch(
      `/api/projects/${activeProject.id}/systems/${activeSystem.id}/sessions/${session.session_id}`,
      { method: 'DELETE' },
    );
    setDeletingSession(null);
    await refreshSystems();
    if (isLast) {
      const now = new Date();
      const suggested = `Session ${now.toISOString().slice(0, 16).replace('T', ' ')}`;
      setNewSessionDefaultName(suggested);
      setNewSessionForced(true);
      setNewSessionDialogOpen(true);
    }
  };

  const handleRename = async (newName: string) => {
    if (!activeProject || !activeSystem || !renamingSession) return;
    await fetch(
      `/api/projects/${activeProject.id}/systems/${activeSystem.id}/sessions/${renamingSession.session_id}`,
      {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_name: newName }),
      },
    );
    setRenamingSession(null);
    await refreshSystems();
  };

  const displayName = activeSession?.session_name || activeSession?.session_id || 'No session';

  return (
    <>
      <div className="relative" ref={dropdownRef}>
        {/* Trigger */}
        <button
          onClick={() => !disabled && setIsOpen(!isOpen)}
          disabled={disabled || isCreating}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold transition-all duration-200
            border border-transparent
            ${disabled || isCreating
              ? 'text-[var(--muted-foreground)] opacity-40 cursor-not-allowed'
              : 'text-[var(--foreground)] hover:bg-[var(--foreground)]/5 hover:border-[var(--muted-foreground)]/20 cursor-pointer'
            }`}
          title={disabled ? 'Select a system first' : 'Switch session'}
        >
          <Clock size={11} className="flex-shrink-0 text-[var(--muted-foreground)]" />
          <span className="max-w-[11rem] truncate">{isCreating ? 'Creating…' : displayName}</span>
          {!disabled && (
            <ChevronDown
              size={12}
              className={`flex-shrink-0 transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`}
            />
          )}
        </button>

        {/* Dropdown */}
        {isOpen && !disabled && (
          <div className="absolute left-0 top-full mt-2 w-80 bg-[var(--background)] border border-[var(--muted-foreground)]/20 rounded-2xl shadow-2xl z-[200] overflow-hidden">
            {/* Session list */}
            <div className="max-h-72 overflow-y-auto py-1.5">
              {sessions.length === 0 ? (
                <p className="px-4 py-3 text-xs text-[var(--muted-foreground)]">No sessions yet.</p>
              ) : (
                sessions.map(session => {
                  const isActive = session.session_id === activeSession?.session_id;
                  return (
                    <div
                      key={session.session_id}
                      className={`flex items-start justify-between px-4 py-2.5 cursor-pointer gap-2
                        hover:bg-[var(--foreground)]/5 transition-colors
                        ${isActive ? 'text-[var(--accent)]' : 'text-[var(--foreground)]'}`}
                      onClick={() => handleSelect(session)}
                    >
                      <div className="flex items-start gap-2 min-w-0 flex-1">
                        {isActive && (
                          <span className="flex-shrink-0 mt-1 w-1.5 h-1.5 rounded-full bg-[var(--accent)]" />
                        )}
                        <div className="min-w-0">
                          <div className="text-xs font-semibold truncate">{session.session_name || session.session_id}</div>
                          <div className="text-[10px] text-[var(--muted-foreground)] mt-0.5 flex items-center gap-1">
                            <RotateCcw size={9} />
                            {formatRelativeTime(session.created_at)}
                            <span className="font-mono opacity-60 ml-1">{session.session_id}</span>
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-1 flex-shrink-0">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setRenamingSession(session);
                            setIsOpen(false);
                          }}
                          className="p-1 rounded-lg hover:bg-[var(--accent)]/10 text-[var(--muted-foreground)] hover:text-[var(--accent)] transition-colors"
                          title="Rename session"
                        >
                          <Pencil size={11} />
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setDeletingSession(session);
                            setIsOpen(false);
                          }}
                          className="p-1 rounded-lg hover:bg-red-500/10 text-[var(--muted-foreground)] hover:text-red-500 transition-colors"
                          title="Delete session"
                        >
                          <Trash2 size={11} />
                        </button>
                      </div>
                    </div>
                  );
                })
              )}
            </div>

            {/* Footer */}
            <div className="border-t border-[var(--muted-foreground)]/10 p-2">
              <button
                onClick={handleNewSession}
                className="flex items-center gap-2 w-full px-3 py-2 text-xs font-bold text-[var(--accent)] hover:bg-[var(--accent)]/5 rounded-xl transition-colors"
              >
                <Plus size={13} />
                New session
              </button>
            </div>
          </div>
        )}
      </div>

      {/* New session dialog */}
      <PromptDialog
        isOpen={newSessionDialogOpen}
        onClose={() => setNewSessionDialogOpen(false)}
        onConfirm={handleCreateSession}
        title="New session"
        description="Give your session a name, or keep the suggestion."
        defaultValue={newSessionDefaultName}
        placeholder="Session name"
        confirmText="Create"
        disableCancel={newSessionForced}
      />

      {/* Delete confirmation */}
      <ConfirmationDialog
        isOpen={!!deletingSession}
        onClose={() => setDeletingSession(null)}
        onConfirm={() => deletingSession && handleDelete(deletingSession)}
        title="Delete session"
        description={`Delete "${deletingSession?.session_name || deletingSession?.session_id}"? This cannot be undone.`}
        confirmText="Delete"
        type="danger"
      />

      {/* Rename dialog */}
      <PromptDialog
        isOpen={!!renamingSession}
        onClose={() => setRenamingSession(null)}
        onConfirm={handleRename}
        title="Rename session"
        description="Enter a new name for this session."
        placeholder={renamingSession?.session_name || 'Session name'}
        confirmText="Rename"
      />
    </>
  );
}



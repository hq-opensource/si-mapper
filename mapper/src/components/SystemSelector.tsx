"use client";

import { useState, useRef, useEffect } from 'react';
import { ChevronDown, Trash2, Plus, X } from 'lucide-react';
import { useWorkspace } from '@/context/WorkspaceContext';
import { ConfirmationDialog } from './ConfirmationDialog';
import type { System } from '@/types';

const DEFAULT_AI_MODEL = 'gemini-2.0-flash';

// ── Inline 2-field dialog for system creation ────────────────────────────────

interface CreateSystemDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (name: string, aiModel: string) => void;
}

function CreateSystemDialog({ isOpen, onClose, onConfirm }: CreateSystemDialogProps) {
  const [name, setName] = useState('');
  const [aiModel, setAiModel] = useState(DEFAULT_AI_MODEL);
  const nameRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isOpen) {
      setName('');
      setAiModel(DEFAULT_AI_MODEL);
      setTimeout(() => nameRef.current?.focus(), 80);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = name.trim();
    if (!trimmed) return;
    onConfirm(trimmed, aiModel.trim() || DEFAULT_AI_MODEL);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-[200] flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/40 backdrop-blur-md"
        onClick={onClose}
      />
      {/* Modal */}
      <form
        onSubmit={handleSubmit}
        className="relative bg-[var(--background)] border border-[var(--muted-foreground)]/20 rounded-[2rem] p-8 max-w-sm w-full shadow-2xl"
      >
        <button
          type="button"
          onClick={onClose}
          className="absolute top-5 right-5 p-1.5 rounded-lg hover:bg-[var(--foreground)]/5 text-[var(--muted-foreground)]"
        >
          <X size={14} />
        </button>
        <h3 className="text-xl font-black text-[var(--foreground)] mb-1">New System</h3>
        <p className="text-xs text-[var(--muted-foreground)] mb-6">
          A system represents one HVAC diagram within your project.
        </p>
        <div className="space-y-4">
          <div>
            <label className="block text-xs font-bold text-[var(--foreground)] mb-1.5">
              Name <span className="text-red-500">*</span>
            </label>
            <input
              ref={nameRef}
              required
              value={name}
              onChange={e => setName(e.target.value)}
              placeholder="e.g. Chilled Water Plant"
              className="w-full px-4 py-2.5 border border-[var(--muted-foreground)]/30 rounded-xl text-sm
                focus:outline-none focus:border-[var(--accent)] focus:ring-1 focus:ring-[var(--accent)]/20
                bg-[var(--background)] text-[var(--foreground)]"
            />
          </div>
          <div>
            <label className="block text-xs font-bold text-[var(--foreground)] mb-1.5">
              AI Model <span className="text-[var(--muted-foreground)] font-normal">(optional)</span>
            </label>
            <input
              value={aiModel}
              onChange={e => setAiModel(e.target.value)}
              placeholder={DEFAULT_AI_MODEL}
              className="w-full px-4 py-2.5 border border-[var(--muted-foreground)]/30 rounded-xl text-sm
                focus:outline-none focus:border-[var(--accent)] focus:ring-1 focus:ring-[var(--accent)]/20
                bg-[var(--background)] text-[var(--foreground)]"
            />
          </div>
        </div>
        <div className="flex justify-end gap-3 mt-7">
          <button
            type="button"
            onClick={onClose}
            className="px-5 py-2 text-sm text-[var(--muted-foreground)] rounded-xl hover:bg-[var(--foreground)]/5 transition-colors"
          >
            Cancel
          </button>
          <button
            type="submit"
            className="px-5 py-2 text-sm font-bold text-white bg-[var(--accent)] rounded-xl hover:opacity-90 transition-opacity"
          >
            Create
          </button>
        </div>
      </form>
    </div>
  );
}

// ── SystemSelector ────────────────────────────────────────────────────────────

export function SystemSelector() {
  const { activeProject, activeSystem, systems, setActiveSystem, refreshSystems } = useWorkspace();
  const [isOpen, setIsOpen] = useState(false);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [deletingSystem, setDeletingSystem] = useState<System | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const disabled = !activeProject;

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

  const handleCreate = async (name: string, aiModel: string) => {
    if (!activeProject) return;
    setIsCreating(true);
    try {
      const res = await fetch(`/api/projects/${activeProject.id}/systems`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, ai_model_name: aiModel }),
      });
      if (res.ok) {
        const created: System = await res.json();
        await refreshSystems();
        setActiveSystem(created);
      }
    } finally {
      setIsCreating(false);
    }
  };

  const handleDelete = async (system: System) => {
    if (!activeProject) return;
    await fetch(`/api/projects/${activeProject.id}/systems/${system.id}`, { method: 'DELETE' });
    setDeletingSystem(null);
    await refreshSystems();
  };

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Trigger */}
      <button
        onClick={() => !disabled && setIsOpen(!isOpen)}
        disabled={disabled || isCreating}
        className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold transition-all duration-200
          border border-transparent
          ${disabled
            ? 'text-[var(--muted-foreground)] opacity-40 cursor-not-allowed'
            : 'text-[var(--foreground)] hover:bg-[var(--foreground)]/5 hover:border-[var(--muted-foreground)]/20 cursor-pointer'
          }`}
        title={disabled ? 'Select a project first' : 'Switch system'}
      >
        <span className="max-w-[12rem] truncate">
          {activeSystem?.name ?? (disabled ? 'No system' : 'No system')}
        </span>
        {!disabled && (
          <ChevronDown
            size={12}
            className={`flex-shrink-0 transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`}
          />
        )}
      </button>

      {/* Dropdown */}
      {isOpen && !disabled && (
        <div className="absolute left-0 top-full mt-2 w-72 bg-[var(--background)] border border-[var(--muted-foreground)]/20 rounded-2xl shadow-2xl z-[200] overflow-hidden">
          {/* System list */}
          <div className="max-h-64 overflow-y-auto py-1.5">
            {systems.length === 0 ? (
              <p className="px-4 py-3 text-xs text-[var(--muted-foreground)]">No systems yet.</p>
            ) : (
              systems.map(system => (
                <div
                  key={system.id}
                  className={`flex items-center justify-between px-4 py-2 cursor-pointer
                    hover:bg-[var(--foreground)]/5 transition-colors
                    ${activeSystem?.id === system.id ? 'text-[var(--accent)]' : 'text-[var(--foreground)]'}`}
                  onClick={() => { setActiveSystem(system); setIsOpen(false); }}
                >
                  <span className="flex items-center gap-2 text-xs font-semibold min-w-0">
                    {activeSystem?.id === system.id && (
                      <span className="flex-shrink-0 w-1.5 h-1.5 rounded-full bg-[var(--accent)]" />
                    )}
                    <span className="truncate">{system.name}</span>
                  </span>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setDeletingSystem(system);
                      setIsOpen(false);
                    }}
                    className="ml-2 flex-shrink-0 p-1 rounded-lg hover:bg-red-500/10 text-[var(--muted-foreground)] hover:text-red-500 transition-colors"
                    title={`Delete "${system.name}"`}
                  >
                    <Trash2 size={12} />
                  </button>
                </div>
              ))
            )}
          </div>

          {/* Footer action */}
          <div className="border-t border-[var(--muted-foreground)]/20 p-1.5">
            <button
              onClick={() => { setShowCreateDialog(true); setIsOpen(false); }}
              className="w-full flex items-center gap-2 px-3 py-2 text-xs text-[var(--foreground)] rounded-xl hover:bg-[var(--foreground)]/5 transition-colors"
            >
              <Plus size={12} className="text-[var(--accent)]" />
              <span>New system</span>
            </button>
          </div>
        </div>
      )}

      {/* Dialogs */}
      <CreateSystemDialog
        isOpen={showCreateDialog}
        onClose={() => setShowCreateDialog(false)}
        onConfirm={handleCreate}
      />
      <ConfirmationDialog
        isOpen={!!deletingSystem}
        onClose={() => setDeletingSystem(null)}
        onConfirm={() => deletingSystem && handleDelete(deletingSystem)}
        title={`Delete "${deletingSystem?.name}"?`}
        description="This will permanently delete the system and all its files. This action cannot be undone."
        confirmText="Delete system"
        type="danger"
      />
    </div>
  );
}


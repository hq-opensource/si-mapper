"use client";

/**
 * ProjectEditDialog
 * Modal dialog for renaming a project.
 * Calls PATCH /api/projects/[id] with { name }.
 */

import { useState, useEffect, useRef } from 'react';
import { X, Pencil } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { Project } from '@/types';

interface ProjectEditDialogProps {
  isOpen: boolean;
  onClose: () => void;
  project: Project;
  /** Called after a successful save so the parent can refresh its data. */
  onSuccess: () => void;
}

export function ProjectEditDialog({
  isOpen,
  onClose,
  project,
  onSuccess,
}: ProjectEditDialogProps) {
  const [name, setName] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isOpen) {
      setName(project.name);
      setError(null);
      setTimeout(() => inputRef.current?.focus(), 80);
    }
  }, [isOpen, project]);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = name.trim();
    if (!trimmed) return;

    setIsSaving(true);
    setError(null);
    try {
      const res = await fetch(`/api/projects/${project.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: trimmed }),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        setError((data as { error?: string }).error ?? 'Failed to update project.');
        return;
      }
      onSuccess();
      onClose();
    } catch {
      setError('Network error. Please try again.');
    } finally {
      setIsSaving(false);
    }
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
        {/* Close button */}
        <button
          type="button"
          onClick={onClose}
          className="absolute top-5 right-5 p-1.5 rounded-lg hover:bg-[var(--foreground)]/5 text-[var(--muted-foreground)] transition-colors"
        >
          <X size={14} />
        </button>

        {/* Header */}
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-xl bg-[var(--accent)]/10 flex items-center justify-center">
            <Pencil size={16} className="text-[var(--accent)]" />
          </div>
          <div>
            <h3 className="text-lg font-black text-[var(--foreground)]">Edit Project</h3>
            <p className="text-xs text-[var(--muted-foreground)]">Update project details</p>
          </div>
        </div>

        {/* Fields */}
        <div className="space-y-4">
          {/* Name */}
          <div>
            <label className="block text-xs font-bold text-[var(--foreground)] mb-1.5">
              Name <span className="text-red-500">*</span>
            </label>
            <input
              ref={inputRef}
              required
              value={name}
              onChange={e => setName(e.target.value)}
              className={cn(
                'w-full px-4 py-2.5 border rounded-xl text-sm',
                'focus:outline-none focus:ring-1',
                'bg-[var(--background)] text-[var(--foreground)]',
                error
                  ? 'border-red-400 focus:border-red-400 focus:ring-red-400/20'
                  : 'border-[var(--muted-foreground)]/30 focus:border-[var(--accent)] focus:ring-[var(--accent)]/20',
              )}
            />
          </div>

          {/* Graphivac Project ID — read-only for reference */}
          <div>
            <label className="block text-xs font-semibold text-[var(--muted-foreground)] mb-1.5">
              Graphivac Project ID{' '}
              <span className="font-normal">(read-only)</span>
            </label>
            <input
              readOnly
              value={project.graphivac_project_id}
              className="w-full px-4 py-2.5 border border-[var(--muted-foreground)]/20 rounded-xl text-xs font-mono bg-[var(--foreground)]/5 text-[var(--muted-foreground)] cursor-default select-all"
            />
          </div>
        </div>

        {error && <p className="text-xs text-red-500 mt-3">{error}</p>}

        {/* Actions */}
        <div className="flex justify-end gap-3 mt-7">
          <button
            type="button"
            onClick={onClose}
            disabled={isSaving}
            className="px-5 py-2 text-sm text-[var(--muted-foreground)] rounded-xl hover:bg-[var(--foreground)]/5 transition-colors disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={isSaving || !name.trim()}
            className="px-5 py-2 text-sm font-bold text-white bg-[var(--accent)] rounded-xl hover:opacity-90 transition-opacity disabled:opacity-50"
          >
            {isSaving ? 'Saving…' : 'Save'}
          </button>
        </div>
      </form>
    </div>
  );
}


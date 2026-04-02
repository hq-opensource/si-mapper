"use client";

/**
 * SystemEditDialog
 * Modal dialog for editing a system's name.
 * Calls PATCH /api/projects/[id]/systems/[sysId] with { name }.
 */

import { useState, useEffect, useRef } from 'react';
import { X, Settings2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { System } from '@/types';

interface SystemEditDialogProps {
  isOpen: boolean;
  onClose: () => void;
  projectId: string;
  system: System;
  /** Called after a successful save so the parent can refresh its data. */
  onSuccess: () => void;
}

export function SystemEditDialog({
  isOpen,
  onClose,
  projectId,
  system,
  onSuccess,
}: SystemEditDialogProps) {
  const [name, setName] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const nameRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isOpen) {
      setName(system.name);
      setError(null);
      setTimeout(() => nameRef.current?.focus(), 80);
    }
  }, [isOpen, system]);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmedName = name.trim();
    if (!trimmedName) return;

    setIsSaving(true);
    setError(null);
    try {
      const body: Record<string, string> = { name: trimmedName };

      const res = await fetch(
        `/api/projects/${projectId}/systems/${system.id}`,
        {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body),
        },
      );
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        setError((data as { error?: string }).error ?? 'Failed to update system.');
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
            <Settings2 size={16} className="text-[var(--accent)]" />
          </div>
          <div>
            <h3 className="text-lg font-black text-[var(--foreground)]">Edit System</h3>
            <p className="text-xs text-[var(--muted-foreground)]">Update system details</p>
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
              ref={nameRef}
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

          {/* Graphivac Grid ID — read-only */}
          <div>
            <label className="block text-xs font-semibold text-[var(--muted-foreground)] mb-1.5">
              Graphivac Grid ID{' '}
              <span className="font-normal">(read-only)</span>
            </label>
            <input
              readOnly
              value={system.graphivac_grid_id}
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

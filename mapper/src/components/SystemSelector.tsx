"use client";

import { useState, useRef, useEffect } from 'react';
import Link from 'next/link';
import { ChevronDown, Trash2, Plus, Cpu } from 'lucide-react';
import { useWorkspace } from '@/context/WorkspaceContext';
import { ConfirmationDialog } from './ConfirmationDialog';
import type { System } from '@/types';

// ── SystemSelector ────────────────────────────────────────────────────────────

export function SystemSelector() {
  const { activeProject, activeSystem, systems, setActiveSystem, refreshSystems } = useWorkspace();
  const [isOpen, setIsOpen] = useState(false);
  const [deletingSystem, setDeletingSystem] = useState<System | null>(null);
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

  const handleDelete = async (system: System) => {
    if (!activeProject) return;
    await fetch(`/api/projects/${activeProject.id}/systems/${system.id}`, { method: 'DELETE' });
    setDeletingSystem(null);
    await refreshSystems();
  };

  // URL for "New system": go to /projects pre-selecting the current project
  // and triggering the system creation form via ?create=system&project=<id>
  const newSystemHref = activeProject
    ? `/projects?create=system&project=${activeProject.id}`
    : '/projects';

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Trigger */}
      <button
        onClick={() => !disabled && setIsOpen(!isOpen)}
        disabled={disabled}
        className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold transition-all duration-200
          border border-transparent
          ${disabled
            ? 'text-[var(--muted-foreground)] opacity-40 cursor-not-allowed'
            : 'text-[var(--foreground)] hover:bg-[var(--foreground)]/5 hover:border-[var(--muted-foreground)]/20 cursor-pointer'
          }`}
        title={disabled ? 'Select a project first' : 'Switch system'}
      >
        <Cpu size={11} className="flex-shrink-0 text-[var(--muted-foreground)]" />
        <span className="max-w-[12rem] truncate">
          {activeSystem?.name ?? 'No system'}
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

          {/* Footer action — navigates to /projects with pre-selected project + create=system */}
          <div className="border-t border-[var(--muted-foreground)]/20 p-1.5">
            <Link
              href={newSystemHref}
              onClick={() => setIsOpen(false)}
              className="w-full flex items-center gap-2 px-3 py-2 text-xs text-[var(--foreground)] rounded-xl hover:bg-[var(--foreground)]/5 transition-colors"
            >
              <Plus size={12} className="text-[var(--accent)]" />
              <span>New system</span>
            </Link>
          </div>
        </div>
      )}

      {/* Delete confirmation */}
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

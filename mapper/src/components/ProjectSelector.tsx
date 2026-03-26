"use client";

import { useState, useRef, useEffect } from 'react';
import Link from 'next/link';
import { ChevronDown, Trash2, Plus, Settings } from 'lucide-react';
import { useWorkspace } from '@/context/WorkspaceContext';
import { ConfirmationDialog } from './ConfirmationDialog';
import type { Project } from '@/types';

export function ProjectSelector() {
  const { activeProject, projects, setActiveProject, refreshProjects } = useWorkspace();
  const [isOpen, setIsOpen] = useState(false);
  const [deletingProject, setDeletingProject] = useState<Project | null>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

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

  const handleDelete = async (project: Project) => {
    await fetch(`/api/projects/${project.id}`, { method: 'DELETE' });
    setDeletingProject(null);
    await refreshProjects();
  };

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Trigger */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold transition-all duration-200
          text-[var(--foreground)] hover:bg-[var(--foreground)]/5 border border-transparent
          hover:border-[var(--muted-foreground)]/20"
        title="Switch project"
      >
        <span className="max-w-[10rem] truncate">
          {activeProject?.name ?? 'No project'}
        </span>
        <ChevronDown
          size={12}
          className={`flex-shrink-0 transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`}
        />
      </button>

      {/* Dropdown */}
      {isOpen && (
        <div className="absolute left-0 top-full mt-2 w-72 bg-[var(--background)] border border-[var(--muted-foreground)]/20 rounded-2xl shadow-2xl z-[200] overflow-hidden">
          {/* Project list */}
          <div className="max-h-64 overflow-y-auto py-1.5">
            {projects.length === 0 ? (
              <p className="px-4 py-3 text-xs text-[var(--muted-foreground)]">No projects yet.</p>
            ) : (
              projects.map(project => (
                <div
                  key={project.id}
                  className={`flex items-center justify-between px-4 py-2 cursor-pointer
                    hover:bg-[var(--foreground)]/5 transition-colors
                    ${activeProject?.id === project.id ? 'text-[var(--accent)]' : 'text-[var(--foreground)]'}`}
                  onClick={() => { setActiveProject(project); setIsOpen(false); }}
                >
                  <span className="flex items-center gap-2 text-xs font-semibold min-w-0">
                    {activeProject?.id === project.id && (
                      <span className="flex-shrink-0 w-1.5 h-1.5 rounded-full bg-[var(--accent)]" />
                    )}
                    <span className="truncate">{project.name}</span>
                  </span>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setDeletingProject(project);
                      setIsOpen(false);
                    }}
                    className="ml-2 flex-shrink-0 p-1 rounded-lg hover:bg-red-500/10 text-[var(--muted-foreground)] hover:text-red-500 transition-colors"
                    title={`Delete "${project.name}"`}
                  >
                    <Trash2 size={12} />
                  </button>
                </div>
              ))
            )}
          </div>

          {/* Footer actions */}
          <div className="border-t border-[var(--muted-foreground)]/20 p-1.5 space-y-0.5">
            {/* Navigate to /projects with ?create=project to auto-open the creation form */}
            <Link
              href="/projects?create=project"
              onClick={() => setIsOpen(false)}
              className="w-full flex items-center gap-2 px-3 py-2 text-xs text-[var(--foreground)] rounded-xl hover:bg-[var(--foreground)]/5 transition-colors"
            >
              <Plus size={12} className="text-[var(--accent)]" />
              <span>New project</span>
            </Link>
            <Link
              href="/projects"
              onClick={() => setIsOpen(false)}
              className="w-full flex items-center gap-2 px-3 py-2 text-xs text-[var(--muted-foreground)] rounded-xl hover:bg-[var(--foreground)]/5 transition-colors"
            >
              <Settings size={12} />
              <span>Manage projects →</span>
            </Link>
          </div>
        </div>
      )}

      {/* Delete confirmation */}
      <ConfirmationDialog
        isOpen={!!deletingProject}
        onClose={() => setDeletingProject(null)}
        onConfirm={() => deletingProject && handleDelete(deletingProject)}
        title={`Delete "${deletingProject?.name}"?`}
        description="This will permanently delete the project and all its systems. This action cannot be undone."
        confirmText="Delete project"
        type="danger"
      />
    </div>
  );
}

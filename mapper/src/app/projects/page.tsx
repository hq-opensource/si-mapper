"use client";

/**
 * /projects — Project & System Management Page
 *
 * Two-panel layout:
 *   • Left sidebar  — list of projects, selectable, with create/edit/delete
 *   • Right panel   — system tabs along the top + SystemFilePanel below
 *
 * URL params (read once on mount):
 *   ?create=project           — immediately opens the New Project form
 *   ?create=system&project=ID — selects project <ID> and opens the New System form
 */

import { useState, useEffect, useCallback, useRef, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft, Plus, Pencil, Trash2, FolderOpen, Folder, Server } from 'lucide-react';
import { useWorkspace } from '@/context/WorkspaceContext';
import type { Project, System } from '@/types';
import { ConfirmationDialog } from '@/components/ConfirmationDialog';
import { ProjectEditDialog } from '@/components/ProjectEditDialog';
import { SystemEditDialog } from '@/components/SystemEditDialog';
import { SystemFilePanel } from '@/components/SystemFilePanel';
import { PromptDialog } from '@/components/PromptDialog';
import { cn } from '@/lib/utils';

// ── Colour palette for project folder icons ───────────────────────────────────

const FOLDER_COLORS = [
  { bg: 'bg-indigo-500/15', icon: 'text-indigo-500' },
  { bg: 'bg-violet-500/15', icon: 'text-violet-500' },
  { bg: 'bg-blue-500/15',   icon: 'text-blue-500'   },
  { bg: 'bg-teal-500/15',   icon: 'text-teal-500'   },
  { bg: 'bg-emerald-500/15',icon: 'text-emerald-500' },
  { bg: 'bg-amber-500/15',  icon: 'text-amber-500'  },
  { bg: 'bg-rose-500/15',   icon: 'text-rose-500'   },
];

const DEFAULT_AI_MODEL = 'gemini-2.0-flash';

// ── Inner page (needs useSearchParams — must be inside Suspense) ──────────────

function ProjectsPageInner() {
  const { projects, refreshProjects, isLoading } = useWorkspace();
  const searchParams = useSearchParams();

  // Selection state
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null);
  const [selectedSystemId,  setSelectedSystemId]  = useState<string | null>(null);

  // Systems for the selected project
  const [systems, setSystems]                   = useState<System[]>([]);
  const [isLoadingSystems, setIsLoadingSystems] = useState(false);

  // Project CRUD
  const [showCreateProject, setShowCreateProject] = useState(false);
  const [editingProject,    setEditingProject]    = useState<Project | null>(null);
  const [deletingProject,   setDeletingProject]   = useState<Project | null>(null);

  // System CRUD
  const [showCreateSystem, setShowCreateSystem] = useState(false);
  const [editingSystem,    setEditingSystem]    = useState<System | null>(null);
  const [deletingSystem,   setDeletingSystem]   = useState<System | null>(null);

  const [, setSystemFileCount] = useState<number | null>(null);

  const selectedProject = projects.find(p => p.id === selectedProjectId) ?? null;
  const selectedSystem  = systems.find(s => s.id === selectedSystemId) ?? null;

  // ── Read URL params once on mount ──────────────────────────────────────────

  const urlParamsApplied = useRef(false);

  useEffect(() => {
    if (urlParamsApplied.current || isLoading) return;
    urlParamsApplied.current = true;

    const create    = searchParams.get('create');
    const projectId = searchParams.get('project');

    if (create === 'project') {
      setShowCreateProject(true);
    } else if (create === 'system' && projectId) {
      setSelectedProjectId(projectId);
      setShowCreateSystem(true);
    }
  }, [searchParams, isLoading]);

  // Auto-select first project after load (only if no URL param already set one)
  useEffect(() => {
    if (!isLoading && projects.length > 0 && !selectedProjectId) {
      setSelectedProjectId(projects[0].id);
    }
  }, [isLoading, projects, selectedProjectId]);

  // ── Systems ────────────────────────────────────────────────────────────────

  const fetchSystems = useCallback(async (projectId: string) => {
    setIsLoadingSystems(true);
    try {
      const res = await fetch(`/api/projects/${projectId}/systems`);
      if (res.ok) {
        const data: System[] = await res.json();
        setSystems(data);
        setSelectedSystemId(prev =>
          data.some(s => s.id === prev) ? prev : data.length > 0 ? data[0].id : null,
        );
      }
    } finally {
      setIsLoadingSystems(false);
    }
  }, []);

  useEffect(() => {
    if (selectedProjectId) {
      fetchSystems(selectedProjectId);
    } else {
      setSystems([]);
      setSelectedSystemId(null);
    }
  }, [selectedProjectId, fetchSystems]);

  // ── CRUD handlers ──────────────────────────────────────────────────────────

  const handleCreateProject = async (name: string) => {
    const res = await fetch('/api/projects', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name }),
    });
    if (res.ok) {
      const created: Project = await res.json();
      await refreshProjects();
      setSelectedProjectId(created.id);
    }
  };

  const handleDeleteProject = async () => {
    if (!deletingProject) return;
    await fetch(`/api/projects/${deletingProject.id}`, { method: 'DELETE' });
    if (selectedProjectId === deletingProject.id) setSelectedProjectId(null);
    await refreshProjects();
    setDeletingProject(null);
  };

  const handleCreateSystem = async (name: string) => {
    if (!selectedProjectId) return;
    const res = await fetch(`/api/projects/${selectedProjectId}/systems`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, ai_model_name: DEFAULT_AI_MODEL }),
    });
    if (res.ok) {
      const created: System = await res.json();
      await fetchSystems(selectedProjectId);
      setSelectedSystemId(created.id);
    }
  };

  const handleDeleteSystem = async () => {
    if (!deletingSystem || !selectedProjectId) return;
    await fetch(
      `/api/projects/${selectedProjectId}/systems/${deletingSystem.id}`,
      { method: 'DELETE' },
    );
    await fetchSystems(selectedProjectId);
    setDeletingSystem(null);
  };

  // ── Render ─────────────────────────────────────────────────────────────────

  return (
    <div className="h-screen flex flex-col bg-[var(--background)] overflow-hidden">

      {/* Page header */}
      <header className="flex items-center gap-4 px-6 py-4 border-b border-[var(--muted-foreground)]/15 flex-shrink-0">
        <Link
          href="/"
          className="flex items-center gap-1.5 text-sm text-[var(--muted-foreground)] hover:text-[var(--foreground)] transition-colors"
        >
          <ArrowLeft size={14} />
          Back
        </Link>
        <span className="text-[var(--muted-foreground)]/30 select-none">|</span>
        <h1 className="text-xs font-black text-[var(--foreground)] uppercase tracking-[0.2em]">
          Project Management
        </h1>
      </header>

      {/* Two-panel body */}
      <div className="flex flex-1 overflow-hidden">

        {/* LEFT SIDEBAR — Projects list */}
        <aside className="w-60 flex-shrink-0 border-r border-[var(--muted-foreground)]/15 flex flex-col bg-[var(--background)]">
          <div className="flex items-center justify-between px-4 py-3 border-b border-[var(--muted-foreground)]/10">
            <span className="text-[10px] font-black text-[var(--muted-foreground)] uppercase tracking-[0.18em]">
              Projects
            </span>
            <button
              onClick={() => setShowCreateProject(true)}
              className="p-1.5 rounded-lg hover:bg-[var(--accent)]/10 text-[var(--muted-foreground)] hover:text-[var(--accent)] transition-colors"
              title="New project"
            >
              <Plus size={14} />
            </button>
          </div>

          <div className="flex-1 overflow-y-auto py-2 space-y-0.5 px-2">
            {isLoading ? (
              <p className="text-xs text-[var(--muted-foreground)] text-center py-8">Loading…</p>
            ) : projects.length === 0 ? (
              <div className="px-2 py-10 text-center space-y-2">
                <p className="text-xs text-[var(--muted-foreground)]">No projects yet.</p>
                <button
                  onClick={() => setShowCreateProject(true)}
                  className="text-xs font-bold text-[var(--accent)] hover:underline"
                >
                  Create one →
                </button>
              </div>
            ) : (
              projects.map((project, idx) => {
                const color    = FOLDER_COLORS[idx % FOLDER_COLORS.length];
                const isActive = project.id === selectedProjectId;
                return (
                  <div
                    key={project.id}
                    role="button"
                    tabIndex={0}
                    onClick={() => setSelectedProjectId(project.id)}
                    onKeyDown={e => e.key === 'Enter' && setSelectedProjectId(project.id)}
                    className={cn(
                      'group flex items-center gap-2.5 px-2.5 py-2 rounded-xl cursor-pointer transition-all duration-200 border',
                      isActive
                        ? 'bg-[var(--accent)]/10 border-[var(--accent)]/20'
                        : 'hover:bg-[var(--foreground)]/[0.035] border-transparent',
                    )}
                  >
                    <div className={cn('w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0', color.bg)}>
                      {isActive
                        ? <FolderOpen size={15} className={color.icon} />
                        : <Folder     size={15} className={color.icon} />
                      }
                    </div>
                    <span className={cn(
                      'flex-1 text-xs font-bold truncate transition-colors',
                      isActive ? 'text-[var(--accent)]' : 'text-[var(--foreground)]',
                    )}>
                      {project.name}
                    </span>
                    <div className="flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0">
                      <button
                        onClick={e => { e.stopPropagation(); setEditingProject(project); }}
                        className="p-1 rounded hover:bg-[var(--foreground)]/10 text-[var(--muted-foreground)] hover:text-[var(--foreground)] transition-colors"
                        title="Rename project"
                      >
                        <Pencil size={11} />
                      </button>
                      <button
                        onClick={e => { e.stopPropagation(); setDeletingProject(project); }}
                        className="p-1 rounded hover:bg-red-500/10 text-[var(--muted-foreground)] hover:text-red-500 transition-colors"
                        title="Delete project"
                      >
                        <Trash2 size={11} />
                      </button>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </aside>

        {/* RIGHT PANEL — Systems & Files */}
        <main className="flex-1 flex flex-col overflow-hidden">
          {selectedProject ? (
            <>
              {/* System tabs strip */}
              <div className="flex items-center gap-1.5 px-6 py-3 border-b border-[var(--muted-foreground)]/15 overflow-x-auto flex-shrink-0">
                <span className="text-[10px] font-black text-[var(--muted-foreground)] uppercase tracking-[0.18em] pr-3 border-r border-[var(--muted-foreground)]/15 mr-0.5 flex-shrink-0">
                  Systems
                </span>
                {isLoadingSystems ? (
                  <span className="text-xs text-[var(--muted-foreground)] italic">Loading…</span>
                ) : systems.length === 0 ? (
                  <span className="text-xs text-[var(--muted-foreground)] italic">No systems yet</span>
                ) : (
                  systems.map(sys => {
                    const isActive = sys.id === selectedSystemId;
                    return (
                      <div key={sys.id} className="group flex items-center gap-0 flex-shrink-0">
                        <button
                          onClick={() => setSelectedSystemId(sys.id)}
                          className={cn(
                            'flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-sm font-bold transition-all duration-200 border',
                            isActive
                              ? 'text-[var(--accent)] bg-[var(--accent)]/15 border-[var(--accent)]/10 shadow-sm'
                              : 'text-[var(--muted-foreground)] hover:text-[var(--foreground)] hover:bg-[var(--foreground)]/5 border-transparent',
                          )}
                        >
                          <Server size={12} />
                          {sys.name}
                        </button>
                        <div className={cn(
                          'flex items-center gap-0 transition-all duration-200 overflow-hidden',
                          isActive ? 'w-auto opacity-100 ml-0.5' : 'w-0 opacity-0',
                        )}>
                          <button
                            onClick={() => setEditingSystem(sys)}
                            className="p-1.5 rounded-lg hover:bg-[var(--foreground)]/10 text-[var(--muted-foreground)] hover:text-[var(--foreground)] transition-colors"
                            title="Edit system"
                          >
                            <Pencil size={11} />
                          </button>
                          <button
                            onClick={() => setDeletingSystem(sys)}
                            className="p-1.5 rounded-lg hover:bg-red-500/10 text-[var(--muted-foreground)] hover:text-red-500 transition-colors"
                            title="Delete system"
                          >
                            <Trash2 size={11} />
                          </button>
                        </div>
                      </div>
                    );
                  })
                )}
                <button
                  onClick={() => setShowCreateSystem(true)}
                  className="flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-bold text-[var(--muted-foreground)] hover:text-[var(--accent)] hover:bg-[var(--accent)]/10 border border-dashed border-[var(--muted-foreground)]/25 hover:border-[var(--accent)]/30 transition-all flex-shrink-0"
                >
                  <Plus size={12} />
                  New system
                </button>
              </div>

              {/* File panel area */}
              <div className="flex-1 overflow-y-auto p-6">
                {selectedSystem ? (
                  <div className="h-full min-h-0 border border-[var(--muted-foreground)]/20 rounded-2xl overflow-hidden shadow-sm">
                    <SystemFilePanel
                      projectId={selectedProject.id}
                      systemId={selectedSystem.id}
                      systemName={selectedSystem.name}
                      isOpen={true}
                      onFileCountChange={setSystemFileCount}
                      className="h-full bg-[var(--background)]"
                    />
                  </div>
                ) : (
                  <div className="flex items-center justify-center h-full">
                    <div className="text-center">
                      <div className="w-16 h-16 rounded-full bg-[var(--accent)]/10 flex items-center justify-center mx-auto mb-4">
                        <Server size={28} className="text-[var(--accent)] opacity-60" />
                      </div>
                      <p className="text-sm font-bold text-[var(--foreground)] mb-1">
                        {systems.length === 0 ? 'No systems yet' : 'Select a system'}
                      </p>
                      <p className="text-xs text-[var(--muted-foreground)]">
                        {systems.length === 0
                          ? 'Click "New system" above to get started.'
                          : 'Choose a system tab above to manage its files.'}
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </>
          ) : (
            <div className="flex items-center justify-center flex-1">
              <div className="text-center">
                <div className="w-16 h-16 rounded-full bg-[var(--accent)]/10 flex items-center justify-center mx-auto mb-4">
                  <Folder size={28} className="text-[var(--accent)] opacity-60" />
                </div>
                <p className="text-sm font-bold text-[var(--foreground)] mb-1">Select a project</p>
                <p className="text-xs text-[var(--muted-foreground)]">
                  Choose a project from the sidebar to view its systems and files.
                </p>
              </div>
            </div>
          )}
        </main>
      </div>

      {/* Dialogs */}
      <PromptDialog
        isOpen={showCreateProject}
        onClose={() => setShowCreateProject(false)}
        onConfirm={handleCreateProject}
        title="New Project"
        description="Enter a name for the new project."
        placeholder="e.g. Building A — HVAC"
        confirmText="Create"
      />
      <PromptDialog
        isOpen={showCreateSystem}
        onClose={() => setShowCreateSystem(false)}
        onConfirm={handleCreateSystem}
        title="New System"
        description="Enter a name for the new system."
        placeholder="e.g. Chilled Water Plant"
        confirmText="Create"
      />
      {editingProject && (
        <ProjectEditDialog
          isOpen={true}
          onClose={() => setEditingProject(null)}
          project={editingProject}
          onSuccess={async () => { await refreshProjects(); setEditingProject(null); }}
        />
      )}
      {editingSystem && selectedProject && (
        <SystemEditDialog
          isOpen={true}
          onClose={() => setEditingSystem(null)}
          projectId={selectedProject.id}
          system={editingSystem}
          onSuccess={async () => { await fetchSystems(selectedProject.id); setEditingSystem(null); }}
        />
      )}
      <ConfirmationDialog
        isOpen={!!deletingProject}
        onClose={() => setDeletingProject(null)}
        onConfirm={handleDeleteProject}
        title={`Delete "${deletingProject?.name}"?`}
        description="This will permanently delete the project, all its systems, and all associated files. This action cannot be undone."
        confirmText="Delete project"
        type="danger"
      />
      <ConfirmationDialog
        isOpen={!!deletingSystem}
        onClose={() => setDeletingSystem(null)}
        onConfirm={handleDeleteSystem}
        title={`Delete "${deletingSystem?.name}"?`}
        description="This will permanently delete the system and all associated files. This action cannot be undone."
        confirmText="Delete system"
        type="danger"
      />
    </div>
  );
}

// ── Page export (Suspense required for useSearchParams in App Router) ─────────

export default function ProjectsPage() {
  return (
    <Suspense>
      <ProjectsPageInner />
    </Suspense>
  );
}

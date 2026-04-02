"use client";

import { useState, useEffect, useMemo } from "react";
import { ExternalPageIframe } from "./ExternalPageIframe";
import { AgentNavbar } from "./AgentNavbar";
import { type AgentState } from "./AgentStateOverlay";
import { SvarFileManager } from "@/components/SvarFileManager";
import { Folder, Eye, Edit3, FolderPlus, Server } from "lucide-react";
import { ThoughtsWindow } from "./ThoughtsWindow";
import { ToolCallsWindow } from "./ToolCallsWindow";
import { StateWindow } from "./StateWindow";
import { SharedPageContainer } from "./SharedPageContainer";
import { PerformanceDashboard } from "./PerformanceDashboard";
import { ArtifactsDashboard } from "./ArtifactsDashboard";
import { CodeWindow } from "./CodeWindow";
import { useWorkspace } from "@/context/WorkspaceContext";
import { PromptDialog } from "@/components/PromptDialog";
import type { Project, System } from "@/types";
import dynamic from "next/dynamic";
const GraphWindow = dynamic(
  () => import("./GraphWindow").then((m) => ({ default: m.GraphWindow })),
  { ssr: false }
);

interface GraphivacConfig {
  graphivacBaseUrl: string;
  graphivacOrgId: string;
}

// Define WorkAreaWrapper outside to prevent remounting subcomponents on every render (stable component tree)
const WorkAreaWrapper = ({ children }: { children: React.ReactNode }) => (
  <div className="w-full h-full flex flex-col p-6 pt-24 bg-[var(--background)]">
    <div className="flex-1 w-full rounded-[1.5rem] border border-[var(--muted-foreground)]/20 overflow-hidden bg-[var(--background)] shadow-[0_20px_50px_rgba(0,0,0,0.1)] transition-all duration-700 hover:border-[var(--accent)]/40 group relative">
      <div className="absolute inset-0 bg-gradient-to-br from-[var(--accent)]/[0.02] to-transparent pointer-events-none z-0" />
      <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-[var(--accent)]/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-1000 z-10 pointer-events-none" />
      <div className="relative z-10 h-full w-full">
        {children}
      </div>
    </div>
  </div>
);

// ── Zero state screens ────────────────────────────────────────────────────────

function ZeroProjectState() {
  const { refreshProjects, setActiveProject } = useWorkspace();
  const [showPrompt, setShowPrompt] = useState(false);

  const handleCreate = async (name: string) => {
    const res = await fetch('/api/projects', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name }),
    });
    if (res.ok) {
      const created: Project = await res.json();
      await refreshProjects();
      await setActiveProject(created);
    }
  };

  return (
    <div className="absolute inset-0 z-20 flex flex-col items-center justify-center gap-6 bg-[var(--background)]">
      <div className="w-20 h-20 rounded-full bg-[var(--accent)]/10 flex items-center justify-center">
        <FolderPlus size={36} className="text-[var(--accent)]" />
      </div>
      <div className="text-center">
        <h2 className="text-2xl font-black text-[var(--foreground)] mb-2">No projects yet</h2>
        <p className="text-sm text-[var(--muted-foreground)] max-w-xs">
          Create your first project to start modelling HVAC systems.
        </p>
      </div>
      <button
        onClick={() => setShowPrompt(true)}
        className="px-6 py-3 bg-[var(--accent)] text-white rounded-2xl font-bold text-sm hover:opacity-90 transition-opacity shadow-lg"
      >
        + New project
      </button>
      <PromptDialog
        isOpen={showPrompt}
        onClose={() => setShowPrompt(false)}
        onConfirm={handleCreate}
        title="New Project"
        description="Enter a name for the new project."
        placeholder="e.g. Building A — HVAC"
        confirmText="Create"
      />
    </div>
  );
}

function ZeroSystemState() {
  const { activeProject, refreshSystems, setActiveSystem } = useWorkspace();
  const [showPrompt, setShowPrompt] = useState(false);

  const handleCreate = async (name: string) => {
    if (!activeProject) return;
    const res = await fetch(`/api/projects/${activeProject.id}/systems`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name }),
    });
    if (res.ok) {
      const created: System = await res.json();
      await refreshSystems();
      setActiveSystem(created);
    }
  };

  return (
    <div className="absolute inset-0 z-20 flex flex-col items-center justify-center gap-6 bg-[var(--background)]">
      <div className="w-20 h-20 rounded-full bg-[var(--accent)]/10 flex items-center justify-center">
        <Server size={36} className="text-[var(--accent)]" />
      </div>
      <div className="text-center">
        <h2 className="text-2xl font-black text-[var(--foreground)] mb-2">No systems yet</h2>
        <p className="text-sm text-[var(--muted-foreground)] max-w-xs">
          Add a system to this project to start drawing your HVAC diagram.
        </p>
      </div>
      <button
        onClick={() => setShowPrompt(true)}
        className="px-6 py-3 bg-[var(--accent)] text-white rounded-2xl font-bold text-sm hover:opacity-90 transition-opacity shadow-lg"
      >
        + New system
      </button>
      <PromptDialog
        isOpen={showPrompt}
        onClose={() => setShowPrompt(false)}
        onConfirm={handleCreate}
        title="New System"
        description="Enter a name for the new system."
        placeholder="e.g. Chilled Water Plant"
        confirmText="Create"
      />
    </div>
  );
}

// ── YourMainContent ───────────────────────────────────────────────────────────

function YourMainContent({
  isEditMode,
  agentState,
  onUseSession,
  onNewSession,
  threadId,
  sessions,
}: {
  isEditMode: boolean,
  agentState: AgentState,
  onUseSession: (sessionId: string) => void,
  onNewSession: (name: string) => void,
  threadId?: string | null,
  sessions?: import('@/types').Session[],
}) {
  const [activeTab, setActiveTab] = useState<'thoughts' | 'files' | 'view' | 'edit' | 'graph' | 'debug' | 'tools' | 'state' | 'performance' | 'artifacts' | 'python' | 'ttl'>(isEditMode ? 'edit' : 'view');
  const [theme, setTheme] = useState<'light' | 'dark'>('light');
  const [graphivacConfig, setGraphivacConfig] = useState<GraphivacConfig | null>(null);

  const { activeProject, activeSystem, projects, systems, isLoading } = useWorkspace();

  // Fetch /api/config once on mount
  useEffect(() => {
    fetch('/api/config')
      .then(r => r.ok ? r.json() : null)
      .then(data => data && setGraphivacConfig(data))
      .catch(console.error);
  }, []);

  // Initialize theme
  useEffect(() => {
    const savedTheme = localStorage.getItem('app-theme') as 'light' | 'dark' | null;
    const initialTheme = savedTheme || 'light';
    setTheme(initialTheme);
    document.documentElement.className = initialTheme;
  }, []);

  const toggleTheme = () => {
    const newTheme = theme === 'light' ? 'dark' : 'light';
    setTheme(newTheme);
    document.documentElement.className = newTheme;
    localStorage.setItem('app-theme', newTheme);
  };

  const handleTabChange = (tab: typeof activeTab) => {
    setActiveTab(tab);
  };

  const [visitedTabs, setVisitedTabs] = useState<Set<string>>(new Set([activeTab]));

  useEffect(() => {
    setVisitedTabs(prev => {
      if (prev.has(activeTab)) return prev;
      const next = new Set(prev);
      next.add(activeTab);
      return next;
    });
  }, [activeTab]);

  // Derive Graphivac iframe base URL from context + config
  const gridBaseUrl = useMemo(() => {
    if (!graphivacConfig || !activeProject || !activeSystem) return '';
    const { graphivacBaseUrl, graphivacOrgId } = graphivacConfig;
    if (!graphivacBaseUrl || !graphivacOrgId) return '';
    const { graphivac_project_id } = activeProject;
    const { graphivac_grid_id } = activeSystem;
    if (!graphivac_project_id || !graphivac_grid_id) return '';
    return `${graphivacBaseUrl}/o/${graphivacOrgId}/p/${graphivac_project_id}/g/${graphivac_grid_id}`;
  }, [graphivacConfig, activeProject, activeSystem]);

  // Zero-state flags
  const noProjects = !isLoading && projects.length === 0;
  const noSystems = !isLoading && !!activeProject && systems.length === 0;
  const showZeroState = noProjects || noSystems;

  return (
    <div
      style={{ backgroundColor: "var(--background)" }}
      className="h-full w-full flex justify-center items-center flex-col transition-colors duration-300 relative overflow-hidden"
    >
      {/* Top Navbar */}
      <AgentNavbar
        agentState={agentState}
        activeTab={activeTab}
        onTabChange={handleTabChange}
        onUseSession={onUseSession}
        onNewSession={onNewSession}
        threadId={threadId}
        sessions={sessions ?? []}
      />

      {/* Main Content Area */}
      <div className="w-full h-full relative z-10">
        <WorkAreaWrapper>
          <div className="w-full h-full relative">
            {/* Zero-state overlays (rendered over tab content) */}
            {!isLoading && noProjects && (
              <ZeroProjectState />
            )}
            {!isLoading && noSystems && !noProjects && (
              <ZeroSystemState />
            )}

            {/* Tab content (hidden while zero state, still mounted for stable tree) */}
            {!showZeroState && Array.from(visitedTabs).map((tab) => (
              <div
                key={tab}
                className={`absolute inset-0 w-full h-full transition-opacity duration-300 ${activeTab === tab ? "opacity-100 z-10 pointer-events-auto" : "opacity-0 z-0 pointer-events-none"}`}
              >
                {(() => {
                  switch (tab) {
                    case 'thoughts': return <ThoughtsWindow />;
                    case 'tools': return <ToolCallsWindow />;
                    case 'state': return <StateWindow />;
                    case 'performance': return <PerformanceDashboard />;
                    case 'artifacts': return <ArtifactsDashboard />;
                    case 'python': return <CodeWindow type="python" />;
                    case 'ttl': return <CodeWindow type="ttl" />;
                    case 'graph': return <GraphWindow />;
                    case 'files': return (
                      <SharedPageContainer title="File Repository" subtitle="Agent Resource Management" icon={Folder} fullWidth fullHeight noPadding>
                        <SvarFileManager />
                      </SharedPageContainer>
                    );
                    case 'view': return (
                      <SharedPageContainer title="View Mode" subtitle="Real-time Asset Monitoring" icon={Eye} fullWidth fullHeight>
                        <ExternalPageIframe src={gridBaseUrl ? `${gridBaseUrl}?iframe=t&init-zoom=t` : ''} />
                      </SharedPageContainer>
                    );
                    case 'edit': return (
                      <SharedPageContainer title="Edit Mode" subtitle="Interactive System Configuration" icon={Edit3} fullWidth fullHeight>
                        <ExternalPageIframe src={gridBaseUrl ? `${gridBaseUrl}?mode=editor&init-zoom=t` : ''} />
                      </SharedPageContainer>
                    );
                    case 'debug': return (
                      <div className="w-full h-full overflow-y-auto p-12 transition-colors duration-300">
                        <div className="w-full space-y-12">
                          <div className="flex items-center justify-between">
                            <h1 className="text-3xl font-bold text-[var(--foreground)]">Theme Debugger</h1>
                            <button onClick={toggleTheme} className="px-6 py-3 bg-[var(--accent)] text-white rounded-xl font-bold shadow-lg hover:opacity-90 transition-all scale-100 active:scale-95">
                              Switch to {theme === 'light' ? 'Dark' : 'Light'} Mode
                            </button>
                          </div>
                          <div className="p-8 border-2 border-dashed border-[var(--muted-foreground)]/30 rounded-3xl">
                            <h3 className="text-lg font-bold text-[var(--foreground)] mb-4">Sample Card (CSS Variables)</h3>
                            <div className="bg-[var(--background)] border border-[var(--muted-foreground)]/20 rounded-2xl p-6 shadow-xl">
                              <h4 className="text-xl font-black text-[var(--foreground)] mb-2">Dual Boiler HVAC Design</h4>
                              <p className="text-[var(--foreground)] opacity-80 mb-4">Theme check for persistence.</p>
                            </div>
                          </div>
                        </div>
                      </div>
                    );
                    default: return null;
                  }
                })()}
              </div>
            ))}
          </div>
        </WorkAreaWrapper>
      </div>
    </div>
  );
}
export { YourMainContent };
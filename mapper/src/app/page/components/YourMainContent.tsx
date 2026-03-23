"use client";

import { useState, useEffect } from "react";
import { ExternalPageIframe } from "./ExternalPageIframe";
import { AgentNavbar } from "./AgentNavbar"; // New component
import { type AgentState } from "./AgentStateOverlay";
import { SvarFileManager } from "@/components/SvarFileManager";
import { Folder, Eye, Edit3 } from "lucide-react";
import { ThoughtsWindow } from "./ThoughtsWindow";
import { ToolCallsWindow } from "./ToolCallsWindow";
import { StateWindow } from "./StateWindow";
import { SharedPageContainer } from "./SharedPageContainer";
import { PerformanceDashboard } from "./PerformanceDashboard";
import { ArtifactsDashboard } from "./ArtifactsDashboard";
import { CodeWindow } from "./CodeWindow";
import dynamic from "next/dynamic";
const GraphWindow = dynamic(
  () => import("./GraphWindow").then((m) => ({ default: m.GraphWindow })),
  { ssr: false }
);

// Define WorkAreaWrapper outside to prevent remounting subcomponents on every render (stable component tree)
const WorkAreaWrapper = ({ children }: { children: React.ReactNode }) => (
  <div className="w-full h-full flex flex-col p-6 pt-24 bg-[var(--background)]">
    <div className="flex-1 w-full rounded-[1.5rem] border border-[var(--muted-foreground)]/20 overflow-hidden bg-[var(--background)] shadow-[0_20px_50px_rgba(0,0,0,0.1)] transition-all duration-700 hover:border-[var(--accent)]/40 group relative">
      {/* Subtle Interactive Glow - Rendered behind for depth */}
      <div className="absolute inset-0 bg-gradient-to-br from-[var(--accent)]/[0.02] to-transparent pointer-events-none z-0" />
      <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-[var(--accent)]/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-1000 z-10 pointer-events-none" />
      
      <div className="relative z-10 h-full w-full">
        {children}
      </div>
    </div>
  </div>
);

function YourMainContent({ isEditMode, agentState }: { isEditMode: boolean, agentState: AgentState }) {
  // Determine initial view based on props but allow internal navigation
  const [activeTab, setActiveTab] = useState<'thoughts' | 'files' | 'view' | 'edit' | 'graph' | 'debug' | 'tools' | 'state' | 'performance' | 'artifacts' | 'python' | 'ttl'>(isEditMode ? 'edit' : 'view');
  const [theme, setTheme] = useState<'light' | 'dark'>('light');
  // Initialize theme: Default to light mode, ignore system preference
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

  const handleTabChange = (tab: 'thoughts' | 'files' | 'view' | 'edit' | 'graph' | 'debug' | 'tools' | 'state' | 'performance' | 'artifacts' | 'python' | 'ttl') => {
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
      />

      {/* Main Content Area */}
      <div className="w-full h-full relative z-10">
        <WorkAreaWrapper>
          <div className="w-full h-full relative">
            {Array.from(visitedTabs).map((tab) => (
              <div 
                key={tab} 
                className={`absolute inset-0 w-full h-full transition-opacity duration-300 ${activeTab === tab ? "opacity-100 z-10 pointer-events-auto" : "opacity-0 z-0 pointer-events-none"}`}
              >
                {/* We need a specialized renderContent that takes the tab name */}
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
                        <ExternalPageIframe src="https://graphivac.hvac.io/o/public/p/P-j8QIvTGH7p/g/G-LAiRS3mgp6?iframe=t&init-zoom=t" />
                      </SharedPageContainer>
                    );
                    case 'edit': return (
                      <SharedPageContainer title="Edit Mode" subtitle="Interactive System Configuration" icon={Edit3} fullWidth fullHeight>
                        <ExternalPageIframe src="https://graphivac.hvac.io/o/public/p/P-j8QIvTGH7p/g/G-LAiRS3mgp6?mode=editor&init-zoom=t" />
                      </SharedPageContainer>
                    );
                    case 'debug': return (
                      <div className="w-full h-full overflow-y-auto p-12 transition-colors duration-300">
                        {/* Summary of debug content */}
                        <div className="w-full space-y-12">
                          <div className="flex items-center justify-between">
                            <h1 className="text-3xl font-bold text-[var(--foreground)]">Theme Debugger</h1>
                            <button onClick={toggleTheme} className="px-6 py-3 bg-[var(--accent)] text-white rounded-xl font-bold shadow-lg hover:opacity-90 transition-all scale-100 active:scale-95">
                              Switch to {theme === 'light' ? 'Dark' : 'Light'} Mode
                            </button>
                          </div>
                          {/* ... more debug content could be here, but for brevity we'll keep it simple or use the old renderContent logic if preferred */}
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
"use client";

import { useState, useEffect } from "react";
import { ExternalPageIframe } from "./ExternalPageIframe";
import { AgentNavbar } from "./AgentNavbar"; // New component
import { type AgentState } from "./AgentStateOverlay";
import { SvarFileManager } from "@/components/SvarFileManager";
import { Markdown } from "@copilotkit/react-ui";
import { FileText, BarChart2, Folder, Eye, Edit3 } from "lucide-react";
import { ThoughtsWindow } from "./ThoughtsWindow";
import { ToolCallsWindow } from "./ToolCallsWindow";
import { TasksWindow } from "./TasksWindow";
import { StateWindow } from "./StateWindow";
import { SharedPageContainer } from "./SharedPageContainer";
import { StatusPlaceholder } from "./StatusPlaceholder";

// Define WorkAreaWrapper outside to prevent remounting subcomponents on every render (stable component tree)
const WorkAreaWrapper = ({ children }: { children: React.ReactNode }) => (
  <div className="w-full h-full flex flex-col p-6 pt-24 bg-[var(--background)]">
    <div className="flex-1 w-full rounded-[1.5rem] border border-[var(--muted-foreground)]/20 overflow-hidden bg-[var(--background)] shadow-[0_20px_50px_rgba(0,0,0,0.1)] transition-all duration-700 hover:border-[var(--accent)]/40 group relative">
      {children}

      {/* Subtle Interactive Glow - Rendered on top for depth */}
      <div className="absolute inset-0 bg-gradient-to-br from-[var(--accent)]/[0.02] to-transparent pointer-events-none z-20" />
      <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-[var(--accent)]/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-1000 z-20 pointer-events-none" />
    </div>
  </div>
);

function YourMainContent({ isEditMode, agentState }: { isEditMode: boolean, agentState: AgentState }) {
  // Determine initial view based on props but allow internal navigation
  const [activeTab, setActiveTab] = useState<'thoughts' | 'plans' | 'todo' | 'files' | 'view' | 'edit' | 'graph' | 'debug' | 'tools' | 'state'>(isEditMode ? 'edit' : 'view');
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

  const handleTabChange = (tab: 'thoughts' | 'plans' | 'todo' | 'files' | 'view' | 'edit' | 'graph' | 'debug' | 'tools' | 'state') => {
    setActiveTab(tab);
  };

  // Helper for plan formatting (reused from previous overlay logic)
  const formatPlanContent = (content: string) => {
    if (!content) return "";
    return content
      .replace(/\[NEW\]/g, '✨ **NEW**')
      .replace(/\[MODIFY\]/g, '🔨 **MODIFY**')
      .replace(/\[REMOVE\]/g, '🗑️ **REMOVE**')
      .replace(/\[IMPORTANT\]/g, '⚠️ **IMPORTANT**')
      .replace(/\[NOTE\]/g, '📝 **NOTE**')
      .replace(/\[INFO\]/g, 'ℹ️ **INFO**');
  };

  const renderContent = () => {
    switch (activeTab) {
      case 'thoughts':
        return <ThoughtsWindow />;
      case 'tools':
        return <ToolCallsWindow />;
      case 'state':
        return <StateWindow />;

      case 'plans':
        return (
          <SharedPageContainer
            title="Plans"
            subtitle="Agent Created Plans"
            icon={FileText}
            fullWidth
            fullHeight
          >
            {
              agentState.plan ? (
                <div className="prose prose-sm max-w-none 
                                  prose-headings:font-bold prose-headings:text-[var(--foreground)] 
                                  prose-p:text-[var(--foreground)] prose-p:leading-relaxed
                                  prose-li:text-[var(--foreground)] prose-li:marker:text-[var(--muted-foreground)]
                                  prose-strong:text-[var(--foreground)] prose-strong:font-extrabold
                                  prose-hr:border-[var(--muted-foreground)]
                                  prose-pre:bg-[var(--card-foreground)] prose-pre:text-[var(--background)]
                              ">
                  <Markdown content={formatPlanContent(agentState.plan)} />
                </div>
              ) : (
                <StatusPlaceholder
                  icon={FileText}
                  title="No Plan Available"
                  subtitle="Agent has not generated a proposal yet"
                />
              )}
          </SharedPageContainer>
        );
      case 'todo':
        return <TasksWindow />;
      case 'view':
        return (
          <SharedPageContainer
            title="View Mode"
            subtitle="Real-time Asset Monitoring"
            icon={Eye}
            fullWidth
            fullHeight
          >
            <ExternalPageIframe src="https://graphivac.hvac.io/o/public/p/P-j8QIvTGH7p/g/G-LAiRS3mgp6?iframe=t&init-zoom=t" />
          </SharedPageContainer>
        );
      case 'edit':
        return (
          <SharedPageContainer
            title="Edit Mode"
            subtitle="Interactive System Configuration"
            icon={Edit3}
            fullWidth
            fullHeight
          >
            <ExternalPageIframe src="https://graphivac.hvac.io/o/public/p/P-j8QIvTGH7p/g/G-LAiRS3mgp6?mode=editor&init-zoom=t" />
          </SharedPageContainer>
        );
      case 'files':
        return (
          <SharedPageContainer
            title="File Repository"
            subtitle="Agent Resource Management"
            icon={Folder}
            fullWidth
            fullHeight
          >
            <SvarFileManager />
          </SharedPageContainer>
        );
      case 'graph':
        return (
          <SharedPageContainer
            title="Architecture Graph"
            subtitle="Visual System Topology"
            icon={BarChart2}
            fullWidth
            fullHeight
          >
            <StatusPlaceholder
              icon={BarChart2}
              title="Graph Mode"
              subtitle="Coming Soon"
            />
          </SharedPageContainer>
        );
      case 'debug':
        const colorVars = [
          { name: '--background', value: 'var(--background)' },
          { name: '--foreground', value: 'var(--foreground)' },
          { name: '--card-foreground', value: 'var(--card-foreground)' },
          { name: '--muted-foreground', value: 'var(--muted-foreground)' },
          { name: '--accent', value: 'var(--accent)' },
        ];
        return (
          <div className="w-full h-full overflow-y-auto p-12 transition-colors duration-300">
            <div className="w-full space-y-12">
              <div className="flex items-center justify-between">
                <h1 className="text-3xl font-bold text-[var(--foreground)]">Theme Debugger</h1>
                <button
                  onClick={toggleTheme}
                  className="px-6 py-3 bg-[var(--accent)] text-white rounded-xl font-bold shadow-lg hover:opacity-90 transition-all scale-100 active:scale-95"
                >
                  Switch to {theme === 'light' ? 'Dark' : 'Light'} Mode
                </button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                {/* Color Samples */}
                <div className="space-y-6">
                  <h2 className="text-xl font-bold text-[var(--foreground)] border-b border-[var(--muted-foreground)]/20 pb-2">CSS Variables (Boxes)</h2>
                  <div className="grid grid-cols-2 gap-4">
                    {colorVars.map((v) => (
                      <div key={v.name} className="flex flex-col gap-2">
                        <div
                          className="h-24 w-full rounded-2xl shadow-inner border border-[var(--muted-foreground)]/10"
                          style={{ backgroundColor: v.value }}
                        ></div>
                        <span className="text-xs font-mono text-[var(--muted-foreground)]">{v.name}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Typography Samples */}
                <div className="space-y-6">
                  <h2 className="text-xl font-bold text-[var(--foreground)] border-b border-[var(--muted-foreground)]/20 pb-2">Typography & Content</h2>
                  <div className="space-y-4">
                    <p className="text-[var(--foreground)] font-bold">This is --foreground text (Bold)</p>
                    <p className="text-[var(--foreground)]">This is --foreground text (Regular). It should be dark in light mode and white in dark mode.</p>
                    <p className="text-[var(--muted-foreground)]">This is --muted-foreground text. It should be gray.</p>
                    <p className="text-[var(--accent)] font-bold">This is --accent text. It should be purple/indigo.</p>
                    <div className="p-4 bg-[var(--card-foreground)] text-[var(--background)] rounded-lg">
                      This is --background text on a --card-foreground background.
                    </div>
                  </div>
                </div>
              </div>

              {/* Real World Test */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                <div className="p-8 border-2 border-dashed border-[var(--muted-foreground)]/30 rounded-3xl">
                  <h3 className="text-lg font-bold text-[var(--foreground)] mb-4">Sample Card (CSS Variables)</h3>
                  <div className="bg-[var(--background)] border border-[var(--muted-foreground)]/20 rounded-2xl p-6 shadow-xl">
                    <h4 className="text-xl font-black text-[var(--foreground)] mb-2">Dual Boiler HVAC Design</h4>
                    <p className="text-[var(--foreground)] opacity-80 mb-4">
                      This card uses <code>var(--foreground)</code> for text and <code>var(--background)</code> for its interior background.
                    </p>
                    <ul className="list-disc pl-5 text-[var(--foreground)] space-y-1">
                      <li>Item 1 with bullet point</li>
                      <li>Item 2 with bullet point</li>
                    </ul>
                  </div>
                </div>

                <div className="p-8 border-2 border-dashed border-slate-300 rounded-3xl bg-slate-50">
                  <h3 className="text-lg font-bold text-slate-800 mb-4">Hardcoded Slate Test (Light Style)</h3>
                  <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-xl">
                    <h4 className="text-xl font-black text-slate-900 mb-2">Dual Boiler HVAC Design</h4>
                    <p className="text-slate-700 opacity-80 mb-4">
                      This card is FORCED to be light mode style. It uses <code>slate-900</code> and <code>slate-700</code>.
                    </p>
                    <ul className="list-disc pl-5 text-slate-700 space-y-1">
                      <li>Item 1 with bullet point</li>
                      <li>Item 2 with bullet point</li>
                    </ul>
                  </div>
                </div>
              </div>

              <div className="p-8 bg-[var(--accent)]/10 rounded-3xl border border-[var(--accent)]/20">
                <h3 className="text-lg font-bold text-[var(--accent)] mb-4">Opacity & Transparency Check</h3>
                <div className="flex flex-wrap gap-4">
                  {[0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100].map(op => (
                    <div key={op} className="flex flex-col items-center gap-1">
                      <div className="h-12 w-12 rounded-lg bg-[var(--foreground)]" style={{ opacity: op / 100 }}></div>
                      <span className="text-[10px] text-[var(--muted-foreground)] font-bold">{op}%</span>
                    </div>
                  ))}
                </div>
                <p className="mt-4 text-xs text-[var(--muted-foreground)]">
                  If 100% is visible but lower % are invisible, it might be due to an unexpected background color or stacking context.
                </p>
              </div>
            </div>
          </div>
        );
      default:
        return null;
    }
  };

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
          {renderContent()}
        </WorkAreaWrapper>
      </div>
    </div>
  );
}
export { YourMainContent };
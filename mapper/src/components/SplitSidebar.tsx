import { CopilotChat } from "@copilotkit/react-ui";
import { ThinkingMessage } from "./ThinkingMessage";
// import { FilesWindow } from "./FilesWindow";

interface SplitSidebarProps {
    isEditMode?: boolean;
    toggleEditMode?: () => void;
}

export function SplitSidebar({ isEditMode, toggleEditMode }: SplitSidebarProps) {
    return (
        <div className="my-split-sidebar h-full w-[28rem] flex-shrink-0 flex flex-col bg-[var(--background)] border-r border-[var(--muted-foreground)]/20 shadow-xl z-40 transition-colors duration-500">
            <div className="flex-1 relative bg-[var(--background)] overflow-hidden px-6 pb-6 pt-24">
                {/* Branding Title - Aligned with Navbar Axis */}
                <div className="absolute top-0 left-8 h-24 flex items-center">
                    <h1 className="text-[20px] font-black text-[var(--muted-foreground)] uppercase tracking-[0.5em] opacity-100">
                        SI — MAPPER
                    </h1>
                </div>

                <div className="h-full border border-[var(--muted-foreground)]/20 rounded-3xl overflow-hidden relative shadow-inner transition-all duration-700 hover:border-[var(--accent)]/40 group">
                    <CopilotChat
                        className="h-full"
                        labels={{
                            title: "SI-MAPPER",
                            initial: "Hi!👋 \n\nI'm SI-MAPPER, an agent created by Hydro-Québec to model HVAC systems using the Ashrae 223P Standard. \n\n How can I help you today?"
                        }}
                        AssistantMessage={ThinkingMessage}
                    />

                    {/* Subtle Interactive Glow - Matching Main Content Area */}
                    <div className="absolute inset-0 bg-gradient-to-br from-[var(--accent)]/[0.02] to-transparent pointer-events-none z-20" />
                    <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-[var(--accent)]/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-1000 z-20 pointer-events-none" />
                </div>
            </div>
        </div>
    );
}

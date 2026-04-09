"use client";

import { useState } from "react";
import { CopilotChat } from "@copilotkit/react-ui";
import { ThinkingMessage } from "./ThinkingMessage";
import { MessageSquareOff } from "lucide-react";

interface SplitSidebarProps {
    isEditMode?: boolean;
    toggleEditMode?: () => void;
    /** When true, overlays the chat with a message asking the user to set up a workspace first. */
    disabled?: boolean;
}

export function SplitSidebar({ disabled = false }: SplitSidebarProps) {
    const [stopVisible, setStopVisible] = useState(false);

    const handleStop = () => {
        fetch("http://localhost:8001/stop", { method: "POST" }).catch(() => {});
        setStopVisible(true);
        setTimeout(() => setStopVisible(false), 2000);
    };

    return (
        <div className="my-split-sidebar relative h-full w-[28rem] flex-shrink-0 flex flex-col bg-[var(--background)] border-r border-[var(--muted-foreground)]/20 shadow-xl z-40 transition-colors duration-500">
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
                        onStopGeneration={handleStop}
                    />

                    {/* Subtle Interactive Glow */}
                    <div className="absolute inset-0 bg-gradient-to-br from-[var(--accent)]/[0.02] to-transparent pointer-events-none z-20" />
                    <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-[var(--accent)]/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-1000 z-20 pointer-events-none" />

                    {/* Disabled overlay */}
                    {disabled && (
                        <div className="absolute inset-0 z-30 flex flex-col items-center justify-center gap-4 bg-[var(--background)]/90 backdrop-blur-sm rounded-3xl">
                            <div className="w-14 h-14 rounded-full bg-[var(--muted-foreground)]/10 flex items-center justify-center">
                                <MessageSquareOff size={24} className="text-[var(--muted-foreground)]" />
                            </div>
                            <p className="text-xs text-[var(--muted-foreground)] text-center max-w-[14rem] leading-relaxed">
                                Select or create a project and system to start chatting with the agent.
                            </p>
                        </div>
                    )}
                </div>
            </div>

            {/* Small pop-up near the stop button, just above the input bar */}
            <div
                className="pointer-events-none"
                style={{
                    position: "absolute",
                    bottom: "88px",
                    right: "56px",
                    zIndex: 50,
                    opacity: stopVisible ? 1 : 0,
                    transform: stopVisible ? "translateY(0)" : "translateY(4px)",
                    transition: "opacity 0.15s ease, transform 0.15s ease",
                    background: "var(--accent)",
                    color: "white",
                    fontSize: "10px",
                    fontWeight: 600,
                    letterSpacing: "0.04em",
                    textTransform: "uppercase",
                    padding: "4px 9px",
                    borderRadius: "6px",
                    whiteSpace: "nowrap",
                }}
            >
                Agent stopped
            </div>
        </div>
    );
}

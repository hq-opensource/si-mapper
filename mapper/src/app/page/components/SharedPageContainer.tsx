"use client";

import React from 'react';
import { LucideIcon } from 'lucide-react';

interface SharedPageContainerProps {
    title: string;
    subtitle: string;
    icon: LucideIcon;
    children: React.ReactNode;
    footerContent?: React.ReactNode;
    containerRef?: React.RefObject<HTMLDivElement | null>;
    onMouseEnter?: () => void;
    onMouseLeave?: () => void;
    maxWidth?: string;
    fullWidth?: boolean;
    fullHeight?: boolean;
}

export function SharedPageContainer({
    title,
    subtitle,
    icon: Icon,
    children,
    footerContent,
    containerRef,
    onMouseEnter,
    onMouseLeave,
    maxWidth = "max-w-5xl",
    fullWidth = false,
    fullHeight = false
}: SharedPageContainerProps) {
    const effectiveMaxWidth = fullWidth ? "max-w-none" : maxWidth;

    return (
        <div
            ref={containerRef as React.RefObject<HTMLDivElement>}
            className="w-full h-full flex flex-col transition-colors duration-500 overflow-hidden"
            onMouseEnter={onMouseEnter}
            onMouseLeave={onMouseLeave}
        >
            {/* Modern Header (Sticky/Fixed Style) - Premium Glassmorphism */}
            <div className="flex-none z-30 bg-[var(--background)]/80 backdrop-blur-md border-b border-[var(--muted-foreground)]/10">
                <div className={`mx-auto w-full ${effectiveMaxWidth} px-8 pt-10 pb-8 flex items-end justify-between animate-in fade-in slide-in-from-top-4 duration-700`}>
                    <div className="flex items-center gap-6">
                        <div className="p-4 bg-[var(--accent)]/10 rounded-[1.5rem] border border-[var(--accent)]/20 shadow-[0_0_30px_rgba(99,102,241,0.1)]">
                            <Icon size={28} className="text-[var(--accent)]" />
                        </div>
                        <div>
                            <h2 className="text-4xl font-black text-[var(--foreground)] tracking-tight leading-none mb-3">{title}</h2>
                            <p className="text-[10px] font-bold text-[var(--muted-foreground)] uppercase tracking-[0.4em] opacity-60 ml-0.5">{subtitle}</p>
                        </div>
                    </div>
                    {footerContent && (
                        <div className="hidden lg:flex flex-col items-end gap-1.5 px-4 py-2 bg-[var(--muted-foreground)]/5 rounded-2xl border border-[var(--muted-foreground)]/10">
                            {footerContent}
                        </div>
                    )}
                </div>
            </div>

            {/* Scrollable Content Area */}
            <div className={`flex-1 overflow-y-auto overflow-x-hidden scrollbar-thin scrollbar-thumb-[var(--muted-foreground)]/20 scrollbar-track-transparent ${fullHeight ? 'flex flex-col' : ''}`}>
                <div className={`mx-auto w-full ${effectiveMaxWidth} px-8 pt-12 pb-20 ${fullHeight ? 'flex-1 flex flex-col' : ''}`}>
                    <div className={`relative animate-in fade-in slide-in-from-bottom-4 duration-1000 ${fullHeight ? 'flex-1 h-full' : ''}`}>
                        {children}
                    </div>
                </div>
            </div>
        </div>
    );
}

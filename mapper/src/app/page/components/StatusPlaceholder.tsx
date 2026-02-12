"use client";

import React from 'react';
import { LucideIcon } from 'lucide-react';

interface StatusPlaceholderProps {
    icon: LucideIcon;
    title: string;
    subtitle?: string;
}

export function StatusPlaceholder({ icon: Icon, title, subtitle }: StatusPlaceholderProps) {
    return (
        <div className="flex-1 flex flex-col items-center justify-center p-8 text-center animate-in fade-in duration-1000">
            <div className="p-10 bg-[var(--muted-foreground)]/5 rounded-full inline-block mb-8 border border-[var(--muted-foreground)]/10 shadow-inner">
                <Icon size={64} strokeWidth={1} className="text-[var(--muted-foreground)]" />
            </div>
            <h3 className="text-[var(--muted-foreground)] font-black uppercase tracking-[0.4em] text-sm mb-2">{title}</h3>
            {subtitle && (
                <p className="text-[10px] font-bold text-[var(--muted-foreground)] uppercase tracking-[0.2em] opacity-60">
                    {subtitle}
                </p>
            )}
        </div>
    );
}

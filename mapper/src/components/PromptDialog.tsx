'use client';

import React, { useEffect, useState, useRef } from 'react';
import { FolderPlus } from 'lucide-react';
import { cn } from '@/lib/utils';

interface PromptDialogProps {
    isOpen: boolean;
    onClose: () => void;
    onConfirm: (value: string) => void;
    title: string;
    description: string;
    placeholder?: string;
    defaultValue?: string;
    confirmText?: string;
    cancelText?: string;
    disableCancel?: boolean;
}

export function PromptDialog({
    isOpen,
    onClose,
    onConfirm,
    title,
    description,
    placeholder = 'Enter value...',
    defaultValue = '',
    confirmText = 'Create',
    cancelText = 'Cancel',
    disableCancel = false,
}: PromptDialogProps) {
    const [isVisible, setIsVisible] = useState(false);
    const [inputValue, setInputValue] = useState('');
    const inputRef = useRef<HTMLInputElement>(null);

    useEffect(() => {
        if (isOpen) {
            setIsVisible(true);
            setInputValue(defaultValue);
            // Focus input after animation
            setTimeout(() => {
                inputRef.current?.focus();
                inputRef.current?.select();
            }, 100);
        } else {
            const timer = setTimeout(() => setIsVisible(false), 300);
            return () => clearTimeout(timer);
        }
    }, [isOpen, defaultValue]);

    if (!isVisible && !isOpen) return null;

    const handleSubmit = (e?: React.FormEvent) => {
        e?.preventDefault();
        if (inputValue.trim()) {
            onConfirm(inputValue.trim());
            onClose();
        }
    };

    return (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
            {/* Backdrop */}
            <div
                className={cn(
                    "absolute inset-0 bg-black/40 backdrop-blur-md transition-opacity duration-300 ease-out",
                    isOpen ? "opacity-100" : "opacity-0"
                )}
                onClick={disableCancel ? undefined : onClose}
            />

            {/* Modal Content */}
            <form
                onSubmit={handleSubmit}
                className={cn(
                    "relative bg-white/80 dark:bg-zinc-900/80 backdrop-blur-2xl border border-white/20 dark:border-zinc-800 rounded-[2.5rem] p-8 max-w-sm w-full shadow-2xl transform transition-all duration-300 ease-out",
                    isOpen ? "scale-100 opacity-100 translate-y-0" : "scale-95 opacity-0 translate-y-4"
                )}
            >
                <div className="flex flex-col items-center">
                    {/* Centered Icon Circle */}
                    <div className="w-20 h-20 rounded-full flex items-center justify-center mb-6 shadow-inner bg-[var(--accent)]/10 text-[var(--accent)]">
                        <FolderPlus size={32} />
                    </div>

                    <h3 className="text-2xl font-black text-[var(--foreground)] mb-2 tracking-tight">
                        {title}
                    </h3>

                    <p className="text-sm text-[var(--muted-foreground)] mb-6 text-center leading-relaxed">
                        {description}
                    </p>

                    <input
                        ref={inputRef}
                        type="text"
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        placeholder={placeholder}
                        className="w-full px-5 py-4 bg-[var(--background)] border border-[var(--muted-foreground)]/20 rounded-2xl text-[var(--foreground)] focus:outline-none focus:ring-2 focus:ring-[var(--accent)]/50 transition-all mb-8 shadow-inner"
                    />

                    <div className="flex flex-col w-full gap-3">
                        <button
                            type="submit"
                            disabled={!inputValue.trim()}
                            className="w-full px-6 py-4 rounded-2xl text-sm font-bold bg-[var(--accent)] hover:bg-[var(--accent)]/90 text-white shadow-lg shadow-[var(--accent)]/20 active:scale-[0.98] transition-all disabled:opacity-50 disabled:scale-100"
                        >
                            {confirmText}
                        </button>
                        <button
                            type="button"
                            onClick={onClose}
                            className="w-full px-6 py-4 rounded-2xl text-sm font-bold text-[var(--foreground)] hover:bg-[var(--muted-foreground)]/10 transition-colors"
                            hidden={disableCancel}
                        >
                            {cancelText}
                        </button>
                    </div>
                </div>
            </form>
        </div>
    );
}

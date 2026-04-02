'use client';

import React, { useEffect, useState } from 'react';
import { createPortal } from 'react-dom';
import { AlertTriangle, Info, CheckCircle } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ConfirmationDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  description: string;
  confirmText?: string;
  cancelText?: string;
  type?: 'danger' | 'info' | 'success';
}

export function ConfirmationDialog({
  isOpen,
  onClose,
  onConfirm,
  title,
  description,
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  type = 'info'
}: ConfirmationDialogProps) {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setIsVisible(true);
    } else {
      const timer = setTimeout(() => setIsVisible(false), 300);
      return () => clearTimeout(timer);
    }
  }, [isOpen]);

  if (!isVisible && !isOpen) return null;
  if (typeof document === 'undefined') return null;

  const getIcon = () => {
    switch (type) {
      case 'danger': return <AlertTriangle className="w-8 h-8 text-red-500" />;
      case 'success': return <CheckCircle className="w-8 h-8 text-green-500" />;
      default: return <Info className="w-8 h-8 text-[var(--accent)]" />;
    }
  };

  const getIconBg = () => {
    switch (type) {
      case 'danger': return 'bg-red-500/10';
      case 'success': return 'bg-green-500/10';
      default: return 'bg-[var(--accent)]/10';
    }
  };

  return createPortal(
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className={cn(
          "absolute inset-0 bg-black/40 backdrop-blur-md transition-opacity duration-300 ease-out",
          isOpen ? "opacity-100" : "opacity-0"
        )}
        onClick={onClose}
      />

      {/* Modal Content */}
      <div
        className={cn(
          "relative bg-[var(--background)] border border-[var(--muted-foreground)]/20 rounded-[2.5rem] p-8 max-w-sm w-full shadow-2xl transform transition-all duration-300 ease-out",
          isOpen ? "scale-100 opacity-100 translate-y-0" : "scale-95 opacity-0 translate-y-4"
        )}
      >
        <div className="flex flex-col items-center text-center">
          {/* Centered Icon Circle */}
          <div className={cn("w-20 h-20 rounded-full flex items-center justify-center mb-6 shadow-inner", getIconBg())}>
            {getIcon()}
          </div>

          <h3 className="text-2xl font-black text-[var(--foreground)] mb-3 tracking-tight">
            {title}
          </h3>

          <p className="text-sm text-[var(--muted-foreground)] mb-8 text-center leading-relaxed">
            {description}
          </p>

          <div className="flex flex-col w-full gap-3">
            <button
              onClick={() => {
                onConfirm();
                onClose();
              }}
              className={cn(
                "w-full px-6 py-4 rounded-2xl text-sm font-bold transition-all shadow-lg active:scale-[0.98]",
                type === 'danger'
                  ? "bg-red-500 hover:bg-red-600 text-white shadow-red-500/20"
                  : "bg-[var(--accent)] hover:bg-[var(--accent)]/90 text-white shadow-[var(--accent)]/20"
              )}
            >
              {confirmText}
            </button>
            <button
              onClick={onClose}
              className="w-full px-6 py-4 rounded-2xl text-sm font-bold text-[var(--foreground)] hover:bg-[var(--muted-foreground)]/10 transition-colors"
            >
              {cancelText}
            </button>
          </div>
        </div>
      </div>
    </div>,
    document.body
  );
}
import React, { useState, useRef, useEffect } from 'react';
import { createPortal } from 'react-dom';

interface CustomTooltipProps {
    content: string;
    children: React.ReactNode;
}

export function CustomTooltip({ content, children }: CustomTooltipProps) {
    const [isVisible, setIsVisible] = useState(false);
    const triggerRef = useRef<HTMLDivElement>(null);
    const [position, setPosition] = useState({ top: 0, left: 0 });
    const [themeColor, setThemeColor] = useState("var(--copilot-kit-primary-color)");

    useEffect(() => {
        if (isVisible && triggerRef.current) {
            const updatePosition = () => {
                const rect = triggerRef.current!.getBoundingClientRect();
                setPosition({
                    top: rect.bottom + 8, // 8px gap
                    left: rect.left + rect.width / 2
                });
            };

            // Read the theme color from the trigger element context
            const color = getComputedStyle(triggerRef.current).getPropertyValue('--copilot-kit-primary-color').trim();
            if (color) {
                setThemeColor(color);
            }

            updatePosition();
            // Optional: update on scroll/resize if needed, but for hover it's usually fine
            window.addEventListener('scroll', updatePosition, true);
            window.addEventListener('resize', updatePosition);

            return () => {
                window.removeEventListener('scroll', updatePosition, true);
                window.removeEventListener('resize', updatePosition);
            };
        }
    }, [isVisible]);

    return (
        <div
            ref={triggerRef}
            className="relative flex items-center"
            onMouseEnter={() => setIsVisible(true)}
            onMouseLeave={() => setIsVisible(false)}
        >
            {children}
            {isVisible && createPortal(
                <div
                    className="fixed transform -translate-x-1/2 px-2 py-1 text-xs text-white rounded shadow-lg whitespace-nowrap z-[9999] pointer-events-none"
                    style={{
                        backgroundColor: themeColor,
                        top: position.top,
                        left: position.left
                    }}
                >
                    {content}
                    {/* Arrow pointing up */}
                    <div
                        className="absolute bottom-full left-1/2 transform -translate-x-1/2 border-4 border-transparent"
                        style={{ borderBottomColor: themeColor }}
                    />
                </div>,
                document.body
            )}
        </div>
    );
}

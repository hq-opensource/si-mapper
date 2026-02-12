import React, { useState } from 'react';
import { ChevronDown, ChevronRight, Brain } from 'lucide-react';
import { Markdown } from "@copilotkit/react-ui";

interface ThinkingBoxProps {
    content: string;
    defaultOpen?: boolean;
}

export function ThinkingBox({ content, defaultOpen = true }: ThinkingBoxProps) {
    const [isOpen, setIsOpen] = useState(defaultOpen);

    if (!content.trim()) return null;

    return (
        <div className="mb-4 border border-gray-200 rounded-lg overflow-hidden bg-gray-50/50">
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="w-full flex items-center gap-2 px-3 py-2 text-xs font-medium text-gray-500 hover:bg-gray-100 transition-colors bg-gray-50 border-b border-gray-100"
            >
                {isOpen ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
                <Brain className="w-3 h-3" />
                <span>Thinking Process</span>
            </button>

            {isOpen && (
                <div className="p-3 bg-white max-h-[200px] overflow-y-auto text-sm text-gray-600 leading-relaxed shadow-inner">
                    <div className="prose prose-sm prose-slate max-w-none">
                        <Markdown content={content} />
                    </div>
                </div>
            )}
        </div>
    );
}

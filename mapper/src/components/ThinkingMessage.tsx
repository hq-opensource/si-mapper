"use client";

import React, { useEffect } from 'react';
import { AssistantMessageProps, Markdown } from "@copilotkit/react-ui";
import { useThoughts } from "@/context/ThoughtsContext";
import { Brain, Loader2 } from 'lucide-react';

export function ThinkingMessage(props: AssistantMessageProps) {
    const { message, isLoading } = props;
    const { addThought, addToolCall } = useThoughts();

    // Check if message content is available
    const content = message?.content;

    // Effect to parse and stream thoughts
    useEffect(() => {
        if (!content || typeof content !== 'string') return;

        let thoughtContent = '';
        const thoughtRegex = /:::thought\s*([\s\S]*?)(\s*:::|$)/g;
        let match;

        while ((match = thoughtRegex.exec(content)) !== null) {
            if (match[1]) {
                thoughtContent += match[1] + '\n\n';
            }
        }

        if (thoughtContent.trim()) {
            // Prefix with 'chat:' to namespace IDs from CopilotKit messages
            addThought(`chat:${message.id}`, thoughtContent.trim());
        }
    }, [content, message?.id, addThought]);

    // Effect to parse and stream tool calls
    useEffect(() => {
        if (!content || typeof content !== 'string') return;

        let toolCallContent = '';
        const toolCallRegex = /:::tool_call\s*([\s\S]*?)(\s*:::|$)/g;
        let match;

        while ((match = toolCallRegex.exec(content)) !== null) {
            if (match[1]) {
                toolCallContent += match[1] + '\n\n';
            }
        }

        if (toolCallContent.trim()) {
            // Prefix with 'chat:' to namespace IDs from CopilotKit messages
            addToolCall(`chat:${message.id}`, toolCallContent.trim());
        }
    }, [content, message?.id, addToolCall]);


    if (typeof content !== 'string') {
        if (isLoading && !content) {
            return (
                <div className="p-4 flex items-center gap-2 text-gray-500 animate-pulse">
                    <Brain className="w-4 h-4" />
                    <span className="text-sm font-medium">Agent is thinking...</span>
                </div>
            );
        }
        return null;
    }

    // --- PARSING STRUCTURED CONTENT ---
    const thoughts: string[] = [];
    const toolCalls: string[] = [];
    const responses: string[] = [];
    let looseText = content;

    // 1. Extract Thoughts - Streaming aware
    const thoughtRegex = /:::thought\s*([\s\S]*?)(\s*:::|$)/g;
    let tMatch;
    while ((tMatch = thoughtRegex.exec(content)) !== null) {
        if (tMatch[1]?.trim()) thoughts.push(tMatch[1].trim());
        looseText = looseText.replace(tMatch[0], '');
    }

    // 2. Extract Tool Calls - Streaming aware
    const toolCallRegex = /:::tool_call\s*([\s\S]*?)(\s*:::|$)/g;
    let tcMatch;
    while ((tcMatch = toolCallRegex.exec(content)) !== null) {
        if (tcMatch[1]?.trim()) toolCalls.push(tcMatch[1].trim());
        looseText = looseText.replace(tcMatch[0], '');
    }

    // 3. Extract Responses
    const responseRegex = /:::response\s*([\s\S]*?)(\s*:::|$)/g;
    let rMatch;
    while ((rMatch = responseRegex.exec(content)) !== null) {
        if (rMatch[1]?.trim()) responses.push(rMatch[1].trim());
        looseText = looseText.replace(rMatch[0], '');
    }

    // Clean up loose text
    looseText = looseText.trim();

    const hasThoughts = thoughts.length > 0;
    const hasToolCalls = toolCalls.length > 0;
    const hasResponses = responses.length > 0;
    const hasLooseText = looseText.length > 0;

    // --- RENDER DECISION ---

    // Condition A: If there's NO structure at all, render as raw legacy/static message.
    if (!hasThoughts && !hasToolCalls && !hasResponses && hasLooseText) {
        return (
            <div className="p-4 bg-[var(--background)] rounded-2xl border border-[var(--muted-foreground)]/20 shadow-sm mb-4 transition-colors duration-500">
                <div className="prose prose-sm max-w-none text-[var(--foreground)]">
                    <Markdown content={content} />
                </div>
            </div>
        );
    }

    // Condition B: If the turn is finished and there's no visible content (neither response nor loose text), hide it.
    if (!hasResponses && !hasLooseText && !isLoading) {
        return null;
    }

    // Condition C: Structural render (Thoughts and Tool Calls handled by context)
    return (
        <div className="p-4 bg-[var(--background)] rounded-2xl border border-[var(--muted-foreground)]/20 shadow-sm mb-4 transition-colors duration-500">
            {/* Show explicit responses first */}
            {responses.map((resp, index) => (
                <div key={`resp-${index}`} className="prose prose-sm max-w-none text-[var(--foreground)] mb-4 last:mb-0">
                    <Markdown content={resp} />
                </div>
            ))}

            {/* Fallback: If no explicit responses but there is loose text, show the loose text */}
            {!hasResponses && hasLooseText && (
                <div className="prose prose-sm max-w-none text-[var(--foreground)]">
                    <Markdown content={looseText} />
                </div>
            )}

            {isLoading && (
                <div className="mt-2 flex gap-2 items-center text-[var(--accent)] animate-pulse">
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    <span className="text-[10px] font-black uppercase tracking-widest leading-none">
                        {hasThoughts || hasToolCalls ? 'Streaming cognition trace...' : 'Generating response...'}
                    </span>
                </div>
            )}
        </div>
    );
}


/**
 * @jest-environment jsdom
 *
 * Unit tests — src/components/ThinkingMessage.tsx
 * Phase 4.4 — addThought/addToolCall called with 'chat:' prefixed IDs
 */

import React from 'react';
import { render } from '@testing-library/react';
import { ThinkingMessage } from '@/components/ThinkingMessage';
import { ThoughtsProvider, useThoughts } from '@/context/ThoughtsContext';

// We capture the context state via a spy component
const spyAddThought = jest.fn();
const spyAddToolCall = jest.fn();

jest.mock('@/context/ThoughtsContext', () => {
    const actual = jest.requireActual('@/context/ThoughtsContext');
    return {
        ...actual,
        useThoughts: () => ({
            ...actual,
            thoughts: [],
            toolCalls: [],
            events: [],
            data: {},
            addThought: spyAddThought,
            addToolCall: spyAddToolCall,
            syncThoughts: jest.fn(),
            syncToolCalls: jest.fn(),
            syncEvents: jest.fn(),
            syncData: jest.fn(),
        }),
    };
});

// Mock Markdown to avoid heavy rendering in unit tests
jest.mock('@copilotkit/react-ui', () => ({
    Markdown: ({ content }: { content: string }) => <span>{content}</span>,
}));

beforeEach(() => {
    spyAddThought.mockClear();
    spyAddToolCall.mockClear();
});

describe('ThinkingMessage — Phase 4.4 chat: prefix', () => {
    it('calls addThought with a chat:-prefixed ID when content has :::thought block', () => {
        const mockMessage = {
            id: 'msg-abc-123',
            content: ':::thought\nI am thinking about this.\n:::',
            role: 'assistant' as const,
            createdAt: new Date(),
        };

        render(
            <ThinkingMessage
                message={mockMessage}
                isLoading={false}
                subMessages={[]}
                index={0}
            />
        );

        expect(spyAddThought).toHaveBeenCalledWith(
            'chat:msg-abc-123',
            expect.any(String)
        );
        // Verify no un-prefixed call was made
        const calls = spyAddThought.mock.calls;
        for (const [id] of calls) {
            expect(id).toMatch(/^chat:/);
        }
    });

    it('calls addToolCall with a chat:-prefixed ID when content has :::tool_call block', () => {
        const mockMessage = {
            id: 'msg-xyz-456',
            content: ':::tool_call\ncreate_duct("duct-1")\n:::',
            role: 'assistant' as const,
            createdAt: new Date(),
        };

        render(
            <ThinkingMessage
                message={mockMessage}
                isLoading={false}
                subMessages={[]}
                index={0}
            />
        );

        expect(spyAddToolCall).toHaveBeenCalledWith(
            'chat:msg-xyz-456',
            expect.any(String)
        );
        const calls = spyAddToolCall.mock.calls;
        for (const [id] of calls) {
            expect(id).toMatch(/^chat:/);
        }
    });

    it('does not call addThought if no :::thought block present', () => {
        const mockMessage = {
            id: 'msg-plain',
            content: 'Just a regular response.',
            role: 'assistant' as const,
            createdAt: new Date(),
        };

        render(
            <ThinkingMessage
                message={mockMessage}
                isLoading={false}
                subMessages={[]}
                index={0}
            />
        );

        expect(spyAddThought).not.toHaveBeenCalled();
    });
});


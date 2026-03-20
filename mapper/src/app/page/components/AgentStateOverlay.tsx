"use client";

export interface AgentState {
    status: string;
    current_step: string;
    observed_steps: string[];
    active_agent?: string;
    [key: string]: unknown;
}

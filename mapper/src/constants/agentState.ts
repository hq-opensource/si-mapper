/**
 * State key ownership contract for SI-Mapper.
 *
 * FRONTEND_OWNED_KEYS   — written by user actions; backend must never overwrite.
 * LIFECYCLE_KEYS        — resolved by source authority rules (see combinedState in page.tsx).
 * EXCLUDED_SYNC_KEYS    — never written into ThoughtsContext.data via StateSyncer.
 * FILTERED_STATE_KEY_PREFIXES — keys with these prefixes are dropped before syncData.
 * ACTIVE_TURN_STATUSES  — CopilotKit status values that indicate an active agent turn
 *                         (fallback when `running` flag is unavailable from useCoAgent).
 *
 * See README_STATES_ABOUT.md for the full data-flow diagram.
 * See README_STATES_PLAN.md for the ownership decision rationale.
 */

/** Keys exclusively controlled by the frontend (user workspace selection). */
export const FRONTEND_OWNED_KEYS = ['active_project', 'active_system'] as const;

/**
 * Keys whose authority switches between sources depending on turn state:
 * - During an active CopilotKit turn: agentState (stream) is authoritative.
 * - At rest: pooledState (ADK poll) is authoritative.
 */
export const LIFECYCLE_KEYS = ['status', 'current_step', 'active_agent'] as const;

/**
 * Keys excluded from the StateSyncer's syncData call.
 * These are handled by dedicated sync functions (syncThoughts, syncEvents, etc.)
 * or are frontend-owned and must not flow through the general data bag.
 */
export const EXCLUDED_SYNC_KEYS = [
    ...LIFECYCLE_KEYS,
    'observed_steps',
    'thoughts', 'tool_calls', 'events',
    ...FRONTEND_OWNED_KEYS,
] as const;

/**
 * Key prefixes that indicate backend lifecycle artefacts.
 * Keys matching these prefixes are dropped entirely before syncData.
 */
export const FILTERED_STATE_KEY_PREFIXES = ['EXIT_'] as const;

/**
 * CopilotKit agent status strings that indicate an active streaming turn.
 * Used as fallback when `running` from useCoAgent is unavailable.
 * Only the LIFECYCLE_KEYS are affected — all other keys retain poll authority.
 */
export const ACTIVE_TURN_STATUSES = ['running', 'active', 'thinking', 'processing'] as const;



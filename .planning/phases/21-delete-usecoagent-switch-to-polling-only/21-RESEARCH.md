# Phase 21: delete-usecoagent-switch-to-polling-only - Research

**Researched:** 2026-04-03
**Domain:** React frontend — CopilotKit hook removal, state management simplification
**Confidence:** HIGH

## Summary

Phase 21 removes `useCoAgent` from `mapper/src/app/page.tsx` and replaces it with a default/empty state so that all agent state flows exclusively through `useAgentPolling`. The goal is to fix a "Maximum update depth exceeded" React render loop caused by `useCoAgent` returning a new object reference on every render, which causes the `useEffect` in `StateSyncer` to fire continuously during active agent sessions.

The research confirms the background analysis fully. `agentState` from `useCoAgent` contributes nothing useful: (1) its array fields (`thoughts`, `tool_calls`, `events`) are always empty because data flows via ADK callbacks into `GLOBAL_SESSION_STORE` and out through the polling endpoint, not via CopilotKit streaming; (2) the two scalar fields it influences (`status`, `active_agent`) in `combinedState` are already overridden by `pooledState` with explicit priority rules. The `AgentState` type used throughout the component tree is defined in `AgentStateOverlay.tsx`, not in `page.tsx`, so removing the local type alias in `page.tsx` requires no downstream changes.

The operation is strictly local to `page.tsx`. No other source file imports `StateSyncer` or the local `AgentState` type alias from `page.tsx`. No frontend tests cover `page.tsx` or `StateSyncer`. The only required TypeScript change is replacing the local `AgentState` type alias with an import from `AgentStateOverlay.tsx`, or using the existing type directly.

**Primary recommendation:** Replace `useCoAgent` with a stable empty default object. Replace the local `AgentState` type alias with an import from `./page/components/AgentStateOverlay`. Simplify `StateSyncer` to accept only `pooledState`. Keep `useCopilotAction` untouched.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `@copilotkit/react-core` | already installed | Provides `useCopilotAction` (kept), previously provided `useCoAgent` (removed) | CopilotKit chat integration still required |
| React `useState`/`useEffect`/`useMemo` | already installed | State management, effects, memoization | Standard React hooks |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `useAgentPolling` | local hook | Polls `/session_state` every 2 s, returns `pooledState` | Already the sole source of truth for agent data |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Remove `useCoAgent` entirely | Fix `useCoAgent` reference identity with `useMemo`/deep-equal | More complex, still needs CopilotKit streaming configured end-to-end; polling already works |

## Architecture Patterns

### Current Component Tree (before change)

```
CopilotKitPage (page.tsx)
├── useAgentPolling → pooledState (all agent data)
├── useCoAgent → agentState (always-empty arrays + overridden scalars)
├── combinedState = { ...agentState, ...pooledState, status: pooledState.status, active_agent: pooledState.active_agent }
├── StateSyncer(pooledState, agentState) — merges arrays, syncs to ThoughtsContext
├── ThoughtsProvider(currentAgentName=combinedState.active_agent)
└── YourMainContent(agentState=combinedState)
    └── AgentNavbar(agentState) — reads agentState.status, agentState.active_agent
```

### Target Component Tree (after change)

```
CopilotKitPage (page.tsx)
├── useAgentPolling → pooledState (all agent data, sole source of truth)
├── combinedState = pooledState OR defaultState (no useCoAgent)
├── StateSyncer(pooledState) — syncs pooledState arrays to ThoughtsContext
├── ThoughtsProvider(currentAgentName=combinedState.active_agent)
└── YourMainContent(agentState=combinedState)
    └── AgentNavbar(agentState) — reads agentState.status, agentState.active_agent
```

### Pattern 1: Stable Default State Object
**What:** Define `DEFAULT_AGENT_STATE` as a module-level constant outside the component. Pass it as the state when `pooledState` is null.
**When to use:** Whenever `useCoAgent` is removed but downstream components still need a non-null `AgentState`.
**Example:**
```typescript
// Stable module-level constant — never causes re-renders
const DEFAULT_AGENT_STATE: AgentState = {
  status: "idle",
  current_step: "",
  observed_steps: [],
  data: {},
};

// In component:
const combinedState: AgentState = pooledState ?? DEFAULT_AGENT_STATE;
```

### Pattern 2: Simplified StateSyncer
**What:** Remove the `agentState` prop. Sync only from `pooledState`. Remove the array-merge logic that combined `agentState.*` with `pooledState.*`.
**When to use:** After `useCoAgent` is removed — only one state source remains.
**Example:**
```typescript
function StateSyncer({ pooledState }: { pooledState: AgentState | null }) {
  const { syncThoughts, syncToolCalls, syncEvents, syncData } = useThoughts();

  useEffect(() => {
    if (!pooledState) return;

    if (pooledState.thoughts?.length) syncThoughts(pooledState.thoughts);
    if (pooledState.tool_calls?.length) syncToolCalls(pooledState.tool_calls);
    if (pooledState.events?.length) syncEvents(pooledState.events);

    const excludedKeys = ['status', 'current_step', 'observed_steps', 'active_agent', 'thoughts', 'tool_calls', 'events', 'data'];
    const pooledRest = Object.fromEntries(
      Object.entries(pooledState).filter(([key]) => !key.startsWith('EXIT_') && !excludedKeys.includes(key))
    );
    const customData: Record<string, unknown> = { ...pooledRest };
    if (pooledState.data && Object.keys(pooledState.data).length > 0) customData.data = pooledState.data;
    if (Object.keys(customData).length > 0) syncData(customData);
  }, [pooledState, syncThoughts, syncToolCalls, syncEvents, syncData]);

  return null;
}
```

### Anti-Patterns to Avoid
- **Keeping the `data` field in `AgentState` local type:** The local `AgentState` type alias in `page.tsx` has a `data: Record<string, unknown>` field that `AgentStateOverlay.AgentState` does not have (that interface uses `[key: string]: unknown` index signature instead). When switching to import from `AgentStateOverlay`, either keep the local type or extend the imported one.
- **Leaving `useCoAgent` import even if unused:** TypeScript will not error on an unused import, but it keeps dead CopilotKit streaming wiring active. Remove the import line entirely.
- **Removing `useCopilotAction`:** This is used for `setThemeColor` and must remain. Do NOT remove it.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Stable reference for default state | Inline object `{}` inside component | Module-level `const DEFAULT_AGENT_STATE` | Object literal inside component creates new reference every render, causing the same bug |
| Deep equality for `pooledState` updates | Manual JSON.stringify in component | Already done inside `useAgentPolling.setPooledState` | The polling hook already guards with JSON.stringify comparison; no extra work needed |

## Common Pitfalls

### Pitfall 1: Type Mismatch Between Local AgentState and AgentStateOverlay.AgentState
**What goes wrong:** The local `AgentState` type in `page.tsx` (lines 10-19) has explicit optional fields (`thoughts?: Thought[]`, `tool_calls?: ToolCall[]`, `events?: AgentEvent[]`, `data: Record<string, unknown>`). `AgentStateOverlay.AgentState` uses an index signature `[key: string]: unknown` with only `status`, `current_step`, `observed_steps`, `active_agent?`.
**Why it happens:** These types were defined separately and have drifted.
**How to avoid:** Two valid paths: (A) keep the richer local type in `page.tsx` and cast `pooledState as AgentState` when building `combinedState`; (B) extend `AgentStateOverlay.AgentState` to add the optional array fields and import that. Path A is simpler for a one-file change.
**Warning signs:** TypeScript error on `combinedState` assignment when `pooledState` (which is `AgentState | null` typed via the generic) is used directly.

### Pitfall 2: combinedState Still References agentState Fields
**What goes wrong:** If the developer simplifies `combinedState` but forgets to remove `...agentState` spread, TypeScript will error because `agentState` is no longer defined.
**Why it happens:** The current `combinedState` block (lines 97-103) spreads `agentState` first.
**How to avoid:** Replace the entire `combinedState` block with `const combinedState: AgentState = pooledState ?? DEFAULT_AGENT_STATE`.

### Pitfall 3: StateSyncer useEffect Dependency Array
**What goes wrong:** If `syncThoughts`, `syncToolCalls`, `syncEvents`, `syncData` are added to the dependency array (they are in the current code), React will warn if they are not stable. These callbacks are wrapped in `useCallback` with no dependencies in `ThoughtsContext.tsx` so they ARE stable — this is fine.
**Why it happens:** Linter/React rules-of-hooks requires all referenced identifiers in the dependency array.
**How to avoid:** Keep all four sync functions in the dependency array. They are stable `useCallback` references, so the effect does not re-fire unnecessarily.

### Pitfall 4: AgentNavbar agentState Prop Type
**What goes wrong:** `AgentNavbar` accepts `agentState: AgentState` where `AgentState` is imported from `AgentStateOverlay.tsx`. The `combinedState` in `page.tsx` must be assignable to that type.
**Why it happens:** `YourMainContent` re-exports the `AgentState` type usage from `AgentStateOverlay.tsx` (line 6 of `YourMainContent.tsx`).
**How to avoid:** Ensure `combinedState` satisfies `AgentStateOverlay.AgentState` — it needs at minimum `status: string`, `current_step: string`, `observed_steps: string[]`. The `DEFAULT_AGENT_STATE` constant must include these.

## Code Examples

### Current imports in page.tsx (lines 1-8)
```typescript
// Source: mapper/src/app/page.tsx
import { useCopilotAction, useCoAgent } from "@copilotkit/react-core";
import { useState, useEffect, useMemo } from "react";
import { SplitSidebar } from "@/components/SplitSidebar";
import { YourMainContent } from "@/app/page/components/YourMainContent";
import { ThoughtsProvider, useThoughts, type Thought, type ToolCall, type AgentEvent } from "@/context/ThoughtsContext";
import { useAgentPolling } from "@/hooks/useAgentPolling";
```

After change — remove `useCoAgent` from the import, remove `Thought`/`ToolCall`/`AgentEvent` type imports (only needed because the local `AgentState` used them), add `AgentState` import from overlay, remove `useEffect` if no longer used in `CopilotKitPage` directly (keep if `StateSyncer` is inside the same file):
```typescript
import { useCopilotAction } from "@copilotkit/react-core";
import { useState, useMemo } from "react";
import { SplitSidebar } from "@/components/SplitSidebar";
import { YourMainContent } from "@/app/page/components/YourMainContent";
import { type AgentState } from "@/app/page/components/AgentStateOverlay";
import { ThoughtsProvider, useThoughts } from "@/context/ThoughtsContext";
import { useAgentPolling } from "@/hooks/useAgentPolling";
```

Note: `useEffect` is still used in `StateSyncer` which lives in the same file. Keep it. Remove `Thought`, `ToolCall`, `AgentEvent` type imports since the local `AgentState` type that referenced them is deleted.

### AgentState type reconciliation
The local `AgentState` in `page.tsx` has fields not in `AgentStateOverlay.AgentState`:
- `data: Record<string, unknown>` — accessed in `StateSyncer` line 44
- `thoughts?: Thought[]` — used in `StateSyncer` merging
- `tool_calls?: ToolCall[]` — used in `StateSyncer` merging
- `events?: AgentEvent[]` — used in `StateSyncer` merging

After removing `agentState`, `StateSyncer` only reads from `pooledState`. `pooledState` is typed as `AgentState | null` via the generic `useAgentPolling<AgentState>`. The generic `AgentState` in `page.tsx` is the local one. After removing the local type, switch the generic to the overlay type or keep a local type that has the extra optional fields.

**Simplest approach:** Keep the richer local type alias but remove `data` from required fields (make it optional), remove the `Thought`/`ToolCall`/`AgentEvent` imports by inlining or removing references, then use the existing `AgentStateOverlay.AgentState` extended type from the overlay.

**Even simpler approach:** Keep the local type alias as-is minus the `Thought`/`ToolCall`/`AgentEvent` references. Change the optional array fields to `unknown[]` or remove them entirely since `StateSyncer` will no longer reference `agentState.*` arrays:
```typescript
type AgentState = {
  status: string;
  current_step: string;
  observed_steps: string[];
  data?: Record<string, unknown>;
  active_agent?: string;
  thoughts?: unknown[];
  tool_calls?: unknown[];
  events?: unknown[];
};
```

### Exact lines to remove from page.tsx

Lines 85-93 (useCoAgent call):
```typescript
// DELETE these lines entirely
const { state: agentState } = useCoAgent<AgentState>({
  name: "my_agent",
  initialState: {
    status: "idle",
    current_step: "",
    observed_steps: [],
    data: {},
  },
});
```

Lines 97-103 (combinedState block):
```typescript
// REPLACE these lines:
const combinedState = {
  ...agentState,
  ...(pooledState || {}),
  status: pooledState?.status || agentState.status,
  current_step: pooledState?.current_step || agentState.current_step,
  active_agent: pooledState?.active_agent || agentState.active_agent,
} as AgentState;

// WITH:
const combinedState: AgentState = pooledState ?? DEFAULT_AGENT_STATE;
```

Line 122 (StateSyncer usage):
```typescript
// REPLACE:
<StateSyncer pooledState={pooledState} agentState={agentState} />
// WITH:
<StateSyncer pooledState={pooledState} />
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Dual-source state (`useCoAgent` + polling) | Polling-only state | Phase 21 | Eliminates render loop; reduces component complexity |
| `StateSyncer` merges two state sources | `StateSyncer` syncs one state source | Phase 21 | Simpler effect, no array merging needed |
| CopilotKit streaming as primary, polling as backup | Polling as the only mechanism | Phase 21 | No functional regression — streaming arrays were always empty |

## Open Questions

1. **Should `data` field be kept in the local `AgentState` type?**
   - What we know: `AgentStateOverlay.AgentState` uses `[key: string]: unknown` index signature, which covers `data` implicitly
   - What's unclear: Whether downstream components (beyond `StateSyncer`) access `agentState.data` specifically
   - Recommendation: Check `StateSyncer` post-simplification — if it no longer references `.data` separately, the field can be dropped from the local type entirely

2. **Is `useMemo` still needed for `pollingConfig`?**
   - What we know: `useMemo` wraps `pollingConfig` to produce a stable reference (lines 77-80)
   - What's unclear: Whether this is still needed after removing `useCoAgent`
   - Recommendation: Keep it — `pollingConfig` memoization prevents unnecessary `useAgentPolling` re-subscriptions and is unrelated to this change

## Validation Architecture

`workflow.nyquist_validation` key is absent from `.planning/config.json` — treat as enabled.

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Jest 30 + ts-jest |
| Config file | `mapper/jest.config.js` |
| Quick run command | `cd mapper && npx jest --testPathPattern="route.test"` |
| Full suite command | `cd mapper && npx jest` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| P21-01 | `useCoAgent` removed from page.tsx, no import | static/compile | `cd mapper && npx tsc --noEmit` | ❌ Wave 0 (TypeScript compile check) |
| P21-02 | `combinedState` derived from `pooledState` only | unit | manual smoke — no existing test | ❌ no test needed (logic is trivial) |
| P21-03 | `StateSyncer` syncs `pooledState` arrays to `ThoughtsContext` | unit | manual smoke | ❌ no existing test |
| P21-04 | `AgentNavbar` still receives `status` and `active_agent` | compile | `cd mapper && npx tsc --noEmit` | ❌ Wave 0 |
| P21-05 | App builds without errors | build | `cd mapper && npm run build` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `cd mapper && npx tsc --noEmit`
- **Per wave merge:** `cd mapper && npm run build`
- **Phase gate:** Full build green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] TypeScript compile check: `cd mapper && npx tsc --noEmit` — covers P21-01, P21-04
- [ ] Build check: `cd mapper && npm run build` — covers P21-05
- No new test files needed — this is a deletion/simplification with no new logic to unit test

## Sources

### Primary (HIGH confidence)
- Direct file inspection: `mapper/src/app/page.tsx` — confirmed `useCoAgent` call, `StateSyncer` implementation, `combinedState` logic
- Direct file inspection: `mapper/src/app/page/components/AgentNavbar.tsx` — confirmed only `agentState.status` and `agentState.active_agent` fields consumed
- Direct file inspection: `mapper/src/app/page/components/YourMainContent.tsx` — confirmed `AgentState` imported from `AgentStateOverlay`, not from `page.tsx`
- Direct file inspection: `mapper/src/app/page/components/AgentStateOverlay.tsx` — confirmed canonical `AgentState` type definition
- Direct file inspection: `mapper/src/hooks/useAgentPolling.ts` — confirmed deep-equality guard in `setPooledState`, stable reference behavior
- Direct file inspection: `mapper/src/context/ThoughtsContext.tsx` — confirmed `syncThoughts`/`syncToolCalls`/`syncEvents`/`syncData` are stable `useCallback` references

### Secondary (MEDIUM confidence)
- Grep scan of all `.tsx` files — confirmed `useCoAgent` appears only in `page.tsx`; `StateSyncer` appears only in `page.tsx`; `AgentState` type is used in `AgentNavbar.tsx`, `YourMainContent.tsx`, `AgentStateOverlay.tsx`, and locally in `page.tsx`
- Grep scan — confirmed no test files exist for `page.tsx` or `StateSyncer`

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all files read directly from repo
- Architecture: HIGH — component tree traced through all relevant files
- Pitfalls: HIGH — TypeScript type discrepancy between local type and overlay type is a concrete finding from file inspection
- Test impact: HIGH — confirmed no existing tests to update

**Research date:** 2026-04-03
**Valid until:** 2026-05-03 (stable frontend, no expected changes to component API)

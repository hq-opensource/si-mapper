---
phase: 21-delete-usecoagent-switch-to-polling-only
verified: 2026-04-03T16:10:00Z
status: passed
score: 5/5 must-haves verified
re_verification: false
---

# Phase 21: Remove useCoAgent / Switch to Polling-Only Verification Report

**Phase Goal:** Remove `useCoAgent` from the frontend entirely and rely exclusively on `useAgentPolling` (polling-based state). Fix the "Maximum update depth exceeded" render loop bug caused by `agentState` being a new unstable object reference on every render.
**Verified:** 2026-04-03T16:10:00Z
**Status:** PASSED
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| #   | Truth                                                                         | Status     | Evidence                                                                                      |
| --- | ----------------------------------------------------------------------------- | ---------- | --------------------------------------------------------------------------------------------- |
| 1   | useCoAgent is not imported or called anywhere in the codebase                 | VERIFIED   | `grep -rn "useCoAgent" mapper/src/` returns no output; import line 3 uses only `useCopilotAction` |
| 2   | combinedState derives exclusively from pooledState with stable default fallback | VERIFIED | Line 67: `const combinedState: AgentState = pooledState ?? DEFAULT_AGENT_STATE` — one-liner, no merge |
| 3   | StateSyncer syncs only from pooledState — no agentState prop                  | VERIFIED   | `function StateSyncer({ pooledState }: { pooledState: AgentState | null })` — single prop; `agentState` absent from props, body, and dependency array |
| 4   | TypeScript compiles without errors (npx tsc --noEmit)                         | VERIFIED   | `cd mapper && npx tsc --noEmit` exits 0 with no output                                       |
| 5   | AgentNavbar still receives status and active_agent via combinedState           | VERIFIED   | `agentState={combinedState}` at page.tsx line 91 → YourMainContent → AgentNavbar line 79 reads `agentState.status` and `agentState.active_agent` |

**Score:** 5/5 truths verified

---

### Required Artifacts

| Artifact                       | Expected                                    | Status     | Details                                                                    |
| ------------------------------ | ------------------------------------------- | ---------- | -------------------------------------------------------------------------- |
| `mapper/src/app/page.tsx`      | Simplified page component without useCoAgent | VERIFIED  | Exists, 97 lines, contains expected pattern and no useCoAgent references   |

**Artifact content checks:**

| Check                                                              | Result  |
| ------------------------------------------------------------------ | ------- |
| `useCoAgent` import absent                                         | PASS — line 3 imports only `useCopilotAction` from `@copilotkit/react-core` |
| `const combinedState: AgentState = pooledState ?? DEFAULT_AGENT_STATE` present | PASS — line 67 |
| `DEFAULT_AGENT_STATE` module-level constant defined                | PASS — lines 12-17 |
| `useCopilotAction` still present (not accidentally removed)        | PASS — line 71 |
| `useAgentPolling` still present                                    | PASS — line 64 |
| Unused type imports (`Thought`, `ToolCall`, `AgentEvent`) removed  | PASS — not present in file |
| `agentState` variable not in scope anywhere                        | PASS — only occurrence is JSX prop `agentState={combinedState}` at line 91 (passes combinedState, not a variable named agentState) |

---

### Key Link Verification

| From                        | To                                           | Via                                   | Status   | Details                                                              |
| --------------------------- | -------------------------------------------- | ------------------------------------- | -------- | -------------------------------------------------------------------- |
| `mapper/src/app/page.tsx`   | `mapper/src/hooks/useAgentPolling.ts`        | `useAgentPolling<AgentState>(pollingConfig)` | WIRED | Line 64: `const { pooledState } = useAgentPolling<AgentState>(pollingConfig)` |
| `mapper/src/app/page.tsx`   | `mapper/src/context/ThoughtsContext.tsx`     | `syncThoughts/syncToolCalls/syncEvents/syncData` | WIRED | StateSyncer lines 21 and 31-46: all four sync functions called conditionally from pooledState |

---

### StateSyncer Dependency Array Verification

The useEffect dependency array at line 48:

```
[pooledState, syncThoughts, syncToolCalls, syncEvents, syncData]
```

- `agentState` is NOT present — the render loop root cause is eliminated.
- `pooledState` IS present — changes in polled state trigger sync.
- All four sync functions present — stable `useCallback` references from ThoughtsContext.

---

### Requirements Coverage

The ROADMAP.md lists P21-01 through P21-05 as requirement IDs for Phase 21, but their descriptions are not enumerated in ROADMAP.md beyond the table entry. The PLAN frontmatter declares all five IDs. Based on the phase goal and what was implemented:

| Requirement | Source Plan | Inferred Scope                              | Status       | Evidence                                              |
| ----------- | ----------- | ------------------------------------------- | ------------ | ----------------------------------------------------- |
| P21-01      | 21-01       | Remove useCoAgent import and call site      | SATISFIED    | Line 3 import; no useCoAgent anywhere in src/         |
| P21-02      | 21-01       | combinedState from pooledState only         | SATISFIED    | Line 67: single-expression derivation                 |
| P21-03      | 21-01       | StateSyncer without agentState prop         | SATISFIED    | Props type and dependency array verified              |
| P21-04      | 21-01       | TypeScript compiles clean                   | SATISFIED    | `npx tsc --noEmit` exits 0                           |
| P21-05      | 21-01       | Downstream components (AgentNavbar) unbroken | SATISFIED   | agentState={combinedState} passes correct shape       |

Note: P21 requirement descriptions are placeholder entries in ROADMAP.md (no detailed text beyond the table). No orphaned requirements detected — all 5 IDs are claimed by plan 21-01.

---

### Anti-Patterns Found

| File                          | Line | Pattern     | Severity | Impact                                                                    |
| ----------------------------- | ---- | ----------- | -------- | ------------------------------------------------------------------------- |
| `mapper/src/app/page.tsx`     | 50   | `return null` | INFO   | Expected and intentional — StateSyncer is a side-effect-only component with no rendered output. Not a stub. |

No TODO, FIXME, placeholder, or empty handler anti-patterns found.

---

### Commit Verification

| Commit    | Description                                                     | Exists |
| --------- | --------------------------------------------------------------- | ------ |
| `a1962cc` | feat(21-01): remove useCoAgent and simplify combinedState       | YES    |
| `efedc8b` | feat(21-01): simplify StateSyncer to single-source sync from pooledState | YES |

Both commits confirmed in `git log`.

---

### Human Verification Required

One item warrants runtime confirmation but is not a blocker for the automated pass:

**Test 1: Render loop is eliminated during active agent session**

- **Test:** Start the backend agent, trigger an active session (status != idle), observe the browser console for 30 seconds.
- **Expected:** No "Maximum update depth exceeded" error in the console. React renders stabilize after the initial polling interval fires.
- **Why human:** The render loop is a runtime dynamic caused by reference instability — it only manifests when useCoAgent is returning a new object every render. Static code analysis confirms the root cause (agentState in dependency array) is removed, but confirming the fix holds during a live session requires runtime observation.

---

### Gaps Summary

No gaps. All five observable truths are verified by static analysis. The render loop root cause (unstable `agentState` reference in StateSyncer's dependency array) is structurally eliminated: `useCoAgent` is gone, `agentState` no longer exists as a variable, `combinedState` uses a stable module-level fallback, and StateSyncer's dependency array contains only `pooledState` and the stable sync callbacks.

---

_Verified: 2026-04-03T16:10:00Z_
_Verifier: Claude (gsd-verifier)_

---
phase: 21
slug: delete-usecoagent-switch-to-polling-only
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-03
---

# Phase 21 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | none — no automated tests for page.tsx or StateSyncer |
| **Config file** | none |
| **Quick run command** | `cd mapper && npx tsc --noEmit` |
| **Full suite command** | `cd mapper && npx tsc --noEmit && npx next build 2>&1 | tail -20` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd mapper && npx tsc --noEmit`
- **After every plan wave:** Run `cd mapper && npx tsc --noEmit && npx next build 2>&1 | tail -20`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 21-01-01 | 01 | 1 | remove useCoAgent | type-check | `cd mapper && npx tsc --noEmit` | ✅ | ⬜ pending |
| 21-01-02 | 01 | 1 | simplify StateSyncer | type-check | `cd mapper && npx tsc --noEmit` | ✅ | ⬜ pending |
| 21-01-03 | 01 | 1 | simplify combinedState | type-check | `cd mapper && npx tsc --noEmit` | ✅ | ⬜ pending |
| 21-01-04 | 01 | 1 | manual render loop test | manual | (see manual verifications) | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Existing infrastructure covers all phase requirements. No new test files needed — this is a pure deletion/simplification refactor with no new logic to unit test.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| No "Maximum update depth exceeded" error | Render loop fix | Requires live browser + active agent run | Start agent, open browser console, confirm no React error during agent execution |
| AgentNavbar ping dot still animates | status field flows correctly | Requires live UI | Run agent, confirm ping dot pulses when agent is active |
| AgentNavbar shows agent name | active_agent field flows correctly | Requires live UI | Run agent, confirm agent name appears in navbar |
| ThoughtsWindow / ToolCallsWindow still populate | pooledState data still reaches context | Requires live agent run | Run agent, open Thoughts/ToolCalls tabs, confirm events appear |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending

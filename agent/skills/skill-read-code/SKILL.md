---
name: skill-read-code
description: Specialized instructions for reading and comparing dated iteration folders to extract error-resolution lessons from previous code generation attempts.
---

# Skill: Reading and Comparing Code Iterations

## 1. Purpose

Navigate and interpret the `resources assets` folder to extract **error-to-resolution lessons** from previous generation attempts. The goal is learning from deltas, not describing what to generate.

---

## 2. Folder Structure (example, actual may vary)

```
2026-03-13-1/
    <prefix>_1.py      ← attempt 1 (has errors)
    <prefix>.py        ← final resolved file
2026-03-13-3/
    <prefix>_1.py
    <prefix>_2.py
    <prefix>_3.py
    <prefix>.py        ← final resolved file
    ...
```

**Conventions:**
- `<prefix>` varies across sessions — do not assume a fixed name.
- `<prefix>_N.py` = failed/incomplete attempt N.
- `<prefix>.py` (no suffix) = **final, working file** for that session.
- Number of `_N` files = attempts needed before convergence.

**Ignore:**
- Files not following `*_N.py` or `*.py` naming inside dated folders.
- Non-Python files (`.txt`, `.md`) unless they contain iteration notes.
- Files outside the dated sub-folders.

---

## 3. Reading Protocol

**Step 0 — Check for LESSONS.md first:**
If `references/LESSONS.md` exists in this skill's directory:
- Read `references/LESSONS.md` only.
- Do NOT walk `assets/` or read any `_N.py` files.
- Do NOT fall back to Steps 1-5 below. LESSONS.md is authoritative.
- Proceed directly to applying the lessons to your current task.

If `LESSONS.md` does not exist, continue with Steps 1-5 below (raw asset walk).

---

**Step 1 — Sequential order within a session:**
```
<prefix>_1.py → <prefix>_2.py → … → <prefix>.py
```
Never start with `<prefix>.py` alone — resolution only makes sense after reading what failed.

**Step 2 — Identify the delta between each consecutive pair:**
- What changed? (added, removed, modified lines)
- What was the likely error in the previous file?
- What is the fix?

The delta **is the lesson**. Small diff = focused fix. Large diff = structural rethink.

**Step 3 — `<prefix>.py` is ground truth.**
Extract reusable patterns only from the final unsuffixed file, never from `_N` files.

**Step 4 — Process sessions in chronological order.**
A pattern corrected in an earlier session must not reappear later — if it does, flag it as a recurring risk.

---

## 4. Diff Categories & Recurring Risks

| Category | Signal to look for |
| :--- | :--- |
| **Imports** | Modules added, removed, or moved between `bob` and `scratch` |
| **Instantiation pattern** | Constructor arguments changed |
| **Connection wiring** | `>>` chain restructured or explicit port names introduced |
| **Sensor API** | Method used to attach a property or observation changed |
| **Serialization** | Function used to write the output file changed |
| **Structural approach** | Class hierarchy replaced with flat pattern (or vice versa) |

Each category is a class of mistake that can recur — note it as a **recurring risk**.

---

## 5. Reading Algorithm

```
FOR EACH dated session folder (chronological order):
    DETECT the filename prefix for this session
    READ <prefix>_1.py
    FOR EACH subsequent _N file:
        COMPARE with previous file
        IDENTIFY what changed and why
    READ <prefix>.py (final)
    COMPARE with last _N file
    RECORD the final fix
```

---

## 6. Verification Checklist

- [ ] Every `_N` file read before `<prefix>.py` for each session?
- [ ] Sessions processed in strict chronological order?
- [ ] Each diff classified into a category from Section 4?
- [ ] Final fix recorded from `<prefix>.py` only (not from any `_N` file)?
- [ ] Error patterns reappearing across sessions flagged as recurring risks?

---

## 7. Distillation Protocol

> This section is for the **master agent**, not the ontology sub-agents.

When the user explicitly requests lesson distillation (e.g. "update lessons", "distill lessons"):

1. **Read all dated session folders** using the Reading Algorithm (Section 5).
2. **Extract error-to-resolution lessons** organized by the 6 categories in Section 4.
3. **Write `references/LESSONS.md`** in this skill's directory with structured findings.
4. **Format:** Use the 6 category headers (Imports, Instantiation pattern, Connection wiring, Sensor API, Serialization, Structural approach). Under each header, list concrete lessons as bullet points with the pattern: `- **Error:** [what went wrong] -> **Fix:** [what resolved it]`.
5. **Overwrite** any existing `references/LESSONS.md` — each distillation is a full refresh, not incremental.

**Trigger:** Explicit human instruction only. Never auto-trigger distillation.

---
name: read-code-iterations
description: Specialized instructions for reading and comparing dated iteration folders to extract error-resolution lessons from previous code generation attempts.
---

# Skill: Reading and Comparing Code Iterations

## 1. Purpose

This skill elaborates on how to properly **read and compare the files inside the `iterations` folder** to extract knowledge from previous attempts.

The goal is not to describe what to generate — it is to describe **how to navigate and interpret the iteration artifacts** so that errors and their resolutions can be understood and learned from.

---

## 2. Folder Structure

Under `iterations/`, there are dated sub-folders, each representing one generation session.

Here is an example of the structure, but more folders and files may be added over time:
```
iterations/
    2026-03-13-1/
        <prefix>_1.py      ← attempt 1 (first try, likely has errors)
        <prefix>.py        ← final resolved file for this session
    2026-03-13-2/
        <prefix>_1.py      ← attempt 1
        <prefix>.py        ← final resolved file
    2026-03-13-3/
        <prefix>_1.py      ← attempt 1
        <prefix>_2.py      ← attempt 2
        <prefix>_3.py      ← attempt 3
        <prefix>.py        ← final resolved file
    2026-03-16-1/
        <prefix>_1.py      ← attempt 1
        <prefix>_2.py      ← attempt 2
        <prefix>.py        ← final resolved file
```

**Key conventions:**
- The `<prefix>` part of the filename (e.g., `ontology`, `mapping`, `pipeline`) may vary across sessions — **do not assume a fixed prefix**.
- Files suffixed `_N` (e.g., `<prefix>_1.py`, `<prefix>_2.py`) are **numbered attempts** — they failed or were incomplete.
- The file **without a suffix** (e.g., `<prefix>.py`) is the **final, resolved, working file** for that session.
- The number of `_N` files in a session indicates how many attempts were needed before convergence.

**To be ignored:**
- Any files that do not follow the `*_N.py` naming pattern.
- Any files that are not in the dated sub-folders.
- Files that are not Python code (e.g., `.txt`, `.md`) unless they contain notes about the iterations.
- Files that are not part of the `iterations` folder (e.g., files in `code_samples` or other folders) when analyzing the iteration process.

---

## 3. Reading Protocol

### Step 1 — Read in strict sequential order

Within a dated folder, always read files **from lowest to highest**, then the final:

```
<prefix>_1.py → <prefix>_2.py → <prefix>_3.py → <prefix>.py
```

Never start with `<prefix>.py` alone. The resolution only makes sense in the context of what failed before it.

### Step 2 — For each consecutive pair, identify the delta

When moving from file N to file N+1 (or from the last `_N` to `<prefix>.py`), ask:

- **What changed?** Look for added, removed, or modified lines.
- **What was the likely error in the previous file?** The change reveals what was wrong.
- **What is the fix?** The new code is the answer to the error.

The delta between two files **is the lesson**. A small diff = one focused correction. A large diff = major structural rethink.

### Step 3 — Treat `<prefix>.py` as ground truth for that session

The unsuffixed `<prefix>.py` is the file that successfully ran (or was accepted as correct). When extracting patterns to reuse, always take them from `<prefix>.py`, not from any `_N` file.

### Step 4 — Read sessions in chronological order

Sessions are named with dates (`2026-03-13-1`, `2026-03-13-2`, etc.). Later sessions build on the knowledge of earlier ones. A pattern corrected in session `2026-03-13-2` should not reappear in `2026-03-16-1` — if it does, that is itself a signal worth noting.

---

## 4. What to Look For When Comparing (Diff Categories & Recurring Risks)

When diffing two consecutive files, focus on these categories:

| Category | Signal to look for |
| :--- | :--- |
| **Imports** | Were modules added, removed, or moved between `bob` and `scratch`? |
| **Instantiation pattern** | Did the object constructor arguments change? |
| **Connection wiring** | Did the `>>` chain change structure, or were explicit port names introduced? |
| **Sensor API** | Did the method used to attach a property or observation change? |
| **Serialization** | Did the function used to write the output file change? |
| **Structural approach** | Was a class hierarchy (e.g., `System.contains()`) replaced with a flat pattern? |

Each of these categories represents a class of mistake that can recur. When you see a change in one of these categories, note it as a **recurring risk** for future generations.

---

## 5. Full Reading Algorithm

```
FOR EACH dated session folder (in chronological order):
    DETECT the filename prefix used in this session
    READ <prefix>_1.py
    FOR EACH subsequent _N file:
        COMPARE with previous file
        IDENTIFY what changed and why
    READ <prefix>.py (final)
    COMPARE with last _N file
    RECORD: what the final fix was
```

This sequential reading reveals the **path from error to resolution**, which is more valuable than the resolved code alone.

---

## 6. Verification Checklist

- [ ] Did you read every `_N` file before reading `<prefix>.py` for each session?
- [ ] Did you process sessions in strict chronological order?
- [ ] For each diff, have you classified the change into one of the categories in Section 4?
- [ ] Did you record the final fix from `<prefix>.py` (not from any `_N` file)?
- [ ] Did you flag any error pattern that reappears across sessions as a recurring risk?

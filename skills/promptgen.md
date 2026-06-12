---
name: promptgen
description: Generate a powerful, best-practice Claude Code prompt.md file. Pass a filename as the argument (e.g. /promptgen my_task.md). Asks clarifying questions, then writes a structured, self-contained prompt following Anthropic guidelines — including an optional parallel-agents section with a live status bar.
icon: ✍️
tags: prompting, agents, productivity
---

# Prompt Generator

## Overview

Generate a high-quality, reusable Claude Code prompt file following Anthropic best practices. The output is a standalone `.md` file — drop it into any project and use it immediately to direct Claude with no prior context required.

A well-structured prompt:
- Defines a precise persona with explicit behaviors
- States a single, testable goal
- Provides enough context for a cold-start (no assumed history)
- Lists explicit constraints so Claude knows what NOT to do
- Describes the expected output format concretely
- Optionally decomposes work across parallel agents with live status tracking

---

# Process

## Phase 1: Parse Arguments and Clarify

### 1.1 Parse the filename

The `args` value is the output filename (e.g. `my_first_prompt.md`). If no argument is provided, default to `prompt.md`. Resolve the path relative to the current working directory.

### 1.2 Ask clarifying questions (conversationally, one question at a time)

Before generating, ask the user the following. Skip any question already answered in their original message.

1. **What is this prompt for?**
   (e.g. "migrate the auth service to a new EC2 instance", "build a fullstack dashboard with 4 tabs", "perform a security audit of the API layer")

2. **What is the target tech stack or domain?**
   (e.g. React + FastAPI + PostgreSQL on Kubernetes, Go microservices, Python data pipeline)

3. **Should this include a parallel agents section?**
   Answer yes or no. If yes: How many agents? Give a one-line summary of each agent's responsibility.

4. **Are there any hard constraints?**
   (e.g. "no direct commits to main", "ask before any destructive action", "PRs required for all changes")

Once you have answers, proceed directly to Phase 2. Do not ask follow-up questions about things you can infer.

---

## Phase 2: Generate the Prompt

### 2.1 Core Structure

Generate the prompt using the following template. Every section is required unless marked `(optional)`.

```markdown
# <Task Title>
<!-- Short imperative phrase. e.g. "Migrate Auth to parthmerchant-backend" or "Build Space Native Markets Tab" -->

## Persona
You are a <seniority> <role> with deep expertise in <domain>. You are <key trait>, <key trait>, and always <key behavior>. When in doubt, you <decision principle>.

## Context
<Background the model needs to understand. Include: repository layout, system architecture, current state of the codebase, who the user is and what they care about. Write this as if starting a brand-new conversation with zero prior history.>

- **Repos / paths involved:** <list>
- **Current state:** <what exists today>
- **Why this task:** <motivation — compliance, performance, user need, etc.>

## Goal
<One sentence. State the end condition. What does "done" look like — concretely and verifiably?>

## Constraints
- Ask before any destructive or irreversible action (file deletion, DB drop, force push)
- All changes require PRs — no direct commits to `main` / `master`
- <User-supplied constraint 1>
- <User-supplied constraint 2>
- Never introduce security vulnerabilities: no secrets in code, no SQL injection, no XSS

## Instructions

Follow these steps in order. Confirm with the user before any step marked ⚠️.

1. <First action — be specific: name the file, command, or service>
2. <Second action>
3. <Third action — if this step has a decision point, state the decision criteria>
4. ⚠️ <Step that requires user sign-off before proceeding>
5. <Continue...>

## Output Format
<Describe what a correct, complete response looks like:>
- Files created or modified: <list format>
- Commands to run: <inline code blocks>
- PRs to open: <one PR per logical unit; title format>
- Confirmation message: <what to report when done>

## Examples (optional)
<!-- Include only if the task is ambiguous or the input/output shape is non-obvious -->

**Input:** <example input>
**Expected output:** <example output>
```

### 2.2 Parallel Agents Section (include only if user said yes)

Append this block after `## Output Format` when parallel execution is requested:

```markdown
---

## Parallel Execution

### Agent Status Display

After spawning agents, render and maintain a live status bar. Update it after every subtask completes — never let progress go silent.

Format the status bar exactly like this (replace agent names and steps with real values):

```
┌─ Agent Status ────────────────────────────────────────────────────┐
│ Agent 1: <Name>   [████████░░]  Step 4/5 — <current action>       │
│ Agent 2: <Name>   [██░░░░░░░░]  Step 1/5 — <current action>       │
│ Agent 3: <Name>   [██████████]  ✓ Complete                        │
│ Agent 4: <Name>   [░░░░░░░░░░]  Waiting on Agent 1...             │
└───────────────────────────────────────────────────────────────────┘
```

Rules:
- Each filled block (`█`) = one completed subtask
- `░` = remaining steps
- Update the bar inline (re-render the full block, don't append new lines)
- Show "Waiting on <Agent N>..." if blocked by a dependency

### Execution Plan

1. **Spawn** all agents simultaneously (Tasks 1–N defined below)
2. **Enforce dependencies**: if Agent B needs Agent A's output, show Agent B as "Waiting on Agent A" until A completes
3. **Reconcile**: after all agents finish, review outputs for conflicts (duplicate components, overlapping API routes, conflicting config)
4. **Queue PRs**: open one PR per agent's scope; do not merge any until all agents complete and conflicts are resolved

### Agent Task 1: <Name>

**Goal:** <One sentence — what this agent is responsible for>

**Subtasks:**
- [ ] <Subtask 1>
- [ ] <Subtask 2>
- [ ] <Subtask 3>
- [ ] <Subtask 4>
- [ ] <Subtask 5>

**Depends on:** _(none | Agent N)_
**PR scope:** <which repo(s) and what files/directories this agent touches>

### Agent Task 2: <Name>

**Goal:** <One sentence>

**Subtasks:**
- [ ] <Subtask 1>
- [ ] <Subtask 2>
- [ ] <Subtask 3>
- [ ] <Subtask 4>
- [ ] <Subtask 5>

**Depends on:** _(none | Agent N)_
**PR scope:** <repo(s) and scope>

<!-- Repeat Agent Task blocks for each additional agent -->
```

### 2.3 Fill in all placeholders

Replace every `<...>` with real content derived from the user's answers. Do not leave any placeholder text in the output.

### 2.4 Quality checklist — verify before writing

- [ ] **Persona** is specific: names role, seniority, domain, and at least two behavioral traits — not a generic "helpful assistant"
- [ ] **Context** is cold-start safe: a fresh conversation with zero history would have everything it needs
- [ ] **Goal** is a single sentence describing a verifiable end state
- [ ] **Constraints** include at least one destructive-action guardrail
- [ ] **Instructions** are numbered and sequential; decision points are explicit
- [ ] **Output Format** describes files, commands, and PRs concretely
- [ ] **If parallel agents**: each agent has a distinct, non-overlapping scope; dependencies are declared; status bar format is included

---

## Phase 3: Write and Report

### 3.1 Write the file

Write the generated prompt to the path resolved from `args`. Do not truncate. Do not add a preamble — write the prompt content directly.

### 3.2 Confirm

After writing, report:

```
✓ Written to <full path>

Sections included:
  • Persona
  • Context
  • Goal
  • Constraints
  • Instructions (<N> steps)
  • Output Format
  • Parallel Agents (<N> agents)    ← omit line if not included

To use: open <filename> in your next Claude Code session and paste its contents as your opening message.
```

Offer one follow-up: "Want me to adjust any section or add more detail to a specific agent's tasks?"

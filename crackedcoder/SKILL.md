---
name: [skill-name]
description: [One-line description of what this skill does and when Claude should use it. Used in skill listings, so be specific about trigger context.]
license: Complete terms in LICENSE.txt
---

# [Skill Name]

## Overview

[What this skill accomplishes and why it exists. Include what "quality" means for this skill — how you measure success.]

---

# Process

## High-Level Workflow

[Brief description of the overall approach, e.g. number of phases and their purpose.]

---

### Phase 1: Research and Planning

#### 1.1 [Understand the Domain]

[What background knowledge or documentation Claude should gather before starting.]

- Key questions to answer before writing any code or taking action
- APIs, services, or specs to review
- How to use WebFetch / WebSearch to load relevant docs

#### 1.2 [Plan the Approach]

[How Claude should scope and sequence the work:]

- What to prioritize first
- Known constraints or gotchas to account for
- Decision criteria (e.g. when to pick option A vs. B)

---

### Phase 2: Implementation

#### 2.1 [Setup]

[Initial scaffolding, configuration, or environment setup steps.]

See language-specific or context-specific guides:
- [📋 Reference Doc](./reference/[filename].md) — [what it covers]

#### 2.2 [Core Work]

[The main implementation steps. Be specific — name commands, file paths, patterns.]

For each unit of work:
- Input: what to expect / validate
- Output: what to produce / verify
- Error handling: what can go wrong and how to handle it

#### 2.3 [Integration or Wiring]

[How the pieces connect. Config, environment variables, service registration, etc.]

---

### Phase 3: Review and Test

#### 3.1 Quality Check

Review for:
- [Criterion 1 — e.g. no duplicated logic]
- [Criterion 2 — e.g. consistent error messages]
- [Criterion 3 — e.g. all edge cases handled]

#### 3.2 Testing

[How to verify the work is correct:]

```bash
# Build / lint
[command]

# Run tests
[command]

# Smoke test / manual verification
[command]
```

---

### Phase 4: [Optional — Evaluation / Delivery / Cleanup]

[If this skill produces a deliverable, artifact, or report, describe the output format here.]

#### 4.1 [Output Format]

```
[Example output structure — XML, JSON, markdown report, etc.]
```

#### 4.2 [Verification]

[How to confirm the output is correct before handing off.]

---

# Reference Files

## Documentation Library

Load these resources as needed during execution:

### Core References (Load First)
- [📋 [Reference Doc Title]](./reference/[filename].md) — [What it covers: conventions, patterns, constraints]

### Implementation Guides (Load During Phase 2)
- [⚡ [Guide Title]](./reference/[filename].md) — [Language/framework-specific patterns and examples]

### Evaluation / Output Guides (Load During Phase 4)
- [✅ [Output Guide Title]](./reference/[filename].md) — [Output format specs and verification steps]

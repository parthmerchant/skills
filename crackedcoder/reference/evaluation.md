# Evaluation Guide

## Overview

Evaluations test whether the skill's output actually accomplishes the goal — not just whether it runs without errors. Create evaluations after implementation to verify end-to-end quality.

---

## Quick Reference

### Requirements
- Create [N] evaluation cases
- Cases must be: independent, non-destructive, verifiable
- Each case should require multiple steps to answer
- Answers must be stable (not change over time)

### Output Format
```xml
<evaluation>
  <qa_pair>
    <question>Your question here</question>
    <answer>Single verifiable answer</answer>
  </qa_pair>
</evaluation>
```

---

## Question Guidelines

1. **Independent** — each case must not depend on the result of another
2. **Non-destructive** — read-only operations only; no state modification
3. **Complex** — requires multiple steps or tool calls, not a direct lookup
4. **Realistic** — reflects a real use case someone would actually care about
5. **Verifiable** — has a single, unambiguous answer checkable by string comparison
6. **Stable** — the answer won't change as data changes over time

## Anti-Patterns to Avoid

- Questions whose answer changes as live data changes (e.g. "how many users are online?")
- Questions solvable with a single keyword search
- Questions that require write or destructive operations to answer
- Questions with multiple valid answers

---

## Evaluation Process

1. **Inspect** — review the skill's outputs and capabilities without calling destructive operations
2. **Explore** — use read-only operations to understand available data
3. **Generate** — write [N] questions following the guidelines above
4. **Verify** — solve each question yourself to confirm the answer is correct and stable

---

## Running Evaluations

```bash
# Install dependencies
pip install -r scripts/requirements.txt

# Run against local implementation
python scripts/evaluation.py evaluation.xml

# Run against remote endpoint
python scripts/evaluation.py -u https://example.com/endpoint evaluation.xml
```

Output: accuracy score, per-case pass/fail, and agent feedback on any failures.

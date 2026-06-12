---
name: promptgen
description: Generate a powerful, best-practice Claude Code prompt.md file. Pass a filename as the argument (e.g. /promptgen my_task.md). Asks clarifying questions, then writes a structured, self-contained prompt following Anthropic guidelines.
---

# Prompt Generator

Parse `args` for the output filename (default: `prompt.md`). Resolve relative to cwd.

## References
- `references/template.md` — the full output template with all required sections

## TL;DR
- Ask **one question only**: "What should the prompt accomplish?"
- Write the file immediately — no follow-ups.
- Fill every `<…>` placeholder with real content. Leave no placeholders in output.
- Print one confirmation line after writing: `✓ <full path> — <N>-step plan`.

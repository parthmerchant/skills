# [Skill Name] Best Practices

## Naming Conventions

- **[Entity type]**: `[naming pattern]` — e.g. snake_case, kebab-case, prefixed with service name
- **[Another entity]**: `[naming pattern]`

## Response / Output Format

- Prefer [JSON / Markdown / plain text] for [structured data / human-readable output]
- Truncate responses longer than [N] characters with a note that content was trimmed
- Include metadata fields: [e.g. `id`, `created_at`, `has_more`] where applicable

## Pagination

When returning lists:
```
{
  "items": [...],
  "total_count": N,
  "has_more": true/false,
  "next_offset": N   // omit if has_more is false
}
```
Default `limit` to [10–50]; accept caller-specified `limit` and `offset`.

## Error Handling

- Return actionable error messages: describe what failed AND what the caller should do next
- Include relevant context in errors: IDs, field names, expected vs. actual values
- [Specific error patterns for this domain]

## Security

- Never log or return secrets, tokens, or credentials
- Validate and sanitize all inputs at system boundaries
- [Domain-specific security constraints]

## Testing

- [Unit test pattern]
- [Integration test pattern]
- [How to run the test suite]

# Code Review

Review changes on the current branch against main.

## Steps

1. Run `git diff main...HEAD` to see all changes
2. Run `git log --oneline main..HEAD` to see all commits
3. Review each changed file for:
   - Correctness: does it do what it's supposed to?
   - Security: any injection, unsanitized input, or exposed secrets?
   - Architecture: does it follow the patterns in CLAUDE.md?
   - Edge cases: missing error handling at system boundaries?
4. Save review to `.agents/reviews/<date>-<branch>.md`

## Review Format

```markdown
# Code Review: <branch>

## Summary
<overall assessment>

## Files Reviewed
- `path/to/file` — <assessment>

## Issues Found
- [ ] **[severity]** <file>:<line> — <description>

## Verdict
APPROVE / REQUEST_CHANGES
```

# Implement Plan

Execute an implementation plan step by step.

## Input

$ARGUMENTS — path to the plan file in `.agents/plans/`, or "latest" to use the most recent plan

## Steps

1. Read the plan file
2. Create a feature branch: `git checkout -b <feature-name>`
3. For each implementation step in the plan:
   a. Write the code
   b. Run the self-correction loop (write → check → fix → repeat):
      - Python: `ruff check backend/` and `python -m py_compile <file>`
      - TypeScript: `cd vscode-extension && npx tsc --noEmit`
   c. Commit the step with a descriptive message
4. After all steps are complete, write a report to `.agents/reports/<date>-<slug>.md`
5. Summarize what was done and any issues encountered

## Report Format

```markdown
# Implementation Report: <title>

## Plan
<link to plan file>

## Commits
- `<hash>` — <message>

## Issues Encountered
- <any problems and how they were resolved>

## Next Steps
- <anything remaining>
```

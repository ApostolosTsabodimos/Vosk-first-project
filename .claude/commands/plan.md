# Plan Implementation

Create a detailed implementation plan for a task.

## Input

$ARGUMENTS — description of the feature, fix, or task to plan

## Steps

1. Read `CLAUDE.md` for architecture and conventions
2. Identify which files need to be created or modified
3. For each file, describe what changes are needed and why
4. Define the validation strategy (how to verify the implementation works)
5. List any dependencies or prerequisites
6. Save the plan to `.agents/plans/<date>-<slug>.md`

## Plan Format

```markdown
# Plan: <title>

## Goal
<what this achieves>

## Files to Change
- `path/to/file.py` — <what and why>

## Implementation Steps
1. ...

## Validation
- [ ] <how to verify each step>

## Dependencies
- <anything needed first>
```

# Validate

Run all validation checks on the current codebase.

## Steps

### Backend (Python)
1. Check if `backend/` exists, skip if not
2. Run linter: `ruff check backend/`
3. Run type compilation check: `find backend/ -name "*.py" -exec python -m py_compile {} \;`
4. Run tests if they exist: `cd backend && python -m pytest tests/ -v` (skip if no tests/ dir)

### Extension (TypeScript)
1. Check if `vscode-extension/` exists, skip if not
2. Run TypeScript compiler: `cd vscode-extension && npx tsc --noEmit`
3. Run tests if configured: `cd vscode-extension && npm test` (skip if no test script)

### Report
- Summarize results: what passed, what failed
- For any failures, suggest the fix

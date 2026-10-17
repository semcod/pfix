# ticket-003: Fix PERF-AUDIT findings, AST caching, and adopt Wellmanifest standards

- **Status**: IN_PROGRESS
- **Workflow state**: VERIFIED

SESSION_EXECUTION_AUTHORIZATION: continue analysis, repairs, and standard alignment across projects using `wellmanifest/wellman`.

## Acceptance Criteria
- [x] AC-01: Bound log file reads in `src/pfix/dashboard.py` (`PERF-AUDIT-IO-001`).
- [x] AC-02: Cache AST parsing outside loops in `graph_builder.py`, `python_version.py`, `third_party.py`, and `multi_fix.py` (`PERF-AUDIT-PARSE-001`).
- [x] AC-03: Resolve unused optional kwargs in `analyzer.py`, `integrations/web.py`, `commands/activation.py`, `commands/config.py`, `commands/others.py`, and `dev_mode.py` (`PERF-AUDIT-KWARG-001`).
- [x] AC-04: Adopt Wellmanifest `baseline` standards in `.governance/` and pass all 186 tests.

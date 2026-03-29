<!-- code2docs:start --># pfix

![version](https://img.shields.io/badge/version-0.1.0-blue) ![python](https://img.shields.io/badge/python-%3E%3D3.10-blue) ![coverage](https://img.shields.io/badge/coverage-unknown-lightgrey) ![functions](https://img.shields.io/badge/functions-641-green)
> **641** functions | **61** classes | **110** files | CC̄ = 3.1

> Auto-generated project documentation from source code analysis.

**Author:** Tom Sapletta  
**License:** Apache-2.0[(LICENSE)](./LICENSE)  
**Repository:** [https://github.com/semcod/pfix](https://github.com/semcod/pfix)

## Installation

### From PyPI

```bash
pip install pfix
```

### From Source

```bash
git clone https://github.com/semcod/pfix
cd pfix
pip install -e .
```

### Optional Extras

```bash
pip install pfix[mcp]    # mcp features
pip install pfix[git]    # Git integration (GitPython)
pip install pfix[watch]    # file watcher (watchdog)
pip install pfix[production]    # production features
pip install pfix[cache]    # cache features
pip install pfix[sentry]    # sentry features
pip install pfix[tui]    # tui features
pip install pfix[dev]    # development tools
pip install pfix[diagnostics]    # diagnostics features
pip install pfix[all]    # all optional features
```

## Quick Start

### CLI Usage

```bash
# Generate full documentation for your project
pfix ./my-project

# Only regenerate README
pfix ./my-project --readme-only

# Preview what would be generated (no file writes)
pfix ./my-project --dry-run

# Check documentation health
pfix check ./my-project

# Sync — regenerate only changed modules
pfix sync ./my-project
```

### Python API

```python
from pfix import generate_readme, generate_docs, Code2DocsConfig

# Quick: generate README
generate_readme("./my-project")

# Full: generate all documentation
config = Code2DocsConfig(project_name="mylib", verbose=True)
docs = generate_docs("./my-project", config=config)
```

## Generated Output

When you run `pfix`, the following files are produced:

```
<project>/
├── README.md                 # Main project README (auto-generated sections)
├── docs/
│   ├── api.md               # Consolidated API reference
│   ├── modules.md           # Module documentation with metrics
│   ├── architecture.md      # Architecture overview with diagrams
│   ├── dependency-graph.md  # Module dependency graphs
│   ├── coverage.md          # Docstring coverage report
│   ├── getting-started.md   # Getting started guide
│   ├── configuration.md    # Configuration reference
│   └── api-changelog.md    # API change tracking
├── examples/
│   ├── quickstart.py       # Basic usage examples
│   └── advanced_usage.py   # Advanced usage examples
├── CONTRIBUTING.md         # Contribution guidelines
└── mkdocs.yml             # MkDocs site configuration
```

## Configuration

Create `pfix.yaml` in your project root (or run `pfix init`):

```yaml
project:
  name: my-project
  source: ./
  output: ./docs/

readme:
  sections:
    - overview
    - install
    - quickstart
    - api
    - structure
  badges:
    - version
    - python
    - coverage
  sync_markers: true

docs:
  api_reference: true
  module_docs: true
  architecture: true
  changelog: true

examples:
  auto_generate: true
  from_entry_points: true

sync:
  strategy: markers    # markers | full | git-diff
  watch: false
  ignore:
    - "tests/"
    - "__pycache__"
```

## Sync Markers

pfix can update only specific sections of an existing README using HTML comment markers:

```markdown
<!-- pfix:start -->
# Project Title
... auto-generated content ...
<!-- pfix:end -->
```

Content outside the markers is preserved when regenerating. Enable this with `sync_markers: true` in your configuration.

## Architecture

```
pfix/
    ├── shared    ├── run_all├── verify_runtime    ├── reset        ├── dashboard        ├── explain        ├── multi_fix        ├── cli        ├── mcp_client        ├── runtime_todo/        ├── fixer        ├── diff_fixer    ├── pfix/        ├── classifiers        ├── config        ├── telemetry        ├── logging        ├── validation        ├── session        ├── production        ├── permissions        ├── analyzer        ├── rollback        ├── types        ├── _auto_activate        ├── dev_mode        ├── init_wizard        ├── pfix_python        ├── cache        ├── dependency        ├── syntax_error_handler        ├── mcp_server        ├── audit        ├── rules            ├── activation        ├── commands/            ├── config            ├── run            ├── others            ├── diagnose            ├── base            ├── process            ├── memory            ├── config_env            ├── import_diagnostic            ├── python_version        ├── env_diagnostics/            ├── hardware            ├── encoding            ├── paths            ├── auto_fix        ├── decorator            ├── concurrency            ├── filesystem            ├── network            ├── serialization            ├── django            ├── flask            ├── pandas            ├── fastapi        ├── strategies/            ├── third_party            ├── fingerprint            ├── todo_file            ├── sentry        ├── integrations/            ├── precommit            ├── imports/            ├── web                ├── extractor        ├── main        ├── main                ├── checks        ├── main        ├── main            ├── collector        ├── degradation        ├── main        ├── main        ├── api_patterns        ├── main        ├── codec_errors        ├── unicode_errors        ├── main        ├── file_errors        ├── class_errors        ├── main        ├── python_gotchas        ├── package_traps        ├── tricky_errors        ├── main        ├── env_var_errors        ├── version_conflicts        ├── main        ├── cascading_errors        ├── main        ├── race_conditions        ├── async_mistakes        ├── missing_module        ├── shadowing        ├── main        ├── circular        ├── platform_specific        ├── wrong_names        ├── numeric_errors        ├── parse_errors├── project        ├── main        ├── llm```

## API Overview

### Classes

- **`MultiFileFixProposal`** — Fix proposal affecting multiple files.
- **`MCPResult`** — —
- **`MCPClient`** — Client for MCP servers (filesystem, editor tools).
- **`DiffParseError`** — Raised when diff parsing fails.
- **`ErrorClassifier`** — Base class for error classification strategies.
- **`ImportErrorClassifier`** — Classify import-related errors.
- **`TypeErrorClassifier`** — Classify type-related errors.
- **`DataStructureErrorClassifier`** — Classify data structure access errors.
- **`IOErrorClassifier`** — Classify file/IO related errors.
- **`SyntaxErrorClassifier`** — Classify syntax errors.
- **`PfixConfig`** — Central configuration.
- **`TelemetryEvent`** — Anonymous telemetry event.
- **`FixEvent`** — Structured log event for each fix operation.
- **`JsonLinesLogger`** — JSON Lines format logger for FixEvents.
- **`SQLiteLogger`** — SQLite-based logger for FixEvents with querying capabilities.
- **`SentryIntegration`** — Optional Sentry integration for error tracking.
- **`Logger`** — Main logger combining multiple backends.
- **`ValidationResult`** — Result of test validation.
- **`PFixSession`** — Session context that catches and auto-fixes exceptions.
- **`CircuitBreaker`** — Circuit breaker pattern for LLM calls.
- **`RateLimiter`** — Rate limiter for LLM calls (token bucket algorithm).
- **`ProductionConfig`** — Configuration for production mode.
- **`PfixMonitor`** — Production-safe error monitor. Never modifies code.
- **`TraceFrame`** — Single frame from a traceback.
- **`RuntimeIssue`** — A runtime error captured for TODO.md tracking.
- **`DiagnosticResult`** — Result from an environment diagnostic check.
- **`ErrorContext`** — Structured error report for LLM consumption.
- **`FixProposal`** — Structured fix from LLM.
- **`PfixConfig`** — Runtime configuration for pfix.
- **`FixEvent`** — Structured log event for each fix operation.
- **`FixCache`** — Cache for fix proposals to avoid redundant LLM calls.
- **`AuditEntry`** — Single audit entry for a fix operation.
- **`ProjectRules`** — Loaded project rules.
- **`BaseDiagnostic`** — Base class for all environment diagnostics.
- **`ProcessDiagnostic`** — Diagnose process and OS-related problems.
- **`MemoryDiagnostic`** — Diagnose memory-related problems.
- **`ConfigEnvDiagnostic`** — Diagnose configuration and environment variable problems.
- **`ImportDiagnostic`** — Diagnose import and dependency problems.
- **`PythonVersionDiagnostic`** — Diagnose Python version compatibility problems.
- **`EnvDiagnostics`** — Orchestrator for all environment diagnostics.
- **`HardwareDiagnostic`** — Diagnose hardware-related problems.
- **`EncodingDiagnostic`** — Diagnose encoding-related problems.
- **`PathDiagnostic`** — Diagnose path-related problems.
- **`ConcurrencyDiagnostic`** — Diagnose concurrency-related problems.
- **`FilesystemDiagnostic`** — Diagnose filesystem-related problems.
- **`NetworkDiagnostic`** — Diagnose network-related problems.
- **`SerializationDiagnostic`** — Diagnose serialization-related problems.
- **`DjangoFixStrategy`** — Strategy for Django framework errors.
- **`FlaskFixStrategy`** — Strategy for Flask framework errors.
- **`PandasFixStrategy`** — Strategy for pandas data manipulation errors.
- **`FastAPIFixStrategy`** — Strategy for FastAPI framework errors.
- **`FixStrategy`** — Base class for framework-specific fix strategies.
- **`StrategyRegistry`** — Registry of fix strategies.
- **`ThirdPartyDiagnostic`** — Diagnose third-party API-related problems.
- **`ErrorFingerprint`** — Generates stable hash for error deduplication.
- **`TodoFile`** — Thread-safe, append-only manager for TODO.md.
- **`PfixSentryIntegration`** — Sentry integration that adds pfix diagnosis to error events.
- **`PfixMiddleware`** — ASGI middleware for FastAPI/Starlette that captures and analyzes errors.
- **`PfixFlaskExtension`** — Flask extension for pfix error monitoring.
- **`PfixDjangoMiddleware`** — Django middleware for pfix error monitoring.
- **`RuntimeCollector`** — Captures runtime errors and writes to TODO.md.

### Functions

- `fetch_json(url)` — Fetch JSON from URL — dependencies auto-installed on first run.
- `average(numbers)` — Calculate average — ZeroDivisionError will be auto-fixed.
- `greet(name, age)` — Greet user — TypeError will be auto-fixed.
- `run_example(examples_dir, category, script)` — Run a single example and return success status.
- `reset_examples(examples_dir)` — Reset all examples to original state using git.
- `main()` — —
- `crash_me()` — This function will crash and should be logged to TODO.md
- `run_git_checkout(paths)` — Run git checkout to restore files.
- `main()` — Reset all example directories to original buggy state.
- `get_log_stats(log_dir)` — Calculate statistics from log files.
- `get_cache_stats(cache_dir)` — Get cache statistics.
- `render_dashboard()` — Render rich console dashboard.
- `run_console_dashboard()` — Run rich console-based dashboard.
- `run_dashboard()` — Main entry point for dashboard command.
- `explain_last()` — Explain the most recent error from logs.
- `explain_exception_type(exc_type)` — Generate general educational content about an exception type.
- `explain(what, file)` — Main entry point for explain command.
- `find_related_files(source_file, error_ctx, max_depth)` — Find files related to the error through imports.
- `build_multi_file_context(error_ctx, related_files)` — Build LLM prompt with multiple files.
- `parse_multi_file_response(raw)` — Parse LLM response for multi-file fix.
- `apply_multi_file_fix(proposal, project_root, create_backups)` — Apply multi-file fix proposal.
- `main(argv)` — —
- `apply_fix(ctx, proposal, confirm)` — Apply a FixProposal. Returns True if anything was applied. CC≤5.
- `parse_unified_diff(diff_text)` — Parse unified diff text into hunks.
- `parse_hunk_header(line)` — Parse hunk header like @@ -1,5 +1,7 @@.
- `apply_hunk(old_lines, hunk_lines, old_start)` — Apply a single hunk to old_lines.
- `apply_diff(original_content, diff_text)` — Apply unified diff to original content.
- `apply_diff_to_file(filepath, diff_text, create_backup)` — Apply diff directly to file.
- `create_unified_diff(old_content, new_content, old_path, new_path)` — Create unified diff between old and new content.
- `classify_error(ctx)` — Classify error using registered classifiers.
- `get_error_category(exc_type)` — Get broad category for an exception type without full context.
- `get_config()` — —
- `configure()` — Override global config programmatically.
- `reset_config()` — Reset global config (useful in tests).
- `is_telemetry_enabled()` — Check if telemetry is enabled (opt-in).
- `get_telemetry_endpoint()` — Get custom telemetry endpoint if configured.
- `record_event(event_type, exception_type, confidence, success)` — Record telemetry event (if enabled).
- `get_telemetry_summary()` — Get aggregate telemetry summary.
- `clear_telemetry()` — Clear all telemetry data.
- `get_logger()` — Get or create global logger.
- `log_fix(ctx, proposal, fix_applied, duration_ms)` — Convenience function to log a fix event.
- `run_tests(command, timeout, cwd)` — Run tests and return result.
- `validate_fix(source_file, proposal, backup_path, command)` — Validate a fix by running tests.
- `quick_validate_syntax(filepath)` — Quick syntax validation for a single file.
- `validate_with_fallback(ctx, proposal, backup_path)` — Full validation workflow with fallback.
- `pfix_session(target_file)` — Create pfix session for file-level auto-healing.
- `auto_pfix(func)` — Decorator that auto-fixes exceptions in wrapped function.
- `install_pfix_hook(target_file, auto_apply)` — Install global pfix excepthook. CC≤5.
- `monitor(webhook_url, rate_limit)` — Create a production monitor with sensible defaults.
- `get_environment()` — Detect current environment.
- `check_auto_apply_allowed()` — Check if auto-apply is permitted in current environment.
- `check_complexity_approval(cc)` — Check if high-complexity fix requires manual approval.
- `check_blocked_path(filepath)` — Check if file path is blocked from modification.
- `check_all_permissions(filepath, cc, auto_apply)` — Check all permissions for a fix operation.
- `get_permissions_summary()` — Get summary of current permissions.
- `analyze_exception(exc, func, local_vars, hints)` — Build ErrorContext from a caught exception. Orkiestrator — CC≤4.
- `scan_missing_deps(project_dir)` — Use pipreqs to detect imports that aren't installed.
- `find_backup_dir(filepath)` — Find backup directory for a file.
- `list_backups(filepath)` — List available backup files.
- `rollback_last()` — Rollback the most recent fix.
- `rollback_file(filepath, before)` — Rollback all fixes to a specific file.
- `rollback_before(cutoff_date)` — Rollback all fixes before a specific date.
- `show_history(limit)` — Show fix history with rollback options.
- `rollback_command(last, filepath, before)` — Main entry point for rollback CLI command.
- `is_site_package(module)` — Check if module is from site-packages (third-party).
- `wrap_module_functions(module)` — Wrap all callable attributes of a module with error handling.
- `install_dev_mode_hook()` — Install the development mode import hook.
- `find_pyproject()` — Find pyproject.toml in current or parent directories.
- `init_wizard()` — Run the interactive setup wizard.
- `update_pyproject(pyproject, model, auto_apply)` — Add [tool.pfix] section to pyproject.toml.
- `get_gitignore_content()` — Get pfix-related .gitignore entries.
- `update_gitignore(gitignore)` — Add pfix entries to existing .gitignore.
- `main()` — CLI entry point.
- `main()` — —
- `get_cache()` — Get or create global cache instance.
- `get_cached_fix(ctx)` — Get cached fix for error context (convenience function).
- `cache_fix(ctx, proposal)` — Cache fix proposal (convenience function).
- `resolve_package_name(module_name)` — Map Python module name → PyPI package name.
- `is_module_available(module_name)` — —
- `install_packages(packages, dry_run)` — Install packages via pip or uv. Returns {package: success}.
- `scan_project_deps(project_dir)` — Use pipreqs to scan project for all imports and find missing ones.
- `update_requirements_file(packages, requirements_path)` — Append packages to requirements.txt.
- `generate_requirements(project_dir)` — Generate requirements.txt via pipreqs for the project.
- `detect_missing_from_error(exception_message)` — Extract module name from ModuleNotFoundError/ImportError.
- `handle_syntax_error(exc, auto_apply)` — Handle SyntaxError by calling pfix to fix it.
- `create_mcp_server()` — Create FastMCP server with pfix tools.
- `start_server(transport, host, port)` — Start the MCP server.
- `log_fix_audit(filepath, function_name, error, error_type)` — Log a fix operation to audit trail.
- `read_audit_log(since, filepath, limit)` — Read audit log with optional filtering.
- `get_audit_summary(days)` — Get summary statistics from audit log.
- `print_audit_report(days)` — Print formatted audit report.
- `load_project_rules(path)` — Load project rules from file.
- `get_rules_for_prompt()` — Get rules formatted for LLM prompt.
- `cmd_enable(args)` — Enable pfix auto-activation and add config to pyproject.toml. CC≤5.
- `cmd_disable(args)` — Disable pfix auto-activation.
- `cmd_check(args)` — —
- `cmd_status(args)` — Show diagnostic status of pfix.
- `path_read_safe(path)` — Safely read file content.
- `cmd_run(args)` — —
- `cmd_dev(args)` — Run with dependency development mode active.
- `cmd_deps(args)` — —
- `cmd_server(args)` — —
- `cmd_rollback(args)` — —
- `cmd_audit(args)` — —
- `cmd_init(args)` — —
- `cmd_dashboard(args)` — —
- `cmd_explain(args)` — —
- `cmd_diagnose(args)` — Run environment diagnostics.
- `can_auto_fix(result)` — Check if this result can be auto-fixed.
- `apply_auto_fix(result, project_root)` — Apply auto-fix for a diagnostic result.
- `pfix(func)` — Self-healing decorator. Catches errors, fixes code via LLM.
- `apfix(func)` — Async version of @pfix. CC≤5.
- `get_collector(config)` — Get or create RuntimeCollector from config.
- `capture_exception(exc, context)` — Capture single exception to TODO.md (convenience function).
- `get_strategy_context(ctx)` — Convenience function to get enhanced context.
- `init_sentry(dsn, auto_analyze, min_confidence)` — Initialize Sentry with pfix integration.
- `check_syntax(filepath)` — Check Python file syntax.
- `check_imports(filepath)` — Check for potentially missing imports.
- `main(argv)` — Pre-commit hook entry point.
- `create_error_handler(auto_fix, notify_url)` — Create a generic error handler for custom frameworks.
- `extract_imports(source)` — Extract top-level imports from source code.
- `get_module_name(pyfile, project_root)` — Convert a file path to a module name.
- `resolve_relative_import(node, module_name)` — Convert a relative import to an absolute module name.
- `extract_module_name(msg)` — Extract module name from error message.
- `get_installed_packages()` — Get lowercase names of currently installed packages.
- `connect_to_database()` — —
- `fetch_from_typo_domain()` — —
- `call_slow_api()` — —
- `download_missing_file()` — —
- `load_and_process_data(filepath)` — Load CSV, process it, return statistics.
- `analyze_users(users)` — Analyze user data with multiple bugs.
- `main()` — —
- `check_missing_imports(project_root, category, get_all_project_imports)` — Check for imports that aren't installed.
- `check_shadow_stdlib(project_root, category)` — Check for local files shadowing stdlib modules.
- `check_stale_bytecode(project_root, category)` — Check for stale .pyc files.
- `check_version_conflicts(category)` — Check for dependency version conflicts using pip check.
- `check_missing_inits(project_root, category)` — Find directories containing .py files but no __init__.py.
- `check_deprecated_apis(project_root, category)` — Check for use of deprecated standard library or third-party APIs.
- `check_import_source(project_root, category)` — Check if local modules are being overshadowed by installed packages.
- `count_lines_in_large_file(path)` — —
- `squares_up_to(n)` — —
- `process_stream()` — —
- `create_circular_ref()` — —
- `attribute_error_test()` — Accessing non-existent attribute.
- `type_error_test()` — Type mismatch in operations.
- `pattern_error_test()` — Common pattern mismatch.
- `get_user_cached(user_id)` — —
- `render_dashboard(features)` — —
- `render_header()` — —
- `render_footer()` — —
- `render_analytics_v2()` — —
- `fetch_with_bad_retry(url)` — —
- `parse_api_v2_response()` — —
- `main()` — —
- `main()` — —
- `handle_request(request)` — —
- `authenticate(request)` — —
- `validate_payload(request)` — —
- `query_database(user, payload)` — —
- `serialize_response(results)` — —
- `run_etl_pipeline()` — —
- `extract_from_api()` — —
- `transform_records(records)` — —
- `load_to_output(records)` — —
- `bootstrap_config()` — —
- `main()` — —
- `run_system_command()` — —
- `write_binary_to_text()` — —
- `log_user_input(text)` — —
- `read_legacy_file()` — —
- `process_api_response(data)` — —
- `format_price(amount, currency)` — —
- `build_search_url(query)` — —
- `read_bom_csv()` — —
- `main()` — —
- `load_config()` — —
- `load_settings()` — —
- `save_report(data)` — —
- `read_ssh_key()` — —
- `read_cross_platform(filename)` — —
- `test_missing_super()` — —
- `test_slots_error()` — —
- `test_dataclass_mutable()` — —
- `test_mro_conflict()` — —
- `main()` — —
- `test_no_with_statement()` — —
- `test_property_called()` — —
- `test_staticmethod_self()` — —
- `test_generator_confusion()` — —
- `test_bad_context_manager()` — —
- `test_wrong_package()` — —
- `fetch_sni_url()` — —
- `resize_image()` — —
- `test_namespace_conflict()` — —
- `apply_to_all(items, func)` — —
- `make_multipliers()` — —
- `validate_positive(func)` — —
- `subtract(a, b)` — —
- `use_dynamic_config()` — —
- `consume_generator()` — —
- `main()` — —
- `get_database_url()` — —
- `get_port()` — —
- `is_debug_mode()` — —
- `read_user_config()` — —
- `use_deprecated_api()` — —
- `get_package_version(name)` — —
- `legacy_json_parse(data)` — —
- `start_mcp_server()` — —
- `main()` — —
- `start_application()` — —
- `load_db_config()` — —
- `connect_database(config)` — —
- `serve_api(db)` — —
- `process_batch(items)` — —
- `transform_item(item)` — —
- `fetch_with_transient_failure()` — —
- `process_with_cleanup()` — —
- `acquire_resource()` — —
- `do_work(resource)` — —
- `release_resource(resource)` — —
- `main()` — —
- `filter_dict_inplace(data)` — —
- `remove_negatives(numbers)` — —
- `fetch_async_in_sync()` — —
- `parallel_count()` — —
- `test_missing_await()` — —
- `test_sync_in_async()` — —
- `test_await_non_coroutine()` — —
- `test_sync_generator_in_async()` — —
- `fetch_api_data(url)` — —
- `load_yaml_config(path)` — —
- `generate_filename(prefix)` — —
- `make_list_from_range(n)` — —
- `parse_json_string(data)` — —
- `get_home_dir()` — —
- `create_instance(type, value)` — Parameter 'type' shadows builtin type().
- `main()` — —
- `register_handler(name, func)` — Register a handler — but tries to import processor which imports this module.
- `process_all()` — Process all registered handlers.
- `load_toml(path)` — —
- `get_inotify_events()` — —
- `test_self_type()` — —
- `test_optional_extra()` — —
- `count_words(text)` — —
- `get_timestamp()` — —
- `encode_base64(data)` — —
- `parse_html(html)` — —
- `find_files(pattern)` — —
- `calculate_average(values)` — —
- `validate_total(items)` — —
- `compute_statistics(data)` — —
- `time_ago(timestamp_ms)` — —
- `distribute_evenly(total, groups)` — —
- `extract_email(user)` — —
- `get_third_element(items)` — —
- `parse_user_age(age_str)` — —
- `parse_json_response(raw)` — —
- `parse_csv_data(csv_text)` — —
- `parse_coordinate(coord_str)` — —
- `main()` — —
- `request_fix(error_ctx)` — Send error to LLM, get fix proposal with fallback chain support.


## Project Structure

📄 `examples.complex_demo.main` (3 functions)
📄 `examples.concurrency.async_mistakes` (4 functions)
📄 `examples.concurrency.main` (1 functions)
📄 `examples.concurrency.race_conditions` (4 functions)
📄 `examples.data.main` (1 functions)
📄 `examples.data.numeric_errors` (5 functions)
📄 `examples.data.parse_errors` (6 functions)
📄 `examples.deps.main` (1 functions)
📄 `examples.deps.package_traps` (4 functions)
📄 `examples.deps.version_conflicts` (4 functions)
📄 `examples.edge_cases.class_errors` (4 functions)
📄 `examples.edge_cases.main` (1 functions)
📄 `examples.edge_cases.python_gotchas` (5 functions)
📄 `examples.edge_cases.tricky_errors` (6 functions)
📄 `examples.encoding.codec_errors` (3 functions)
📄 `examples.encoding.main` (1 functions)
📄 `examples.encoding.unicode_errors` (5 functions)
📄 `examples.environment.env_var_errors` (4 functions)
📄 `examples.environment.main` (1 functions)
📄 `examples.filesystem.file_errors` (5 functions)
📄 `examples.filesystem.main` (1 functions)
📄 `examples.getting_started.main` (1 functions)
📄 `examples.imports.circular` (2 functions)
📄 `examples.imports.main` (1 functions)
📄 `examples.imports.missing_module` (3 functions)
📄 `examples.imports.platform_specific` (4 functions)
📄 `examples.imports.shadowing` (4 functions)
📄 `examples.imports.wrong_names` (5 functions)
📄 `examples.memory.main` (4 functions)
📄 `examples.network.main` (4 functions)
📄 `examples.production.api_patterns` (10 functions)
📄 `examples.production.cascading_errors` (11 functions)
📄 `examples.production.degradation` (7 functions)
📄 `examples.production.main` (1 functions)
📄 `examples.reset` (2 functions)
📄 `examples.run_all` (3 functions)
📄 `examples.shared` (3 functions)
📄 `examples.types.main` (3 functions)
📄 `project`
📦 `src.pfix` (4 functions)
📄 `src.pfix._auto_activate` (7 functions)
📄 `src.pfix.analyzer` (14 functions)
📄 `src.pfix.audit` (5 functions, 1 classes)
📄 `src.pfix.cache` (14 functions, 1 classes)
📄 `src.pfix.classifiers` (8 functions, 6 classes)
📄 `src.pfix.cli` (3 functions)
📦 `src.pfix.commands`
📄 `src.pfix.commands.activation` (8 functions)
📄 `src.pfix.commands.config` (10 functions)
📄 `src.pfix.commands.diagnose` (5 functions)
📄 `src.pfix.commands.others` (7 functions)
📄 `src.pfix.commands.run` (4 functions)
📄 `src.pfix.config` (15 functions, 1 classes)
📄 `src.pfix.dashboard` (7 functions)
📄 `src.pfix.decorator` (11 functions)
📄 `src.pfix.dependency` (14 functions)
📄 `src.pfix.dev_mode` (4 functions)
📄 `src.pfix.diff_fixer` (9 functions, 1 classes)
📦 `src.pfix.env_diagnostics` (8 functions, 1 classes)
📄 `src.pfix.env_diagnostics.auto_fix` (13 functions)
📄 `src.pfix.env_diagnostics.base` (3 functions, 1 classes)
📄 `src.pfix.env_diagnostics.concurrency` (6 functions, 1 classes)
📄 `src.pfix.env_diagnostics.config_env` (12 functions, 1 classes)
📄 `src.pfix.env_diagnostics.encoding` (7 functions, 1 classes)
📄 `src.pfix.env_diagnostics.filesystem` (12 functions, 1 classes)
📄 `src.pfix.env_diagnostics.hardware` (8 functions, 1 classes)
📄 `src.pfix.env_diagnostics.import_diagnostic` (5 functions, 1 classes)
📦 `src.pfix.env_diagnostics.imports`
📄 `src.pfix.env_diagnostics.imports.checks` (7 functions)
📄 `src.pfix.env_diagnostics.imports.extractor` (5 functions)
📄 `src.pfix.env_diagnostics.memory` (10 functions, 1 classes)
📄 `src.pfix.env_diagnostics.network` (8 functions, 1 classes)
📄 `src.pfix.env_diagnostics.paths` (10 functions, 1 classes)
📄 `src.pfix.env_diagnostics.process` (10 functions, 1 classes)
📄 `src.pfix.env_diagnostics.python_version` (15 functions, 1 classes)
📄 `src.pfix.env_diagnostics.serialization` (6 functions, 1 classes)
📄 `src.pfix.env_diagnostics.third_party` (6 functions, 1 classes)
📄 `src.pfix.explain` (4 functions)
📄 `src.pfix.fixer` (18 functions)
📄 `src.pfix.init_wizard` (14 functions)
📦 `src.pfix.integrations`
📄 `src.pfix.integrations.precommit` (3 functions)
📄 `src.pfix.integrations.sentry` (4 functions, 1 classes)
📄 `src.pfix.integrations.web` (10 functions, 3 classes)
📄 `src.pfix.llm` (4 functions)
📄 `src.pfix.logging` (18 functions, 5 classes)
📄 `src.pfix.mcp_client` (6 functions, 2 classes)
📄 `src.pfix.mcp_server` (8 functions)
📄 `src.pfix.multi_fix` (6 functions, 1 classes)
📄 `src.pfix.permissions` (6 functions)
📄 `src.pfix.pfix_python` (1 functions)
📄 `src.pfix.production` (13 functions, 4 classes)
📄 `src.pfix.rollback` (7 functions)
📄 `src.pfix.rules` (7 functions, 1 classes)
📦 `src.pfix.runtime_todo` (2 functions)
📄 `src.pfix.runtime_todo.collector` (16 functions, 1 classes)
📄 `src.pfix.runtime_todo.fingerprint` (2 functions, 1 classes)
📄 `src.pfix.runtime_todo.todo_file` (8 functions, 1 classes)
📄 `src.pfix.session` (13 functions, 1 classes)
📦 `src.pfix.strategies` (7 functions, 2 classes)
📄 `src.pfix.strategies.django` (3 functions, 1 classes)
📄 `src.pfix.strategies.fastapi` (3 functions, 1 classes)
📄 `src.pfix.strategies.flask` (3 functions, 1 classes)
📄 `src.pfix.strategies.pandas` (3 functions, 1 classes)
📄 `src.pfix.syntax_error_handler` (3 functions)
📄 `src.pfix.telemetry` (10 functions, 1 classes)
📄 `src.pfix.types` (1 functions, 7 classes)
📄 `src.pfix.validation` (4 functions, 1 classes)
📄 `verify_runtime` (1 functions)

## Requirements

- Python >= >=3.10
- litellm >=1.40.0- python-dotenv >=1.0.0- rich >=13.0.0- pipreqs >=0.4.0- pathspec >=0.12.0

## Contributing

**Contributors:**
- Tom Softreck <tom@sapletta.com>
- Tom Sapletta <tom-sapletta-com@users.noreply.github.com>

We welcome contributions! Please see [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.

### Development Setup

```bash
# Clone the repository
git clone https://github.com/semcod/pfix
cd pfix

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest
```

## Documentation

- 📖 [Full Documentation](https://github.com/semcod/pfix/tree/main/docs) — API reference, module docs, architecture
- 🚀 [Getting Started](https://github.com/semcod/pfix/blob/main/docs/getting-started.md) — Quick start guide
- 📚 [API Reference](https://github.com/semcod/pfix/blob/main/docs/api.md) — Complete API documentation
- 🔧 [Configuration](https://github.com/semcod/pfix/blob/main/docs/configuration.md) — Configuration options
- 💡 [Examples](./examples) — Usage examples and code samples

### Generated Files

| Output | Description | Link |
|--------|-------------|------|
| `README.md` | Project overview (this file) | — |
| `docs/api.md` | Consolidated API reference | [View](./docs/api.md) |
| `docs/modules.md` | Module reference with metrics | [View](./docs/modules.md) |
| `docs/architecture.md` | Architecture with diagrams | [View](./docs/architecture.md) |
| `docs/dependency-graph.md` | Dependency graphs | [View](./docs/dependency-graph.md) |
| `docs/coverage.md` | Docstring coverage report | [View](./docs/coverage.md) |
| `docs/getting-started.md` | Getting started guide | [View](./docs/getting-started.md) |
| `docs/configuration.md` | Configuration reference | [View](./docs/configuration.md) |
| `docs/api-changelog.md` | API change tracking | [View](./docs/api-changelog.md) |
| `CONTRIBUTING.md` | Contribution guidelines | [View](./CONTRIBUTING.md) |
| `examples/` | Usage examples | [Browse](./examples) |
| `mkdocs.yml` | MkDocs configuration | — |

<!-- code2docs:end -->
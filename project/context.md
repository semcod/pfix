# System Architecture Analysis

## Overview

- **Project**: /home/tom/github/semcod/pfix
- **Primary Language**: python
- **Languages**: python: 104, shell: 1
- **Analysis Mode**: static
- **Total Functions**: 636
- **Total Classes**: 55
- **Modules**: 105
- **Entry Points**: 416

## Architecture by Module

### src.pfix.env_diagnostics.imports
- **Functions**: 19
- **Classes**: 1
- **File**: `imports.py`

### src.pfix.fixer
- **Functions**: 18
- **File**: `fixer.py`

### src.pfix.logging
- **Functions**: 18
- **Classes**: 5
- **File**: `logging.py`

### src.pfix.runtime_todo.collector
- **Functions**: 16
- **Classes**: 1
- **File**: `collector.py`

### src.pfix.config
- **Functions**: 15
- **Classes**: 1
- **File**: `config.py`

### src.pfix.analyzer
- **Functions**: 15
- **File**: `analyzer.py`

### src.pfix.env_diagnostics.python_version
- **Functions**: 15
- **Classes**: 1
- **File**: `python_version.py`

### src.pfix.init_wizard
- **Functions**: 14
- **File**: `init_wizard.py`

### src.pfix.cache
- **Functions**: 14
- **Classes**: 1
- **File**: `cache.py`

### src.pfix.dependency
- **Functions**: 14
- **File**: `dependency.py`

### src.pfix.session
- **Functions**: 13
- **Classes**: 1
- **File**: `session.py`

### src.pfix.production
- **Functions**: 13
- **Classes**: 4
- **File**: `production.py`

### src.pfix.env_diagnostics.auto_fix
- **Functions**: 13
- **File**: `auto_fix.py`

### src.pfix.env_diagnostics.config_env
- **Functions**: 12
- **Classes**: 1
- **File**: `config_env.py`

### src.pfix.env_diagnostics.filesystem
- **Functions**: 12
- **Classes**: 1
- **File**: `filesystem.py`

### src.pfix.decorator
- **Functions**: 11
- **File**: `decorator.py`

### examples.production.cascading_errors
- **Functions**: 11
- **File**: `cascading_errors.py`

### src.pfix.telemetry
- **Functions**: 10
- **Classes**: 1
- **File**: `telemetry.py`

### src.pfix.commands.config
- **Functions**: 10
- **File**: `config.py`

### src.pfix.env_diagnostics.process
- **Functions**: 10
- **Classes**: 1
- **File**: `process.py`

## Key Entry Points

Main execution flows into the system:

### examples.imports.main.main
- **Calls**: print, print, print, exec, print, print, exec, print

### examples.run_all.main
- **Calls**: argparse.ArgumentParser, parser.add_argument, parser.add_argument, parser.add_argument, parser.parse_args, print, print, print

### src.pfix.session.PFixSession._handle_exception
> Handle exception — analyze and fix. Returns True if fixed.
- **Calls**: console.print, isinstance, src.pfix.analyzer.analyze_exception, src.pfix.analyzer.classify_error, console.print, src.pfix.llm.request_fix, src.pfix.fixer.apply_fix, src.pfix.dependency.detect_missing_from_error

### src.pfix.env_diagnostics.filesystem.FilesystemDiagnostic.check
> Run all filesystem checks.
- **Calls**: results.extend, results.extend, results.extend, results.extend, results.extend, results.extend, results.extend, results.extend

### src.pfix.commands.config.cmd_check
- **Calls**: src.pfix.config.get_config, config.validate, Table, table.add_column, table.add_column, console.print, console.print, table.add_row

### src.pfix.commands.run.cmd_dev
> Run with dependency development mode active.
- **Calls**: None.resolve, src.pfix.config.configure, console.print, console.print, console.print, src.pfix.dev_mode.install_dev_mode_hook, importlib.util.spec_from_file_location, importlib.util.module_from_spec

### src.pfix.multi_fix.parse_multi_file_response
> Parse LLM response for multi-file fix.

Args:
    raw: Raw LLM response text

Returns:
    MultiFileFixProposal or None if parsing fails
- **Calls**: raw.strip, re.search, m.group, json.loads, MultiFileFixProposal, text.startswith, console.print, text.find

### examples.production.main.main
- **Calls**: print, print, print, exec, print, print, exec, print

### examples.edge_cases.main.main
- **Calls**: print, print, print, exec, print, print, exec, print

### src.pfix.commands.activation.cmd_disable
> Disable pfix auto-activation.
- **Calls**: dest_file.exists, site.getsitepackages, Path, Path, console.print, console.print, site.getusersitepackages, site_packages.exists

### src.pfix.commands.run.cmd_run
- **Calls**: None.resolve, src.pfix.config.configure, src.pfix.commands.run._install_excepthook, importlib.util.spec_from_file_location, importlib.util.module_from_spec, script.is_file, console.print, str

### src.pfix.env_diagnostics.process.ProcessDiagnostic.check
> Run all process/OS checks.
- **Calls**: results.extend, results.extend, results.extend, results.extend, results.extend, results.extend, results.extend, results.extend

### src.pfix.env_diagnostics.memory.MemoryDiagnostic.check
> Run all memory checks.
- **Calls**: results.extend, results.extend, results.extend, results.extend, results.extend, results.extend, results.extend, results.extend

### src.pfix.env_diagnostics.python_version.PythonVersionDiagnostic.check
> Run all Python version checks.
- **Calls**: results.extend, results.extend, results.extend, results.extend, results.extend, results.extend, results.extend, results.extend

### src.pfix.env_diagnostics.paths.PathDiagnostic.check
> Run all path checks.
- **Calls**: results.extend, results.extend, results.extend, results.extend, results.extend, results.extend, results.extend, results.extend

### src.pfix.env_diagnostics.imports.ImportDiagnostic.check
> Run all import/dependency checks.
- **Calls**: results.extend, results.extend, results.extend, results.extend, results.extend, results.extend, results.extend, results.extend

### src.pfix.env_diagnostics.encoding.EncodingDiagnostic._check_file_encoding
> Check Python files for encoding issues.
- **Calls**: project_root.rglob, str, content.startswith, open, f.read, results.append, content.decode, DiagnosticResult

### src.pfix.env_diagnostics.filesystem.FilesystemDiagnostic.diagnose_exception
> Diagnose filesystem-related exceptions.
- **Calls**: isinstance, isinstance, isinstance, DiagnosticResult, DiagnosticResult, DiagnosticResult, str, str

### src.pfix.integrations.precommit.main
> Pre-commit hook entry point.
- **Calls**: argparse.ArgumentParser, parser.add_argument, parser.add_argument, parser.parse_args, print, Path, src.pfix.integrations.precommit.check_syntax, print

### examples.reset.main
> Reset all example directories to original buggy state.
- **Calls**: print, print, Path.cwd, Path, os.chdir, examples.reset.run_git_checkout, os.chdir, print

### src.pfix.production.PfixMonitor.handle_exception
> Handle exception in production mode.

Returns dict with diagnosis info (for logging/webhook).
- **Calls**: src.pfix.analyzer.analyze_exception, src.pfix.cache.get_cached_fix, self.circuit_breaker.is_open, self.rate_limiter.record_call, None.isoformat, self._log_proposal, self._send_webhook, self.rate_limiter.can_call

### src.pfix.env_diagnostics.config_env.ConfigEnvDiagnostic.check
> Run all config/env checks.
- **Calls**: results.extend, results.extend, results.extend, results.extend, results.extend, results.extend, results.extend, self._check_dotenv

### src.pfix.env_diagnostics.python_version.PythonVersionDiagnostic._check_deprecated_imports
> Check for deprecated stdlib imports.
- **Calls**: src.pfix.cache.FixCache.set, self.DEPRECATED_MODULES.items, project_root.rglob, deprecated.update, str, pyfile.read_text, ast.parse, ast.walk

### src.pfix.env_diagnostics.imports.ImportDiagnostic._check_import_source
> Check if local modules are being overshadowed by installed packages.
- **Calls**: project_root.iterdir, item.is_file, local_modules.append, None.lower, item.is_dir, None.exists, local_modules.append, None.metadata.distributions

### src.pfix.types.ErrorContext.to_prompt
- **Calls**: parts.append, None.join, parts.append, parts.append, parts.append, parts.append, self.hints.items, list

### src.pfix.env_diagnostics.EnvDiagnostics.generate_report
> Generate formatted text report from results.
- **Calls**: lines.extend, lines.extend, lines.extend, sum, lines.append, None.join, self._format_severity_section, self._format_severity_section

### src.pfix.env_diagnostics.imports.ImportDiagnostic._build_import_graph
> Build import dependency graph from project files.
- **Calls**: project_root.rglob, self._get_module_name, ast.parse, src.pfix.cache.FixCache.set, ast.walk, str, str, pyfile.read_text

### src.pfix.runtime_todo.capture_exception
> Capture single exception to TODO.md (convenience function).
- **Calls**: src.pfix.config.get_config, getattr, None.get, rt_config.get, RuntimeCollector, collector.capture, collector.shutdown, rt_config.get

### src.pfix.logging.SQLiteLogger.query
> Query events with filters.
- **Calls**: sqlite3.connect, conn.execute, cursor.fetchall, conn.close, str, params.append, params.append, params.append

### src.pfix.rules.ProjectRules._load
> Load and parse rules file.
- **Calls**: self.rules_file.read_text, self.raw_content.splitlines, line.strip, line.startswith, None.replace, line.startswith, line.startswith, None.strip

## Process Flows

Key execution flows identified:

### Flow 1: main
```
main [examples.imports.main]
```

### Flow 2: _handle_exception
```
_handle_exception [src.pfix.session.PFixSession]
  └─ →> analyze_exception
      └─> _fill_traceback_context
          └─> _extract_frame_context
      └─> _fill_function_context
  └─ →> classify_error
```

### Flow 3: check
```
check [src.pfix.env_diagnostics.filesystem.FilesystemDiagnostic]
```

### Flow 4: cmd_check
```
cmd_check [src.pfix.commands.config]
  └─ →> get_config
```

### Flow 5: cmd_dev
```
cmd_dev [src.pfix.commands.run]
  └─ →> configure
```

### Flow 6: parse_multi_file_response
```
parse_multi_file_response [src.pfix.multi_fix]
```

### Flow 7: cmd_disable
```
cmd_disable [src.pfix.commands.activation]
```

### Flow 8: cmd_run
```
cmd_run [src.pfix.commands.run]
  └─> _install_excepthook
      └─> _create_excepthook
          └─ →> analyze_exception
          └─ →> request_fix
  └─ →> configure
```

### Flow 9: _check_file_encoding
```
_check_file_encoding [src.pfix.env_diagnostics.encoding.EncodingDiagnostic]
```

### Flow 10: diagnose_exception
```
diagnose_exception [src.pfix.env_diagnostics.filesystem.FilesystemDiagnostic]
```

## Key Classes

### src.pfix.env_diagnostics.imports.ImportDiagnostic
> Diagnose import and dependency problems.
- **Methods**: 19
- **Key Methods**: src.pfix.env_diagnostics.imports.ImportDiagnostic.check, src.pfix.env_diagnostics.imports.ImportDiagnostic._check_missing_imports, src.pfix.env_diagnostics.imports.ImportDiagnostic._get_all_project_imports, src.pfix.env_diagnostics.imports.ImportDiagnostic._get_installed_packages, src.pfix.env_diagnostics.imports.ImportDiagnostic._build_import_graph, src.pfix.env_diagnostics.imports.ImportDiagnostic._get_module_name, src.pfix.env_diagnostics.imports.ImportDiagnostic._resolve_relative_import, src.pfix.env_diagnostics.imports.ImportDiagnostic._find_cycle_dfs, src.pfix.env_diagnostics.imports.ImportDiagnostic._create_cycle_result, src.pfix.env_diagnostics.imports.ImportDiagnostic._check_circular_imports
- **Inherits**: BaseDiagnostic

### src.pfix.runtime_todo.collector.RuntimeCollector
> Captures runtime errors and writes to TODO.md.

Collection modes:
1. sys.excepthook — catches unhand
- **Methods**: 16
- **Key Methods**: src.pfix.runtime_todo.collector.RuntimeCollector.__init__, src.pfix.runtime_todo.collector.RuntimeCollector.capture, src.pfix.runtime_todo.collector.RuntimeCollector._should_capture, src.pfix.runtime_todo.collector.RuntimeCollector._build_issue, src.pfix.runtime_todo.collector.RuntimeCollector._get_location_info, src.pfix.runtime_todo.collector.RuntimeCollector._get_system_info, src.pfix.runtime_todo.collector.RuntimeCollector._get_timestamps, src.pfix.runtime_todo.collector.RuntimeCollector._extract_frames, src.pfix.runtime_todo.collector.RuntimeCollector._should_exclude_path, src.pfix.runtime_todo.collector.RuntimeCollector._filepath_to_module

### src.pfix.env_diagnostics.python_version.PythonVersionDiagnostic
> Diagnose Python version compatibility problems.
- **Methods**: 15
- **Key Methods**: src.pfix.env_diagnostics.python_version.PythonVersionDiagnostic.check, src.pfix.env_diagnostics.python_version.PythonVersionDiagnostic._check_pyproject_requires, src.pfix.env_diagnostics.python_version.PythonVersionDiagnostic._get_requires_python, src.pfix.env_diagnostics.python_version.PythonVersionDiagnostic._parse_version_requirement, src.pfix.env_diagnostics.python_version.PythonVersionDiagnostic._create_version_error, src.pfix.env_diagnostics.python_version.PythonVersionDiagnostic._check_version_features, src.pfix.env_diagnostics.python_version.PythonVersionDiagnostic._check_file_features, src.pfix.env_diagnostics.python_version.PythonVersionDiagnostic._check_deprecated_imports, src.pfix.env_diagnostics.python_version.PythonVersionDiagnostic._get_deprecated_version, src.pfix.env_diagnostics.python_version.PythonVersionDiagnostic._check_eol_status
- **Inherits**: BaseDiagnostic

### src.pfix.env_diagnostics.config_env.ConfigEnvDiagnostic
> Diagnose configuration and environment variable problems.
- **Methods**: 12
- **Key Methods**: src.pfix.env_diagnostics.config_env.ConfigEnvDiagnostic.check, src.pfix.env_diagnostics.config_env.ConfigEnvDiagnostic._check_dotenv, src.pfix.env_diagnostics.config_env.ConfigEnvDiagnostic._create_missing_env_result, src.pfix.env_diagnostics.config_env.ConfigEnvDiagnostic._check_secrets_in_env, src.pfix.env_diagnostics.config_env.ConfigEnvDiagnostic._check_env_whitespace, src.pfix.env_diagnostics.config_env.ConfigEnvDiagnostic._check_required_vars, src.pfix.env_diagnostics.config_env.ConfigEnvDiagnostic._check_env_gitignore, src.pfix.env_diagnostics.config_env.ConfigEnvDiagnostic._check_pyproject_validity, src.pfix.env_diagnostics.config_env.ConfigEnvDiagnostic._check_pfix_config_missing, src.pfix.env_diagnostics.config_env.ConfigEnvDiagnostic._check_secret_exposure_env
- **Inherits**: BaseDiagnostic

### src.pfix.env_diagnostics.filesystem.FilesystemDiagnostic
> Diagnose filesystem-related problems.
- **Methods**: 12
- **Key Methods**: src.pfix.env_diagnostics.filesystem.FilesystemDiagnostic.check, src.pfix.env_diagnostics.filesystem.FilesystemDiagnostic._check_disk_space, src.pfix.env_diagnostics.filesystem.FilesystemDiagnostic._check_file_references, src.pfix.env_diagnostics.filesystem.FilesystemDiagnostic._check_symlinks, src.pfix.env_diagnostics.filesystem.FilesystemDiagnostic._check_large_files, src.pfix.env_diagnostics.filesystem.FilesystemDiagnostic._check_writable, src.pfix.env_diagnostics.filesystem.FilesystemDiagnostic._check_inodes, src.pfix.env_diagnostics.filesystem.FilesystemDiagnostic._check_permissions, src.pfix.env_diagnostics.filesystem.FilesystemDiagnostic._check_filename_encoding, src.pfix.env_diagnostics.filesystem.FilesystemDiagnostic._check_case_conflicts
- **Inherits**: BaseDiagnostic

### src.pfix.env_diagnostics.process.ProcessDiagnostic
> Diagnose process and OS-related problems.
- **Methods**: 10
- **Key Methods**: src.pfix.env_diagnostics.process.ProcessDiagnostic.check, src.pfix.env_diagnostics.process.ProcessDiagnostic._check_ulimits, src.pfix.env_diagnostics.process.ProcessDiagnostic._check_signal_handlers, src.pfix.env_diagnostics.process.ProcessDiagnostic._check_tmp_writable, src.pfix.env_diagnostics.process.ProcessDiagnostic._check_zombies, src.pfix.env_diagnostics.process.ProcessDiagnostic._check_nice_priority, src.pfix.env_diagnostics.process.ProcessDiagnostic._check_fd_usage, src.pfix.env_diagnostics.process.ProcessDiagnostic._check_core_dumps, src.pfix.env_diagnostics.process.ProcessDiagnostic._check_parent_alive, src.pfix.env_diagnostics.process.ProcessDiagnostic.diagnose_exception
- **Inherits**: BaseDiagnostic

### src.pfix.env_diagnostics.memory.MemoryDiagnostic
> Diagnose memory-related problems.
- **Methods**: 10
- **Key Methods**: src.pfix.env_diagnostics.memory.MemoryDiagnostic.check, src.pfix.env_diagnostics.memory.MemoryDiagnostic._check_available_memory, src.pfix.env_diagnostics.memory.MemoryDiagnostic._check_recursion_limit, src.pfix.env_diagnostics.memory.MemoryDiagnostic._check_gc_pressure, src.pfix.env_diagnostics.memory.MemoryDiagnostic._check_object_count, src.pfix.env_diagnostics.memory.MemoryDiagnostic._check_swap_usage, src.pfix.env_diagnostics.memory.MemoryDiagnostic._check_ulimits, src.pfix.env_diagnostics.memory.MemoryDiagnostic._check_shm_usage, src.pfix.env_diagnostics.memory.MemoryDiagnostic._check_process_memory, src.pfix.env_diagnostics.memory.MemoryDiagnostic.diagnose_exception
- **Inherits**: BaseDiagnostic

### src.pfix.env_diagnostics.paths.PathDiagnostic
> Diagnose path-related problems.
- **Methods**: 10
- **Key Methods**: src.pfix.env_diagnostics.paths.PathDiagnostic.check, src.pfix.env_diagnostics.paths.PathDiagnostic._check_sys_path, src.pfix.env_diagnostics.paths.PathDiagnostic._check_pythonpath, src.pfix.env_diagnostics.paths.PathDiagnostic._check_cwd_space, src.pfix.env_diagnostics.paths.PathDiagnostic._check_long_paths, src.pfix.env_diagnostics.paths.PathDiagnostic._check_cwd_deleted, src.pfix.env_diagnostics.paths.PathDiagnostic._check_root_permissions, src.pfix.env_diagnostics.paths.PathDiagnostic._check_tmp_writable, src.pfix.env_diagnostics.paths.PathDiagnostic._check_symlink_cycles, src.pfix.env_diagnostics.paths.PathDiagnostic.diagnose_exception
- **Inherits**: BaseDiagnostic

### src.pfix.env_diagnostics.EnvDiagnostics
> Orchestrator for all environment diagnostics.
- **Methods**: 9
- **Key Methods**: src.pfix.env_diagnostics.EnvDiagnostics.__init__, src.pfix.env_diagnostics.EnvDiagnostics.diagnostics, src.pfix.env_diagnostics.EnvDiagnostics.check_all, src.pfix.env_diagnostics.EnvDiagnostics.diagnose_exception, src.pfix.env_diagnostics.EnvDiagnostics.generate_report, src.pfix.env_diagnostics.EnvDiagnostics._format_severity_section, src.pfix.env_diagnostics.EnvDiagnostics._generate_summary_footer, src.pfix.env_diagnostics.EnvDiagnostics._format_result, src.pfix.env_diagnostics.EnvDiagnostics.to_todo_issues

### src.pfix.env_diagnostics.hardware.HardwareDiagnostic
> Diagnose hardware-related problems.
- **Methods**: 8
- **Key Methods**: src.pfix.env_diagnostics.hardware.HardwareDiagnostic.check, src.pfix.env_diagnostics.hardware.HardwareDiagnostic._check_gpu_availability, src.pfix.env_diagnostics.hardware.HardwareDiagnostic._check_cpu_count, src.pfix.env_diagnostics.hardware.HardwareDiagnostic._check_docker_limits, src.pfix.env_diagnostics.hardware.HardwareDiagnostic._check_thermal_throttling, src.pfix.env_diagnostics.hardware.HardwareDiagnostic._check_battery_status, src.pfix.env_diagnostics.hardware.HardwareDiagnostic._check_avx_support, src.pfix.env_diagnostics.hardware.HardwareDiagnostic.diagnose_exception
- **Inherits**: BaseDiagnostic

### src.pfix.env_diagnostics.network.NetworkDiagnostic
> Diagnose network-related problems.
- **Methods**: 8
- **Key Methods**: src.pfix.env_diagnostics.network.NetworkDiagnostic.check, src.pfix.env_diagnostics.network.NetworkDiagnostic._check_dns, src.pfix.env_diagnostics.network.NetworkDiagnostic._check_outbound, src.pfix.env_diagnostics.network.NetworkDiagnostic._check_ssl_certs, src.pfix.env_diagnostics.network.NetworkDiagnostic._check_proxy, src.pfix.env_diagnostics.network.NetworkDiagnostic._check_latency, src.pfix.env_diagnostics.network.NetworkDiagnostic._check_system_clock, src.pfix.env_diagnostics.network.NetworkDiagnostic.diagnose_exception
- **Inherits**: BaseDiagnostic

### src.pfix.runtime_todo.todo_file.TodoFile
> Thread-safe, append-only manager for TODO.md.

Features:
- File locking (fcntl on Linux/Unix)
- Appe
- **Methods**: 8
- **Key Methods**: src.pfix.runtime_todo.todo_file.TodoFile.__init__, src.pfix.runtime_todo.todo_file.TodoFile.append_issue, src.pfix.runtime_todo.todo_file.TodoFile._file_lock, src.pfix.runtime_todo.todo_file.TodoFile._load_existing_fingerprints, src.pfix.runtime_todo.todo_file.TodoFile._increment_counter, src.pfix.runtime_todo.todo_file.TodoFile._append_new_entry, src.pfix.runtime_todo.todo_file.TodoFile._format_entry, src.pfix.runtime_todo.todo_file.TodoFile.get_section_content

### src.pfix.env_diagnostics.encoding.EncodingDiagnostic
> Diagnose encoding-related problems.
- **Methods**: 7
- **Key Methods**: src.pfix.env_diagnostics.encoding.EncodingDiagnostic.check, src.pfix.env_diagnostics.encoding.EncodingDiagnostic._check_locale, src.pfix.env_diagnostics.encoding.EncodingDiagnostic._check_file_encoding, src.pfix.env_diagnostics.encoding.EncodingDiagnostic._check_line_endings, src.pfix.env_diagnostics.encoding.EncodingDiagnostic._check_stdio_encoding, src.pfix.env_diagnostics.encoding.EncodingDiagnostic._check_os_environ_encoding, src.pfix.env_diagnostics.encoding.EncodingDiagnostic.diagnose_exception
- **Inherits**: BaseDiagnostic

### src.pfix.mcp_client.MCPClient
> Client for MCP servers (filesystem, editor tools).
- **Methods**: 6
- **Key Methods**: src.pfix.mcp_client.MCPClient.__init__, src.pfix.mcp_client.MCPClient.connect, src.pfix.mcp_client.MCPClient.disconnect, src.pfix.mcp_client.MCPClient.call_tool, src.pfix.mcp_client.MCPClient.edit_file, src.pfix.mcp_client.MCPClient.run_command

### src.pfix.production.PfixMonitor
> Production-safe error monitor. Never modifies code.
- **Methods**: 6
- **Key Methods**: src.pfix.production.PfixMonitor.__init__, src.pfix.production.PfixMonitor.watch, src.pfix.production.PfixMonitor.handle_exception, src.pfix.production.PfixMonitor._log_proposal, src.pfix.production.PfixMonitor._send_webhook, src.pfix.production.PfixMonitor.get_stats

### src.pfix.cache.FixCache
> Cache for fix proposals to avoid redundant LLM calls.
- **Methods**: 6
- **Key Methods**: src.pfix.cache.FixCache.__init__, src.pfix.cache.FixCache.get, src.pfix.cache.FixCache.set, src.pfix.cache.FixCache.clear, src.pfix.cache.FixCache.stats, src.pfix.cache.FixCache.close

### src.pfix.env_diagnostics.concurrency.ConcurrencyDiagnostic
> Diagnose concurrency-related problems.
- **Methods**: 6
- **Key Methods**: src.pfix.env_diagnostics.concurrency.ConcurrencyDiagnostic.check, src.pfix.env_diagnostics.concurrency.ConcurrencyDiagnostic._check_thread_count, src.pfix.env_diagnostics.concurrency.ConcurrencyDiagnostic._check_asyncio_loop, src.pfix.env_diagnostics.concurrency.ConcurrencyDiagnostic._check_thread_hangs, src.pfix.env_diagnostics.concurrency.ConcurrencyDiagnostic._check_async_lag, src.pfix.env_diagnostics.concurrency.ConcurrencyDiagnostic.diagnose_exception
- **Inherits**: BaseDiagnostic

### src.pfix.env_diagnostics.third_party.ThirdPartyDiagnostic
> Diagnose third-party API-related problems.
- **Methods**: 6
- **Key Methods**: src.pfix.env_diagnostics.third_party.ThirdPartyDiagnostic.check, src.pfix.env_diagnostics.third_party.ThirdPartyDiagnostic._check_api_keys_in_env, src.pfix.env_diagnostics.third_party.ThirdPartyDiagnostic._check_hardcoded_key, src.pfix.env_diagnostics.third_party.ThirdPartyDiagnostic._check_missing_timeout, src.pfix.env_diagnostics.third_party.ThirdPartyDiagnostic._check_api_client_configs, src.pfix.env_diagnostics.third_party.ThirdPartyDiagnostic.diagnose_exception
- **Inherits**: BaseDiagnostic

### src.pfix.env_diagnostics.serialization.SerializationDiagnostic
> Diagnose serialization-related problems.
- **Methods**: 6
- **Key Methods**: src.pfix.env_diagnostics.serialization.SerializationDiagnostic.check, src.pfix.env_diagnostics.serialization.SerializationDiagnostic._check_pickle_protocol, src.pfix.env_diagnostics.serialization.SerializationDiagnostic._check_cache_files, src.pfix.env_diagnostics.serialization.SerializationDiagnostic._check_yaml_safety, src.pfix.env_diagnostics.serialization.SerializationDiagnostic._check_json_manifest_validity, src.pfix.env_diagnostics.serialization.SerializationDiagnostic.diagnose_exception
- **Inherits**: BaseDiagnostic

### src.pfix.logging.SQLiteLogger
> SQLite-based logger for FixEvents with querying capabilities.
- **Methods**: 5
- **Key Methods**: src.pfix.logging.SQLiteLogger.__init__, src.pfix.logging.SQLiteLogger._init_db, src.pfix.logging.SQLiteLogger.log, src.pfix.logging.SQLiteLogger.query, src.pfix.logging.SQLiteLogger.get_stats

## Data Transformation Functions

Key functions that process and transform data:

### src.pfix.dashboard._process_log_file
> Process single log file and update stats/history.
- **Output to**: None.strip, content.split, log_file.read_text, json.loads, src.pfix.dashboard._update_stats_from_entry

### src.pfix.cli._build_parser
> Build and configure ArgumentParser for pfix CLI.
- **Output to**: argparse.ArgumentParser, parser.add_subparsers, sub.add_parser, run_p.add_argument, run_p.add_argument

### src.pfix.multi_fix.parse_multi_file_response
> Parse LLM response for multi-file fix.

Args:
    raw: Raw LLM response text

Returns:
    MultiFile
- **Output to**: raw.strip, re.search, m.group, json.loads, MultiFileFixProposal

### src.pfix.fixer._confirm_and_validate
> Check permissions, show diff, and get user confirmation. CC≤5.
- **Output to**: src.pfix.permissions.check_all_permissions, src.pfix.fixer._display_diff, console.print, src.pfix.fixer._record_fix_telemetry, console.print

### src.pfix.fixer._validate_syntax
- **Output to**: ast.parse

### src.pfix.diff_fixer.parse_unified_diff
> Parse unified diff text into hunks.
Returns list of (old_path, new_path, hunk_lines).
- **Output to**: diff_text.splitlines, len, None.startswith, src.pfix.diff_fixer._parse_file_header, src.pfix.diff_fixer._collect_hunk_lines

### src.pfix.diff_fixer._parse_file_header
> Parse --- and +++ lines.
- **Output to**: None.strip, None.strip, len, DiffParseError, new_line.startswith

### src.pfix.diff_fixer.parse_hunk_header
> Parse hunk header like @@ -1,5 +1,7 @@.
Returns (old_start, old_count, new_start, new_count).
- **Output to**: re.match, int, int, DiffParseError, match.group

### src.pfix.diff_fixer._process_hunk_body
> Process lines within a hunk body and return new lines and count of old lines consumed.
- **Output to**: line.startswith, line.startswith, new_lines.append, line.startswith, len

### src.pfix.config.PfixConfig.validate
- **Output to**: warnings.append

### src.pfix.validation.validate_fix
> Validate a fix by running tests.

If tests fail and rollback is enabled, restore from backup.

Args:
- **Output to**: src.pfix.config.get_config, getattr, src.pfix.validation.run_tests, console.print, console.print

### src.pfix.validation.quick_validate_syntax
> Quick syntax validation for a single file.
- **Output to**: filepath.read_text, ast.parse

### src.pfix.validation.validate_with_fallback
> Full validation workflow with fallback.

1. Validate syntax
2. Run tests
3. Rollback if needed
- **Output to**: Path, src.pfix.validation.validate_fix, console.print, ValidationResult, src.pfix.validation.quick_validate_syntax

### src.pfix.session._restart_process
> Restart current process. CC≤2.
- **Output to**: console.print, os.execv, src.pfix.analyzer.analyze_exception, src.pfix.session._clear_pycache, Path

### src.pfix.analyzer._format_local_vars
> Anonymize and repr local variables.
- **Output to**: src.pfix.analyzer._safe_repr, local_vars.items, k.startswith

### src.pfix.commands.diagnose._format_diagnostic_results
> Format diagnostic results for output (JSON or text).
- **Output to**: json.dumps, diag.generate_report

### src.pfix.env_diagnostics.memory.MemoryDiagnostic._check_process_memory
> Check if current process occupies too much of system memory.
- **Output to**: psutil.Process, proc.memory_info, os.getpid, psutil.virtual_memory, results.append

### src.pfix.env_diagnostics.EnvDiagnostics._format_severity_section
> Format a section of results with given status.
- **Output to**: lines.append, lines.append, self._format_result

### src.pfix.env_diagnostics.EnvDiagnostics._format_result
> Format single result as markdown.
- **Output to**: lines.append, lines.append, lines.append, None.join, lines.append

### src.pfix.env_diagnostics.python_version.PythonVersionDiagnostic._parse_version_requirement
> Parse version numbers from a requirement string.
- **Output to**: re.search, int, int

### src.pfix.integrations.sentry.PfixSentryIntegration._process_event
> Process Sentry event to add pfix context.
- **Output to**: hint.get, src.pfix.analyzer.analyze_exception, src.pfix.llm.request_fix, len

### src.pfix.runtime_todo.todo_file.TodoFile._format_entry
> Format RuntimeIssue as markdown TODO entry.
- **Output to**: enumerate, issue.timestamp.strftime, trace_parts.append, None.join, Path

### examples.complex_demo.main.load_and_process_data
> Load CSV, process it, return statistics.
- **Output to**: pd.read_csv, None.mean, len, list, None.sum

### examples.memory.main.process_stream
- **Output to**: src.pfix.decorator.pfix, range, len, list, results.extend

### examples.production.degradation.parse_api_v2_response
- **Output to**: src.pfix.decorator.pfix

## Behavioral Patterns

### state_machine_MCPClient
- **Type**: state_machine
- **Confidence**: 0.70
- **Functions**: src.pfix.mcp_client.MCPClient.__init__, src.pfix.mcp_client.MCPClient.connect, src.pfix.mcp_client.MCPClient.disconnect, src.pfix.mcp_client.MCPClient.call_tool, src.pfix.mcp_client.MCPClient.edit_file

### state_machine_PFixSession
- **Type**: state_machine
- **Confidence**: 0.70
- **Functions**: src.pfix.session.PFixSession.__init__, src.pfix.session.PFixSession.__enter__, src.pfix.session.PFixSession.__exit__, src.pfix.session.PFixSession.__call__, src.pfix.session.PFixSession._handle_exception

## Public API Surface

Functions exposed as public API (no underscore prefix):

- `src.pfix.dashboard.render_dashboard` - 32 calls
- `examples.imports.main.main` - 27 calls
- `examples.run_all.main` - 21 calls
- `src.pfix.env_diagnostics.filesystem.FilesystemDiagnostic.check` - 20 calls
- `src.pfix.commands.config.cmd_check` - 19 calls
- `src.pfix.commands.run.cmd_dev` - 19 calls
- `src.pfix.multi_fix.parse_multi_file_response` - 18 calls
- `src.pfix.rollback.rollback_file` - 18 calls
- `src.pfix.audit.print_audit_report` - 18 calls
- `examples.production.main.main` - 17 calls
- `examples.edge_cases.main.main` - 17 calls
- `src.pfix.commands.activation.cmd_disable` - 16 calls
- `src.pfix.commands.run.cmd_run` - 16 calls
- `src.pfix.env_diagnostics.process.ProcessDiagnostic.check` - 16 calls
- `src.pfix.env_diagnostics.memory.MemoryDiagnostic.check` - 16 calls
- `src.pfix.env_diagnostics.python_version.PythonVersionDiagnostic.check` - 16 calls
- `src.pfix.env_diagnostics.paths.PathDiagnostic.check` - 16 calls
- `src.pfix.env_diagnostics.imports.ImportDiagnostic.check` - 16 calls
- `src.pfix.runtime_todo.get_collector` - 16 calls
- `src.pfix.validation.run_tests` - 15 calls
- `src.pfix.rollback.show_history` - 15 calls
- `src.pfix.env_diagnostics.filesystem.FilesystemDiagnostic.diagnose_exception` - 15 calls
- `src.pfix.integrations.precommit.check_imports` - 15 calls
- `src.pfix.integrations.precommit.main` - 15 calls
- `examples.reset.main` - 14 calls
- `src.pfix.production.PfixMonitor.handle_exception` - 14 calls
- `src.pfix.cache.FixCache.set` - 14 calls
- `src.pfix.env_diagnostics.config_env.ConfigEnvDiagnostic.check` - 14 calls
- `src.pfix.diff_fixer.apply_diff` - 13 calls
- `src.pfix.types.ErrorContext.to_prompt` - 13 calls
- `src.pfix.audit.log_fix_audit` - 13 calls
- `src.pfix.env_diagnostics.EnvDiagnostics.generate_report` - 13 calls
- `src.pfix.runtime_todo.capture_exception` - 13 calls
- `src.pfix.dashboard.get_log_stats` - 12 calls
- `src.pfix.explain.explain_last` - 12 calls
- `src.pfix.diff_fixer.parse_hunk_header` - 12 calls
- `src.pfix.logging.SQLiteLogger.query` - 12 calls
- `src.pfix.commands.config.cmd_status` - 12 calls
- `src.pfix.commands.others.cmd_deps` - 12 calls
- `src.pfix.env_diagnostics.hardware.HardwareDiagnostic.check` - 12 calls

## System Interactions

How components interact:

```mermaid
graph TD
    main --> print
    main --> exec
    main --> ArgumentParser
    main --> add_argument
    main --> parse_args
    _handle_exception --> print
    _handle_exception --> isinstance
    _handle_exception --> analyze_exception
    _handle_exception --> classify_error
    check --> extend
    cmd_check --> get_config
    cmd_check --> validate
    cmd_check --> Table
    cmd_check --> add_column
    cmd_dev --> resolve
    cmd_dev --> configure
    cmd_dev --> print
    parse_multi_file_res --> strip
    parse_multi_file_res --> search
    parse_multi_file_res --> group
    parse_multi_file_res --> loads
    parse_multi_file_res --> MultiFileFixProposal
    cmd_disable --> exists
    cmd_disable --> getsitepackages
    cmd_disable --> Path
    cmd_disable --> print
    cmd_run --> resolve
    cmd_run --> configure
    cmd_run --> _install_excepthook
    cmd_run --> spec_from_file_locat
```

## Reverse Engineering Guidelines

1. **Entry Points**: Start analysis from the entry points listed above
2. **Core Logic**: Focus on classes with many methods
3. **Data Flow**: Follow data transformation functions
4. **Process Flows**: Use the flow diagrams for execution paths
5. **API Surface**: Public API functions reveal the interface

## Context for LLM

Maintain the identified architectural patterns and public API surface when suggesting changes.
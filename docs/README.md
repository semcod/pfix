<!-- code2docs:start --># pfix

![version](https://img.shields.io/badge/version-0.1.0-blue) ![python](https://img.shields.io/badge/python-%3E%3D3.10-blue) ![coverage](https://img.shields.io/badge/coverage-unknown-lightgrey) ![functions](https://img.shields.io/badge/functions-75-green)
> **75** functions | **6** classes | **16** files | CC̄ = 4.5

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
pip install pfix[dev]    # development tools
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
    ├── demo_auto    ├── demo        ├── cli        ├── analyzer        ├── fixer    ├── pfix/        ├── mcp_client        ├── config        ├── dev_mode        ├── dependency        ├── mcp_server        ├── main├── project        ├── decorator        ├── session        ├── llm```

## API Overview

### Classes

- **`ErrorContext`** — Structured error report for LLM consumption.
- **`MCPResult`** — —
- **`MCPClient`** — Client for MCP servers (filesystem, editor tools).
- **`PfixConfig`** — Central configuration.
- **`PFixSession`** — Session context that catches and auto-fixes exceptions.
- **`FixProposal`** — Structured fix from LLM.

### Functions

- `fetch_json(url)` — Fetch JSON — dependencies auto-installed.
- `average(numbers)` — Calculate average — will auto-fix on error.
- `greet(name, age)` — Greet user — will auto-fix on error.
- `main()` — —
- `fetch_json(url)` — Fetch JSON from URL — dependencies auto-installed on first run.
- `average(numbers)` — Calculate average — ZeroDivisionError will be auto-fixed.
- `greet(name, age)` — Greet user — TypeError will be auto-fixed.
- `main()` — —
- `main(argv)` — —
- `cmd_run(args)` — —
- `cmd_dev(args)` — Run with dependency development mode active.
- `cmd_check()` — —
- `cmd_enable()` — Enable pfix auto-activation and add config to pyproject.toml.
- `cmd_disable()` — Disable pfix auto-activation.
- `cmd_deps(args)` — —
- `cmd_server(args)` — —
- `analyze_exception(exc, func, local_vars, hints)` — Build ErrorContext from a caught exception.
- `classify_error(ctx)` — Classify error to guide fix strategy.
- `scan_missing_deps(project_dir)` — Use pipreqs to detect imports that aren't installed.
- `apply_fix(ctx, proposal, confirm)` — Apply a FixProposal. Returns True if anything was applied.
- `get_config()` — —
- `configure()` — Override global config programmatically.
- `reset_config()` — Reset global config (useful in tests).
- `is_site_package(module)` — Check if module is from site-packages (third-party).
- `wrap_module_functions(module)` — Wrap all callable attributes of a module with error handling.
- `install_dev_mode_hook()` — Install the development mode import hook.
- `resolve_package_name(module_name)` — Map Python module name → PyPI package name.
- `is_module_available(module_name)` — —
- `install_packages(packages, dry_run)` — Install packages via pip or uv. Returns {package: success}.
- `scan_project_deps(project_dir)` — Use pipreqs to scan project for all imports and find missing ones.
- `update_requirements_file(packages, requirements_path)` — Append packages to requirements.txt.
- `generate_requirements(project_dir)` — Generate requirements.txt via pipreqs for the project.
- `detect_missing_from_error(exception_message)` — Extract module name from ModuleNotFoundError/ImportError.
- `create_mcp_server()` — Create FastMCP server with pfix tools.
- `start_server(transport, host, port)` — Start the MCP server.
- `load_and_process_data(filepath)` — Load CSV, process it, return statistics.
- `analyze_users(users)` — Analyze user data with multiple bugs.
- `main()` — —
- `pfix(func)` — Self-healing decorator. Catches errors, fixes code via LLM.
- `apfix(func)` — Async version of @pfix.
- `pfix_session(target_file)` — Create pfix session for file-level auto-healing.
- `auto_pfix(func)` — Decorator that auto-fixes exceptions in wrapped function.
- `install_pfix_hook(target_file, auto_apply)` — Install global pfix excepthook.
- `request_fix(error_ctx)` — Send error to LLM, get fix proposal.


## Project Structure

📄 `examples.complex_demo.main` (3 functions)
📄 `examples.demo` (4 functions)
📄 `examples.demo_auto` (4 functions)
📄 `project`
📦 `src.pfix` (1 functions)
📄 `src.pfix.analyzer` (6 functions, 1 classes)
📄 `src.pfix.cli` (9 functions)
📄 `src.pfix.config` (6 functions, 1 classes)
📄 `src.pfix.decorator` (7 functions)
📄 `src.pfix.dependency` (7 functions)
📄 `src.pfix.dev_mode` (4 functions)
📄 `src.pfix.fixer` (7 functions)
📄 `src.pfix.llm` (2 functions, 1 classes)
📄 `src.pfix.mcp_client` (6 functions, 2 classes)
📄 `src.pfix.mcp_server` (3 functions)
📄 `src.pfix.session` (8 functions, 1 classes)

## Requirements

- Python >= >=3.10
- litellm >=1.40.0- python-dotenv >=1.0.0- rich >=13.0.0- pipreqs >=0.4.0- pathspec >=0.12.0

## Contributing

**Contributors:**
- Tom Sapletta

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
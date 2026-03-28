# pfix Examples

[![pfix](https://img.shields.io/badge/pfix-0.1.5-blue)](https://github.com/semcod/pfix)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

Example scripts demonstrating different usage patterns of the pfix self-healing library.

## Available Examples

### 1. `demo_auto.py` — Zero-Configuration Mode

**The simplest way to use pfix.** Just `import pfix` with `PFIX_AUTO_APPLY=true` in `.env`.

```bash
# Set up environment
export OPENROUTER_API_KEY=sk-or-v1-...
export PFIX_AUTO_APPLY=true

# Run - that's it!
python demo_auto.py
```

**What it demonstrates:**
- Auto-activation on import (no decorators needed)
- Global exception hook catching all errors
- Automatic dependency installation (`requests`)
- Auto-fixing `ZeroDivisionError` (empty list → guard clause)
- Auto-fixing `TypeError` (str + int → str conversion)

**Key code:**
```python
import pfix  # That's all you need!

def average(numbers: list[float]) -> float:
    return sum(numbers) / len(numbers)  # Bug: auto-fixed

def greet(name: str, age: int) -> str:
    return "Hello " + name + "! Age: " + age  # Bug: auto-fixed

average([])  # Triggers ZeroDivisionError → gets fixed
greet("Alice", 30)  # Triggers TypeError → gets fixed
```

**Library behavior:**
1. Exception propagates to global `sys.excepthook`
2. pfix hook intercepts and analyzes error
3. LLM receives: traceback, source code, local vars, imports
4. Fix is proposed and auto-applied (since `PFIX_AUTO_APPLY=true`)
5. Source file is modified in-place with fix
6. Backup created in `.pfix_backups/`
7. Program continues (or restarts if `PFIX_AUTO_RESTART=true`)

---

### 2. `demo.py` — Explicit Session Control

**Fine-grained control** using `pfix_session` context manager.

```bash
python demo.py
```

**What it demonstrates:**
- Explicit configuration via `configure()`
- `pfix_session` context manager
- Targeted file-level protection
- Custom auto-apply settings per session

**Key code:**
```python
from pfix import configure, pfix_session

configure(auto_apply=True, dry_run=False)

def risky_function():
    return 1 / 0  # Division by zero

with pfix_session(__file__, auto_apply=True):
    # Only code inside this block is protected
    risky_function()

# Code outside is NOT protected by pfix
```

**Library behavior:**
1. `configure()` sets global options
2. `pfix_session(__file__)` creates session for this specific file
3. `__enter__` installs custom excepthook
4. If exception occurs in block, `__exit__` handles it
5. Fix is applied to the file specified (`__file__`)
6. `__exit__` restores original excepthook

**Use when:**
- You want to protect only specific code blocks
- You need different settings for different parts of code
- You want explicit control over when pfix is active

---

## Usage Patterns Explained

### Pattern 1: Zero-Config (Recommended for Development)

```python
# .env
OPENROUTER_API_KEY=sk-or-v1-...
PFIX_AUTO_APPLY=true
PFIX_CREATE_BACKUPS=true
```

```python
# script.py
import pfix  # Auto-activates if PFIX_AUTO_APPLY=true

# Your code here - all exceptions auto-fixed
```

**Best for:**
- Rapid prototyping
- Development environments
- Scripts and one-off tools
- Learning/experimenting

**Caveats:**
- Affects entire process
- All exceptions trigger LLM calls (API costs)
- May mask issues you want to see

---

### Pattern 2: Session-Based (Recommended for Production)

```python
from pfix import pfix_session

# Only protect critical sections
with pfix_session(__file__, auto_apply=True):
    untrusted_user_code()

# Other code runs normally
reliable_code()
```

**Best for:**
- Production applications
- Specific error-prone sections
- Untrusted/user code execution
- Fine-grained control

---

### Pattern 3: Decorator (Recommended for Libraries)

```python
from pfix import pfix

@pfix(retries=3, hint="Processes user data")
def process_user_input(data):
    # Only this function is protected
    return parse(data)
```

**Best for:**
- Library functions with known failure modes
- Functions with external dependencies
- Specific functions needing hints
- Granular, function-level control

---

## How Fixes Are Applied

### Step-by-Step Process

```
1. EXCEPTION OCCURS
   └─> Code raises ZeroDivisionError, TypeError, etc.

2. ERROR CONTEXT BUILT
   ├─> Traceback captured
   ├─> Source file read
   ├─> Function located in AST
   ├─> Local variables snapshot
   └─> Imports analyzed

3. LLM ANALYSIS
   ├─> ErrorContext sent to model
   ├─> Model returns FixProposal
   ├─> Diagnosis (what went wrong)
   ├─> Fixed code
   └─> Confidence score (0-100%)

4. FIX VALIDATION
   ├─> Confidence > 10%? (skip if too low)
   ├─> New code is syntactically valid?
   ├─> Show diff (or auto-apply)
   └─> User confirmation (if auto_apply=false)

5. FIX APPLICATION
   ├─> Create backup (if create_backups=true)
   ├─> Write fixed code to file
   ├─> Git commit (if git_auto_commit=true)
   └─> Log action

6. RECOVERY
   ├─> Module reload → retry (for @pfix)
   └─> Or: os.execv restart (if auto_restart=true)
```

### Confidence Thresholds

| Confidence | Action | Typical Fixes |
|------------|--------|---------------|
| 90-100% | High confidence auto-apply | Type conversions (`str(x)`), simple guards |
| 50-89% | Medium confidence | Logic changes, API adjustments |
| 10-49% | Low confidence | Complex refactorings, structural changes |
| <10% | Skipped | Manual review recommended |

### Error Types & Auto-Fix Strategies

| Error | Fix Strategy | Example |
|-------|-------------|---------|
| `ModuleNotFoundError` | pip/uv install | `pip install missing_pkg` |
| `NameError` | Add import | `import os` at file top |
| `TypeError` | Type conversion | `str(age)` vs `age` |
| `AttributeError` | Fix access pattern | `dict.get()` vs `dict[key]` |
| `ZeroDivisionError` | Guard clause | `if x == 0: return 0` |
| `IndexError` | Bounds check | `if i < len(list):` |
| `KeyError` | Safe access | `dict.get(key, default)` |
| `ValueError` | Input validation | Try/except, validation |
| `FileNotFoundError` | Path check | `if os.path.exists():` |

---

## Configuration Reference

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PFIX_AUTO_APPLY` | `false` | Auto-apply without confirmation |
| `PFIX_AUTO_INSTALL_DEPS` | `true` | Auto `pip install` missing packages |
| `PFIX_AUTO_RESTART` | `false` | Restart process after fix |
| `PFIX_CREATE_BACKUPS` | `true` | Create `.pfix_backups/` files |
| `PFIX_MAX_RETRIES` | `3` | Max fix attempts per error |
| `PFIX_DRY_RUN` | `false` | Show fixes, don't apply |
| `PFIX_MODEL` | `claude-sonnet-4` | LLM model for fixes |
| `PFIX_GIT_COMMIT` | `false` | Auto-commit to git |

### Programmatic Configuration

```python
from pfix import configure

configure(
    auto_apply=True,
    dry_run=False,
    create_backups=True,
    max_retries=3,
    pkg_manager="uv",  # or "pip"
)
```

---

## Running the Examples

### Prerequisites

```bash
# 1. Install pfix
pip install -e ..

# 2. Set up API key
export OPENROUTER_API_KEY=sk-or-v1-...

# 3. (Optional) Create .env file
cat > .env << EOF
OPENROUTER_API_KEY=sk-or-v1-...
PFIX_AUTO_APPLY=true
PFIX_MODEL=openrouter/anthropic/claude-sonnet-4
EOF
```

### Run Zero-Config Example

```bash
python demo_auto.py
```

Expected output:
```
=== pfix Demo (zero config) ===

1. fetch_json:
   ✓ dict

💥 pfix caught: ZeroDivisionError: division by zero
🔍 Analyzing (other)...
╭─ 🔧 Add a guard condition... ─────────────────────────────╮
│ --- a/demo_auto.py                                         │
│ +++ b/demo_auto.py                                         │
│ @@ -17,6 +17,8 @@                                         │
│  def average(numbers: list[float]) -> float:              │
│      """Calculate average — will auto-fix on error."""    │
│ +    if len(numbers) == 0:                                 │
│ +        return float('nan')                               │
│      return sum(numbers) / len(numbers)                   │
╰────────────────────────── confidence: 95% ─────────────────╯
  Backup: .pfix_backups/demo_auto.py.20250115_120000.bak
✓ Fix applied to demo_auto.py

2. average([]):
   ✓ nan

3. greet('Alice', 30):
   ✓ Hello Alice! Age: 30
```

---

## Troubleshooting

### "LLM confidence too low"
**Problem:** Fix confidence below 10%, skipping.
**Solutions:**
- Add hint: `@pfix(hint="What this function does")`
- Check API key is valid
- Try different model in `PFIX_MODEL`
- Simplify the failing code

### "Could not locate function"
**Problem:** pfix can't find function in AST to replace.
**Solutions:**
- Ensure error is in a named function (not lambda/exec)
- Use `pfix_session` for module-level code
- Check the function is defined in the expected file

### Too many backup files
**Problem:** `.pfix_backups/` directory growing.
**Solution:**
```bash
# Disable backups
export PFIX_CREATE_BACKUPS=false

# Or clean periodically
rm -rf .pfix_backups/
```

### Endless restart loops
**Problem:** Process keeps restarting on same error.
**Solution:**
```bash
# Disable restart
export PFIX_AUTO_RESTART=false

# Or limit retries
export PFIX_MAX_RETRIES=1
```

---

## See Also

- [Main README](../README.md) — Full documentation
- [Configuration Guide](../README.md#configuration) — All config options
- [Troubleshooting](../README.md#troubleshooting) — Common issues
- [PyPI](https://pypi.org/project/pfix/) — Package page

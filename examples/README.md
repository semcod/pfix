# pfix Examples

This directory contains example scripts demonstrating different ways to use pfix.

## Files

### `demo_auto.py` — Zero-Configuration Auto-Healing

The simplest way to use pfix. Just `import pfix` and it automatically:
- Catches all exceptions
- Auto-fixes code via LLM
- Installs missing dependencies

**Usage:**
```bash
# 1. Set PFIX_AUTO_APPLY=true in your .env
# 2. Run the script
python demo_auto.py
```

**Key features:**
- No decorators needed
- No `configure()` call needed
- No context manager needed
- Global exception hook auto-installed on import

---

### `demo.py` — Explicit Session Control

Demonstrates explicit control using `pfix_session` context manager.

**Usage:**
```bash
python demo.py
```

**Key features:**
- Uses `with pfix_session(__file__)` block
- Explicit auto-apply configuration
- Targets specific file for fixes
- Good when you want fine-grained control

---

## Quick Start

1. **Copy the examples:**
   ```bash
   cp examples/demo_auto.py my_project/
   ```

2. **Set up your .env:**
   ```bash
   OPENROUTER_API_KEY=sk-or-v1-...
   PFIX_AUTO_APPLY=true
   PFIX_MODEL=openrouter/anthropic/claude-sonnet-4
   ```

3. **Just add the import:**
   ```python
   import pfix  # That's it!
   ```

4. **Run your buggy code:**
   ```python
   def broken():
       return 1 / 0  # Will be auto-fixed!
   
   broken()
   ```

## See Also

- [Main README](../README.md)
- [Configuration Options](../README.md#configuration)

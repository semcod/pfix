# Getting Started with pfix

This example demonstrates the simplest way to use pfix: **Zero-Configuration Mode**.

## Features
- Auto-activation on import (no decorators needed).
- Global exception hook catching all errors.
- Automatic dependency installation.
- Auto-fixing common errors (ZeroDivisionError, TypeError).

## Usage

1. Create a `.env` file with your API key:
   ```bash
   OPENROUTER_API_KEY=sk-or-v1-...
   PFIX_AUTO_APPLY=true
   ```

2. Run the example:
   ```bash
   python main.py
   ```

## How it works
By just importing `pfix`, the library checks your environment variables. If `PFIX_AUTO_APPLY` is true, it installs a global exception hook that intercepts any unhandled exceptions and attempts to fix the source code using an LLM.

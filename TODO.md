# TODO

## Runtime Errors (Production)

- [x] /home/tom/github/semcod/pfix/verify_runtime.py:20 - ZeroDivisionError: division by zero
      ↳ **INTENTIONAL** - Test code to verify error capture system
      ↳ This is expected behavior, not a bug
- [x] /home/tom/github/semcod/pfix/src/pfix/cli.py:153 - TypeError: cmd_status() takes 0 positional arguments but 1 was given
      ↳ **FIXED** - Changed `cmd_status(args=None)` to `cmd_status(args)` in config.py:53
- [ ] /home/tom/github/semcod/pfix/src/pfix/env_diagnostics/__init__.py:34 - ImportError: cannot import name 'ImportDiagnostic' from 'src.pfix.env_diagnostics.imports' (/home/tom/github/semcod/pfix/src/pfix/env_diagnostics/imports/__init__.py)
      ↳ function: <module>()
      ↳ trace: __init__.py:34 → <string>:1
      ↳ seen: 2026-03-29T17:03:25Z (1x)
      ↳ env: py3.13.7 | nvidia | venv:system
      <!-- pfix:fp=c647756874b4e053 count=2 first=2026-03-29T17:03:25Z last=2026-03-29T17:05:05.675850+00:00 -->
- [ ] /home/tom/github/semcod/pfix/src/pfix/env_diagnostics/imports/__init__.py:34 - RecursionError: maximum recursion depth exceeded
      ↳ function: __getattr__()
      ↳ trace: __init__.py:34 → <frozen importlib._bootstrap>:1412 → __init__.py:34 → <frozen importlib._bootstrap>:1412 → __init__.py:34
      ↳ seen: 2026-03-29T17:05:36Z (1x)
      ↳ env: py3.13.7 | nvidia | venv:system
      <!-- pfix:fp=f44f61bb2e9ffe16 count=1 first=2026-03-29T17:05:36Z last=2026-03-29T17:05:36Z -->
- [ ] /home/tom/github/semcod/pfix/src/pfix/env_diagnostics/__init__.py:35 - AttributeError: module 'src.pfix.env_diagnostics.imports' has no attribute 'ImportDiagnostic'
      ↳ function: <module>()
      ↳ trace: __init__.py:35 → <string>:1
      ↳ seen: 2026-03-29T17:06:11Z (1x)
      ↳ env: py3.13.7 | nvidia | venv:system
      <!-- pfix:fp=818e1daea37bede1 count=1 first=2026-03-29T17:06:11Z last=2026-03-29T17:06:11Z -->
- [ ] /home/tom/github/semcod/pfix/src/pfix/env_diagnostics/__init__.py:36 - AttributeError: module 'src.pfix.env_diagnostics.imports' has no attribute 'ImportDiagnostic'
      ↳ function: <module>()
      ↳ trace: __init__.py:36 → <string>:1
      ↳ seen: 2026-03-29T17:06:30Z (1x)
      ↳ env: py3.13.7 | nvidia | venv:system
      <!-- pfix:fp=da6fad5d393d83ae count=1 first=2026-03-29T17:06:30Z last=2026-03-29T17:06:30Z -->

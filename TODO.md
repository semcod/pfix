# TODO

## Runtime Errors (Production)

- [ ] /home/tom/github/semcod/pfix/verify_runtime.py:20 - ZeroDivisionError: division by zero
      ↳ function: crash_me()
      ↳ trace: verify_runtime.py:20 → decorator.py:115
      ↳ seen: 2026-03-29T06:26:08Z (1x)
      ↳ env: py3.13.7 | nvidia | venv:system
      <!-- pfix:fp=a409871babd9c0ba count=1 first=2026-03-29T06:26:08Z last=2026-03-29T06:26:08Z -->
- [ ] /home/tom/github/semcod/pfix/src/pfix/cli.py:153 - TypeError: cmd_status() takes 0 positional arguments but 1 was given
      ↳ function: _dispatch()
      ↳ trace: cli.py:153 → cli.py:32 → cli.py:160 → <frozen runpy>:88 → <frozen runpy>:198
      ↳ seen: 2026-03-29T07:35:54Z (1x)
      ↳ env: py3.13.7 | nvidia | venv:system
      <!-- pfix:fp=ba805e3ec0bdb4bc count=1 first=2026-03-29T07:35:54Z last=2026-03-29T07:35:54Z -->

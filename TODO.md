# TODO

## Runtime Errors (Production)

- [x] /home/tom/github/semcod/pfix/verify_runtime.py:20 - ZeroDivisionError: division by zero
      ↳ **INTENTIONAL** - Test code to verify error capture system
      ↳ This is expected behavior, not a bug
- [x] /home/tom/github/semcod/pfix/src/pfix/cli.py:153 - TypeError: cmd_status() takes 0 positional arguments but 1 was given
      ↳ **FIXED** - Changed `cmd_status(args=None)` to `cmd_status(args)` in config.py:53

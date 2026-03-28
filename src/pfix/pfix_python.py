#!/usr/bin/env python3
"""
pfix-python wrapper - runs any Python script with pfix auto-repair enabled.

Usage: pfix-python script.py [args...]
       pfix-python -m module [args...]

This wrapper replaces the standard python command and automatically
enables pfix for all scripts without needing 'import pfix' in code.
"""

import sys
import os
import subprocess
from pathlib import Path

def main():
    # Ensure pfix auto-activation is enabled
    os.environ['PFIX_AUTO_APPLY'] = os.getenv('PFIX_AUTO_APPLY', 'true')
    
    # Get the real python executable
    python_exe = sys.executable
    
    # Pass through all arguments
    args = sys.argv[1:]
    
    # Run with pfix enabled via .pth file
    # The .pth file in site-packages will auto-activate pfix
    try:
        result = subprocess.run([python_exe] + args, check=False)
        sys.exit(result.returncode)
    except KeyboardInterrupt:
        sys.exit(130)
    except Exception as e:
        print(f"pfix-python error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()

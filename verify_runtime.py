
import os
import sys
from pathlib import Path

# Fix path to ensure we use the local src
sys.path.insert(0, str(Path.cwd() / "src"))

import pfix
from pfix import pfix, reset_config

# Reset config to ensure it picks up the latest pyproject.toml
reset_config()

# Set retries=0 so it logs to TODO.md on the first failure
@pfix(auto_apply=False, retries=0)
def crash_me():
    """This function will crash and should be logged to TODO.md"""
    print("Executing crash_me...")
    x = 1 / 0

if __name__ == "__main__":
    print("Testing runtime error capture...")
    
    # Remove old TODO.md if exists
    if os.path.exists("TODO.md"):
        os.remove("TODO.md")
        print("Removed old TODO.md")

    try:
        crash_me()
    except ZeroDivisionError:
        print("Caught expected ZeroDivisionError.")
    
    # Wait for flush (Collector shutdown() in decorator should force it)
    print("Checking for TODO.md...")
    
    if os.path.exists("TODO.md"):
        print("✓ TODO.md created!")
        content = open("TODO.md").read()
        print("--- TODO.md content ---")
        print(content)
        print("-----------------------")
        if "ZeroDivisionError" in content:
            print("🎉 SUCCESS: ZeroDivisionError found in TODO.md")
        else:
            print("❌ FAILURE: ZeroDivisionError NOT found in TODO.md")
    else:
        # Check if maybe it's still being flushed
        import time
        time.sleep(2)
        if os.path.exists("TODO.md"):
             print("✓ TODO.md created after delay!")
        else:
             print("❌ FAILURE: TODO.md NOT created even after delay!")

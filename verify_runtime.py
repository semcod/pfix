
from pfix import apfix
import os

@apfix(auto_apply=False)
def crash_me():
    """This function will crash and should be logged to TODO.md"""
    x = 1 / 0

if __name__ == "__main__":
    print("Testing runtime error capture...")
    try:
        crash_me()
    except ZeroDivisionError:
        print("Caught expected error. Checking TODO.md...")
    
    if os.path.exists("TODO.md"):
        print("✓ TODO.md created!")
        content = open("TODO.md").read()
        print("--- TODO.md content ---")
        print(content)
        print("-----------------------")
    else:
        print("✗ TODO.md NOT created!")

#!/usr/bin/env python3
"""Resource leaks and large object handling."""

from pfix import pfix


@pfix(hint="Reading entire large file into memory instead of line-by-line")
def count_lines_in_large_file(path: str) -> int:
    content = open(path).read()  # Loads entire file — OOM on large files
    return len(content.splitlines())


@pfix(hint="Creating huge list when generator would suffice")
def squares_up_to(n: int) -> int:
    all_squares = [i ** 2 for i in range(n)]  # Allocates entire list
    return sum(all_squares)


@pfix(hint="Accumulating results without clearing — memory grows forever")
def process_stream():
    results = []
    for batch_num in range(100):
        batch = list(range(10_000))
        processed = [x * 2 for x in batch]
        results.extend(processed)  # Never cleared — grows to 1M+ items
    # Should process and clear each batch, or use itertools.chain
    return len(results)


@pfix(hint="Circular reference prevents garbage collection")
def create_circular_ref():
    class Node:
        def __init__(self, name):
            self.name = name
            self.children = []
            self.parent = None

    root = Node("root")
    child = Node("child")
    child.parent = root      # child → root
    root.children.append(child)  # root → child (circular)

    # With __del__ defined, GC can't collect these
    Node.__del__ = lambda self: None  # Adding __del__ blocks GC for cycles

    return f"Created {root.name} with {len(root.children)} children"


if __name__ == "__main__":
    import tempfile, os
    tmp = tempfile.mktemp()
    with open(tmp, "w") as f:
        for i in range(100):
            f.write(f"line {i}\n")

    tests = [
        ("1. Read entire file (small for demo)", lambda: count_lines_in_large_file(tmp)),
        ("2. List vs generator", lambda: squares_up_to(1_000_000)),
        ("3. Unbounded accumulation", lambda: process_stream()),
        ("4. Circular reference", lambda: create_circular_ref()),
    ]
    for label, fn in tests:
        print(f"{label}:")
        try:
            result = fn()
            print(f"   OK: {result}")
        except Exception as e:
            print(f"   FAIL: {type(e).__name__}: {e}")

    os.unlink(tmp)

# Memory Examples — Recursion, Leaks & Large Allocations

Demonstrates memory-related issues: RecursionError, resource leaks, unbounded growth.

## Files

- `recursion_and_alloc.py` — Infinite recursion, exponential fibonacci, O(n²) string concat
- `resource_leaks.py` — File reading, large list allocation, circular references

## Usage

```bash
# Run all memory tests
python main.py

# Or run individual files
python recursion_and_alloc.py
python resource_leaks.py
```

## Bugs Demonstrated

| Test | Error | Description |
|------|-------|-------------|
| Infinite recursion | `RecursionError` | No base case in factorial |
| Exponential fib | Performance | O(2^n) without memoization |
| O(n²) string concat | Memory/Perf | Repeated concatenation in loop |
| Read entire file | Memory | Loading large file at once |
| List vs generator | Memory | Allocating full list unnecessarily |
| Unbounded accumulation | Memory | Growing list without clearing |
| Circular reference | GC issue | Blocks garbage collection |

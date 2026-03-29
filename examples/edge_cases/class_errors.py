#!/usr/bin/env python3
"""Class & inheritance errors — MRO, slots, super(), dataclass issues."""

from pfix import pfix


@pfix(hint="super().__init__() not called — parent state missing")
def test_missing_super():
    class Animal:
        def __init__(self, name: str):
            self.name = name

    class Dog(Animal):
        def __init__(self, name: str, breed: str):
            # Forgot super().__init__(name)
            self.breed = breed

    dog = Dog("Rex", "Labrador")
    return dog.name  # AttributeError: 'Dog' has no attribute 'name'


@pfix(hint="__slots__ blocks dynamic attribute assignment")
def test_slots_error():
    class Point:
        __slots__ = ("x", "y")
        def __init__(self, x, y):
            self.x = x
            self.y = y

    p = Point(1, 2)
    p.z = 3  # AttributeError: 'Point' has no attribute 'z'
    return p


@pfix(hint="Mutable default in dataclass — shared list across instances")
def test_dataclass_mutable():
    from dataclasses import dataclass

    @dataclass
    class Config:
        name: str
        tags: list = []  # ValueError: mutable default — should use field(default_factory=list)

    c1 = Config("a")
    c2 = Config("b")
    c1.tags.append("x")
    return c2.tags  # Would be ["x"] — shared!


@pfix(hint="Diamond inheritance MRO conflict")
def test_mro_conflict():
    class A:
        def method(self): return "A"
    class B(A):
        def method(self): return "B"
    class C(A):
        def method(self): return "C"

    # This works, but confusing MRO:
    class D(B, C): pass
    d = D()
    result = d.method()  # Returns "B" (MRO: D → B → C → A)

    # This fails with TypeError: inconsistent MRO
    try:
        class E(A, B): pass  # TypeError: Cannot create a consistent MRO
    except TypeError as e:
        raise TypeError(f"MRO conflict: {e}")
    return result


if __name__ == "__main__":
    tests = [
        ("1. Missing super().__init__()", lambda: test_missing_super()),
        ("2. __slots__ blocks new attr", lambda: test_slots_error()),
        ("3. Dataclass mutable default", lambda: test_dataclass_mutable()),
        ("4. Diamond MRO conflict", lambda: test_mro_conflict()),
    ]
    for label, fn in tests:
        print(f"{label}:")
        try:
            print(f"   OK: {fn()}")
        except Exception as e:
            print(f"   FAIL: {type(e).__name__}: {e}")

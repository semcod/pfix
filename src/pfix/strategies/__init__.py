"""
pfix.strategies — Framework-specific fix strategies.

Auto-detects framework from imports and applies specialized context.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from ..analyzer import ErrorContext


class FixStrategy(ABC):
    """Base class for framework-specific fix strategies."""

    name: str = ""

    @abstractmethod
    def detect(self, ctx: ErrorContext) -> bool:
        """Detect if this strategy applies to the error context."""
        pass

    @abstractmethod
    def enhance_prompt(self, ctx: ErrorContext) -> str:
        """Generate additional context for LLM prompt."""
        pass

    def get_priority(self) -> int:
        """Return priority (higher = applied first)."""
        return 0


class StrategyRegistry:
    """Registry of fix strategies."""

    _strategies: list[type[FixStrategy]] = []

    @classmethod
    def register(cls, strategy_class: type[FixStrategy]) -> type[FixStrategy]:
        """Decorator to register a strategy."""
        cls._strategies.append(strategy_class)
        return strategy_class

    @classmethod
    def get_matching(cls, ctx: ErrorContext) -> list[FixStrategy]:
        """Get strategies that match the context, sorted by priority."""
        matching = []
        for strategy_class in cls._strategies:
            strategy = strategy_class()
            if strategy.detect(ctx):
                matching.append(strategy)
        return sorted(matching, key=lambda s: s.get_priority(), reverse=True)

    @classmethod
    def enhance_prompt(cls, ctx: ErrorContext) -> str:
        """Get enhanced prompt from all matching strategies."""
        strategies = cls.get_matching(ctx)
        if not strategies:
            return ""

        parts = ["\n### Framework-Specific Context"]
        for strategy in strategies:
            enhancement = strategy.enhance_prompt(ctx)
            if enhancement:
                parts.append(f"\n**{strategy.name}:**")
                parts.append(enhancement)

        return "\n".join(parts)


def get_strategy_context(ctx: ErrorContext) -> str:
    """Convenience function to get enhanced context."""
    return StrategyRegistry.enhance_prompt(ctx)

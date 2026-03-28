"""
pfix.strategies.pandas — Pandas-specific fix strategy.
"""

from ..analyzer import ErrorContext
from . import FixStrategy, StrategyRegistry


@StrategyRegistry.register
class PandasFixStrategy(FixStrategy):
    """Strategy for pandas data manipulation errors."""

    name = "Pandas"

    PANDAS_KEYWORDS = ["pandas", "pd.DataFrame", "pd.Series", "numpy", "np."]

    def detect(self, ctx: ErrorContext) -> bool:
        """Detect pandas by imports or code patterns."""
        for imp in ctx.imports:
            if "pandas" in imp.lower() or "pd" in imp:
                return True

        # Check function source for pandas patterns
        if ctx.function_source:
            for kw in ["DataFrame", "Series", "groupby", "merge", "concat"]:
                if kw in ctx.function_source:
                    return True

        return False

    def enhance_prompt(self, ctx: ErrorContext) -> str:
        """Add pandas-specific context."""
        parts = [
            "- This code uses pandas for data manipulation",
            "- Check column names exist in DataFrame",
            "- Ensure proper handling of NaN/None values",
            "- Consider using .loc[] or .iloc[] for indexing",
        ]

        # Add specific guidance
        if "KeyError" in ctx.exception_type:
            parts.append("- Column/key not found - verify column names with df.columns")
        elif "IndexError" in ctx.exception_type:
            parts.append("- Index out of bounds - check DataFrame shape with df.shape")
        elif "ValueError" and "Length" in ctx.exception_message:
            parts.append("- Length mismatch - ensure aligned Series/DataFrames")

        return "\n".join(parts)

    def get_priority(self) -> int:
        return 50

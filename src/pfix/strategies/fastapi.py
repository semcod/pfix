"""
pfix.strategies.fastapi — FastAPI-specific fix strategy.
"""

from ..analyzer import ErrorContext
from . import FixStrategy, StrategyRegistry


@StrategyRegistry.register
class FastAPIFixStrategy(FixStrategy):
    """Strategy for FastAPI framework errors."""

    name = "FastAPI"

    FASTAPI_KEYWORDS = [
        "fastapi", "starlette", "pydantic", "uvicorn", "app.get",
        "app.post", "app.put", "app.delete", "APIRouter",
    ]

    def detect(self, ctx: ErrorContext) -> bool:
        """Detect FastAPI by imports."""
        for imp in ctx.imports:
            if any(kw in imp.lower() for kw in self.FASTAPI_KEYWORDS):
                return True

        if "fastapi" in ctx.source_file.lower():
            return True

        return False

    def enhance_prompt(self, ctx: ErrorContext) -> str:
        """Add FastAPI-specific context."""
        parts = [
            "- This is a FastAPI project",
            "- Check for proper type hints on route parameters",
            "- Ensure Pydantic models match expected schema",
            "- Check dependency injection with Depends()",
        ]

        # Add specific guidance
        if "ValidationError" in ctx.exception_type:
            parts.append("- Pydantic validation failed - check request/response models")
        elif "HTTPException" in ctx.exception_type:
            parts.append("- HTTP exception - ensure proper error handling")

        return "\n".join(parts)

    def get_priority(self) -> int:
        return 100

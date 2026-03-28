"""
pfix.strategies.django — Django-specific fix strategy.
"""

from ..analyzer import ErrorContext
from . import FixStrategy, StrategyRegistry


@StrategyRegistry.register
class DjangoFixStrategy(FixStrategy):
    """Strategy for Django framework errors."""

    name = "Django"

    DJANGO_KEYWORDS = [
        "django", "models", "views", "urls", "forms", "admin",
        "migrate", "migration", "queryset", "manager", "settings",
    ]

    def detect(self, ctx: ErrorContext) -> bool:
        """Detect Django by imports or file paths."""
        # Check imports
        for imp in ctx.imports:
            if any(kw in imp.lower() for kw in self.DJANGO_KEYWORDS):
                return True

        # Check file paths
        if "django" in ctx.source_file.lower():
            return True
        if "/models.py" in ctx.source_file or "/views.py" in ctx.source_file:
            return True

        return False

    def enhance_prompt(self, ctx: ErrorContext) -> str:
        """Add Django-specific context."""
        parts = [
            "- This is a Django project",
            "- Check models.py for Model definitions",
            "- Check urls.py for URL routing",
            "- Check settings.py for configuration",
        ]

        # Add specific guidance based on error
        if "DoesNotExist" in ctx.exception_type:
            parts.append("- Model query failed - ensure proper .get() or .filter() usage")
        elif "IntegrityError" in ctx.exception_type:
            parts.append("- Database integrity error - check unique constraints")
        elif "Migration" in ctx.exception_type or "migration" in ctx.exception_message.lower():
            parts.append("- Migration issue - may need to run makemigrations/migrate")

        return "\n".join(parts)

    def get_priority(self) -> int:
        return 100

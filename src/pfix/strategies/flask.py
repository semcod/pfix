"""
pfix.strategies.flask — Flask-specific fix strategy.
"""

from ..analyzer import ErrorContext
from . import FixStrategy, StrategyRegistry


@StrategyRegistry.register
class FlaskFixStrategy(FixStrategy):
    """Strategy for Flask framework errors."""

    name = "Flask"

    FLASK_KEYWORDS = [
        "flask", "werkzeug", "jinja2", "render_template",
        "@app.route", "Blueprint", "request", "session",
    ]

    def detect(self, ctx: ErrorContext) -> bool:
        """Detect Flask by imports."""
        for imp in ctx.imports:
            if any(kw in imp.lower() for kw in self.FLASK_KEYWORDS):
                return True

        if "flask" in ctx.source_file.lower():
            return True

        return False

    def enhance_prompt(self, ctx: ErrorContext) -> str:
        """Add Flask-specific context."""
        parts = [
            "- This is a Flask project",
            "- Check route definitions with @app.route()",
            "- Ensure templates exist in templates/ folder",
            "- Check for proper request context (request, session)",
        ]

        # Add specific guidance
        if "TemplateNotFound" in ctx.exception_type:
            parts.append("- Jinja2 template missing - check templates/ folder")
        elif "BuildError" in ctx.exception_type:
            parts.append("- URL build error - check endpoint names in url_for()")

        return "\n".join(parts)

    def get_priority(self) -> int:
        return 100

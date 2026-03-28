"""
pfix.llm — LLM integration via LiteLLM/OpenRouter.
"""

from __future__ import annotations

import json
import re
import time
from typing import Optional

import litellm

from .analyzer import classify_error
from .config import get_config
from .types import ErrorContext, FixProposal

litellm.suppress_debug_info = True

SYSTEM_PROMPT = """\
You are pfix — an automated Python code repair agent.
Analyze the runtime error and produce a precise, minimal fix.

RULES:
1. Return ONLY valid JSON. No markdown fences, no commentary.
2. Produce the smallest change that fixes the error.
3. If fix requires a pip package, include it in "dependencies".
4. If fix requires imports, include them in the fixed code.
5. Use "fixed_file_content" for full file replacement or "fixed_function" for single function.
6. Never remove existing functionality.
7. Preserve type hints, docstrings, comments.
8. For missing deps, always suggest the correct PyPI package name.

RESPONSE JSON:
{
  "diagnosis": "what caused the error",
  "error_category": "missing_import|missing_dependency|type_error|attribute_error|logic_error|other",
  "fix_description": "what the fix does",
  "fixed_function": "corrected function source (or empty)",
  "fixed_file_content": "corrected full file (or empty)",
  "dependencies": ["package==version"],
  "new_imports": ["import statement"],
  "confidence": 0.0-1.0,
  "breaking_changes": false
}
"""

# Default fallback chain: cheapest first
DEFAULT_LLM_CHAIN = [
    "ollama/codellama:7b",  # local, free
    "openrouter/anthropic/claude-haiku-4",  # cloud, cheap
    "openrouter/anthropic/claude-sonnet-4",  # cloud, quality
]


def request_fix(error_ctx: ErrorContext) -> FixProposal:
    """Send error to LLM, get fix proposal with fallback chain support."""
    config = get_config()

    # Get chain of models to try
    chain = getattr(config, "llm_chain", None) or DEFAULT_LLM_CHAIN
    strategy = getattr(config, "llm_chain_strategy", "cheapest_first")

    # If single model configured, use legacy behavior
    if len(chain) == 1 or not chain:
        return _request_single_model(error_ctx, config.llm_model)

    # Try models in chain order
    return _request_with_chain(error_ctx, chain)


def _request_with_chain(error_ctx: ErrorContext, chain: list[str]) -> FixProposal:
    """Try models in chain, escalating if confidence is low."""
    last_error = None

    for i, model in enumerate(chain):
        try:
            start_time = time.time()
            proposal = _request_single_model(error_ctx, model)
            duration_ms = int((time.time() - start_time) * 1000)

            # Success with good confidence - use this
            if proposal.confidence >= 0.5 and not proposal.diagnosis.startswith("LLM request failed"):
                proposal.raw_response = f"[Model {i+1}/{len(chain)}: {model}, {duration_ms}ms]\n{proposal.raw_response}"
                return proposal

            # Low confidence - try next model
            if i < len(chain) - 1:
                last_error = f"Model {model} returned low confidence ({proposal.confidence:.2f}), escalating..."
                continue

            # Last model - return whatever we got
            return proposal

        except Exception as e:
            last_error = str(e)
            if i < len(chain) - 1:
                continue

    # All models failed
    return FixProposal(
        diagnosis=f"All models in chain failed. Last error: {last_error}",
        confidence=0.0,
        raw_response=str(last_error),
    )


def _request_single_model(error_ctx: ErrorContext, model: str) -> FixProposal:
    """Send request to single LLM model."""
    config = get_config()

    error_class = classify_error(error_ctx)
    prompt = error_ctx.to_prompt()
    prompt += f"\n\n### Error Classification: `{error_class}`"

    if config.extra_context:
        prompt += "\n\n### Project Context"
        for k, v in config.extra_context.items():
            prompt += f"\n- **{k}**: {v}"

    try:
        response = litellm.completion(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=config.llm_temperature,
            max_tokens=config.llm_max_tokens,
            api_key=config.llm_api_key,
            api_base=config.llm_api_base if "openrouter" in model else None,
        )
        raw = response.choices[0].message.content or ""
        return _parse_response(raw)
    except Exception as e:
        import traceback
        error_msg = f"{e}\n{traceback.format_exc()}"
        return FixProposal(
            diagnosis=f"LLM request failed: {error_msg}",
            confidence=0.0,
            raw_response=str(e),
        )


def _parse_response(raw: str) -> FixProposal:
    """Parse LLM JSON response."""
    proposal = FixProposal(raw_response=raw)
    text = raw.strip()

    # Strip markdown code fences
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if m:
        text = m.group(1)
    elif not text.startswith("{"):
        s, e = text.find("{"), text.rfind("}")
        if s != -1 and e != -1:
            text = text[s : e + 1]

    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        proposal.diagnosis = f"Failed to parse LLM JSON response: {e}"
        proposal.raw_response = text[:500]  # Include partial response for debugging
        return proposal

    proposal.diagnosis = data.get("diagnosis", "")
    proposal.error_category = data.get("error_category", "other")
    proposal.fix_description = data.get("fix_description", "")
    proposal.fixed_function = data.get("fixed_function", "")
    proposal.fixed_file_content = data.get("fixed_file_content", "")
    proposal.dependencies = data.get("dependencies", [])
    proposal.new_imports = data.get("new_imports", [])
    proposal.confidence = float(data.get("confidence", 0.0))
    proposal.breaking_changes = data.get("breaking_changes", False)
    return proposal

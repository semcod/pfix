.PHONY: help install install-dev install-all test lint format clean build upload check server example check-env

help:
	@echo "Available commands:"
	@echo "  make install      - Install the package (production)"
	@echo "  make install-dev  - Install with dev dependencies"
	@echo "  make install-all  - Install with all optional dependencies"
	@echo "  make test         - Run pytest with coverage"
	@echo "  make lint         - Run ruff linter"
	@echo "  make format       - Run ruff formatter"
	@echo "  make clean        - Remove build artifacts"
	@echo "  make build        - Build wheel and sdist"
	@echo "  make upload       - Upload to PyPI (requires credentials)"
	@echo "  make check        - Run pfix check"
	@echo "  make server       - Start MCP server"
	@echo "  make example      - Run example script"
	@echo "  make check-env    - Check if .env exists"

install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

install-all:
	pip install -e ".[all]"

test:
	pytest -v --cov=src/pfix --cov-report=term-missing

lint:
	ruff check src tests

format:
	ruff check --fix src tests
	ruff format src tests

clean:
	rm -rf build/ dist/ *.egg-info .pytest_cache .coverage .pfix_backups/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

build:
	python -m build

upload:
	python -m twine upload dist/*

check:
	pfix check

server:
	pfix server

example:
	@python examples/example.py || echo "Run 'make check-env' first if it fails"

check-env:
	@test -f .env || (echo "⚠️  .env file not found! Copy .env.example to .env and set OPENROUTER_API_KEY" && exit 1)
	@echo "✅ .env file exists"

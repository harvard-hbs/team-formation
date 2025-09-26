.PHONY: install test build check-dist upload sync

# Install the package with development dependencies
install:
	uv sync --extra dev

# Sync dependencies from lock file (faster for CI/existing environments)
sync:
	uv sync --extra dev

test:
	uv run pytest

test-info:
	uv run pytest --log-cli-level=INFO

build:
	uv build

check-dist:
	uv run twine check dist/*

upload:
	uv run twine upload dist/*

dist-clean:
	/bin/rm -rf dist

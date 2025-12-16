.PHONY: all format lint test tests test_watch integration_tests docker_tests help extended_tests docs docs-install build publish clean

# Default target executed when no arguments are given to make.
all: help

# Define a variable for the test file path.
TEST_FILE ?= tests/unit_tests/

######################
# TESTING
######################

test:
	uv run pytest $(TEST_FILE)

test_watch:
	uv run ptw --snapshot-update --now . -- -vv tests/unit_tests

test_profile:
	uv run pytest -vv tests/unit_tests/ --profile-svg

extended_tests:
	uv run pytest --only-extended $(TEST_FILE)

######################
# LINTING AND FORMATTING
######################

# Define a variable for Python and notebook files.
PYTHON_FILES=src/
MYPY_CACHE=.mypy_cache
lint format: PYTHON_FILES=.
lint_diff format_diff: PYTHON_FILES=$(shell git diff --name-only --diff-filter=d main | grep -E '\.py$$|\.ipynb$$')
lint_package: PYTHON_FILES=src
lint_tests: PYTHON_FILES=tests
lint_tests: MYPY_CACHE=.mypy_cache_test

lint lint_diff lint_package lint_tests:
	uv run ruff check .
	[ "$(PYTHON_FILES)" = "" ] || uv run ruff format $(PYTHON_FILES) --diff
	[ "$(PYTHON_FILES)" = "" ] || uv run ruff check --select I $(PYTHON_FILES)

format format_diff:
	uv run ruff format $(PYTHON_FILES)
	uv run ruff check --select I --fix $(PYTHON_FILES)

spell_check:
	codespell --toml pyproject.toml

spell_fix:
	codespell --toml pyproject.toml -w

######################
# DOCUMENTATION
######################

docs:
	@echo "Starting Mintlify docs server at http://localhost:3000..."
	@echo "Press Ctrl+C to stop"
	@cd docs && mintlify dev

docs-install:
	@echo "Installing Mintlify CLI..."
	npm install -g mintlify

######################
# BUILD AND PUBLISH
######################

build:
	@echo "Building package..."
	uv run python -m build

publish-test:
	@echo "Publishing to TestPyPI..."
	uv run twine upload --repository testpypi dist/*

publish:
	@echo "Publishing to PyPI..."
	uv run twine upload dist/*

clean:
	rm -rf dist/ build/ *.egg-info src/*.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

######################
# HELP
######################

help:
	@echo '==================== Development ===================='
	@echo 'test                         - run unit tests'
	@echo 'test TEST_FILE=<test_file>   - run specific test file'
	@echo 'test_watch                   - run tests in watch mode'
	@echo 'format                       - run code formatters'
	@echo 'lint                         - run linters'
	@echo ''
	@echo '==================== Documentation ===================='
	@echo 'docs                         - start local docs server (http://localhost:3000)'
	@echo 'docs-install                 - install Mintlify CLI globally'
	@echo ''
	@echo '==================== Build & Publish ===================='
	@echo 'build                        - build package for distribution'
	@echo 'publish-test                 - publish to TestPyPI'
	@echo 'publish                      - publish to PyPI'
	@echo 'clean                        - remove build artifacts'


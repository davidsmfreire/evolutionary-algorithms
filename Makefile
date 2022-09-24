.DEFAULT_GOAL := help

RUN_COMMAND ?= poetry run

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

# CLEAN -------------------------------------------------------------------------------------------
pyc-clean: ## Remove python byte code files
	find . -iname "*.pyc" -delete

rm-venv-clean: ## Remove the virtual environment
	-poetry env remove python

py-cache-clean: ## Remove all .pyc and .pyo files as well as __pycache__ directories
	find . | grep -E "(/__pycache__$|\.pyc$|\.pyo$)" | xargs rm -rf

clean: pyc-clean rm-venv-clean py-cache-clean ## Cleans the environment

# DEV-SETUP ---------------------------------------------------------------------------------------
hooks:  ## Installs git hooks
	$(RUN_COMMAND) pre-commit install

deps: ## Installs all project package dependencies
	poetry install --no-root

dev-setup: deps hooks ## Sets up the development environment


# FORMAT ------------------------------------------------------------------------------------------
format:  ## Formats the code
	$(RUN_COMMAND) black -l 120 ./src
	$(RUN_COMMAND) black -l 120 ./tests

# STATIC ANALYSES ---------------------------------------------------------------------------------
type-analysis: ## Checks the code regarding types
	$(RUN_COMMAND) mypy --config-file pyproject.toml ./src ./tests

lint-analysis:  ## Lints the code
	$(RUN_COMMAND) flake8 --max-line-length 120 --max-complexity 10 ./src ./tests

static-analysis: type-analysis lint-analysis ## Checks the code for errors and inconsistency

# SECURITY ----------------------------------------------------------------------------------------
code-security: ## Checks the code for potential security issues
	# Bandit has an issue where it doesn't ignore the test files. See .pre-commit-config.yaml
	# $(RUN_COMMAND) bandit -c pyproject.toml -r ./src

package-security: ## Checks 3rd party packages for potential security issues
	$(RUN_COMMAND) safety check --full-report

security: code-security package-security ## Looks for security issues in the project

# TESTS -------------------------------------------------------------------------------------------
acceptance-tests: ## Runs the acceptance tests
	$(RUN_COMMAND) pytest ./tests -svv

integration-tests: ## Runs the integration tests
	$(RUN_COMMAND) coverage run -a -m pytest ./src -svv -m "integration"

unit-tests:  ## Runs the unit tests
	$(RUN_COMMAND) coverage run -a -m pytest ./src -svv -m "not integration"

test: unit-tests integration-tests acceptance-tests ## Runs the tests

pre-coverage:
	$(RUN_COMMAND) coverage erase

post-coverage:
	$(RUN_COMMAND) coverage report --skip-empty --fail-under=100

coverage: pre-coverage unit-tests integration-tests post-coverage

show-coverage: ## Opens a browser with the coverage report
	$(RUN_COMMAND) coverage html
	open htmlcov/index.html

# FUTURE COMPATIBILITY ----------------------------------------------------------------------------
future: ## Checks the code against compatibility with future python versions
	$(RUN_COMMAND) nox

# PACKAGE BUILDING --------------------------------------------------------------------------------
build:  ## Builds the python packages(s)
	poetry build

# ALL ---------------------------------------------------------------------------------------------
all: clean dev-setup format static-analysis security test build future  ## Runs all development flow steps

distribute:
	$(RUN_COMMAND) twine upload dist/*

wingo:
	cd src && $(RUN_COMMAND) python -m example.wingo

moore:
	cd src && $(RUN_COMMAND) python -m example.moore
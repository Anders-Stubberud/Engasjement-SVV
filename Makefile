#################################################################################
# GLOBALS                                                                       #
#################################################################################

PROJECT_NAME = engasjement_svv
PYTHON_VERSION = 3.12
PYTHON_INTERPRETER = python

mode = 0

#################################################################################
# COMMANDS                                                                      #
#################################################################################


## Install Python Dependencies
.PHONY: requirements
requirements:
	$(PYTHON_INTERPRETER) -m pip install -U pip
	$(PYTHON_INTERPRETER) -m pip install -r requirements.txt
	



## Delete all compiled Python files
.PHONY: clean
clean:
	find . -type f -name "*.py[co]" -delete
	find . -type d -name "__pycache__" -delete

## Lint using flake8 and black (use `make format` to do formatting)
.PHONY: lint
lint:
	flake8 source
	isort --check --diff --profile black source
	black --check --config pyproject.toml source

## Format source code with black, autoflake and isort
.PHONY: format
format:
	autoflake --remove-all-unused-imports --in-place --recursive source
	isort --profile black --force-single-line-imports source
	black --config pyproject.toml source
	isort --profile black --force-single-line-imports source

## Set up python interpreter environment
.PHONY: create_environment
create_environment:
	@bash -c "if [ ! -z `which virtualenvwrapper.sh` ]; then source `which virtualenvwrapper.sh`; mkvirtualenv $(PROJECT_NAME) --python=$(PYTHON_INTERPRETER); else mkvirtualenv.bat $(PROJECT_NAME) --python=$(PYTHON_INTERPRETER); fi"
	@echo ">>> New virtualenv created. Activate with:\nworkon $(PROJECT_NAME)"
	



#################################################################################
# PROJECT RULES                                                                 #
#################################################################################

## Make Dataset
.PHONY: data
data: requirements
	$(PYTHON_INTERPRETER) source/dataset.py --mode $(mode)

## Make Features
.PHONY: features
features: data
	$(PYTHON_INTERPRETER) source/features.py --mode $(mode)

## Make plots
.PHONY: plots
plots: features
	$(PYTHON_INTERPRETER) source/plots.py --mode $(mode)

## Make report
.PHONY: report
report: plots
	$(PYTHON_INTERPRETER) source/report.py --mode $(mode)

#################################################################################
# Self Documenting Commands                                                     #
#################################################################################

.DEFAULT_GOAL := help

define PRINT_HELP_PYSCRIPT
import re, sys; \
lines = '\n'.join([line for line in sys.stdin]); \
matches = re.findall(r'\n## (.*)\n[\s\S]+?\n([a-zA-Z_-]+):', lines); \
print('Available rules:\n'); \
print('\n'.join(['{:25}{}'.format(*reversed(match)) for match in matches]))
endef
export PRINT_HELP_PYSCRIPT

help:
	@$(PYTHON_INTERPRETER) -c "${PRINT_HELP_PYSCRIPT}" < $(MAKEFILE_LIST)

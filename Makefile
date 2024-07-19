PROACTIVE_PYTHON_SDK_HOME := ../proactive-python-client
PROACTIVE_JUPYTER_NOTEBOOKS := ../proactive-jupyter-notebooks
PYTHON := python3
VENV_VERSIONS := 2 3 4
DEFAULT_VERSION := 4

.DEFAULT_GOAL := help

help:
	@echo "Available commands:"
	@echo "  help                           : Show this help message"
	@echo "  virtualenv[2|3|4]              : Create or update virtual environment (default: 4)"
	@echo "  clean[2|3|4]                   : Clean build artifacts (default: 4)"
	@echo "  build[2|3|4]                   : Build the package (default: 4)"
	@echo "  uninstall[2|3|4]               : Uninstall proactive-jupyter-kernel (default: 4)"
	@echo "  install[2|3|4]                 : Install proactive-jupyter-kernel (default: 4)"
	@echo "  run[2|3|4]                     : Run JupyterLab (default: 4)"
	@echo "  setup[2|3|4]                   : Run virtualenv, build, and install (default: 4)"
	@echo "  publish_test[2|3|4]            : Publish to TestPyPI (default: 4)"
	@echo "  publish_test_using_secrets[2|3|4] : Publish to TestPyPI using secrets (default: 4)"
	@echo "  publish_prod[2|3|4]            : Publish to PyPI (default: 4)"
	@echo "  publish_prod_using_secrets[2|3|4] : Publish to PyPI using secrets (default: 4)"
	@echo "  print_version[2|3|4]           : Print proactive version (default: 4)"
	@echo ""
	@echo "Usage:"
	@echo "  make virtualenv PROACTIVE_PYTHON_SDK_RELEASE=[test|local]"
	@echo "  make run PROACTIVE_JUPYTER_NOTEBOOKS=/path/to/notebooks"

# Default targets (no version specified, defaults to 4)
virtualenv:
	@$(MAKE) virtualenv$(DEFAULT_VERSION)

define make_default_target
$(1): $(1)$(DEFAULT_VERSION)
endef

$(foreach target,clean build uninstall install run setup publish_test publish_test_using_secrets publish_prod publish_prod_using_secrets print_version,\
    $(eval $(call make_default_target,$(target))))

# Versioned targets
define make_venv_target
virtualenv$(1):
	@bash create_venv.sh "$(1)" "$(PROACTIVE_PYTHON_SDK_RELEASE)"
endef

$(foreach version,$(VENV_VERSIONS),$(eval $(call make_venv_target,$(version))))

define make_target
$(1)$(2):
	@. env$(2)/bin/activate && $$(MAKE) $(1)_impl VERSION=$(2)
endef

$(foreach version,$(VENV_VERSIONS),\
    $(foreach target,clean build uninstall install run publish_test publish_test_using_secrets publish_prod publish_prod_using_secrets print_version,\
        $(eval $(call make_target,$(target),$(version)))))

# Setup targets
define make_setup_target
setup$(1): virtualenv$(1) build$(1) install$(1)
	@echo "Setup completed for version $(1)"
endef

$(foreach version,$(VENV_VERSIONS),$(eval $(call make_setup_target,$(version))))

# Implementation targets
clean_impl:
	@echo "Cleaning..."
	@rm -rf dist/ build/ proactive_jupyter_kernel.egg-info/
	@echo "Clean done."

build_impl: clean_impl
	@echo "Building package..."
	which $(PYTHON) && $(PYTHON) -V && $(PYTHON) -m pip -V
	$(PYTHON) setup.py sdist --formats=zip
	$(PYTHON) setup.py bdist_wheel
	twine check dist/*
	@echo "Package built."

uninstall_impl:
	@echo "Uninstalling proactive-jupyter-kernel package..."
	which $(PYTHON) && $(PYTHON) -V && $(PYTHON) -m pip -V
	$(PYTHON) -m pip uninstall -y proactive-jupyter-kernel
	@echo "proactive-jupyter-kernel package uninstalled."

install_impl: uninstall_impl
	@echo "Installing proactive-jupyter-kernel from dist..."
	which $(PYTHON) && $(PYTHON) -V && $(PYTHON) -m pip -V
	$(PYTHON) -m pip install . --no-dependencies
	$(PYTHON) -m proactive-jupyter-kernel.install
	$(PYTHON) -m pip show proactive proactive-jupyter-kernel
	@echo "proactive-jupyter-kernel installed."

run_impl:
	@echo "Running jupyterlab..."
	jupyter lab --ip=0.0.0.0 --no-browser --allow-root --notebook-dir=$(PROACTIVE_JUPYTER_NOTEBOOKS)

publish_test_impl:
	@echo "Publishing to TestPyPI..."
	which $(PYTHON) && $(PYTHON) -V && $(PYTHON) -m pip -V
	twine upload --repository-url https://test.pypi.org/legacy/ dist/* --config-file .pypirc
	@echo "Publishing completed."

publish_test_using_secrets_impl:
	@echo "Publishing to TestPyPI using secrets..."
	which $(PYTHON) && $(PYTHON) -V && $(PYTHON) -m pip -V
	twine upload --repository-url https://test.pypi.org/legacy/ dist/*
	@echo "Publishing completed."

publish_prod_impl:
	@echo "Publishing to PyPI..."
	which $(PYTHON) && $(PYTHON) -V && $(PYTHON) -m pip -V
	twine upload dist/* --config-file .pypirc
	@echo "Publishing completed."

publish_prod_using_secrets_impl:
	@echo "Publishing to PyPI using secrets..."
	which $(PYTHON) && $(PYTHON) -V && $(PYTHON) -m pip -V
	twine upload dist/*
	@echo "Publishing completed."

print_version_impl:
	@echo "Printing proactive version..."
	which $(PYTHON) && $(PYTHON) -V && $(PYTHON) -m pip -V
	$(PYTHON) -m pip show proactive proactive-jupyter-kernel
	$(PYTHON) -c "import proactive; print(proactive.__version__)"

.PHONY: help virtualenv setup clean build uninstall install run publish_test publish_test_using_secrets publish_prod publish_prod_using_secrets print_version \
    $(foreach version,$(VENV_VERSIONS),\
    virtualenv$(version) clean$(version) build$(version) uninstall$(version) install$(version) run$(version) setup$(version) \
    publish_test$(version) publish_test_using_secrets$(version) publish_prod$(version) publish_prod_using_secrets$(version) print_version$(version))
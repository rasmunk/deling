PACKAGE_NAME=deling
PACKAGE_NAME_FORMATTED=$(subst -,_,$(PACKAGE_NAME))
ARGS=

.PHONY: all init clean dist distclean maintainer-clean
.PHONY: install uninstall installcheck check

all: venv install-dep init

init:
	mkdir -p tests/tmp
ifeq ($(shell test -e defaults.env && echo yes), yes)
ifneq ($(shell test -e .env && echo yes), yes)
		ln -s defaults.env .env
endif
endif

clean:
	rm -fr .env
	rm -fr .pytest_cache
	rm -fr tests/__pycache__
	rm -fr tests/tmp

dist:
	$(VENV)/python setup.py sdist bdist_wheel

distclean:
	rm -fr dist build $(PACKAGE_NAME).egg-info $(PACKAGE_NAME_FORMATTED).egg-info

maintainer-clean: distclean clean venv-clean

install-dev:
	$(VENV)/pip install -r requirements-dev.txt

install-dep:
	$(VENV)/pip install -r requirements.txt

uninstall-dep:
	$(VENV)/pip uninstall -r requirements.txt

install:
	$(MAKE) install-dep
	$(VENV)/pip install .

uninstall:
	$(VENV)/pip uninstall -y -r requirements.txt
	$(VENV)/pip uninstall -y -r requirements-dev.txt
	$(VENV)/pip uninstall -y -r $(PACKAGE_NAME)

installcheck:
	$(VENV)/pip install -r tests/requirements.txt
# deling must be installed into the relative venv before it can be tested
	. $(VENV)/activate; pip install .

uninstallcheck:
	$(VENV)/pip uninstall -y -r requirements.txt

check_pre:
	. $(VENV)/activate; python3 setup.py check -rms

# The tests requires access to the docker socket
check: check_pre
	. $(VENV)/activate; pytest -s -v tests/

include Makefile.venv
# Copyright (C) 2024  rasmunk
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

PACKAGE_NAME=deling
PACKAGE_NAME_FORMATTED=$(subst -,_,$(PACKAGE_NAME))
ARGS=

.PHONY: all
all: venv install-dep init

.PHONY: init
init:
	mkdir -p tests/tmp
ifeq ($(shell test -e defaults.env && echo yes), yes)
ifneq ($(shell test -e .env && echo yes), yes)
		ln -s defaults.env .env
endif
endif

.PHONY: clean
clean:
	rm -fr .env
	rm -fr .pytest_cache
	rm -fr tests/__pycache__
	rm -fr tests/tmp

.PHONY: dist
dist: venv install-dist-dep
	$(VENV)/python -m build .

.PHONY: install-dist-dep
install-dist-dep: venv
	$(VENV)/pip install build

.PHONY: distclean
distclean:
	rm -fr dist build $(PACKAGE_NAME).egg-info $(PACKAGE_NAME_FORMATTED).egg-info

.PHONY: maintainer-clean
maintainer-clean: distclean clean venv-clean

.PHONY: install-dev
install-dev:
	$(VENV)/pip install -r requirements-dev.txt

.PHONY: install-dep
install-dep:
	$(VENV)/pip install -r requirements.txt

.PHONY: uninstall-dep
uninstall-dep:
	$(VENV)/pip uninstall -r requirements.txt

.PHONY: install
install:
	$(MAKE) install-dep
	$(VENV)/pip install .

.PHONY: uninstall
uninstall:
	$(VENV)/pip uninstall -y -r requirements.txt
	$(VENV)/pip uninstall -y -r requirements-dev.txt
	$(VENV)/pip uninstall -y -r $(PACKAGE_NAME)

.PHONY: installtest
installtest:
	$(VENV)/pip install -r tests/requirements.txt
# deling must be installed into the relative venv before it can be tested
	. $(VENV)/activate; pip install .

.PHONY: uninstalltest
uninstalltest:
	$(VENV)/pip uninstall -y -r requirements.txt

.PHONY: test_pre
test_pre:
	. $(VENV)/activate; python3 setup.py test -rms

# The tests requires access to the docker socket
.PHONY: test
test: test_pre
	. $(VENV)/activate; pytest -s -v tests/

include Makefile.venv
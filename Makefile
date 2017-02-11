all: setup doc
	@echo "SETUP PROJECT AND DOCUMENTATION"
	
setup: .pip-freeze

clean:
	@echo "REMOVE PIP FREEZE, PYCACHE AND CLEAN DOCUMENTATION"
	rm -f .pip-freeze
	rm -rf 'find . -name __pycache__'
	rm -f `find . -type f -name '*.py[co]' `
	rm -f `find . -type f -name '*~' `
	rm -f `find . -type f -name '.*~' `
	rm -f `find . -type f -name '@*' `
	rm -f `find . -type f -name '#*#' ` `
	rm -f .coverage
	rm -rf cover
	make -C docs clean

.pip-freeze: requirements.txt setup.py
	@echo "SETUP REQUIREMENTS"
	pip install -Ur requirements.txt
	pip install -Ue .
	pip freeze > .pip-freeze

flake: .flake-alembic
	pyflakes maplocate tests
	pep8 maplocate tests

.flake-alembic:
	@echo "INSPECT CODE FOR PEP8"
	pyflakes alembic/versions
	pep8 alembic/versions

doc:
	@echo "BUILD HTML DOCUMENTATION"
	make -C docs html

test: flake
	@echo "RUN TESTS"
	pytest tests

vtest: flake
	@echo "RUN TESTS IN VERBOSE MODE"
	pytest -v tests

cov cover coverage: flake
	@echo "RUN TESTS WITH COVERAGE"
	pytest --cov=maplocate tests
	@echo "open file://`pwd`/coverage/index.html"

migrate:
	@echo "UPGRADE POSTGRESQL TO HEAD MIGRATION VERSION"
	alembic -c config/alembic.ini upgrade head

initdb:
	@echo "CREATE MAPLOCATE POSTGRESQL DB WITH USER AND PRIVILEGES"
	sudo -u postgres psql -c "CREATE DATABASE maplocate ENCODING 'UTF8' LC_COLLATE='en_US.UTF-8' LC_CTYPE='en_US.UTF-8';"
	sudo -u postgres psql -c "CREATE USER maplocate WITH PASSWORD 'maplocate';"
	sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE maplocate TO maplocate;"

help:
	@echo "  all        to make setup of project and documentation"
	@echo "  setup      to make project setup"
	@echo "  clean      to make pip and docs clean"
	@echo "  flake      to make PEP8 code inspection"
	@echo "  doc        to make documentation"
	@echo "  migrate    to make upgrade of postgresql DB to head migration version"
	@echo "  initdb     to make initialization of project postgresql DB"
	@echo "  test       to make tests run"
	@echo "  vtest      to make tests run with verbose mode turned on"
	@echo "  cov        to make application coverage with tests"

.PHONY: all setup flake doc migrate initdb help test vtest cov


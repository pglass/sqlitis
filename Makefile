.PHONY: clean test

VENV=.venv
VENV_ACTIVATE=. $(VENV)/bin/activate

$(VENV):
	virtualenv $(VENV)
	$(VENV_ACTIVATE); pip install tox

test: $(VENV)
	$(VENV_ACTIVATE); tox

release: test
	python setup.py sdist upload -r pypi

clean:
	rm -rf $(VENV)

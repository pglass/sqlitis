.PHONY: test format dist bump test-release release clean-dist clean

VENV=.venv
VENV_ACTIVATE=. $(VENV)/bin/activate
BUMPTYPE=patch

$(VENV):
	virtualenv $(VENV)
	$(VENV_ACTIVATE); pip install tox bumpversion black twine 'readme_renderer[md]'

test: $(VENV)
	$(VENV_ACTIVATE); tox

format: $(VENV)
	$(VENV_ACTIVATE); black setup.py sqlitis tests

dist: clean-dist $(VENV)
	$(VENV_ACTIVATE); python setup.py sdist
	ls -ls dist
	tar tzf dist/*
	$(VENV_ACTIVATE); twine check dist/*

bump: $(VENV)
	$(VENV_ACTIVATE); bumpversion $(BUMPTYPE)
	git show -q
	@echo
	@echo "SUCCESS: Version was bumped and committed"

test-release: clean test dist
	$(VENV_ACTIVATE); twine upload --repository-url https://test.pypi.org/legacy/ dist/*

release: clean test dist
	$(VENV_ACTIVATE); twine upload dist/*

clean-dist:
	rm -rf dist
	rm -rf sqlitis.egg-info

clean: clean-dist
	rm -rf $(VENV) .tox

SHELL := /bin/bash

test: fmt lint
	tox -e py27

fmt:
	yapf -i -r sqlitis tests || true

lint:
	tox -e flake8

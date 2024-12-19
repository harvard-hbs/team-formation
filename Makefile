.PHONY: install test build check-dist upload

install:
	pip install -r requirements-dev.txt

test:
	pytest

test-info:
	pytest --log-cli-level=INFO

build:
	python -m build

check-dist:
	twine check dist/*

upload:
	python -m twine upload dist/*

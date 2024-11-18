.PHONY: install test build check-dist upload

install:
	pip install -r requirements-dev.txt

test:
	pytest

build:
	python -m build

check-dist:
	twine check dist/*

upload:
	python -m twine upload dist/*

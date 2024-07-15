install-dev:
	pip install -r requirements-dev.txt

test:
	pytest

distribution:
	python -m build

distribution-check:
	twine check dist/*

upload:
	twine upload dist/*


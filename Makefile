install-dev:
	pip install -r requirements-dev.txt

test:
	pytest

distribution:
	python setup.py sdist bdist_wheel

distribution-check:
	twine check dist/*

upload:
	twine upload dist/*


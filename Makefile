PYTHON ?= python3

.PHONY: test

test:
	$(PYTHON) -m unittest discover -s tests -p 'test_*.py' -v

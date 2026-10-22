.PHONY: test compile check example

PYTHON ?= python3

test:
	PYTHONPATH=src $(PYTHON) -m unittest discover -s tests -v

compile:
	PYTHONPATH=src $(PYTHON) -m compileall -q src tests

check: test compile

example:
	PYTHONPATH=src $(PYTHON) -m dataset_preflight validate examples/orders.csv examples/orders.contract.json

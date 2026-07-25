.PHONY: all current historical future figures table check clean

PYTHON ?= python

all: current historical future figures table check

current:
	$(PYTHON) scripts/run_current.py

historical:
	$(PYTHON) scripts/run_historical.py

future:
	$(PYTHON) scripts/run_future.py

figures:
	$(PYTHON) scripts/make_figures.py

table:
	$(PYTHON) scripts/make_population_table.py

check:
	$(PYTHON) scripts/check_outputs.py

clean:
	rm -rf build dist *.egg-info .pytest_cache .ruff_cache
	find . -type d -name __pycache__ -prune -exec rm -rf {} +

.DEFAULT_GOAL := all
PYTHON ?= python3
WITH_GUI ?= 1

.PHONY: all setup dev run train evaluate test lint bonuses bonus-demo \
	clean fclean re

all: setup

setup:
	PYTHON="$(PYTHON)" WITH_GUI="$(WITH_GUI)" sh setup.sh

dev:
	PYTHON="$(PYTHON)" WITH_GUI="$(WITH_GUI)" INSTALL_DEV=1 sh setup.sh

run: all
	.venv/bin/python main.py --menu -load models/best.json -dontlearn

bonuses: all
	.venv/bin/python benchmark.py

bonus-demo: all
	.venv/bin/python main.py -load models/best.json -dontlearn --speed 60 --seed 12

train: all
	.venv/bin/python main.py -visual off --quiet -sessions 30000 --seed 42 \
		--checkpoint-dir models -save models/candidate.json

evaluate: all
	.venv/bin/python main.py -visual off --quiet -load models/best.json -dontlearn \
		-sessions 200 --seed 2026 --report results/evaluation.json

test: all
	.venv/bin/python -m unittest discover -s tests -v

lint:
	.venv/bin/python -m flake8 . snake

clean:
	$(PYTHON) clean.py

fclean:
	$(PYTHON) clean.py --full

re: fclean
	$(MAKE) all

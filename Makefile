PYTHON := python3

.PHONY = lint test dev prod build
.DEFAULT_GOAL = build

lint:
	@echo "Linting..."

	@# There is a problem with Pylint doing its own discovery. Issue here:
	@# https://github.com/PyCQA/pylint/issues/352
	@${PYTHON} -m pylint \
		*.py \
		*/*.py \
		*/*/*.py \
		*/*/*/*.py \
		*/*/*/*/*.py \

test:
	@echo "Testing..."
	@${PYTHON} -m pytest --disable-pytest-warnings tests

build: test lint

dev: build
	@echo "Launching..."

	@# Run without optimization. Python's -O will set __debug__ to False and
	@# apply production protections. On a development machine, it should be
	@# possible to, say, delete all tables on startup.
	@${PYTHON} bot.py

prod:
	@echo "Launching..."

	@# Use a single -O here because, with -OO, Python will remove docstrings
	@# which discord.py relies on for !help messages.
	@${PYTHON} -O bot.py

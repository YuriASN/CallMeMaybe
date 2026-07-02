EXCLUDES = --exclude .venv --exclude src/llm_sdk/*

install:
	uv sync

run:
	uv run main.py

clean:
	find . -type d \( -name '.mypy_cache' -o -name '__pycache__' \) -print -exec rm -rf {} +

lint:
	-flake8 src/*.py
	-mypy --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs src/*.py

lint-strict:
	-flake8 --strict src/*.py
	-mypy --strict src/*.py
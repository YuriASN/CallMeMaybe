EXCLUDES = --exclude .venv --exclude src/llm_sdk/*

install:
	uv sync

run:
	uv run main.py

clean:
	find . -type d \( -name '.mypy_cache' -o -name '__pycache__' \) -print -exec rm -rf {} +

lint:
	-flake8 --exclude "llm_sdk", ".venv"
	-mypy --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs --exclude llm_sdk --exclude .venv

lint-strict:
	-flake8 --strict --exclude "llm_sdk", ".venv"
	-mypy --strict --exclude llm_sdk --exclude .venv
.ONESHELL:

install:
	@poetry install

clean:
	@find . -name '*.pyc' -delete
	@find . -name '__pycache__' -delete
	@find . -name '.coverage' -delete
	@rm -rf "htmlcov" || true
	@rm -rf "dist" || true
	@rm -rf ".tox" || true

build: clean
	poetry build

lint:
	@poetry run flake8 llm_context_generator tests

format:
	@poetry run isort .
	@poetry run black .

typecheck:
	@poetry run mypy --install-types --non-interactive llm_context_generator

test:
	@poetry run pytest .

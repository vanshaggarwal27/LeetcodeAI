.PHONY: lint format test

lint:
	cd backend && ruff check .

format:
	cd backend && ruff format .

test:
	cd backend && pytest -v

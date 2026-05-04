.PHONY: install run build clean

install:
	poetry install

run:
	poetry run python -m currency_bot

build:
	docker build -t currency-bot .

clean:
	rm -rf .venv
	find . -type d -name "__pycache__" -exec rm -rf {} +

ENTRY = src
SRC = src/
ARGS = $(wordlist 2, $(words $(MAKECMDGOALS)), $(MAKECMDGOALS))

install:
	uv sync

run: install
	uv run python3 $(ENTRY) $(ARGS)

debug: install
	uv run python3 -m pdb $(ENTRY) $(ARGS)

fclean: clean
	rm -rf uv.lock

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .mypy_cache -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +

lint:
	uv run flake8 $(SRC) $(ENTRY)
	uv run mypy $(SRC) $(ENTRY)

lint-strict:
	uv run flake8 $(SRC) $(ENTRY)
	uv run mypy $(SRC) $(ENTRY) --strict

%:
	@:
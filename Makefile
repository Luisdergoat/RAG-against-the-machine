ENTRY = src
SRC = src/
ARGS = $(wordlist 2, $(words $(MAKECMDGOALS)), $(MAKECMDGOALS))

install:
	uv sync

run: install
	uv run python3 $(ENTRY) $(ARGS)

server-setup: install
	uv run python3 src index --max_chunk_size 2000
	uv run python3 src search_dataset --dataset_path data/datasets/UnansweredQuestions/dataset_docs_public.json --k 10 --save_directory data/output/search_results/UnansweredQuestions
	uv run python3 src search_dataset --dataset_path data/datasets/UnansweredQuestions/dataset_code_public.json --k 10 --save_directory data/output/search_results/UnansweredQuestions

run-server: server-setup
	uv run python3 -m uvicorn $(ENTRY).server.server:app --reload

debug: install
	uv run python3 -m pdb $(ENTRY) $(ARGS)

fclean: clean
	rm -rf uv.lock
	rm -rf data/output
	rm -rf data/processed

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .mypy_cache -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +

lint:
	uv run flake8
	uv run mypy $(SRC)

lint-strict:
	uv run flake8 $(SRC) $(ENTRY)
	uv run mypy $(SRC) $(ENTRY) --strict

%:
	@:
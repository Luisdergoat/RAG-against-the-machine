from fire import Fire
from pathlib import Path
from python_indexing import python_indexer
from markdown_indexing import markdown_indexer
from models import Chunk, MinimalSearchResults, StudentSearchResults
from tokenizer import tokenize
from tqdm import tqdm
from retriever import Retriever
import bm25s
import json


class CLI:
    def __init__(self):
        self.project_root = Path(__file__).resolve().parent.parent
        self.datasets = self.project_root / 'data'
        self.indexed_python_files = []
        self.indexed_markdown_files = []
        self.processed_dir = Path(__file__).resolve().parent.parent / "data" / "processed"

    def index(self, max_chunk_size: int = 2000) -> None:
        self.datasets = Path(self.datasets).resolve() / 'raw'
        print(f"Indexing data from {self.datasets}")
        for data in self.datasets.rglob("*.py"):
            self.indexed_python_files.append(data)
        for data in self.datasets.rglob("*.md"):
            self.indexed_markdown_files.append(data)
        for data in self.datasets.rglob("*.txt"):
            self.indexed_markdown_files.append(data)
        print(f"Python files {len(self.indexed_python_files)}")
        print(f"Markdown files {len(self.indexed_markdown_files)}")
        all_chunks: list[Chunk] = []
        for file in tqdm(self.indexed_python_files, desc="Python files"):
            all_chunks.extend(python_indexer(file, self.project_root, max_chunk_size))

        for file in tqdm(self.indexed_markdown_files, desc="Markdown files"):
            all_chunks.extend(markdown_indexer(file, self.project_root, max_chunk_size))
        corpus_tokens = []
        for chunks in tqdm(all_chunks, desc="Tokenizing"):
            corpus_tokens.append(tokenize(chunks.text))

        self.processed_dir.mkdir(exist_ok=True)
        retriever = bm25s.BM25()
        retriever.index(corpus_tokens)
        retriever.save(self.processed_dir / "bm25")

        with open(self.processed_dir / "chunks.json", "w", encoding="utf-8") as f:
            json.dump([chunk.model_dump() for chunk in all_chunks], f, indent=2)

        print("Ingestion complete! Indices saved under data/processed/")

    def search(self, query: str, k: int) -> None:
        retriever = Retriever(self.processed_dir)
        try:
            results = retriever.search(query, k)
            for result in results:
                print(json.dumps(result.model_dump(), indent=2))
        except Exception as e:
            print(f"Error during search: {e}")

    def search_dataset(self, dataset_path: Path, save_directory: Path, k: int = 3) -> None:
        with open(dataset_path, "r", encoding="utf-8") as f:
            dataset = json.load(f)
            minimal_search_result = []
            retriever = Retriever(self.processed_dir)
            for entry in dataset["rag_questions"]:
                query = entry["question"]
                minimal_search_result.append(MinimalSearchResults(
                    question_id=entry["question_id"],
                    question=entry["question"],
                    retrieved_sources=retriever.search(query, k)
                ))
            StudentSearchResults(
                search_results=minimal_search_result,
                k=k
            )
            save_directory = Path(save_directory)
            save_directory.mkdir(parents=True, exist_ok=True)
            with open(save_directory / "search_results.json", "w", encoding="utf-8") as f:
                json.dump(StudentSearchResults(
                    search_results=minimal_search_result,
                    k=k
                ).model_dump(), f, indent=2)

    def answer(self, query: str, k: int = 3):
        retriever = Retriever(self.processed_dir)
        retriever.answer(query, k)


def main():
    Fire(CLI)


if __name__ == "__main__":
    main()

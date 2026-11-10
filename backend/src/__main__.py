from fire import Fire
from pathlib import Path
from python_indexing import python_indexer
from markdown_indexing import markdown_indexer
from models import Chunk
from tokenizer import tokenize
from tqdm import tqdm
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
        print(f"The Question was: {query} with the number {k}")


def main():
    Fire(CLI)


if __name__ == "__main__":
    main()

from fire import Fire
from pathlib import Path
from python_indexing import python_indexer
from markdown_indexing import markdown_indexer
from models import Chunk


class CLI:
    def __init__(self):
        self.project_root = Path(__file__).resolve().parent.parent
        self.datasets = self.project_root / 'data'
        self.indexed_python_files = []
        self.indexed_markdown_files = []

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
        for file in self.indexed_python_files:
            all_chunks.extend(
                python_indexer(file, self.project_root, max_chunk_size))
        for file in self.indexed_markdown_files:
            all_chunks.extend(
                markdown_indexer(file, self.project_root, max_chunk_size))
        print(f"Indexed {len(all_chunks)} chunks")
        if all_chunks:
            print(f"Example path: {all_chunks[0].file_path}")

    def search(self, query: str, k: int) -> None:
        print(f"The Question was: {query} with the number {k}")


def main():
    Fire(CLI)


if __name__ == "__main__":
    main()

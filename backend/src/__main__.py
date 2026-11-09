import fire
from pathlib import Path
from indexing import python_indexer


class CLI:
    def __init__(self):
        self.datasets = Path(__file__).resolve().parent.parent / 'data'
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
        for file in self.indexed_python_files:
            chunks = python_indexer(file, max_chunk_size)
            counter = 0
            while counter < len(chunks):
                if len(chunks[counter] + chunks[counter + 1]) < max_chunk_size:
                    chunks[counter] = chunks[counter] + chunks[counter + 1]
                counter += 2
            print(chunks[0])
            print(chunks[1])
            print(chunks[2])

    def search(self, query: str, k: int) -> None:
        print(f"The Question was: {query} with the number {k}")


def main():
    fire.Fire(CLI)


if __name__ == "__main__":
    main()

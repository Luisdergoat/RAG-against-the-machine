import fire
from pathlib import Path


class CLI:
    def __init__(self):
        self.datasets = Path(__file__).resolve().parent.parent / 'data/datasets'

    def index(self, max_chunk_size: int = 2000) -> None:
        

    def search(self, query: str, k: int) -> None:
        print(f"The Question was: {query} with the number {k}")


def main():
    fire.Fire(CLI)


if __name__ == "__main__":
    main()

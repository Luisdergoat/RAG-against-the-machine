from models import Chunk, MinimalSource
from tokenizer import tokenize
from pathlib import Path
import json
import bm25s


class Retriever():
    def __init__(self, processed_dir: Path) -> None:
        self.bm25 = bm25s.BM25.load(processed_dir / "bm25")

        with open(processed_dir / "chunks.json", encoding="utf-8") as f:
            self.chunks = [Chunk.model_validate(d) for d in json.load(f)]

    def search(self, query: str, k: int) -> list[MinimalSource]:
        query_tokens = tokenize(query)
        documents, scores = self.bm25.retrieve([query_tokens], k=k)
        print(f"Retrieved {len(documents)} documents for query '{query}'")
        print(f"Scores: {scores}")






if __name__ == "__main__":
    retriever = Retriever(Path(__file__).resolve().parent.parent / "data" / "processed")
    retriever.search("What is the purpose of the tokenize function?", 5)

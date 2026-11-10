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
        print(f"Documents: {documents}")
        print(f"Scores: {scores}")

        found_chunk = []
        for doc_id, score in zip(documents[0], scores[0]):
            chunk = self.chunks[doc_id]
            found_chunk.append(MinimalSource(
                file_path=chunk.file_path,
                first_character_index=chunk.first_character_index,
                last_character_index=chunk.last_character_index,
                text=chunk.text,
                score=score
            ))
            json_string = json.dumps(found_chunk[0].model_dump(), indent=2)
            print(f"\n{json_string}")






if __name__ == "__main__":
    retriever = Retriever(Path(__file__).resolve().parent.parent / "data" / "processed")
    retriever.search("What is the purpose of the tokenize function?", 3)

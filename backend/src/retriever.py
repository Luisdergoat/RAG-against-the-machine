from models import Chunk, MinimalSource
from tokenizer import tokenize
from transformers import AutoTokenizer, AutoModelForCausalLM
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

        found_chunk = []
        for doc_id, score in zip(documents[0], scores[0]):
            chunk = self.chunks[doc_id]
            found_chunk.append(MinimalSource(
                file_path=chunk.file_path,
                first_character_index=chunk.first_character_index,
                last_character_index=chunk.last_character_index,
            ))
        return found_chunk

    def generate_answer(self, text: str) -> str:
        model_name = "Qwen/Qwen3-0.6B"
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForCausalLM.from_pretrained(model_name)

        messages = [
            {"role": "system", "content": "Answer only using the given context."},
            {"role": "user", "content": text}
        ]

        prompt = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=False
            )

        inputs = tokenizer(prompt, return_tensors="pt")
        output = model.generate(**inputs, max_new_tokens=256)

        new_tokens = output[0][len(inputs.input_ids[0]):]
        answer = tokenizer.decode(new_tokens, skip_special_tokens=True)
        return answer

    def answer(self, query: str, k: int = 5):
        found_chunks = self.search(query, k)
        for chunk in found_chunks:
            try:
                with open(chunk.file_path, encoding="utf-8") as f:
                    text = f.read()
                    answer_text = text[chunk.first_character_index:chunk.last_character_index]

            except Exception as e:
                print(f"ERROR: {e}")
        answer = self.generate_answer(answer_text)
        print(f"Answer: {answer}")






if __name__ == "__main__":
    retriever = Retriever(Path(__file__).resolve().parent.parent / "data" / "processed")
    retriever.search("What is the purpose of the tokenize function?", 3)

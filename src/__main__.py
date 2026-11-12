from fire import Fire
from pathlib import Path
from pydantic import ValidationError


from models import (
    Chunk, MinimalSearchResults, StudentSearchResults,
    MinimalAnswer, StudentSearchResultsAndAnswer)

from tokenizer import tokenize
from retriever import Retriever
from generator import Generator, build_context
from python_indexing import python_indexer
from markdown_indexing import markdown_indexer


from tqdm import tqdm
from typing import Any
import bm25s
import json

CONTEXT_SOURCES = 5


def calculate_iou(source_a: dict[str, Any], source_b: dict[str, Any]) -> float:

    intersection = max(
        0,
        min(
            source_a["last_character_index"],
            source_b["last_character_index"]
            )
        - max(
            source_a["first_character_index"],
            source_b["first_character_index"]
            )
    )

    union = (
        max(
            source_a["last_character_index"],
            source_b["last_character_index"]
            )
        - min(
            source_a["first_character_index"],
            source_b["first_character_index"]
            )
    )

    return intersection / union if union > 0 else 0.0


def question_recall(
    correct_sources: list[dict], retrieved_sources: list[dict]
) -> float:

    found = 0
    for correct in correct_sources:
        for retrieved in retrieved_sources:
            if (
                correct["file_path"] == retrieved["file_path"]
                    and calculate_iou(correct, retrieved) >= 0.05):
                found += 1
                break

    return found / len(correct_sources)


class CLI:
    def __init__(self) -> None:
        self.project_root = Path(__file__).resolve().parent.parent
        self.datasets = self.project_root / 'data'
        self.indexed_python_files: list = []
        self.indexed_markdown_files: list = []
        self.processed_dir = (
            Path(__file__).resolve().parent.parent / "data" / "processed")

    def index(self, max_chunk_size: int = 2000) -> None:
        try:
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
                all_chunks.extend(
                    python_indexer(file, self.project_root, max_chunk_size))

            for file in tqdm(
                    self.indexed_markdown_files, desc="Markdown files"):
                all_chunks.extend(
                    markdown_indexer(file, self.project_root, max_chunk_size))
            corpus_tokens = []
            for chunks in tqdm(all_chunks, desc="Tokenizing"):
                corpus_tokens.append(tokenize(chunks.text))

            self.processed_dir.mkdir(exist_ok=True)
            retriever = bm25s.BM25()
            retriever.index(corpus_tokens)
            retriever.save(self.processed_dir / "bm25")

            with open(
                self.processed_dir / "chunks.json", "w", encoding="utf-8"
            ) as f:
                json.dump(
                    [chunk.model_dump() for chunk in all_chunks], f, indent=2)

            print("Ingestion complete! Indices saved under data/processed/")
        except Exception as e:
            print(f"Error during indexing: {e}")

    def search(self, query: str, k: int) -> None:
        retriever = Retriever(self.processed_dir)
        try:
            results = retriever.search(query, k)
            for result in results:
                print(json.dumps(result.model_dump(), indent=2))
        except Exception as e:
            print(f"Error during search: {e}")

    def search_dataset(
            self, dataset_path: Path, save_directory: Path, k: int = 3
            ) -> None:
        try:
            with open(dataset_path, "r", encoding="utf-8") as f:
                dataset = json.load(f)
                minimal_search_result = []
                retriever = Retriever(self.processed_dir)
                for entry in tqdm(
                        dataset["rag_questions"], desc="Searching dataset"):
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
                output_path = save_directory / Path(dataset_path).name
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(StudentSearchResults(
                        search_results=minimal_search_result,
                        k=k
                    ).model_dump(), f, indent=2)
            print(f"Saved student_search_results to {output_path}")
        except Exception as e:
            print(f"Error during search_dataset: {e}")

    def answer(self, query: str, k: int = 5) -> None:
        if not isinstance(query, str):
            print("Error: Query must be a string.")
            return
        if not isinstance(k, int) or k <= 0:
            print("Error: k must be a positive integer.")
            return
        try:
            retriever = Retriever(self.processed_dir)
        except Exception as e:
            print(f"Error initializing Retriever: {e}")
            return
        sources = retriever.search(query, k)
        context = build_context(self.project_root, sources)
        generator = Generator()
        answer = generator.generate(context, query)
        for source in sources:
            print(f"Source: {source.file_path} "
                  f"[{source.first_character_index}:"
                  f"{source.last_character_index}]")
            print(f"Answer: {answer}")

    def answer_dataset(
        self, student_search_results: Path, save_directory: Path, k: int = 5
    ) -> None:

        try:
            with open(student_search_results, encoding="utf-8") as f:
                search_results = StudentSearchResults.model_validate(
                    json.load(f))
        except (OSError, json.JSONDecodeError, ValidationError) as e:
            print(f"ERROR: Could not load search results: {e}")
            return

        generator = Generator()
        answers = []
        for entry in tqdm(search_results.search_results, desc="Answering"):
            sources = entry.retrieved_sources[:CONTEXT_SOURCES]
            context = build_context(self.project_root, sources)
            answers.append(MinimalAnswer(
                question_id=entry.question_id,
                question=entry.question,
                retrieved_sources=entry.retrieved_sources,
                answer=generator.generate(context, entry.question),
            ))

        result = StudentSearchResultsAndAnswer(
            search_results=answers, k=search_results.k
        )

        output_dir = Path(save_directory)
        output_path = output_dir / Path(student_search_results).name
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(result.model_dump_json(indent=2))
        except Exception as e:
            print(f"ERROR: Could not save results: {e}")
            return
        print(f"Saved student_search_results_and_answer to {output_path}")

    def evaluate(self, student_answer_path: Path, solution_path: Path) -> None:

        try:
            with open(student_answer_path, "r", encoding="utf-8") as f:
                student = json.load(f)
            with open(solution_path, "r", encoding="utf-8") as f:
                solution = json.load(f)
            student_by_id = {
                e["question_id"]: e for e in student["search_results"]}
            solution_by_id = {
                e["question_id"]: e for e in solution["rag_questions"]}
        except Exception as e:
            print(f"ERROR: Could not load files: {e}")
            return

        k_values = [1, 3, 5, 10]
        recalls: dict = {k: [] for k in k_values}

        try:
            for question_id, solution_entry in tqdm(
                    solution_by_id.items(), desc="Evaluating"):
                student_entry = student_by_id.get(question_id)
                correct_sources = solution_entry.get("sources", [])
                if student_entry is None or not correct_sources:
                    continue
                retrieved = student_entry["retrieved_sources"]
                for k in k_values:
                    recalls[k].append(
                        question_recall(correct_sources, retrieved[:k]))

            if not recalls[1]:
                print("Error: No matching question found")
                return

            print(f"Evaluated {len(recalls[1])} questions")
            print(" ".join(f"Recall@{k}: {sum(r) / len(r):.3f}"
                           for k, r in recalls.items()))
        except Exception as e:
            print(f"ERROR: Evaluation failed: {e}")


def main() -> None:
    Fire(CLI)


if __name__ == "__main__":
    main()

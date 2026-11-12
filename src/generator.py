from pathlib import Path
from typing import Any

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from models import MinimalSource

MODEL_NAME = "Qwen/Qwen3-0.6B"
SYSTEM_PROMPT = (
    "Answer the question using only the given context. "
    "Answer in the same language as the question. "
    "Translate the question to English if it is not in English, then search "
    "for the answer in the context, and translate the answer back to the "
    "original language of the question."
    "If the question is not answerable using the context, say so. "
    "If the context is empty, say so. "
    "If the answer is not contained in the context, say so. "
    "Do not make up an answer and do not explain the context. "
    "Answer directly in a few sentences, in the same language as the question."
)


def read_source_text(project_root: Path, source: MinimalSource) -> str:
    """Liest den Textausschnitt einer Quelle aus ihrer Datei."""
    with open(project_root / source.file_path, encoding="utf-8") as f:
        text = f.read()
    return text[source.first_character_index:source.last_character_index]


def build_context(project_root: Path,
                  sources: list[MinimalSource]) -> str:
    """Baut aus mehreren Quellen einen Kontext-String für das Modell."""
    parts: list[str] = []
    for i, source in enumerate(sources, start=1):
        try:
            snippet = read_source_text(project_root, source)
        except (OSError, UnicodeDecodeError) as e:
            print(f"WARNING: Could not read {source.file_path}: {e}")
            continue
        parts.append(f"[Source {i}: {source.file_path}]\n{snippet}")
    return "\n\n".join(parts)


class Generator:
    """Lädt Qwen einmal und erzeugt Antworten aus Kontext + Frage."""

    def __init__(self, model_name: str = MODEL_NAME) -> None:
        if torch.cuda.is_available():
            self.device = "cuda"
        elif torch.backends.mps.is_available():
            self.device = "mps"
        else:
            self.device = "cpu"

        dtype = torch.float32 if self.device == "cpu" else torch.float16
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model: Any = AutoModelForCausalLM.from_pretrained(
            model_name, torch_dtype=dtype).to(self.device)

    def generate(self, context: str, query: str) -> str:
        """Erzeugt eine Antwort auf query, gestützt auf context."""
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",
             "content": f"Context:\n{context}\n\nQuestion: {query}"},
        ]
        prompt = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=False,
        )
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        output = self.model.generate(**inputs, max_new_tokens=256)
        new_tokens = output[0][len(inputs.input_ids[0]):]
        return str(self.tokenizer.decode(new_tokens,
                                         skip_special_tokens=True)).strip()

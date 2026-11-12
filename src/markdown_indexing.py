from pathlib import Path
from markdown_it import MarkdownIt
import python_indexing as pyi


def markdown_units(text: str, starts: list[int]) -> list[tuple[int, int]]:
    try:
        md = MarkdownIt()
        tokens = md.parse(text)
    except Exception:
        return [(0, len(text))] if text else []

    if not tokens:
        return [(0, len(text))] if text else []

    positions = []
    for token in tokens:
        if token.type == "heading_open" and token.map is not None:
            start_line = token.map[0]
            positions.append(starts[start_line])

    if not positions:
        return [(0, len(text))]
    positions[0] = 0
    positions.append(len(text))

    units = []
    for i in range(len(positions) - 1):
        units.append((positions[i], positions[i + 1]))
    return units


def markdown_indexer(file_path: Path, project_root: Path,
                     max_chunk_size: int) -> list[pyi.Chunk]:
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
    except Exception:
        return []

    starts = pyi.line_starts(text)
    units = markdown_units(text, starts)
    units = pyi.split_oversized(units, starts, max_chunk_size)
    packed_units = pyi.pack_units(units, max_chunk_size)

    relative_path = Path(file_path).relative_to(project_root).as_posix()
    chunks = []
    for start, end in packed_units:
        chunk_text = text[start:end]
        chunk = pyi.Chunk(
            file_path=relative_path,
            first_character_index=start,
            last_character_index=end,
            text=chunk_text,
        )
        chunks.append(chunk)

    return chunks

import ast
from pathlib import Path
from models import Chunk


def count_letters(text: str) -> int:
    return len(text)


def python_units(text: str, starts: list[int]) -> list[tuple[int, int]]:
    try:
        tree = ast.parse(text)

    except SyntaxError:
        return [(0, len(text))] if text else []

    if not tree.body:
        return [(0, len(text))] if text else []

    positions = []
    for node in tree.body:
        decorators = getattr(node, "decorator_list", [])
        if decorators:
            start_line = decorators[0].lineno
        else:
            start_line = node.lineno
        positions.append(starts[start_line - 1])

    positions[0] = 0
    positions.append(len(text))

    units = []
    for i in range(len(positions) - 1):
        units.append((positions[i], positions[i + 1]))
    return units


def pack_units(
    units: list[tuple[int, int]], max_chunk_size: int
) -> list[tuple[int, int]]:

    chunks = []
    current_chunk = []
    current_chunk_size = 0

    for start, end in units:
        unit_size = end - start
        if current_chunk_size + unit_size > max_chunk_size:
            if current_chunk:
                chunks.append((current_chunk[0][0], current_chunk[-1][1]))
            current_chunk = [(start, end)]
            current_chunk_size = unit_size
        else:
            current_chunk.append((start, end))
            current_chunk_size += unit_size

    if current_chunk:
        chunks.append((current_chunk[0][0], current_chunk[-1][1]))

    return chunks


def line_starts(text: str) -> list:
    text = text.splitlines(keepends=True)
    return [sum(len(line) for line in text[:i]) for i in range(len(text) + 1)]


def split_by_lines(start: int, end: int, starts: list[int],
                   max_chunk_size: int) -> list[tuple[int, int]]:
    positions = [start]
    for pos in starts:
        if start < pos < end:
            positions.append(pos)
    positions.append(end)

    line_units: list[tuple[int, int]] = []
    for i in range(len(positions) - 1):
        line_start = positions[i]
        line_end = positions[i + 1]
        if line_end - line_start <= max_chunk_size:
            line_units.append((line_start, line_end))
        else:
            for piece in range(line_start, line_end, max_chunk_size):
                line_units.append(
                    (piece, min(piece + max_chunk_size, line_end)))

    return pack_units(line_units, max_chunk_size)


def split_oversized(units: list[tuple[int, int]], starts: list[int],
                    max_chunk_size: int) -> list[tuple[int, int]]:

    result: list[tuple[int, int]] = []
    for start, end in units:
        if end - start > max_chunk_size:
            result.extend(split_by_lines(start, end, starts, max_chunk_size))
        else:
            result.append((start, end))
    return result


def python_indexer(file_path: Path, project_root: Path,
                   max_chunk_size: int) -> list[Chunk]:

    try:
        with open(file_path, 'r', encoding="utf-8") as file:
            text = file.read()

    except (UnicodeDecodeError, OSError):
        print(f"Fehler beim Lesen der Datei: {file_path}")
        return []

    relative_path = Path(file_path).relative_to(project_root).as_posix()
    chunks: list[Chunk] = []
    starts = line_starts(text)
    units = python_units(text, starts)
    units = split_oversized(units, starts, max_chunk_size)
    units = pack_units(units, max_chunk_size)
    for start, end in units:
        chunks.append(Chunk(
                file_path=relative_path,
                first_character_index=start,
                last_character_index=end,
                text=text[start:end]
            ))
    return chunks

import ast


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


def pack_units(units: list[tuple[int, int]], max_chunk_size: int) -> list[tuple[int, int]]:
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


def python_indexer(file_path: str, max_chunk_size: int) -> list:

    with open(file_path, 'r', encoding="utf-8") as file:
        try:
            tree = ast.parse(file.read())
        except SyntaxError as e:
            print(f"Syntax error in file {file_path}: {e}")
            return []

        chunks = []
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                chunks.append(ast.get_source_segment(open(file_path).read(), node))

        return chunks


def line_starts(text: str) -> list:
    text = text.splitlines(keepends=True)
    return [sum(len(line) for line in text[:i]) for i in range(len(text) + 1)]

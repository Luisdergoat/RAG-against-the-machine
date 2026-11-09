from pathlib import Path
from indexing import python_indexer


CODE = '''import os

X = 5

@decorator
def foo(a, b):
    """Addiert zwei Zahlen."""
    return a + b

class Bar:
    def methode(self):
        pass
'''


def make_file(root: Path, relative: str, content: str) -> Path:
    """Legt eine Datei unter root an und gibt ihren Pfad zurück."""
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def test_returns_chunks(tmp_path: Path) -> None:
    file = make_file(tmp_path, "data/raw/test.py", CODE)
    chunks = python_indexer(file, 2000)
    assert len(chunks) == 1
    assert chunks[0].text == CODE


def test_file_path_is_relative(tmp_path: Path) -> None:
    file = make_file(tmp_path, "data/raw/test.py", CODE)
    for chunk in python_indexer(file, 50):
        assert chunk.file_path == "data/raw/test.py"
        assert not chunk.file_path.startswith("/")


def test_text_matches_indices(tmp_path: Path) -> None:
    file = make_file(tmp_path, "data/raw/test.py", CODE)
    for chunk in python_indexer(file, 50):
        start = chunk.first_character_index
        end = chunk.last_character_index
        assert chunk.text == CODE[start:end]


def test_no_chunk_too_big(tmp_path: Path) -> None:
    file = make_file(tmp_path, "data/raw/test.py", CODE)
    for max_size in (2000, 100, 50, 10):
        for chunk in python_indexer(file, max_size):
            length = chunk.last_character_index - chunk.first_character_index
            assert length <= max_size, f"Zu groß bei max={max_size}"


def test_whole_file_covered(tmp_path: Path) -> None:
    file = make_file(tmp_path, "data/raw/test.py", CODE)
    chunks = python_indexer(file, 50)
    assert chunks[0].first_character_index == 0
    assert chunks[-1].last_character_index == len(CODE)
    assert "".join(c.text for c in chunks) == CODE


def test_example_chunks_50(tmp_path: Path) -> None:
    file = make_file(tmp_path, "data/raw/test.py", CODE)
    positions = [(c.first_character_index, c.last_character_index)
                 for c in python_indexer(file, 50)]
    assert positions == [(0, 44), (44, 93), (93, 140)]


def test_syntax_error_no_crash(tmp_path: Path) -> None:
    content = "def kaputt(:\n    pass\n"
    file = make_file(tmp_path, "data/raw/broken.py", content)
    chunks = python_indexer(file, 2000)
    assert "".join(c.text for c in chunks) == content


def test_missing_file(tmp_path: Path) -> None:
    missing = tmp_path / "data/raw/gibts_nicht.py"
    assert python_indexer(missing, 2000) == []


def test_invalid_utf8(tmp_path: Path) -> None:
    file = tmp_path / "data/raw/binary.py"
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_bytes(b"\xff\xfe\x00 kaputt")
    assert python_indexer(file, 2000) == []


def test_empty_file(tmp_path: Path) -> None:
    file = make_file(tmp_path, "data/raw/empty.py", "")
    assert python_indexer(file, 2000) == []


def test_umlauts_count_as_one_char(tmp_path: Path) -> None:
    content = '# Größe ändern\nx = "über"\n'
    file = make_file(tmp_path, "data/raw/umlaut.py", content)
    chunks = python_indexer(file, 2000)
    assert chunks[0].last_character_index == len(content)

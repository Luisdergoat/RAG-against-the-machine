from indexing import line_starts, python_units


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


def get_units(text: str) -> list[tuple[int, int]]:
    """Hilfsfunktion: line_starts + python_units in einem Aufruf."""
    return python_units(text, line_starts(text))


def test_expected_units() -> None:
    assert get_units(CODE) == [(0, 11), (11, 18), (18, 93), (93, 140)]


def test_no_gaps() -> None:
    units = get_units(CODE)
    assert units[0][0] == 0
    assert units[-1][1] == len(CODE)
    for (_, end), (next_start, _) in zip(units, units[1:]):
        assert end == next_start, f"Lücke/Überlappung bei {end}"


def test_text_is_unchanged() -> None:
    units = get_units(CODE)
    assert "".join(CODE[s:e] for s, e in units) == CODE


def test_decorator_belongs_to_function() -> None:
    start, end = get_units(CODE)[2]
    assert CODE[start:end].startswith("@decorator")


def test_comment_at_top_is_kept() -> None:
    text = "# Kommentar\n\nimport os\n"
    units = get_units(text)
    assert units[0][0] == 0
    assert text[units[0][0]:units[0][1]].startswith("# Kommentar")


def test_syntax_error() -> None:
    text = "def kaputt(:\n    pass\n"
    assert get_units(text) == [(0, len(text))]


def test_empty_file() -> None:
    assert get_units("") == []


def test_only_comments() -> None:
    text = "# nur ein Kommentar\n"
    assert get_units(text) == [(0, len(text))]

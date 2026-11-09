from indexing import (line_starts, pack_units, python_units,
                      split_by_lines, split_oversized)


THREE_LINES = "aaaa\nbbbb\ncccc\n"   # 3 Zeilen à 5 Zeichen = 15

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


def full_chain(text: str, max_size: int) -> list[tuple[int, int]]:
    """Die komplette Kette: units -> split_oversized -> pack_units."""
    starts = line_starts(text)
    units = python_units(text, starts)
    units = split_oversized(units, starts, max_size)
    return pack_units(units, max_size)


# --- split_by_lines ---------------------------------------------------------

def test_two_lines_fit() -> None:
    starts = line_starts(THREE_LINES)
    assert split_by_lines(0, 15, starts, 10) == [(0, 10), (10, 15)]


def test_one_line_per_chunk() -> None:
    starts = line_starts(THREE_LINES)
    assert split_by_lines(0, 15, starts, 5) == [(0, 5), (5, 10), (10, 15)]


def test_only_lines_inside_range() -> None:
    starts = line_starts(THREE_LINES)
    assert split_by_lines(5, 15, starts, 10) == [(5, 15)]


def test_long_line_hard_cut() -> None:
    text = "x" * 25
    starts = line_starts(text)
    assert split_by_lines(0, 25, starts, 10) == [(0, 10), (10, 20), (20, 25)]


def test_no_empty_pieces() -> None:
    starts = line_starts(THREE_LINES)
    for max_size in (1, 3, 5, 10, 15):
        for start, end in split_by_lines(0, 15, starts, max_size):
            assert end > start, f"Leeres Stück bei max={max_size}"


# --- split_oversized --------------------------------------------------------

def test_small_units_unchanged() -> None:
    units = [(0, 11), (11, 18)]
    starts = line_starts(CODE)
    assert split_oversized(units, starts, 2000) == units


def test_big_unit_gets_split() -> None:
    starts = line_starts(CODE)
    result = split_oversized([(18, 93)], starts, 50)   # foo = 75 Zeichen
    assert len(result) > 1
    assert result[0][0] == 18
    assert result[-1][1] == 93


# --- komplette Kette --------------------------------------------------------

def test_chain_example_50() -> None:
    assert full_chain(CODE, 50) == [(0, 44), (44, 93), (93, 140)]


def test_chain_never_too_big() -> None:
    for max_size in (2000, 100, 80, 50, 20, 5, 1):
        for start, end in full_chain(CODE, max_size):
            assert end - start <= max_size, f"Zu groß bei max={max_size}"


def test_chain_text_unchanged() -> None:
    for max_size in (2000, 100, 80, 50, 20, 5, 1):
        chunks = full_chain(CODE, max_size)
        rebuilt = "".join(CODE[s:e] for s, e in chunks)
        assert rebuilt == CODE, f"Text kaputt bei max={max_size}"


def test_chain_no_gaps() -> None:
    for max_size in (2000, 100, 50, 5):
        chunks = full_chain(CODE, max_size)
        assert chunks[0][0] == 0
        assert chunks[-1][1] == len(CODE)
        for (_, end), (next_start, _) in zip(chunks, chunks[1:]):
            assert end == next_start, f"Lücke bei max={max_size}"

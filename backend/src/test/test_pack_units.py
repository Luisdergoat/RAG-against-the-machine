from python_indexing import line_starts, python_units, split_by_lines, split_oversized, pack_units


# Einheiten aus dem Beispielcode (Längen: 11, 7, 75, 47)
UNITS = [(0, 11), (11, 18), (18, 93), (93, 140)]


def test_everything_fits() -> None:
    assert pack_units(UNITS, 2000) == [(0, 140)]


def test_max_100() -> None:
    assert pack_units(UNITS, 100) == [(0, 93), (93, 140)]


def test_max_80() -> None:
    assert pack_units(UNITS, 80) == [(0, 18), (18, 93), (93, 140)]


def test_unit_too_big_goes_through() -> None:
    assert pack_units(UNITS, 50) == [(0, 18), (18, 93), (93, 140)]


def test_exact_fit() -> None:
    # Genau 18 Zeichen: (0, 18) muss noch passen (<=, nicht <)
    assert pack_units([(0, 11), (11, 18)], 18) == [(0, 18)]


def test_empty() -> None:
    assert pack_units([], 2000) == []


def test_single_unit() -> None:
    assert pack_units([(0, 500)], 2000) == [(0, 500)]


def test_last_chunk_not_forgotten() -> None:
    chunks = pack_units(UNITS, 80)
    assert chunks[-1][1] == 140


def test_no_gaps() -> None:
    for max_size in (2000, 100, 80, 50, 10):
        chunks = pack_units(UNITS, max_size)
        assert chunks[0][0] == 0
        assert chunks[-1][1] == 140
        for (_, end), (next_start, _) in zip(chunks, chunks[1:]):
            assert end == next_start, f"Lücke bei max={max_size}"


def test_chunks_not_too_big() -> None:
    # Jeder Chunk aus mehreren Einheiten muss <= max sein
    for max_size in (2000, 100, 80):
        for start, end in pack_units(UNITS, max_size):
            assert end - start <= max_size

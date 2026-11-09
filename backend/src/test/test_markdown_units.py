from python_indexing import line_starts, split_oversized, pack_units
from markdown_indexing import markdown_units, markdown_indexer


DOC = """# Titel
Intro.

## Abschnitt A
Text A.

```bash
# kein Header
pip install vllm
```

## Abschnitt B
Text B.
"""


def get_units(text: str) -> list[tuple[int, int]]:
    """Hilfsfunktion: line_starts + markdown_units in einem Aufruf."""
    return markdown_units(text, line_starts(text))


def full_chain(text: str, max_size: int) -> list[tuple[int, int]]:
    """Die komplette Kette für Markdown."""
    starts = line_starts(text)
    units = markdown_units(text, starts)
    units = split_oversized(units, starts, max_size)
    return pack_units(units, max_size)


def test_expected_units() -> None:
    assert get_units(DOC) == [(0, 16), (16, 84), (84, 107)]


def test_three_sections() -> None:
    assert len(get_units(DOC)) == 3


def test_sections_start_with_heading() -> None:
    texts = [DOC[s:e] for s, e in get_units(DOC)]
    assert texts[0].startswith("# Titel")
    assert texts[1].startswith("## Abschnitt A")
    assert texts[2].startswith("## Abschnitt B")


def test_code_block_comment_is_not_heading() -> None:
    for start, _ in get_units(DOC):
        assert not DOC[start:].startswith("# kein Header")


def test_code_block_stays_in_section_a() -> None:
    start, end = get_units(DOC)[1]
    assert "pip install vllm" in DOC[start:end]


def test_no_gaps() -> None:
    units = get_units(DOC)
    assert units[0][0] == 0
    assert units[-1][1] == len(DOC)
    for (_, end), (next_start, _) in zip(units, units[1:]):
        assert end == next_start, f"Lücke/Überlappung bei {end}"


def test_text_is_unchanged() -> None:
    assert "".join(DOC[s:e] for s, e in get_units(DOC)) == DOC


def test_text_before_first_heading_is_kept() -> None:
    text = "Ein Satz ohne Überschrift.\n\n# Titel\nText.\n"
    units = get_units(text)
    assert units[0][0] == 0
    assert text[units[0][0]:units[0][1]].startswith("Ein Satz")


def test_no_headings() -> None:
    text = "Nur Text.\nNoch eine Zeile.\n"
    assert get_units(text) == [(0, len(text))]


def test_empty_file() -> None:
    assert get_units("") == []


def test_hash_without_space_inside_text() -> None:
    # "#5" am Zeilenanfang ist in Markdown keine Überschrift
    text = "# Titel\nText.\n#5 ist keine Überschrift\n"
    assert len(get_units(text)) == 1


def test_chain_never_too_big() -> None:
    for max_size in (2000, 50, 20, 5, 1):
        for start, end in full_chain(DOC, max_size):
            assert end - start <= max_size, f"Zu groß bei max={max_size}"


def test_chain_text_unchanged() -> None:
    for max_size in (2000, 50, 20, 5, 1):
        chunks = full_chain(DOC, max_size)
        assert "".join(DOC[s:e] for s, e in chunks) == DOC


def test_chain_2000_one_chunk() -> None:
    assert full_chain(DOC, 2000) == [(0, len(DOC))]

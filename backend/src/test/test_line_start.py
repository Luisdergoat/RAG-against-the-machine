from backend.src.test.test_line_start import line_starts


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

EXPECTED = [0, 10, 11, 17, 18, 29, 44, 75, 92, 93, 104, 127, 140]


def test_line_starts() -> None:
    result = line_starts(CODE)
    print("Ergebnis: ", result)
    print("Erwartet: ", EXPECTED)

    assert result == EXPECTED, "Liste stimmt nicht"
    assert result[-1] == len(CODE), "Letzter Wert ist nicht len(text)"

    # Jede Zeile muss genau an ihrer Startposition beginnen
    for i, line in enumerate(CODE.splitlines(keepends=True)):
        start = result[i]
        assert CODE[start:start + len(line)] == line, f"Zeile {i + 1} falsch"

    print("Alles korrekt ✅")


if __name__ == "__main__":
    test_line_starts()

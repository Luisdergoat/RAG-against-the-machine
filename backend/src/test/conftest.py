import sys
from pathlib import Path

# Macht src/ importierbar, damit "from indexing import ..." klappt
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

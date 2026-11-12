import asyncio
import json
import sys
from pathlib import Path
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles

# src/ zum Suchpfad hinzufügen, damit die flachen Imports in retriever.py,
# generator.py usw. ("from models import ...") auch hier funktionieren.
SRC_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SRC_DIR))

from retriever import Retriever  # noqa: E402
from generator import Generator, build_context  # noqa: E402

PROJECT_ROOT = SRC_DIR.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
FRONTEND_DIR = PROJECT_ROOT / "frontend"


def create_app() -> FastAPI:
    """Erstellt die FastAPI-App mit WebSocket-Endpunkt und Frontend."""
    app = FastAPI()
    retriever = Retriever(PROCESSED_DIR)
    generator = Generator()

    def answer_question(query: str, k: int) -> dict[str, Any]:
        sources = retriever.search(query, k)
        context = build_context(PROJECT_ROOT, sources)
        answer = generator.generate(context, query)
        return {"answer": answer,
                "sources": [s.model_dump() for s in sources]}

    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket) -> None:
        await websocket.accept()
        try:
            while True:
                raw = await websocket.receive_text()
                try:
                    data = json.loads(raw)
                except json.JSONDecodeError:
                    await websocket.send_json({"error": "Invalid JSON."})
                    continue

                if data.get("prompt") != "answer":
                    await websocket.send_json({"error": "Unknown prompt."})
                    continue

                query = data.get("query")
                k = data.get("k", 5)
                if not isinstance(query, str) or not query.strip():
                    await websocket.send_json(
                        {"error": "Query must be a non-empty string."})
                    continue
                if not isinstance(k, int) or k <= 0:
                    await websocket.send_json(
                        {"error": "k must be a positive integer."})
                    continue

                # Qwen blockiert einige Sekunden: in einem Thread laufen
                # lassen, damit die WebSocket-Verbindung lebendig bleibt.
                result = await asyncio.to_thread(answer_question, query, k)
                await websocket.send_json(result)
        except WebSocketDisconnect:
            print("Client disconnected")

    # Muss NACH /ws kommen, sonst fängt "/" auch die WebSocket-Anfragen ab.
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True),
              name="frontend")
    return app


app = create_app()

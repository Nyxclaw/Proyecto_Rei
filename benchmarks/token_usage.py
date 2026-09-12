"""Dos preguntas reales con el mismo contexto; ejecutar desde la raíz del repo."""
import argparse
import json
from pathlib import Path
import time

import requests

from rei.ai.ollama_provider import OllamaProvider


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("token_benchmark.json"))
    args = parser.parse_args()
    brain = OllamaProvider()
    report = {"model": brain.model, "turns": []}
    report["loaded_before"] = requests.get(
        brain.host + "/api/ps", timeout=5
    ).json()
    questions = [
        "¿Cuál es la capital de Japón? Responde en una sola frase.",
        "¿Por qué esa ciudad es importante? Explícalo en tres frases breves.",
    ]
    for question in questions:
        print("Tú:", question, flush=True)
        started = time.perf_counter()
        first_chunk = None
        chunks = []
        for chunk in brain.chat_stream(question):
            if first_chunk is None:
                first_chunk = time.perf_counter() - started
            chunks.append(chunk)
            print(chunk, end="", flush=True)
        elapsed = time.perf_counter() - started
        metrics = brain.get_last_metrics()
        print("\n", metrics, flush=True)
        report["turns"].append({
            "question": question,
            "answer": "".join(chunks),
            "metrics": metrics,
            "first_chunk_seconds": first_chunk,
            "wall_seconds": elapsed,
            "loaded_after": requests.get(brain.host + "/api/ps", timeout=5).json(),
        })
        if not metrics["available"]:
            break
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    if len(report["turns"]) != 2 or not all(t["metrics"]["available"] for t in report["turns"]):
        raise SystemExit("Prueba incompleta: consultar errores en el informe.")


if __name__ == "__main__":
    main()

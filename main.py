import time

from rei.ai.ollama_provider import OllamaProvider


def main():
    brain = OllamaProvider()

    print("Rei iniciada.")
    print("Comandos: 'salir' para terminar, 'reiniciar' para borrar el contexto.\n")

    while True:
        user_message = input("Tú: ").strip()
        if not user_message:
            continue
        command = user_message.lower()
        if command in {"salir", "exit", "quit"}:
            print("Rei: Hasta luego.")
            break
        if command == "reiniciar":
            brain.clear_history()
            print("Rei: Contexto reiniciado.\n")
            continue

        start_time = time.perf_counter()
        first_chunk_time = None
        print("Rei: ", end="", flush=True)
        for chunk in brain.chat_stream(user_message):
            if first_chunk_time is None:
                first_chunk_time = time.perf_counter()
            print(chunk, end="", flush=True)

        end_time = time.perf_counter()
        # Ollama entrega las métricas en el último fragmento del stream.
        metrics = brain.get_last_metrics()
        print()
        if not metrics["available"]:
            print("[Métricas no disponibles para esta petición.]\n")
            continue

        print(
            f"[Tokens entrada: {metrics['input_tokens']} | "
            f"salida: {metrics['output_tokens']} | "
            f"total de esta petición: {metrics['total_tokens']}]"
        )
        print(f"[Velocidad de generación: {metrics['tokens_per_second']:.2f} tokens/s]")
        if first_chunk_time is not None:
            print(f"[Primer fragmento: {first_chunk_time - start_time:.2f} s]")
        print(f"[Tiempo total: {end_time - start_time:.2f} s]\n")


if __name__ == "__main__":
    main()

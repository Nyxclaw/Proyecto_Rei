import argparse
import time

from rei.ai.ollama_provider import OllamaProvider
from rei.core.conversation import Conversation


def text_chat():
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


def main(debug=False):
    conversation = Conversation()
    print("Rei iniciada. Puedes pedir abrir Bloc de notas o Calculadora.")
    print("Comandos: salir, reiniciar.\n")

    def show_tool(action):
        result = action["result"]
        print(f"[Verificación: {result.get('status', result.get('error', 'desconocido'))}]")
        if debug:
            print(f"[Herramienta: {action['tool']} | Resultado: {result}]")

    while True:
        try:
            text = input("Tú: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nRei: Hasta luego.")
            break
        if not text:
            continue
        if text.lower() in {"salir", "exit", "quit"}:
            break
        if text.lower() == "reiniciar":
            conversation.clear_history()
            print("Rei: Contexto reiniciado.")
            continue
        started = time.perf_counter()
        print("Rei está procesando la solicitud…", flush=True)
        result = conversation.run_turn(text, on_tool=show_tool)
        print("Rei:", result["answer"])
        for index, metrics in enumerate(result["calls"], 1):
            if metrics["available"]:
                print(f"[Llamada {index}: entrada {metrics['input_tokens']} | "
                      f"salida {metrics['output_tokens']} | {metrics['tokens_per_second']:.2f} tokens/s]")
            else:
                print(f"[Llamada {index}: métricas no disponibles]")
        qualifier = "" if result["metrics_complete"] else "parcial "
        print(f"[Total {qualifier}del turno: {result['total_tokens']} tokens | "
              f"Tiempo: {time.perf_counter() - started:.2f} s]\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true", help="Mostrar evidencia de las herramientas")
    parser.add_argument("--text-only", action="store_true", help="Chat de texto con streaming, sin herramientas")
    args = parser.parse_args()
    if args.text_only:
        text_chat()
    else:
        main(debug=args.debug)

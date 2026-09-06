import time

from rei.ai.ollama_provider import OllamaProvider


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
    first_token_time = None

    print("Rei: ", end="", flush=True)

    for chunk in brain.chat_stream(user_message):

        if first_token_time is None:
            first_token_time = time.perf_counter()

        print(chunk, end="", flush=True)

    end_time = time.perf_counter()

    print()

    if first_token_time is not None:
        ttft = first_token_time - start_time
        total = end_time - start_time

        print(f"[Primer fragmento: {ttft:.2f} s]")
        print(f"[Tiempo total: {total:.2f} s]\n")
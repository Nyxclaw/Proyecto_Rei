import time
from rei.ai.ollama_provider import OllamaProvider


from rei.core.tool_router import ToolRouter
from rei.tools.tool_definitions import TOOLS


brain = OllamaProvider()
router = ToolRouter()

result = brain.chat_with_tools(
    #"Abre el bloc de notas.",
    #TOOLS,
)

print("Respuesta del modelo:")
print(result)


metrics = brain.get_last_metrics()

print(
    f"[Tokens entrada: {metrics['input_tokens']} | "
    f"salida: {metrics['output_tokens']} | "
    f"total: {metrics['total_tokens']}]"
)

tool_calls = result.get("tool_calls", [])

if tool_calls:
    for tool_call in tool_calls:
        function = tool_call["function"]

        tool_name = function["name"]
        arguments = function["arguments"]

        print(f"\nTool solicitada: {tool_name}")
        print(f"Argumentos: {arguments}")

        tool_result = router.execute(
            tool_name,
            arguments,
        )

        print(f"Resultado: {tool_result}")


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

    print(
        f"[Tokens entrada: {metrics['input_tokens']} | "
        f"salida: {metrics['output_tokens']} | "
        f"total: {metrics['total_tokens']}]"
    )
    
    print(
        f"[Velocidad: "
        f"{metrics['tokens_per_second']:.2f} tokens/s]"
    )

    if first_token_time is not None:
        ttft = first_token_time - start_time
        total = end_time - start_time

        print(f"[Primer fragmento: {ttft:.2f} s]")
        print(f"[Tiempo total: {total:.2f} s]\n")
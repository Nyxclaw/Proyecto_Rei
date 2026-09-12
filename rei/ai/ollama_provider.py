import requests
import json


class OllamaProvider:
    def __init__(
        self,
        model: str = "qwen3:4b-instruct",
        host: str = "http://localhost:11434",

    ):
        self.model = model
        self.host = host

        self.last_metrics = {
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "load_duration": 0,
            "prompt_eval_duration": 0,
            "eval_duration": 0,
            "total_duration": 0,
            "tokens_per_second": 0.0,
        }

        self.system_prompt = (
            "Eres Rei, una asistente virtual de escritorio. "
            "Respondes siempre en español, salvo que el usuario pida otro idioma. "
            "Tu estilo es conciso y directo. "
            "Para acciones simples, responde de forma mínima. "
            "No afirmes que una acción fue completada si no has recibido "
            "una confirmación explícita de éxito desde una herramienta. "
            "Si una petición es ambigua y requiere una acción, pide una aclaración breve. "
            "No inventes resultados de acciones ni estados del sistema."
        )

        self.messages = [
            {
                "role": "system",
                "content": self.system_prompt,
            }
        ]

        self.last_metrics = {
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "total_tokens": 0,
                    "load_duration": 0,
                    "prompt_eval_duration": 0,
                    "eval_duration": 0,
                    "total_duration": 0,
        }

    def get_last_metrics(self) -> dict:
        return self.last_metrics.copy()

    def chat(self, message: str) -> str:
        url = f"{self.host}/api/chat"

        user_message = {
            "role": "user",
            "content": message,
        }

        pending_messages = self.messages + [user_message]

        data = {
            "model": self.model,
            "messages": pending_messages,
            "stream": False,
        }

        try:
            response = requests.post(
                url,
                json=data,
                timeout=60,
            )

            response.raise_for_status()

            result = response.json()

            input_tokens = result.get("prompt_eval_count", 0)
            output_tokens = result.get("eval_count", 0)

            self.last_metrics = {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens,
                "load_duration": result.get("load_duration", 0),
                "prompt_eval_duration": result.get("prompt_eval_duration", 0),
                "eval_duration": result.get("eval_duration", 0),
                "total_duration": result.get("total_duration", 0),
            }

            assistant_message = result["message"]["content"]

            self.messages = pending_messages

            self.messages.append(
                {
                    "role": "assistant",
                    "content": assistant_message,
                }
            )

            return assistant_message

        except requests.exceptions.ConnectionError:
            return "Error: no se pudo conectar con Ollama."

        except requests.exceptions.Timeout:
            return "Error: Ollama tardó demasiado en responder."

        except requests.exceptions.HTTPError as error:
            return f"Error HTTP de Ollama: {error}"

        except (KeyError, ValueError, TypeError):
            return "Error: Ollama devolvió una respuesta inesperada."

        except requests.exceptions.RequestException as error:
            return f"Error de comunicación con Ollama: {error}"

    def chat_stream(self, message: str):
        url = f"{self.host}/api/chat"

        user_message = {
            "role": "user",
            "content": message,
        }

        pending_messages = self.messages + [user_message]

        data = {
            "model": self.model,
            "messages": pending_messages,
            "stream": True,
        }

        try:
            response = requests.post(
                url,
                json=data,
                timeout=60,
                stream=True,
            )

            response.raise_for_status()

            assistant_message = ""

            for line in response.iter_lines():
                if not line:
                    continue

                data_chunk = json.loads(line.decode("utf-8"))

                content = data_chunk.get("message", {}).get("content", "")

                if content:
                    assistant_message += content
                    yield content

                if data_chunk.get("done"):
                    self._update_metrics(data_chunk)

            self.messages = pending_messages

            self.messages.append(
                {
                    "role": "assistant", "content": assistant_message,
                }
            )

        except requests.exceptions.ConnectionError:
            yield "\nError: no se pudo conectar con Ollama."

        except requests.exceptions.Timeout:
            yield "\nError: Ollama tardó demasiado en responder."

        except requests.exceptions.RequestException as error:
            yield f"\nError de comunicación con Ollama: {error}"

        except (json.JSONDecodeError, KeyError, TypeError):
            yield "\nError: Ollama devolvió una respuesta inesperada."        
                

    def chat_with_tools(self, message: str, tools: list) -> dict:
        url = f"{self.host}/api/chat"

        user_message = {
            "role": "user",
            "content": message,
        }

        pending_messages = self.messages + [user_message]

        data = {
            "model": self.model,
            "messages": pending_messages,
            "tools": tools,
            "stream": False,
        }

        try:
            response = requests.post(
                url,
                json=data,
                timeout=60,
            )

            response.raise_for_status()

            result = response.json()
            self._update_metrics(result)

            return result["message"]

        except requests.exceptions.ConnectionError:
            return {
                "error": "No se pudo conectar con Ollama."
            }

        except requests.exceptions.Timeout:
            return {
                "error": "Ollama tardó demasiado en responder."
            }

        except requests.exceptions.RequestException as error:
            return {
                "error": f"Error de comunicación con Ollama: {error}"
            }

        except (KeyError, ValueError, TypeError):
            return {
                "error": "Ollama devolvió una respuesta inesperada."
            }

    def clear_history(self):
        self.messages = [
            {
                "role": "system",
                "content": self.system_prompt,
            }
        ]

    def get_last_metrics(self) -> dict:
        return self.last_metrics.copy()

    def _update_metrics(self, result: dict) -> None:
        input_tokens = result.get("prompt_eval_count", 0)
        output_tokens = result.get("eval_count", 0)

        eval_duration = result.get("eval_duration", 0)  

        if eval_duration > 0:
            eval_seconds = eval_duration / 1_000_000_000
            tokens_per_second = output_tokens / eval_seconds
        else:
            tokens_per_second = 0.0

        self.last_metrics = {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "load_duration": result.get("load_duration", 0),
            "prompt_eval_duration": result.get(
                "prompt_eval_duration",
            0,
        ),
        "eval_duration": eval_duration,
        "total_duration": result.get("total_duration", 0),
        "tokens_per_second": tokens_per_second,
    }
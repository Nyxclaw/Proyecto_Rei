import contextlib
import io
import json
import unittest
from unittest.mock import Mock, patch

import requests

from rei.ai.ollama_provider import OllamaProvider
from main import main


def response(input_tokens=100, output_tokens=20):
    result = {
        "message": {"role": "assistant", "content": "Hola"},
        "done": True,
        "prompt_eval_count": input_tokens,
        "eval_count": output_tokens,
        "eval_duration": 2_000_000_000,
    }
    reply = Mock()
    reply.json.return_value = result
    reply.iter_lines.return_value = [json.dumps(result).encode()]
    return reply


class MetricsTests(unittest.TestCase):
    @patch("rei.ai.ollama_provider.requests.post")
    def test_all_chat_modes_use_same_units_and_schema(self, post):
        for mode in ("chat", "chat_stream", "chat_with_tools"):
            with self.subTest(mode=mode):
                post.return_value = response()
                brain = OllamaProvider()
                if mode == "chat_stream":
                    self.assertEqual("".join(brain.chat_stream("Hola")), "Hola")
                elif mode == "chat_with_tools":
                    brain.chat_with_tools("Hola", [])
                else:
                    brain.chat("Hola")
                metrics = brain.get_last_metrics()
                self.assertTrue(metrics["available"])
                self.assertEqual(metrics["total_tokens"], 120)
                self.assertEqual(metrics["tokens_per_second"], 10.0)

    @patch("rei.ai.ollama_provider.requests.post")
    def test_failed_request_does_not_reuse_previous_metrics(self, post):
        for mode in ("chat", "chat_stream", "chat_with_tools"):
            with self.subTest(mode=mode):
                post.side_effect = None
                post.return_value = response()
                brain = OllamaProvider()
                brain.chat("Hola")
                post.side_effect = requests.exceptions.ConnectionError()
                if mode == "chat_stream":
                    list(brain.chat_stream("Otra"))
                elif mode == "chat_with_tools":
                    brain.chat_with_tools("Otra", [])
                else:
                    brain.chat("Otra")
                self.assertFalse(brain.get_last_metrics()["available"])

    @patch("rei.ai.ollama_provider.requests.post")
    def test_incomplete_stream_does_not_commit_history_or_metrics(self, post):
        post.return_value = response()
        post.return_value.iter_lines.return_value = [
            b'{"message": {"content": "Parcial"}, "done": false}'
        ]
        brain = OllamaProvider()
        output = "".join(brain.chat_stream("Hola"))
        self.assertIn("Error", output)
        self.assertEqual(len(brain.messages), 1)
        self.assertFalse(brain.get_last_metrics()["available"])

    @patch("rei.ai.ollama_provider.requests.post")
    def test_missing_counts_are_unavailable_and_zero_duration_is_safe(self, post):
        post.return_value = response()
        post.return_value.json.return_value["eval_duration"] = 0
        brain = OllamaProvider()
        brain.chat("Hola")
        self.assertEqual(brain.get_last_metrics()["tokens_per_second"], 0.0)
        del post.return_value.json.return_value["eval_count"]
        brain.chat("Otra")
        self.assertFalse(brain.get_last_metrics()["available"])

    @patch("rei.ai.ollama_provider.requests.post")
    def test_cli_starts_and_refreshes_metrics_for_each_turn(self, post):
        post.side_effect = [response(100, 20), response(160, 30)]
        output = io.StringIO()
        with patch("builtins.input", side_effect=["Hola", "Otra", "salir"]):
            with contextlib.redirect_stdout(output):
                main()
        self.assertEqual(post.call_count, 2)
        self.assertIn("entrada: 100 | salida: 20", output.getvalue())
        self.assertIn("entrada: 160 | salida: 30", output.getvalue())

    @patch("rei.ai.ollama_provider.requests.post")
    def test_reset_preserves_system_prompt_and_clears_metrics(self, post):
        post.return_value = response()
        brain = OllamaProvider()
        brain.chat("Hola")
        brain.clear_history()
        self.assertEqual(brain.messages, [{"role": "system", "content": brain.system_prompt}])
        self.assertFalse(brain.get_last_metrics()["available"])


if __name__ == "__main__":
    unittest.main()

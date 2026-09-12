from copy import deepcopy
import json
import unittest
from unittest.mock import Mock, patch

from rei.ai.ollama_provider import OllamaProvider
from rei.core.conversation import Conversation
from rei.core.tool_router import ToolRouter
from rei.tools import application_tools as apps


def call(name="open_application", application="notepad"):
    return {"function": {"name": name, "arguments": {"application": application}}}


def message(calls=None, content=""):
    return {"role": "assistant", "content": content, "tool_calls": calls or []}


class ConversationTests(unittest.TestCase):
    def setup_conversation(self, replies):
        brain = Mock()
        brain.messages = [{"role": "system", "content": "Rei"}]
        brain.request_message.side_effect = replies
        brain.get_last_metrics.return_value = {
            "available": True, "total_tokens": 30,
            "input_tokens": 20, "output_tokens": 10,
        }
        router = Mock()
        router.execute.return_value = {
            "success": True, "status": "opened", "message": "Ventana confirmada.",
            "evidence": {"hwnd": 123, "pid": 456},
        }
        return Conversation(brain, router), brain, router

    def test_result_returns_to_model_and_history_and_metrics_are_complete(self):
        c, brain, router = self.setup_conversation([message([call()], "Ya lo abrí"), message(content="Listo")])
        result = c.run_turn("Abre Bloc de notas")
        router.execute.assert_called_once_with("open_application", {"application": "notepad"})
        self.assertEqual(result["answer"], "Listo")
        self.assertEqual(result["total_tokens"], 60)
        sent = brain.request_message.call_args_list[1].args[0]
        self.assertEqual([m["role"] for m in sent], ["system", "user", "assistant", "tool"])
        self.assertEqual(json.loads(sent[-1]["content"])["evidence"]["hwnd"], 123)
        self.assertEqual(c.messages[-1]["content"], "Listo")

    def test_normal_conversation_never_calls_router(self):
        c, _, router = self.setup_conversation([message(content="Hola")])
        self.assertEqual(c.run_turn("Hola")["answer"], "Hola")
        router.execute.assert_not_called()

    def test_failure_cannot_be_reworded_as_success(self):
        c, _, router = self.setup_conversation([message([call()]), message(content="Listo, abierto")])
        router.execute.return_value = {"success": False, "message": "Ventana no confirmada."}
        self.assertEqual(c.run_turn("Abre")["answer"], "Ventana no confirmada.")

    def test_duplicate_calls_do_not_reexecute(self):
        c, _, router = self.setup_conversation([message([call()]), message([call()]), message(content="Listo")])
        result = c.run_turn("Abre")
        router.execute.assert_called_once()
        self.assertEqual(result["actions"][1]["result"]["error"], "duplicate_call")

    def test_call_limit_and_round_limit(self):
        c, brain, router = self.setup_conversation([
            message([call(), call(application="calculator")]),
            message([call(application="bloc de notas")]),
        ])
        c.max_calls = 1
        # Bloque demasiado grande: ninguna apertura parcial.
        c.run_turn("Abre ambas")
        router.execute.assert_not_called()
        c, brain, router = self.setup_conversation([message([call()]), message([call(application="calculator")])])
        c.max_rounds = 1
        result = c.run_turn("Abre")
        router.execute.assert_called_once()
        self.assertEqual(brain.request_message.call_args_list[1].args[1], [])
        self.assertEqual(result["actions"][-1]["result"]["error"], "tool_limit")

    def test_model_failure_after_execution_keeps_result_without_retry(self):
        c, _, router = self.setup_conversation([message([call()]), {"error": "Ollama desconectado"}])
        result = c.run_turn("Abre")
        router.execute.assert_called_once()
        self.assertIn("Ollama desconectado", result["answer"])
        self.assertTrue(any(m["role"] == "tool" for m in c.messages))

    def test_uncertainty_disables_followup_tools_even_with_another_alias(self):
        c, brain, router = self.setup_conversation([
            message([call()]), message([call(application="bloc de notas")]),
        ])
        router.execute.return_value = {"success": False, "status": "unconfirmed"}
        c.run_turn("Abre")
        router.execute.assert_called_once()
        self.assertEqual(brain.request_message.call_args_list[1].args[1], [])

    def test_default_cli_accepts_a_natural_instruction(self):
        import contextlib
        import io
        from main import main
        with patch("main.Conversation") as factory:
            factory.return_value.run_turn.return_value = {
                "answer": "Listo", "calls": [], "total_tokens": 0,
                "metrics_complete": True,
            }
            with patch("builtins.input", side_effect=["Abre la calculadora", "salir"]):
                with contextlib.redirect_stdout(io.StringIO()):
                    main()
            self.assertEqual(factory.return_value.run_turn.call_args.args[0], "Abre la calculadora")


class ApplicationTests(unittest.TestCase):
    def test_unknown_and_wrong_type_are_rejected(self):
        with patch.object(apps.subprocess, "Popen") as launch:
            for value in ("powershell", "notepad.exe & calc.exe", 3, ""):
                self.assertFalse(apps.open_application(value)["success"])
            launch.assert_not_called()

    @patch.object(apps.subprocess, "Popen")
    @patch.object(apps, "find_application_window")
    def test_existing_window_does_not_launch_another(self, find, launch):
        find.return_value = {"hwnd": 1, "pid": 2}
        result = apps.open_application("bloc de notas")
        self.assertEqual(result["status"], "already_open")
        launch.assert_not_called()

    @patch.object(apps.subprocess, "Popen")
    @patch.object(apps, "find_application_window")
    def test_launch_requires_window_evidence(self, find, launch):
        find.side_effect = [None, {"hwnd": 1, "pid": 2}]
        result = apps.open_application("calculadora")
        self.assertTrue(result["success"])
        self.assertEqual(result["status"], "opened")
        self.assertEqual(result["evidence"]["hwnd"], 1)
        self.assertEqual(len(launch.call_args.args[0]), 1)

    @patch.object(apps.subprocess, "Popen")
    @patch.object(apps, "find_application_window", return_value=None)
    def test_started_process_without_window_is_not_success(self, find, launch):
        with patch.object(apps, "VERIFY_TIMEOUT", 0):
            self.assertEqual(apps.open_application("notepad")["status"], "unconfirmed")
        launch.assert_called_once()

    @patch.object(apps.subprocess, "Popen", side_effect=OSError())
    @patch.object(apps, "find_application_window", return_value=None)
    def test_launch_failure(self, find, launch):
        self.assertEqual(apps.open_application("notepad")["error"], "launch_failed")

    @patch.object(apps.subprocess, "Popen")
    @patch.object(apps, "find_application_window", side_effect=OSError())
    def test_inaccessible_desktop_does_not_launch_blindly(self, find, launch):
        self.assertEqual(apps.open_application("notepad")["error"], "verification_unavailable")
        launch.assert_not_called()

    def test_router_honors_failure_dictionary_and_permissions(self):
        router = ToolRouter()
        tool = Mock(return_value={"success": False, "error": "window_not_confirmed"})
        router.tools["open_application"]["function"] = tool
        self.assertFalse(router.execute("open_application", {"application": "notepad"})["success"])
        tool.reset_mock()
        router.permission_manager = Mock()
        router.permission_manager.is_allowed.return_value = False
        self.assertEqual(router.execute("open_application", {})["error"], "permission_denied")
        tool.assert_not_called()
        self.assertEqual(router.execute("missing", {})["error"], "tool_not_found")
        self.assertEqual(router.execute([], {})["error"], "invalid_arguments")


class ProviderTests(unittest.TestCase):
    @patch("rei.ai.ollama_provider.requests.post")
    def test_rejects_malformed_tool_arguments_before_execution(self, post):
        response = Mock()
        post.return_value.__enter__ = Mock(return_value=response)
        post.return_value.__exit__ = Mock(return_value=False)
        response.json.return_value = {"done": True, "message": message([call()])}
        response.json.return_value["message"]["tool_calls"][0]["function"]["arguments"] = "bad"
        brain = OllamaProvider()
        self.assertIn("error", brain.request_message([], []))


if __name__ == "__main__":
    unittest.main()

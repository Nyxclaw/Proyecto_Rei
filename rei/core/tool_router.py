from rei.permissions.permission_manager import (
    PermissionLevel,
    PermissionManager,
)
from rei.tools.application_tools import open_application


class ToolRouter:
    def __init__(self):
        self.permission_manager = PermissionManager()

        self.tools = {
            "open_application": {
                "function": open_application,
                "permission": PermissionLevel.P1_SAFE,
            }
        }

    def execute(self, tool_name: str, arguments: dict) -> dict:
        tool = self.tools.get(tool_name)

        if tool is None:
            return {
                "success": False,
                "error": "tool_not_found",
                "message": f"La herramienta '{tool_name}' no existe.",
            }

        permission = tool["permission"]

        if not self.permission_manager.is_allowed(permission):
            return {
                "success": False,
                "error": "permission_denied",
                "message": "La acción no está permitida.",
            }

        function = tool["function"]

        try:
            result = function(**arguments)

        except TypeError as error:
            return {
                "success": False,
                "error": "invalid_arguments",
                "message": str(error),
            }

        except Exception as error:
            return {
                "success": False,
                "error": "tool_execution_error",
                "message": str(error),
            }

        return {
            "success": bool(result),
            "result": result,
        }
import subprocess

from rei.permissions.permission_manager import (
    PermissionLevel,
    PermissionManager,
)


permission_manager = PermissionManager()


def open_application(application: str) -> bool:
    permission = PermissionLevel.P1_SAFE

    if not permission_manager.is_allowed(permission):
        return False

    applications = {
        "notepad": "notepad.exe",
        "bloc de notas": "notepad.exe",
        "calculator": "calc.exe",
        "calculadora": "calc.exe",
    }

    executable = applications.get(application.lower())

    if executable is None:
        return False

    try:
        subprocess.Popen([executable])
        return True

    except OSError:
        return False
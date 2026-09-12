import os
from pathlib import Path
import subprocess
import time

from rei.permissions.permission_manager import PermissionLevel, PermissionManager
from rei.tools.windows_apps import find_application_window


APPLICATIONS = {
    "notepad": ("Bloc de notas", "notepad.exe", ("notepad.exe",)),
    "calculator": ("Calculadora", "calc.exe", ("calculatorapp.exe", "calculator.exe", "calc.exe")),
}
ALIASES = {"bloc de notas": "notepad", "calculadora": "calculator"}
VERIFY_TIMEOUT = 8.0


def open_application(application: str) -> dict:
    if not isinstance(application, str) or not application.strip():
        return {"success": False, "status": "failed", "error": "invalid_arguments"}
    key = application.strip().lower()
    key = ALIASES.get(key, key)
    if key not in APPLICATIONS:
        return {"success": False, "status": "failed", "error": "application_not_supported",
                "message": "Sólo están disponibles Bloc de notas y Calculadora."}
    if not PermissionManager().is_allowed(PermissionLevel.P1_SAFE):
        return {"success": False, "status": "failed", "error": "permission_denied"}
    if os.name != "nt":
        return {"success": False, "status": "failed", "error": "windows_required"}
    label, executable, process_names = APPLICATIONS[key]
    try:
        existing = find_application_window(process_names)
    except OSError:
        return {"success": False, "status": "unconfirmed", "error": "verification_unavailable",
                "message": "No se pudo consultar Windows; no se intentó abrir la aplicación."}
    if existing:
        return {"success": True, "status": "already_open", "application": label,
                "message": "La aplicación ya tenía una ventana visible.", "evidence": existing}
    try:
        # Ruta fija: ningún argumento del modelo se interpreta como comando.
        subprocess.Popen([str(Path(os.environ["SystemRoot"]) / "System32" / executable)])
    except OSError:
        return {"success": False, "status": "failed", "application": label,
                "error": "launch_failed", "message": "Windows no pudo iniciar la aplicación."}
    deadline = time.monotonic() + VERIFY_TIMEOUT
    while True:
        try:
            window = find_application_window(process_names)
        except OSError:
            window = None
            break
        if window:
            return {"success": True, "status": "opened", "application": label,
                    "message": "Se detectó una ventana visible después de solicitar la apertura.",
                    "evidence": window}
        if time.monotonic() >= deadline:
            break
        time.sleep(0.2)
    return {"success": False, "status": "unconfirmed", "application": label,
            "error": "window_not_confirmed",
            "message": "Se solicitó la apertura, pero no se pudo confirmar su ventana. No se reintentó."}

"""Consulta ventanas Win32 sin dependencias adicionales ni acceso al shell."""
import ctypes
from ctypes import wintypes
import os
from pathlib import Path


def find_application_window(process_names: tuple[str, ...]) -> dict | None:
    if os.name != "nt":
        raise OSError("La comprobación de ventanas requiere Windows.")
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    dwm = ctypes.WinDLL("dwmapi")
    callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    user32.EnumWindows.argtypes = [callback_type, wintypes.LPARAM]
    user32.EnumWindows.restype = wintypes.BOOL
    user32.EnumChildWindows.argtypes = [wintypes.HWND, callback_type, wintypes.LPARAM]
    user32.IsWindowVisible.argtypes = [wintypes.HWND]
    user32.IsWindowVisible.restype = wintypes.BOOL
    user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel32.OpenProcess.restype = wintypes.HANDLE
    kernel32.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
    kernel32.QueryFullProcessImageNameW.restype = wintypes.BOOL
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    dwm.DwmGetWindowAttribute.argtypes = [wintypes.HWND, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD]
    dwm.DwmGetWindowAttribute.restype = ctypes.c_long
    windows = Path(os.environ["SystemRoot"]).resolve()
    packages = Path(os.environ["ProgramFiles"]) / "WindowsApps"
    found = []

    def inspect(hwnd):
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        handle = kernel32.OpenProcess(0x1000, False, pid.value)
        if not handle:
            return None
        try:
            size = wintypes.DWORD(32768)
            buffer = ctypes.create_unicode_buffer(size.value)
            if not kernel32.QueryFullProcessImageNameW(handle, 0, buffer, ctypes.byref(size)):
                return None
            path = Path(buffer.value)
            if path.name.lower() not in process_names:
                return None
            # Rechazar ejecutables homónimos fuera de las instalaciones de Windows.
            system_app = path.parent == windows / "System32"
            package_app = path.is_relative_to(packages) and any(
                part.lower().startswith(("microsoft.windowsnotepad_", "microsoft.windowscalculator_"))
                for part in path.relative_to(packages).parts[:-1]
            )
            if system_app or package_app:
                return {"pid": pid.value, "executable": path.name}
        finally:
            kernel32.CloseHandle(handle)
        return None

    @callback_type
    def visit(hwnd, _):
        if not user32.IsWindowVisible(hwnd):
            return True
        cloaked = wintypes.DWORD()
        if dwm.DwmGetWindowAttribute(hwnd, 14, ctypes.byref(cloaked), ctypes.sizeof(cloaked)) != 0:
            return True  # No afirmar visibilidad si no pudimos comprobarla.
        if cloaked.value:
            return True
        match = inspect(hwnd)
        if match is None:
            # Algunas aplicaciones empaquetadas usan una ventana contenedora.
            children = []

            @callback_type
            def visit_child(child, _):
                if user32.IsWindowVisible(child):
                    candidate = inspect(child)
                    if candidate:
                        children.append(candidate)
                return True

            user32.EnumChildWindows(hwnd, visit_child, 0)
            match = children[0] if children else None
        if match:
            found.append({"hwnd": int(hwnd), **match})
        return True

    if not user32.EnumWindows(visit, 0):
        raise ctypes.WinError(ctypes.get_last_error())
    return found[0] if found else None

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "open_application",
            "description": (
                "Abre una aplicación conocida instalada en Windows. "
                "Utilízala cuando el usuario solicite explícitamente "
                "abrir o iniciar una aplicación."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "application": {
                        "type": "string",
                        "description": (
                            "Nombre de la aplicación que se desea abrir. "
                            "Ejemplos: notepad, calculator."
                        ),
                    }
                },
                "required": ["application"],
            },
        },
    }
]
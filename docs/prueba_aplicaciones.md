# Probar aperturas desde la conversación

Esta versión permite escribir una orden a Rei, recibir una solicitud estructurada
de Qwen, comprobar permisos, abrir una aplicación y devolver la evidencia al modelo.
Las aplicaciones disponibles son Bloc de notas y Calculadora. No se ejecutan comandos
arbitrarios ni se guardan o modifican documentos.

## Obtener esta versión

Desde PowerShell, en tu repositorio local:

```powershell
git status
git fetch origin
git switch fix/token-metrics
git pull --ff-only origin fix/token-metrics
```

Si la rama no existe localmente, usa
`git switch --track origin/fix/token-metrics` en lugar del primer `git switch`.
Si `git status` muestra trabajo pendiente, consérvalo con un commit antes de cambiar
de rama. No uses `reset --hard` ni fuerces el cambio. Esta rama reutiliza el PR #1;
todavía no se ha integrado en develop.

Con tu entorno virtual habitual activado, Python 3.11, las dependencias existentes
instaladas y Ollama ejecutándose con qwen3:4b-instruct:

```powershell
python -m unittest discover -s tests -v
python main.py --debug
```

Ejecuta Rei desde tu escritorio normal de Windows. Servicios, sesiones sin escritorio
o entornos aislados pueden no tener acceso a las ventanas. No es necesario ejecutarlo
como administrador. `--debug` muestra el resultado y HWND/PID de la ventana comprobada.

## Prueba manual

1. Cierra Bloc de notas y Calculadora tú mismo, conservando antes cualquier trabajo.
2. Escribe: **Abre el Bloc de notas.** Debe aparecer su ventana; el resultado debe
   mostrar `opened`, `success: True`, y evidencia con `hwnd`, `pid` y `executable`.
3. Repite la misma orden. Debe mostrar `already_open` y no crear otra ventana.
4. Escribe: **Abre la calculadora.** Comprueba visualmente la ventana y su evidencia.
5. Escribe: **¿Cuánto es dos más dos?** Debe responder sin ejecutar herramientas.
6. Escribe: **Abre Photoshop.** Debe explicar la limitación o devolver
   `application_not_supported`; no debe abrirlo.
7. Escribe: **reiniciar**. Se limpia el contexto; no se cierran las aplicaciones.
8. Escribe: **salir**. Se termina Rei; no se cierran tus aplicaciones.

Un turno de apertura normalmente requiere dos llamadas a Ollama: decidir la herramienta
y redactar la respuesta después de recibir el resultado. Los contadores se muestran por
llamada y se suman para el turno. Esa suma incluye contexto repetido y no mide VRAM.

## Qué significa la verificación

| Estado | Significado |
| --- | --- |
| `opened` | Tras solicitar la apertura, se detectó una ventana visible del ejecutable permitido. |
| `already_open` | Ya existía una ventana visible; no se lanzó otra instancia. |
| `failed` | La petición no es válida, no está permitida o Windows rechazó el inicio. |
| `unconfirmed` | No se pudo comprobar la ventana; no se afirma éxito. |

`verification_unavailable` significa que la consulta a Windows falló antes de abrir;
no hubo intento de lanzamiento. `window_not_confirmed` significa que sí se solicitó
la apertura pero no se confirmó dentro de aproximadamente ocho segundos o falló
la consulta posterior. La aplicación podría aparecer más tarde. Rei no la vuelve a
lanzar automáticamente en ese turno.

La evidencia comprueba una ventana visible, asociada a un ejecutable de las ubicaciones
permitidas de Windows. No se basa en el título, que puede cambiar de idioma o contener
nombres de archivos. Incluye ventanas contenedoras de aplicaciones empaquetadas.
No demuestra que la aplicación responda a todos sus controles, esté en primer plano,
ni que esa ventana haya sido creada exclusivamente por nuestra petición. Una ventana
minimizada puede seguir siendo visible según Win32. No se cierran ventanas para probar.

## Cómo está dividido el código

- `main.py`: recibe tu texto y muestra la respuesta, verificaciones y métricas.
- `rei/core/conversation.py`: conserva el historial, coordina solicitudes y resultados,
  limita a dos rondas de herramientas y cuatro solicitudes por turno, y bloquea duplicados.
- `rei/ai/ollama_provider.py`: se comunica con Ollama; no ejecuta aplicaciones.
- `rei/core/tool_router.py`: valida el nombre/argumentos y consulta PermissionManager.
- `rei/tools/application_tools.py`: usa la lista permitida, inicia y espera la ventana.
- `rei/tools/windows_apps.py`: consulta ventanas/procesos mediante ctypes y las APIs Win32.

Los resultados de herramientas se guardan con rol `tool` y regresan a Qwen. Si la
redacción del modelo contradice un fallo, el Core muestra el resultado de la herramienta.
Si Ollama falla después de ejecutar, se conserva la evidencia y no se repite la acción.

El ciclo de herramientas espera mensajes completos antes de mostrarlos, para no presentar
una frase de éxito previa a la ejecución. El chat de texto con streaming sigue disponible:

```powershell
python main.py --text-only
```

## Validación de esta entrega

Las pruebas automáticas usan dobles de Windows/Ollama para comprobar aperturas confirmadas,
ventanas existentes, fallos, tiempo agotado, permisos, duplicados, límites, historial y métricas.
No equivalen a observar una ventana real. En el entorno de ejecución de Codex, EnumWindows
no pudo enumerar el escritorio. Qwen real sí solicitó ambas herramientas, recibió la falta
de confirmación y devolvió el control. La apertura visual desde una terminal interactiva
queda pendiente de esta prueba manual. No se declara validada de extremo a extremo.

Referencias técnicas:
- https://docs.ollama.com/capabilities/tool-calling
- https://learn.microsoft.com/windows/win32/api/winuser/nf-winuser-enumwindows
- https://learn.microsoft.com/windows/win32/api/winuser/nf-winuser-getwindowthreadprocessid
- https://learn.microsoft.com/windows/win32/api/winbase/nf-winbase-queryfullprocessimagenamew

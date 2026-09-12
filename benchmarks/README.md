# Medición de tokens

Desde la raíz del repositorio, con Python 3.11 y las dependencias existentes:

```powershell
python -m unittest discover -s tests -v
python -m benchmarks.token_usage --output token_benchmark.json
```

La segunda orden requiere Ollama activo con qwen3:4b-instruct. Ejecuta dos preguntas
relacionadas en una conversación nueva, sin herramientas ni cambios de configuración.
Guarda preguntas, respuestas, contadores, latencia observada y el estado de carga
que informa /api/ps. Las respuestas y los tiempos pueden variar entre ejecuciones.

El chat habitual sigue disponible con `python main.py`. Escribe `reiniciar` para
borrar la conversación activa.

## Interpretación

- Entrada: instrucciones de sistema, historial y pregunta, incluyendo el formato del modelo.
- Salida: tokens generados en esa petición.
- Total: entrada + salida de esa petición; no es un contador de memoria ni de tokens únicos.
- Tokens/s: salida dividida entre eval_duration, convertida de nanosegundos a segundos.
- Primer fragmento: latencia observada por el cliente; un fragmento no necesariamente es un token.
- Tiempo total del cliente: incluye comunicación y procesamiento, no sólo generación.
- available=false: faltan métricas de la petición actual; no significa consumo cero.

Conservar historial hace crecer la entrada. Dos preguntas sólo ofrecen una línea
base; no validan conversaciones largas, herramientas, memoria persistente ni picos
de RAM/VRAM. El script observa la memoria reportada por Ollama después de responder,
no mide el pico del proceso.

## Criterios iniciales para el prototipo

Bajo: respuestas proporcionadas a la tarea y contexto con amplio margen.
Mantener la configuración y registrar una línea base.

Regular: respuestas útiles, pero el historial crece y reduce el margen.
Establecer un presupuesto de entrada y reservar espacio de salida; decidir qué
historial conservar o resumir, preservando instrucciones y ciclos de herramientas.

Excesivo: respuestas desproporcionadas, contexto próximo al límite, truncamiento
o presión de memoria/latencia observada. Revisar prompts e historial, limitar
salida y ajustar contexto con mediciones. No aumentar automáticamente num_ctx.

No existen umbrales universales de tokens para estas categorías.
Reducir tokens no garantiza por sí solo reducir la VRAM asignada al modelo.

Referencias:
- https://docs.ollama.com/api/usage
- https://docs.ollama.com/context-length

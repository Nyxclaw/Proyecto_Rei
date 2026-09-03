# Proyecto IA Rei

Proyecto IA Rei es un asistente virtual de escritorio basado en inteligencia
artificial, diseñado principalmente para Windows y construido bajo una
arquitectura local-first.

El objetivo es desarrollar una asistente capaz de interactuar mediante lenguaje
natural, ejecutar acciones controladas sobre el sistema, comprender el contexto
del escritorio y evolucionar progresivamente hacia un agente personal supervisado.

> Estado actual: desarrollo inicial / Proof of Concept.

---

## Objetivos principales

Proyecto IA Rei busca implementar progresivamente:

- Interacción mediante lenguaje natural.
- Ejecución local de modelos LLM.
- Control seguro de aplicaciones.
- Automatización de rutinas.
- Interacción por voz.
- Wake word: "Oye Rei".
- Síntesis de voz.
- Screen Awareness.
- Memoria persistente.
- Avatar interactivo.
- Tool Calling.
- Sistema estricto de permisos.
- Arquitectura modular.
- Funcionamiento offline siempre que sea posible.

---

## Principios de diseño

### Local First

Las funciones esenciales de Rei deben funcionar localmente sin depender de
servicios externos o pagos recurrentes.

### Modular

Los componentes principales deben poder sustituirse independientemente.

Ejemplos:

- LLM
- Speech-to-Text
- Text-to-Speech
- Wake Word
- Avatar
- Vision Model

### Security by Design

El LLM nunca tendrá acceso directo e ilimitado al sistema.

Las acciones serán ejecutadas mediante herramientas controladas por Rei Core y
un Permission Engine.

### Responsiveness First

Las acciones simples deben utilizar rutas rápidas y evitar razonamiento
innecesario mediante modelos grandes.

---

## Hardware de desarrollo

Actualmente el proyecto se desarrolla sobre:

- AMD Ryzen 5 5600X
- NVIDIA GeForce RTX 5060
- 8 GB VRAM
- 32 GB RAM
- SSD NVMe
- Windows

---

## Arquitectura conceptual

```text
User
 │
 ▼
Rei Core
 │
 ├── LLM
 ├── Tool Router
 ├── Permission Engine
 ├── Memory
 ├── Voice
 ├── Screen Awareness
 └── Avatar
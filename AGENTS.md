# Proyecto IA Rei — Agent Instructions

## Project Goal

Proyecto IA Rei is a local-first Windows desktop AI assistant.

The assistant uses a local LLM through Ollama and is designed
to progressively support voice, desktop tools, screen awareness,
memory and an interactive avatar.

## Current Architecture

- Python 3.11
- Ollama
- qwen3:4b-instruct
- OllamaProvider
- ToolRouter
- PermissionManager
- structured tool calling

## Core Design Rules

1. Local-first. Core functionality must work without cloud services.

2. The LLM never directly controls Windows.

3. All actions must go through ToolRouter.

4. ToolRouter must consult PermissionManager before execution.

5. Never expose unrestricted CMD, PowerShell or arbitrary shell execution.

6. Permission policy:

   - P0_READ_ONLY: automatic
   - P1_SAFE: automatic
   - P2_MODIFICATION: requires explicit confirmation
   - P3_DESTRUCTIVE: requires strict explicit confirmation
   - P4_CRITICAL: prohibited

7. File modification, moving, renaming and deletion must show
   the exact affected path before confirmation.

8. Rei must never claim an action succeeded until the Tool
   returned success.

9. Simple successful actions should receive minimal responses,
   such as "Listo" or "Claro".

10. Preserve modularity. LLM, voice, memory, tools and avatar
    must remain replaceable components.

## Current Milestone

M0 — Rei Core Proof of Concept.

Currently completed:

- local Qwen conversation
- streaming
- conversation context
- basic system prompt
- open_application Tool
- PermissionManager
- ToolRouter
- Qwen structured tool calls
- Qwen → ToolRouter → Windows execution

Current work:

- instrument token usage and inference metrics

Next work:

- complete Tool Result → LLM → final response cycle

## Safety

Do not introduce unrestricted shell execution.

Do not weaken PermissionManager to make implementation easier.

Do not allow the LLM to bypass ToolRouter.
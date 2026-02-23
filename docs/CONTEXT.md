# Project Context

This project consists of building a desktop Integrated Development Environment (IDE) for a compiler course.

## Current Phase

We are implementing Phase 1: IDE only.

The compiler does NOT exist yet and will be implemented in a later phase.

For now:

- The IDE must use mock data.
- No real compiler logic should be implemented.
- The architecture must allow future integration of a Python CLI compiler via system calls.

## Technologies

- Language: Python
- UI Framework: PySide6 (Qt for Python)
- Target OS: Windows
- Application Type: Native Desktop Application (NOT web)

## Architecture Rules

1. IDE and compiler must be separate modules.
2. IDE invokes the compiler only through system calls.
3. Compiler must run independently from the IDE via CLI.
4. Communication must occur through files and command-line arguments.
5. No compiler logic should be embedded inside the IDE.

## Language Rules

- All documentation in /docs must be in English (technical), except UI labels which must be Spanish.
- All user interface text must be in Spanish.
- All source code (Python) must use Spanish identifiers (variables, functions, classes), with short, readable names.
- Avoid overly long names; prefer concise Spanish identifiers (e.g., `arch`, `ruta`, `txt`, `tok`, `err`, `arb`, `sim`).
- Use consistent abbreviations:
  - tokens: `tok`
  - errors: `err`
  - symbols: `sim`
  - AST/tree: `arb`
  - intermediate code: `ir`
  - output: `sal`


## UI Goals

The interface must be:

- Modern
- Minimalist
- Professional
- Dark theme
- Inspired by modern IDEs like VSCode
- Not similar to DevC++

## Deliverable Goal

Provide a fully functional IDE layout ready to integrate with a compiler in Phase 2.

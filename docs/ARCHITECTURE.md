# System Architecture

## High-Level Structure

The system consists of two main modules:

1. IDE (PySide6 Desktop Application)
2. Compiler (Python CLI Application)

## Folder Structure

ide/
    main.py
    ui/
    services/
    models/

compiler/
    compiler.py

docs/

## Execution Flow

1. User edits code in the editor.
2. User selects a compilation phase.
3. IDE saves the source file.
4. IDE invokes compiler via system call.
5. Compiler generates output files.
6. IDE reads files and displays results.

## IDE Services

A service called CompilerService will:

- Execute compiler commands (future)
- Provide mock outputs (current phase)
- Read output files
- Send data to UI

## Separation of Responsibilities

UI Layer:
- Rendering
- User interaction

Services Layer:
- Compiler communication

Models Layer:
- Data structures

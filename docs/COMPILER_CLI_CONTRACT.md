# Compiler CLI Contract

The compiler will be an independent Python program executable from the command line.

## Base Command

python compiler.py --phase <phase> --in <input_file> --out <output_file>

## Supported Phases

- lexical
- syntax
- semantic
- ir
- run

## Examples

python compiler.py --phase lexical --in program.src --out tokens.json

python compiler.py --phase ir --in program.src --out ir.txt

## IDE Responsibility

The IDE will:

- Execute commands
- Read generated files
- Display results

The IDE will NOT implement compilation logic.

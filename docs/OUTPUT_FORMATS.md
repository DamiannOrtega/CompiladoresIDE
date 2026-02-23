# Compiler Output Formats

## Tokens

tokens.json

[
  {
    "lexeme": "int",
    "type": "KEYWORD",
    "line": 1,
    "column": 1
  }
]

## Errors

errors.json

[
  {
    "type": "syntax",
    "line": 3,
    "column": 10,
    "message": "Unexpected token"
  }
]

## Symbol Table

symbols.json

[
  {
    "name": "x",
    "type": "int",
    "scope": "global",
    "line": 1
  }
]

## Intermediate Code

ir.txt

t1 = a + b
x = t1

## Execution Output

output.txt

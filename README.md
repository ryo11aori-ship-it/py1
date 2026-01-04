# py1 Language

A strict, single-character token dialect of Python.
Designed for obfuscation and CTF challenges.

## Specification

1. **Definition Phase**: Define identifiers using `@v char 'value'`. Ends with `$`.
2. **Body Phase**: Only 1-char identifiers allowed.
   - `"` (double quotes) only for strings.
   - Strings must be 1-char length inside body (expanded at compile time).
   - Python keywords are mapped to reserved single characters (see `spec_consts.py`).

## Usage

```bash
python py1.py source.py1 > out.py
python out.py

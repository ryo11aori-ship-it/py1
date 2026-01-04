#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# py1.py -- py1 transpiler (safe bootstrap version)

import sys
import tokenize
import io
import re
import json
import codecs
from tokenize import TokenInfo
from spec_consts import RESERVED_MAP, RESERVED_CHARS

had_error = False


def error(msg, line_num=None):
    global had_error
    prefix = f"[Line {line_num}] " if line_num else ""
    sys.stderr.write(f"Error: {prefix}{msg}\n")
    had_error = True


def _maybe_fix_latin1_bytes_as_str(s: str) -> str:
    """
    Try to recover strings that are actually UTF-8 bytes
    incorrectly represented as Latin-1 characters.
    """
    if not s:
        return s

    high = sum(1 for ch in s if ord(ch) > 127)
    if high == 0:
        return s

    if high / len(s) < 0.3:
        return s

    try:
        b = bytes(ord(ch) & 0xFF for ch in s)
        candidate = b.decode("utf-8")
    except Exception:
        return s

    # Heuristic: if CJK appears, accept
    for ch in candidate:
        if "\u3040" <= ch <= "\u30ff" or "\u4e00" <= ch <= "\u9fff":
            return candidate

    return s


def parse_definitions(source_text):
    """
    Parse @v definitions.
    """
    lines = source_text.splitlines()
    symbol_table = {}
    body_lines = []
    is_body = False

    def_pattern = re.compile(r"^@v\s+(.)\s+'([^']*)'\s*$")

    for i, line in enumerate(lines):
        line_num = i + 1
        stripped = line.strip()

        if not is_body:
            if stripped == "$":
                is_body = True
                continue
            if not stripped or stripped.startswith("#"):
                continue

            m = def_pattern.match(stripped)
            if not m:
                error("Invalid syntax in definition phase.", line_num)
                continue

            key = m.group(1)
            raw_value = m.group(2)

            try:
                value = codecs.decode(raw_value, "unicode_escape")
            except Exception:
                value = raw_value

            value = _maybe_fix_latin1_bytes_as_str(value)

            if key in RESERVED_CHARS:
                error(f"Character '{key}' is reserved.", line_num)
            if key in symbol_table:
                error(f"Redefinition of '{key}'.", line_num)

            symbol_table[key] = value
        else:
            body_lines.append(line)

    if not is_body:
        error("Separator '$' not found.", 0)

    return symbol_table, "\n".join(body_lines)


def transpile(source_path):
    global had_error
    had_error = False

    with open(source_path, "r", encoding="utf-8") as f:
        source_text = f.read()

    symbol_table, body_text = parse_definitions(source_text)

    if had_error:
        sys.exit(1)

    stream = io.BytesIO(body_text.encode("utf-8")).readline
    tokens = list(tokenize.tokenize(stream))

    new_tokens = []

    for tok in tokens:
        if tok.type == tokenize.NAME:
            if len(tok.string) != 1:
                error(
                    f"Invalid identifier '{tok.string}'. Only 1-char allowed.",
                    tok.start[0],
                )
                new_tokens.append(tok)
                continue

            if tok.string in RESERVED_MAP:
                new_tokens.append(
                    TokenInfo(
                        tok.type,
                        RESERVED_MAP[tok.string],
                        tok.start,
                        tok.end,
                        tok.line,
                    )
                )
            elif tok.string in symbol_table:
                new_tokens.append(
                    TokenInfo(
                        tok.type,
                        symbol_table[tok.string],
                        tok.start,
                        tok.end,
                        tok.line,
                    )
                )
            else:
                error(f"Undefined identifier '{tok.string}'.", tok.start[0])
                new_tokens.append(tok)

        elif tok.type == tokenize.STRING:
            if tok.string.startswith('"') and tok.string.endswith('"'):
                inner = tok.string[1:-1]
                if inner in symbol_table:
                    safe = json.dumps(symbol_table[inner], ensure_ascii=False)
                    new_tokens.append(
                        TokenInfo(
                            tokenize.STRING,
                            safe,
                            tok.start,
                            tok.end,
                            tok.line,
                        )
                    )
                else:
                    new_tokens.append(tok)
            else:
                new_tokens.append(tok)
        else:
            new_tokens.append(tok)

    if had_error:
        sys.exit(1)

    result = tokenize.untokenize(new_tokens)
    return result.decode("utf-8") if isinstance(result, bytes) else result


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python py1.py <source_file>")
        sys.exit(1)

    print(transpile(sys.argv[1]))
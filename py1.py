#!/usr/bin/env python3
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

def parse_definitions(source_text):
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
            if not stripped:
                continue
            if stripped.startswith("#"):
                continue
            m = def_pattern.match(stripped)
            if not m:
                error("Invalid syntax in definition phase.", line_num)
                continue
            key = m.group(1)
            raw_value = m.group(2)

            # バックスラッシュがある場合のみデコード
            value = raw_value
            if "\\" in raw_value:
                try:
                    value = codecs.decode(raw_value, "unicode_escape")
                except Exception:
                    pass

            if key in RESERVED_CHARS:
                error(f"Character '{key}' is reserved by system.", line_num)
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
    try:
        tokens = list(tokenize.tokenize(stream))
    except tokenize.TokenError as e:
        error(f"Tokenization failed: {e}", 0)
        sys.exit(1)

    new_tokens = []
    for tok in tokens:
        t_type = tok.type
        t_str = tok.string
        t_start = tok.start
        t_end = tok.end
        t_line = tok.line

        # IDENTIFIERS (NAME) -- must be single-char identifiers
        if t_type == tokenize.NAME:
            if len(t_str) != 1:
                error(
                    f"Invalid identifier '{t_str}'. Only 1-char identifiers allowed.",
                    t_start[0]
                )
                # keep original token so error context remains
                new_tokens.append(TokenInfo(t_type, t_str, t_start, t_end, t_line))
                continue

            # Replace reserved names or symbol table entries
            if t_str in RESERVED_MAP:
                repl = RESERVED_MAP[t_str]
                new_tokens.append(TokenInfo(t_type, repl, t_start, t_end, t_line))
            elif t_str in symbol_table:
                repl = symbol_table[t_str]
                # symbol_table values are raw strings (without quotes). If you want
                # them treated as string tokens in the output, ensure they include quotes.
                new_tokens.append(TokenInfo(t_type, repl, t_start, t_end, t_line))
            else:
                error(f"Undefined identifier '{t_str}'.", t_start[0])
                new_tokens.append(TokenInfo(t_type, t_str, t_start, t_end, t_line))

        # STRING LITERALS -- must be double-quoted and non-empty in body
        elif t_type == tokenize.STRING:
            # Ensure it's a double-quoted literal (source style)
            if not (t_str.startswith('"') and t_str.endswith('"')):
                error("Only double quotes allowed in body.", t_start[0])
                new_tokens.append(TokenInfo(t_type, t_str, t_start, t_end, t_line))
                continue

            inner = t_str[1:-1]
            # In your language, body string literals must be exactly one character.
            # Here we accept non-empty strings in definitions, but for body ensure non-empty.
            if len(inner) < 1:
                error("Empty string", t_start[0])
                new_tokens.append(TokenInfo(t_type, t_str, t_start, t_end, t_line))
                continue

            # If inner char (or token) names a defined symbol, substitute its value (JSON-escaped)
            if inner in symbol_table:
                safe_val = json.dumps(symbol_table[inner])  # will include enclosing quotes
                new_tokens.append(TokenInfo(tokenize.STRING, safe_val, t_start, t_end, t_line))
            else:
                new_tokens.append(TokenInfo(t_type, t_str, t_start, t_end, t_line))

        # Everything else: copy through unchanged
        else:
            new_tokens.append(TokenInfo(t_type, t_str, t_start, t_end, t_line))

    if had_error:
        sys.exit(1)

    result = tokenize.untokenize(new_tokens)
    if isinstance(result, bytes):
        compiled = result.decode("utf-8")
    else:
        compiled = result
    return compiled

def main():
    if len(sys.argv) < 2:
        sys.stderr.write("Usage: python py1.py <source_file>\n")
        sys.exit(1)
    src = sys.argv[1]
    compiled = transpile(src)
    sys.stdout.buffer.write(compiled.encode("utf-8"))

if __name__ == "__main__":
    main()
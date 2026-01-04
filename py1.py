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

def _maybe_fix_latin1_bytes_as_str(s: str) -> str:
    if not s:
        return s
    high = sum(1 for ch in s if ord(ch) > 127)
    if high == 0:
        return s
    if high / len(s) < 0.3:
        return s
    try:
        b = bytes((ord(ch) & 0xFF) for ch in s)
        candidate = b.decode("utf-8")
    except Exception:
        return s
    for ch in candidate:
        if "\u3040" <= ch <= "\u30ff" or "\u4e00" <= ch <= "\u9fff":
            return candidate
    return s

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
            try:
                value = codecs.decode(raw_value, "unicode_escape")
            except Exception:
                value = raw_value
            value = _maybe_fix_latin1_bytes_as_str(value)
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
        if t_type == tokenize.NAME:
            if len(t_str) != 1:
                error(f"Invalid identifier '{t_str}'. Only 1-char identifiers allowed.", t_start[0])
                new_tokens.append(TokenInfo(tok.type, tok.string, tok.start, tok.end, tok.line))
                continue
            if t_str in RESERVED_MAP:
                repl = RESERVED_MAP[t_str]
                new_tokens.append(TokenInfo(t_type, repl, t_start, t_end, t_line))
            elif t_str in symbol_table:
                repl = symbol_table[t_str]
                new_tokens.append(TokenInfo(t_type, repl, t_start, t_end, t_line))
            else:
                error(f"Undefined identifier '{t_str}'.", t_start[0])
                new_tokens.append(TokenInfo(tok.type, tok.string, tok.start, tok.end, tok.line))
        elif t_type == tokenize.STRING:
            if not (t_str.startswith('"') and t_str.endswith('"')):
                error("Only double quotes allowed in body.", t_start[0])
                new_tokens.append(TokenInfo(tok.type, tok.string, tok.start, tok.end, tok.line))
                continue
            inner = t_str[1:-1]
            if len(inner) != 1:
                error(f"String literal must be exactly 1 char. Found: '{inner}'", t_start[0])
                new_tokens.append(TokenInfo(tok.type, tok.string, tok.start, tok.end, tok.line))
                continue
            if inner in symbol_table:
                # 【ここを変更】ensure_ascii=False を削除！
                # これでASCIIエスケープ出力 (\uXXXX) になり、文字化けしなくなる
                safe_val = json.dumps(symbol_table[inner])
                new_tokens.append(TokenInfo(tokenize.STRING, safe_val, t_start, t_end, t_line))
            else:
                new_tokens.append(TokenInfo(tokenize.STRING, t_str, t_start, t_end, t_line))
        else:
            new_tokens.append(TokenInfo(tok.type, tok.string, tok.start, tok.end, tok.line))
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

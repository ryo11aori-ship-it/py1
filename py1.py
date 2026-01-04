#!/usr/bin/env python3
# py1.py -- py1 トランスパイラ（Unicode/エスケープ復元強化版）
# - codecs.decode(..., 'unicode_escape') で \xNN / \uXXXX を展開
# - 展開後に「Latin-1 表現のバイト列が str として残っている」場合は
#   latin-1 -> utf-8 の復元を試みる（これが今回の \u00e6...\u0097... を直す）

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
    s が「各バイトが U+00xx として入っている文字列」（Latin-1-as-str）なら
    latin-1 -> utf-8 デコードを試み、結果にCJKなどの想定文字が含まれれば採用する。
    そうでない場合は元の s を返す。
    """
    # 判断基準：文字列に U+0080..U+00FF の文字が一定比率以上含まれ、
    #         UTF-8 として解釈すると CJK が現れる（簡易ヒューリスティック）
    if not s:
        return s

    # count high-ord chars (above 127)
    high = sum(1 for ch in s if ord(ch) > 127)
    if high == 0:
        return s

    ratio = high / len(s)
    # 比率が低いならおそらく普通の Unicode（例: 単語にアクセント）なので無視
    if ratio < 0.3:
        return s

    try:
        # treat each codepoint 0..255 as a byte value
        b = bytes((ord(ch) & 0xFF) for ch in s)
        candidate = b.decode('utf-8')
    except Exception:
        return s

    # 判定：candidate にCJK（漢字ひらがなカタカナ）等が含まれるか
    if any('\u3040' <= ch <= '\u30ff' or '\u4e00' <= ch <= '\u9fff' for ch in candidate):
        return candidate
    # そうでなければ採用しない
    return s

def parse_definitions(source_text):
    """
r"""
parse @v 定義部.
- 右辺は生の文字列だが、'\x27' や '\uXXXX' のようなエスケープ表現が
  含まれる可能性がある（compiler.py1 がそのように出力するため）。
- ここではまず unicode_escape を使ってエスケープを展開し、
  さらに必要なら latin-1->utf-8 の復元を試みる。
"""
    lines = source_text.splitlines()
    symbol_table = {}
    body_lines = []
    is_body = False

    # @v <char> '<...>'
    def_pattern = re.compile(r"^@v\s+(.)\s+'([^']*)'\s*$")

    for i, line in enumerate(lines):
        line_num = i + 1
        stripped = line.strip()

        if not is_body:
            if stripped == '$':
                is_body = True
                continue
            if not stripped:
                continue
            if stripped.startswith('#'):
                continue

            m = def_pattern.match(stripped)
            if not m:
                error("Invalid syntax in definition phase.", line_num)
                continue

            key = m.group(1)
            raw_value = m.group(2)

            # 1) \xNN や \uXXXX 等を展開 (例: '\x27' -> "'")
            try:
                value = codecs.decode(raw_value, 'unicode_escape')
            except Exception:
                # 万が一失敗したら raw_value をそのまま使う
                value = raw_value

            # 2) もし value が「バイト列をそのまま str 化した」様に見えるなら
            #    latin-1 -> utf-8 復元を試みる
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

    with open(source_path, 'r', encoding='utf-8') as f:
        source_text = f.read()

    symbol_table, body_text = parse_definitions(source_text)

    if had_error:
        sys.exit(1)

    stream = io.BytesIO(body_text.encode('utf-8')).readline
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
                # safe_val: 実体Unicodeを含む安定した Python 文字列リテラル（常にダブルクォート）
                safe_val = json.dumps(symbol_table[inner], ensure_ascii=False)
                new_tokens.append(TokenInfo(tokenize.STRING, safe_val, t_start, t_end, t_line))
            else:
                new_tokens.append(TokenInfo(tokenize.STRING, t_str, t_start, t_end, t_line))
        else:
            new_tokens.append(TokenInfo(tok.type, tok.string, tok.start, tok.end, tok.line))

    if had_error:
        sys.exit(1)

    result = tokenize.untokenize(new_tokens)
    if isinstance(result, bytes):
        return result.decode('utf-8')
    return result

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python py1.py <source_file>")
        sys.exit(1)
    try:
        compiled_python = transpile(sys.argv[1])
        print(compiled_python)
    except Exception as e:
        sys.stderr.write(str(e) + "\n")
        sys.exit(1)
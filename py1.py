#!/usr/bin/env python3
# py1.py -- py1 トランスパイラ（修正版：unicode_escape と \xNN の扱い改善）

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
    """
    parse @v 定義部.
    - 右辺は生の文字列だが、'\x27' や '\uXXXX' のようなエスケープ表現が
      含まれる可能性がある（compiler.py1 がそう書くため）。
    - そこで codecs.decode(..., 'unicode_escape') を用いて、\xNN / \uNNNN 等を展開する。
      既に実体の Unicode が入っている場合は何も壊さない（安全）。
    """
    lines = source_text.splitlines()
    symbol_table = {}
    body_lines = []
    is_body = False

    # 定義は @v <1char> '<any>' （単一引用で囲まれた右辺）
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
                # 続行してデバッグ情報を集める
                continue

            key = m.group(1)
            raw_value = m.group(2)

            # ここが重要：raw_value 中の \xNN や \uNNNN を正しく展開する
            try:
                value = codecs.decode(raw_value, 'unicode_escape')
            except Exception:
                # もし何かおかしければ、raw_value をそのまま使う
                value = raw_value

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

    # ソース読み取り（UTF-8 前提）
    with open(source_path, 'r', encoding='utf-8') as f:
        source_text = f.read()

    symbol_table, body_text = parse_definitions(source_text)

    # 定義フェーズで重大なエラーがあればここで止める
    if had_error:
        sys.exit(1)

    # tokenize はバイトストリームの readline を要求
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
            # NAME は 1 文字のみ許可
            if len(t_str) != 1:
                error(f"Invalid identifier '{t_str}'. Only 1-char identifiers allowed.", t_start[0])
                # 続行のためそのまま追加
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
                # 続行するために元トークンを追加
                new_tokens.append(TokenInfo(tok.type, tok.string, tok.start, tok.end, tok.line))

        elif t_type == tokenize.STRING:
            # 本文ではダブルクォートのみ許可："x"
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
                # 実体 Unicode を含む安全な Python 文字列リテラルを生成（常にダブルクォート）
                safe_val = json.dumps(symbol_table[inner], ensure_ascii=False)
                new_tokens.append(TokenInfo(tokenize.STRING, safe_val, t_start, t_end, t_line))
            else:
                new_tokens.append(TokenInfo(tokenize.STRING, t_str, t_start, t_end, t_line))

        else:
            # 他トークンは TokenInfo に統一して追加
            new_tokens.append(TokenInfo(tok.type, tok.string, tok.start, tok.end, tok.line))

    # 最終エラーチェック
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
        # CI ではこの出力をファイルにリダイレクトしている想定
        print(compiled_python)
    except Exception as e:
        sys.stderr.write(str(e) + "\n")
        sys.exit(1)
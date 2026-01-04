#!/usr/bin/env python3
# py1.py -- py1 (あなたの1文字言語) -> Python トランスパイラ（安定版）
# - 定義フェーズでは Unicode をそのまま扱う（unicode_escape を使用しない）
# - トークンは常に TokenInfo に正規化して untokenize に渡す
# - 文字列は json.dumps(..., ensure_ascii=False) でダブルクォート表現に正規化

import sys
import tokenize
import io
import re
import json
from tokenize import TokenInfo
from spec_consts import RESERVED_MAP, RESERVED_CHARS


def error(msg, line_num=None):
    """致命的エラーを出して終了"""
    prefix = f"[Line {line_num}] " if line_num else ""
    sys.stderr.write(f"Error: {prefix}{msg}\n")
    sys.exit(1)


def parse_definitions(source_text):
    """
    定義フェーズを解析して symbol_table と本文テキストを返す。
    仕様:
      - 各定義は行の先頭で @v <1char> '<任意の文字列>' の形式
      - 右辺は生の文字列（エスケープはここでは解釈しない）
      - '$' 行で定義フェーズ終了（以降が本文）
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

            match = def_pattern.match(stripped)
            if not match:
                error("Invalid syntax in definition phase.", line_num)

            char_key = match.group(1)
            raw_value = match.group(2)

            # **重要**: 定義フェーズでは原則としてエスケープ解釈を行わない
            # ユーザーが明示的に \ を含めたい場合の扱いは将来仕様化する
            value = raw_value

            if char_key in RESERVED_CHARS:
                error(f"Character '{char_key}' is reserved by system.", line_num)
            if char_key in symbol_table:
                error(f"Redefinition of '{char_key}'.", line_num)

            symbol_table[char_key] = value
        else:
            body_lines.append(line)

    if not is_body:
        error("Separator '$' not found.")

    return symbol_table, "\n".join(body_lines)


def transpile(source_path):
    """
    .py1 ファイルを読み、トークンレベルで展開して Python ソース文字列を返す。
    - NAME トークンは 1 文字のみ許可
    - NAME が RESERVED_MAP にあればキーワードに置換
    - NAME が symbol_table にあれば対応名に置換
    - STRING トークン (本文) は "x" のみ許可（中身1文字）
      - 中身が定義済みのキーなら json.dumps(value, ensure_ascii=False) で文字列リテラルを生成
    """
    with open(source_path, 'r', encoding='utf-8') as f:
        source_text = f.read()

    symbol_table, body_text = parse_definitions(source_text)

    # tokenize.tokenize はバイトストリームの readlines を要求する
    stream = io.BytesIO(body_text.encode('utf-8')).readline
    tokens = list(tokenize.tokenize(stream))
    new_tokens = []

    for tok in tokens:
        t_type = tok.type
        t_str = tok.string
        t_start = tok.start
        t_end = tok.end
        t_line = tok.line

        # NAME トークン（識別子）
        if t_type == tokenize.NAME:
            if len(t_str) != 1:
                error(f"Invalid identifier '{t_str}'. Only 1-char identifiers allowed.", t_start[0])

            if t_str in RESERVED_MAP:
                repl = RESERVED_MAP[t_str]
                new_tok = TokenInfo(t_type, repl, t_start, t_end, t_line)
                new_tokens.append(new_tok)
            elif t_str in symbol_table:
                repl = symbol_table[t_str]
                new_tok = TokenInfo(t_type, repl, t_start, t_end, t_line)
                new_tokens.append(new_tok)
            else:
                error(f"Undefined identifier '{t_str}'.", t_start[0])

        # 文字列リテラル（本文では "x" のみ）
        elif t_type == tokenize.STRING:
            # 本文ではダブルクォートのみ許可（例："H"）
            if not (t_str.startswith('"') and t_str.endswith('"')):
                error("Only double quotes allowed in body.", t_start[0])

            inner = t_str[1:-1]
            if len(inner) != 1:
                error(f"String literal must be exactly 1 char. Found: '{inner}'", t_start[0])

            if inner in symbol_table:
                # safe_val はダブルクォートで囲まれた有効な Python 文字列リテラル（Unicode そのまま）
                safe_val = json.dumps(symbol_table[inner], ensure_ascii=False)
                new_tok = TokenInfo(tokenize.STRING, safe_val, t_start, t_end, t_line)
                new_tokens.append(new_tok)
            else:
                # 定義されていない1文字リテラルは、そのまま（例: 数字や 'a' のようなリテラル）
                new_tok = TokenInfo(tokenize.STRING, t_str, t_start, t_end, t_line)
                new_tokens.append(new_tok)

        else:
            # 他のトークンも TokenInfo に正規化して追加
            new_tok = TokenInfo(tok.type, tok.string, tok.start, tok.end, tok.line)
            new_tokens.append(new_tok)

    result = tokenize.untokenize(new_tokens)
    # untokenize は bytes または str を返すことがあるため安全に処理する
    if isinstance(result, bytes):
        return result.decode('utf-8')
    return result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python py1.py <source_file>")
        sys.exit(1)

    try:
        compiled_python = transpile(sys.argv[1])
        # トランスパイル結果を標準出力へ（CI ではこれをファイルへリダイレクトしている想定）
        print(compiled_python)
    except Exception as e:
        sys.stderr.write(str(e) + "\n")
        sys.exit(1)
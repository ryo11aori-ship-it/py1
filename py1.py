import sys
import tokenize
import io
import re
from spec_consts import RESERVED_MAP, RESERVED_CHARS

def error(msg, line_num=None):
    """エラーを出力して終了"""
    prefix = f"[Line {line_num}] " if line_num else ""
    sys.stderr.write(f"Error: {prefix}{msg}\n")
    sys.exit(1)

def parse_definitions(source_text):
    """
    ソースコード全体を受け取り、定義フェーズ(@v)と本文フェーズ($以降)に分離し、
    シンボルテーブルを構築する。
    """
    lines = source_text.splitlines()
    symbol_table = {}
    body_lines = []
    is_body = False
    
    # 正規表現: @v <1文字> '<文字列>'
    # 厳格な構文チェックのため、余計な空白等は許容しつつ形式を守らせる
    def_pattern = re.compile(r"^@v\s+([a-zA-Z_])\s+'([^']*)'\s*$")

    for i, line in enumerate(lines):
        line_num = i + 1
        stripped = line.strip()

        if not is_body:
            if stripped == '$':
                is_body = True
                continue
            
            if not stripped: # 空行は無視
                continue
            
            if stripped.startswith('#'): # コメント
                continue

            match = def_pattern.match(stripped)
            if match:
                char_key = match.group(1)
                value = match.group(2)

                # 予約語チェック
                if char_key in RESERVED_CHARS:
                    error(f"Character '{char_key}' is reserved by system.", line_num)
                
                # 重複定義チェック（必要なら）
                if char_key in symbol_table:
                    error(f"Redefinition of '{char_key}'.", line_num)

                symbol_table[char_key] = value
            else:
                # 定義フェーズで @v 以外（かつ空行・コメント以外）はエラー
                error("Invalid syntax in definition phase. Expected @v definition or $.", line_num)
        else:
            body_lines.append(line)

    if not is_body:
        error("Separator '$' not found.")

    return symbol_table, "\n".join(body_lines)

def transpile(source_path):
    with open(source_path, 'r', encoding='utf-8') as f:
        source_text = f.read()

    symbol_table, body_text = parse_definitions(source_text)
    
    # 本文を字句解析用のバッファにする
    # tokenizeモジュールはbytesを期待することがあるためencode
    tokens = list(tokenize.tokenize(io.BytesIO(body_text.encode('utf-8')).readline))
    
    new_tokens = []
    
    for tok in tokens:
        token_type = tok.type
        token_string = tok.string
        start = tok.start
        end = tok.end
        line_text = tok.line

        if token_type == tokenize.NAME:
            # NAMEトークンの長さチェック
            if len(token_string) > 1:
                # Pythonの標準キーワードかどうか確認（tokenizeはキーワードもNAMEとして出す場合がある）
                # しかし仕様上、本文中の識別子は全て1文字である必要がある。
                error(f"Invalid identifier '{token_string}'. Only 1-char identifiers allowed in body.", start[0])

            # マッピング処理
            if token_string in RESERVED_MAP:
                # 予約語への展開
                new_val = RESERVED_MAP[token_string]
                new_tokens.append((token_type, new_val, start, end, line_text))
            elif token_string in symbol_table:
                # ユーザー定義への展開
                new_val = symbol_table[token_string]
                new_tokens.append((token_type, new_val, start, end, line_text))
            else:
                error(f"Undefined identifier '{token_string}'.", start[0])

        elif token_type == tokenize.STRING:
            # 文字列リテラルのチェックと展開
            # 仕様: "" のみ許可、中身は1文字。
            if not (token_string.startswith('"') and token_string.endswith('"')):
                error("Only double quotes allowed for strings in body.", start[0])
            
            # 中身を取り出す ("H" -> H)
            inner = token_string[1:-1]
            if len(inner) != 1:
                error(f"String literal must contain exactly 1 char. Found: '{inner}'", start[0])
            
            # 中身を展開: 定義テーブルにあればその中身に置換
            if inner in symbol_table:
                expanded_content = symbol_table[inner]
                # 元が "H" で H='Hello' なら "Hello" になる
                new_val = f'"{expanded_content}"'
                new_tokens.append((token_type, new_val, start, end, line_text))
            else:
                # テーブルになければそのまま（ただし仕様上エラーにすべきか？
                # 仕様書に「複数文字を本文で使う場合は...定義フェーズで」とあるので
                # ここでは未定義の1文字リテラルはそのまま通すか、厳格にするならエラー。
                # 安全側に倒して「そのまま通す」実装にする（" "スペース等ありえるため）
                new_tokens.append((tokenize.STRING, token_string, start, end, line_text))

        else:
            # その他のトークン（演算子、数値、改行、インデント等）はそのまま
            new_tokens.append(tok)

    # トークン列からコードを再構築
    result_code = tokenize.untokenize(new_tokens)
    return result_code

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python py1.py <source_file>")
        sys.exit(1)
    
    try:
        compiled_python = transpile(sys.argv[1])
        print(compiled_python) # 標準出力へ吐く
    except Exception as e:
        sys.stderr.write(str(e) + "\n")
        sys.exit(1)

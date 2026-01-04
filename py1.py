import sys
import tokenize
import io
import re
from spec_consts import RESERVED_MAP, RESERVED_CHARS

def error(msg, line_num=None):
    prefix = f"[Line {line_num}] " if line_num else ""
    sys.stderr.write(f"Error: {prefix}{msg}\n")
    sys.exit(1)

def parse_definitions(source_text):
    lines = source_text.splitlines()
    symbol_table = {}
    body_lines = []
    is_body = False
    
    # Unicode1文字を許可
    def_pattern = re.compile(r"^@v\s+(.)\s+'([^']*)'\s*$")

    for i, line in enumerate(lines):
        line_num = i + 1
        stripped = line.strip()

        if not is_body:
            if stripped == '$':
                is_body = True
                continue
            if not stripped: continue
            if stripped.startswith('#'): continue

            match = def_pattern.match(stripped)
            if match:
                char_key = match.group(1)
                value = match.group(2)

                if char_key in RESERVED_CHARS:
                    error(f"Character '{char_key}' is reserved by system.", line_num)
                if char_key in symbol_table:
                    error(f"Redefinition of '{char_key}'.", line_num)
                symbol_table[char_key] = value
            else:
                error("Invalid syntax in definition phase.", line_num)
        else:
            body_lines.append(line)

    if not is_body:
        error("Separator '$' not found.")

    return symbol_table, "\n".join(body_lines)

def transpile(source_path):
    with open(source_path, 'r', encoding='utf-8') as f:
        source_text = f.read()

    symbol_table, body_text = parse_definitions(source_text)
    
    tokens = list(tokenize.tokenize(io.BytesIO(body_text.encode('utf-8')).readline))
    new_tokens = []
    
    for tok in tokens:
        token_type = tok.type
        token_string = tok.string
        start = tok.start
        end = tok.end
        line_text = tok.line

        if token_type == tokenize.NAME:
            if len(token_string) > 1:
                error(f"Invalid identifier '{token_string}'. Only 1-char identifiers allowed.", start[0])

            if token_string in RESERVED_MAP:
                new_tokens.append((token_type, RESERVED_MAP[token_string], start, end, line_text))
            elif token_string in symbol_table:
                new_tokens.append((token_type, symbol_table[token_string], start, end, line_text))
            else:
                error(f"Undefined identifier '{token_string}'.", start[0])

        elif token_type == tokenize.STRING:
            # 本文中の文字列は "" のみ、かつ中身は1文字のみ
            if not (token_string.startswith('"') and token_string.endswith('"')):
                error("Only double quotes allowed in body.", start[0])
            
            inner = token_string[1:-1]
            if len(inner) != 1:
                error(f"String literal must be exactly 1 char. Found: '{inner}'", start[0])
            
            if inner in symbol_table:
                # 【修正箇所】 展開時にエスケープ処理を追加！
                # \ と " をエスケープして、構文破壊を防ぐ
                raw_val = symbol_table[inner]
                safe_val = raw_val.replace('\\', '\\\\').replace('"', '\\"')
                new_tokens.append((token_type, f'"{safe_val}"', start, end, line_text))
            else:
                new_tokens.append((tokenize.STRING, token_string, start, end, line_text))

        else:
            new_tokens.append(tok)

    result_code = tokenize.untokenize(new_tokens)
    return result_code.decode('utf-8')

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

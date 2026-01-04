import sys
import tokenize
import io
import re
import json
from tokenize import TokenInfo
from spec_consts import RESERVED_MAP, RESERVED_CHARS


def error_die(msg_txt, line_num=0):
    if line_num:
        msg = "Error: [Line {}] {}\n".format(line_num, msg_txt)
    else:
        msg = "Error: {}\n".format(msg_txt)
    sys.stderr.write(msg)
    sys.exit(1)


def parse_definitions(source_text):
    lines = source_text.splitlines()
    symbols = {}
    body_lines = []
    in_body = False

    # @v <char> '<string>'
    def_re = re.compile(r"^@v\s+(.)\s+'([^']*)'\s*$")

    for idx, line in enumerate(lines):
        line_str = line.strip()
        line_no = idx + 1

        if not in_body:
            if line_str == "$":
                in_body = True
                continue

            if not line_str or line_str.startswith("#"):
                continue

            m = def_re.match(line_str)
            if not m:
                error_die("Invalid def", line_no)

            key = m.group(1)
            val = m.group(2)

            try:
                val = val.encode("utf-8").decode("unicode_escape")
            except Exception:
                pass

            if key in RESERVED_CHARS:
                error_die("Reserved: {}".format(key), line_no)
            if key in symbols:
                error_die("Redefined: {}".format(key), line_no)

            symbols[key] = val
        else:
            body_lines.append(line)

    if not in_body:
        error_die("No $ separator", 0)

    joined_body = "\n".join(body_lines)
    return symbols, joined_body


def transpile(path):
    source_text = open(path, "r", encoding="utf-8").read()
    symbols, body = parse_definitions(source_text)

    stream = io.BytesIO(body.encode("utf-8")).readline
    tokens = list(tokenize.tokenize(stream))

    new_tokens = []

    for tok in tokens:
        t_type = tok.type
        t_str = tok.string
        t_start = tok.start

        if t_type == tokenize.NAME:
            if len(t_str) != 1:
                error_die("Long name: {}".format(t_str), t_start[0])

            if t_str in RESERVED_MAP:
                new_tokens.append(
                    TokenInfo(t_type, RESERVED_MAP[t_str], tok.start, tok.end, tok.line)
                )
            elif t_str in symbols:
                new_tokens.append(
                    TokenInfo(t_type, symbols[t_str], tok.start, tok.end, tok.line)
                )
            else:
                error_die("Undefined: {}".format(t_str), t_start[0])

        elif t_type == tokenize.STRING:
            if not (t_str.startswith("\"") and t_str.endswith("\"")):
                error_die("Use double quotes", t_start[0])

            inner = t_str[1:-1]
            if len(inner) != 1:
                error_die("String len != 1", t_start[0])

            if inner in symbols:
                # ★ json.dumps は常にダブルクォートを使う → 正規化保証
                lit = json.dumps(symbols[inner], ensure_ascii=False)
                new_tokens.append(
                    TokenInfo(tokenize.STRING, lit, tok.start, tok.end, tok.line)
                )
            else:
                new_tokens.append(tok)

        else:
            new_tokens.append(tok)

    result = tokenize.untokenize(new_tokens)

    if isinstance(result, bytes):
        result = result.decode("utf-8")

    return result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python py1.py <source_file>")
        sys.exit(1)

    print(transpile(sys.argv[1]))
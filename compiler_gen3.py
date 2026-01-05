import sys

sys.stderr.write("DEBUG: Using SMART compiler_gen3.py v8 (Indent+Keywords)\n")

def compile(src):
    lines = src.split('\n')
    macros = {}
    
    in_code = False
    
    for line in lines:
        # インデントがない状態での判定用
        stripped = line.strip()
        if not stripped:
            continue
            
        if stripped == '$':
            in_code = True
            continue
            
        if not in_code:
            # 定義パート
            if stripped.startswith('@v'):
                parts = stripped.split()
                if len(parts) >= 3:
                    k = parts[1]
                    v = " ".join(parts[2:])
                    macros[k] = v
        else:
            # コードパート
            
            # 1. インデントを保護して分離
            indent = ""
            content = line
            if len(line) > len(line.lstrip()):
                indent = line[:len(line) - len(line.lstrip())]
                content = line.lstrip()
            
            # 2. マクロ置換 (長いもの優先)
            for k in sorted(macros.keys(), key=len, reverse=True):
                if k in content:
                    content = content.replace(k, macros[k])
            
            # 3. 1文字キーワードの翻訳 (行頭のみ)
            tokens = content.split()
            if tokens:
                head = tokens[0]
                rest = content[len(head):]
                
                new_head = head
                if head == 'm': new_head = 'import'
                elif head == 'd': new_head = 'def'
                elif head == 'i': new_head = 'if'
                elif head == 'e:': new_head = 'else:'
                elif head == 'f': new_head = 'for'
                elif head == 'r': new_head = 'return'
                elif head == 'C': new_head = 'continue'
                # w (while) はマクロで定義されることが多いが念のため
                elif head == 'w': new_head = 'while'
                
                content = new_head + rest

            # 出力 (インデント + 変換後コード)
            print(indent + content)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.stderr.write("Usage: python compiler_gen3.py <file>\n")
        sys.exit(1)
        
    with open(sys.argv[1], 'r', encoding='utf-8') as f:
        src = f.read()
        
    compile(src)

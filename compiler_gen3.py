import sys

# 【重要】実行されているバージョンを確認するためのデバッグ表示
print("--- BOOTSTRAP COMPILER v6 RUNNING ---")

def compile(src):
    lines = src.split('\n')
    macros = {}
    
    in_code = False
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
            
        if line == '$':
            in_code = True
            continue
            
        if not in_code:
            # 定義パート
            if line.startswith('@v'):
                parts = line.split()
                if len(parts) >= 3:
                    k = parts[1]
                    v = " ".join(parts[2:])
                    # 【修正】チェックを完全撤廃。
                    # ここでエラーを出さないことで、compiler_ir.py1 の修正を生かす。
                    macros[k] = v
        else:
            # コードパート：マクロ置換
            # 長いキーから順に置換 (誤爆防止)
            for k in sorted(macros.keys(), key=len, reverse=True):
                if k in line:
                    line = line.replace(k, macros[k])
            
            print(line)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python compiler_gen3.py <file>")
        sys.exit(1)
        
    with open(sys.argv[1], 'r', encoding='utf-8') as f:
        src = f.read()
        
    compile(src)

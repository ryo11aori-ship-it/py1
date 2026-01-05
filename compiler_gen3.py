import sys

# 【重要】標準エラー出力にバージョンを表示（ファイル出力を邪魔しない）
sys.stderr.write("--- BOOTSTRAP COMPILER v7 (NO CHECKS) RUNNING ---\n")

def compile(src):
    lines = src.split('\n')
    macros = {}
    
    in_code = False
    
    for line in lines:
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
                    # 【修正】長さチェックを完全に削除しました
                    macros[k] = v
        else:
            # コードパート：マクロ置換
            # 長いキーから順に置換
            for k in sorted(macros.keys(), key=len, reverse=True):
                if k in line:
                    line = line.replace(k, macros[k])
            
            print(line)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.stderr.write("Usage: python compiler_gen3.py <file>\n")
        sys.exit(1)
        
    with open(sys.argv[1], 'r', encoding='utf-8') as f:
        src = f.read()
        
    compile(src)

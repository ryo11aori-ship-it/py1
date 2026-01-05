import sys

# 実行時に必ずログが出るようにする
sys.stderr.write("DEBUG: Using UNRESTRICTED compiler_gen3.py\n")

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
            # 定義パート: @v KEY VAL
            if line.startswith('@v'):
                parts = line.split()
                if len(parts) >= 3:
                    k = parts[1]
                    # 値部分はスペースを含めて結合
                    v = " ".join(parts[2:])
                    
                    # 【重要】長さチェックを削除！
                    # どんなキー(k)でも無条件で登録する
                    macros[k] = v
        else:
            # コードパート: 置換実行
            # 長いキーから順に置換して誤爆を防ぐ
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

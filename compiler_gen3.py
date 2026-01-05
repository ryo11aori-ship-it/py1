import sys

def compile(src):
    lines = src.split('\n')
    macros = {}
    
    # Header: definitions
    code_lines = []
    in_code = False
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        if line == '$':
            in_code = True
            continue
            
        if not in_code:
            if line.startswith('@v'):
                parts = line.split()
                if len(parts) >= 3:
                    k = parts[1]
                    v = " ".join(parts[2:])
                    
                    # 【復活】厳格な1文字チェック
                    # Python 3なので漢字(Multi-byte)も len=1 と判定されるため安全
                    if len(k) != 1:
                        print(f"Error: Key '{k}' must be exactly 1 char")
                        sys.exit(1)
                        
                    macros[k] = v
        else:
            # Code section: replace macros
            # Sort by length desc (safety)
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

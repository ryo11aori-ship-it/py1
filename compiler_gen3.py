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
                    # Join the rest as value (in case it contains spaces)
                    v = " ".join(parts[2:])
                    # 【修正】ここで len(k) != 1 のチェックをしていたのを削除
                    macros[k] = v
        else:
            # Code section: replace macros
            # Sort by length desc to replace longest matches first (safety)
            for k in sorted(macros.keys(), key=len, reverse=True):
                # Simple replacement (can be risky for substrings but sufficient for py1)
                # Adding word boundaries logic roughly
                if k in line:
                    # Replace whole words only? 
                    # For py1 simple syntax, direct replace is usually used in bootstrap
                    # But let's stick to simple replace as before
                    line = line.replace(k, macros[k])
            
            # Print the processed line
            print(line)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python compiler_gen3.py <file>")
        sys.exit(1)
        
    with open(sys.argv[1], 'r', encoding='utf-8') as f:
        src = f.read()
        
    compile(src)

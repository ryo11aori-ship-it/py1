# spec_consts.py
RESERVED_MAP = {
    # --- 制御構文 ---
    'i': 'if',
    'e': 'else',
    'f': 'for',
    
    # チューリング完全性の証 (while)
    'W': 'while',
    
    'b': 'break',
    'C': 'continue',
    'P': 'pass',
    'r': 'return',
    'Y': 'yield',
    
    # --- 定義・スコープ ---
    'd': 'def',
    'c': 'class',
    'G': 'global',
    'Q': 'nonlocal',
    'D': 'del',
    
    # --- 例外処理 ---
    't': 'try',
    'x': 'except',
    'L': 'finally',
    'R': 'raise',
    'S': 'assert',
    
    # --- 非同期 ---
    'U': 'async',
    'V': 'await',
    
    # --- インポート ---
    'm': 'import',
    'o': 'from',
    'A': 'as',
    
    # --- 論理・比較・演算 ---
    'a': 'and',
    'O': 'or',
    'N': 'not',
    'I': 'is',
    'n': 'in',
    'l': 'lambda',
    
    # --- 定数 ---
    'T': 'True',
    'F': 'False', # 【重要】有効化
    'Z': 'None',
    
    # --- パターンマッチ ---
    'M': 'match',
    'K': 'case',
}

RESERVED_CHARS = set(RESERVED_MAP.keys())

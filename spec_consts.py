# spec_consts.py
# Pythonの予約語とpy1の1文字トークンの固定マッピング
# ユーザー定義(@v)では、この表にある文字を使用できません。

RESERVED_MAP = {
    # --- 小文字 (頻出キーワード) ---
    'd': 'def',
    'r': 'return',
    'i': 'if',
    'e': 'else',
    'f': 'for',
    'w': 'while',
    'n': 'in',
    'm': 'import',
    'o': 'from',
    'c': 'class',
    'b': 'break',
    't': 'try',
    'x': 'except',
    'l': 'lambda',
    'a': 'and',
    
    # --- 大文字 (衝突回避または2軍キーワード) ---
    'P': 'pass',      # p はユーザー(print等)のために空ける
    'O': 'or',        # o は from で使用済み
    'N': 'not',       # n は in で使用済み
    'I': 'is',        # i は if で使用済み
    'A': 'as',        # a は and で使用済み
    'W': 'with',      # w は while で使用済み
    'Y': 'yield',
    'G': 'global',
    'T': 'True',
    'F': 'False',
    'Z': 'None',      # N は not で使用済み
    'S': 'assert',
    'U': 'async',
    'V': 'await',
    
    # --- 追加 (完全性のため) ---
    'D': 'del',
    'R': 'raise',
    'C': 'continue',
    'L': 'finally',   # Last
    'Q': 'nonlocal',  # 他の文字が埋まっているためQ
}

RESERVED_CHARS = set(RESERVED_MAP.keys())

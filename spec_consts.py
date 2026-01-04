# spec_consts.py
# Pythonの予約語とpy1の1文字トークンの固定マッピング
# keyword.kwlist (Python 3.10+) を参考に網羅

RESERVED_MAP = {
    # --- 制御構文 ---
    'i': 'if',
    'e': 'else',  # elif は else if で代用想定だが、定義するならEなどで
    'f': 'for',
    'w': 'while',
    'b': 'break',
    'C': 'continue', # cはclassで使う
    'P': 'pass',     # pはprint用
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
    'L': 'finally', # Last
    'R': 'raise',
    'S': 'assert',
    
    # --- 非同期 ---
    'U': 'async',
    'V': 'await',
    
    # --- インポート ---
    'm': 'import',
    'o': 'from', # Origin
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
    'F': 'False',
    'Z': 'None', # Zero/Null
    
    # --- パターンマッチ (Soft keywords) ---
    # 文脈依存だが、py1では予約語として扱う方が安全
    'M': 'match',
    'K': 'case',
    
    # --- その他 ---
    'W': 'with',
}

RESERVED_CHARS = set(RESERVED_MAP.keys())

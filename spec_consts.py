# spec_consts.py
RESERVED_MAP = {
    # --- 制御構文 ---
    'i': 'if',
    'e': 'else',
    'f': 'for',
    
    # 【変更】ここがチューリング完全性の証
    'W': 'while', # 元は 'w' でしたが、大文字 'W' を while に割り当てて強調
    
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
    # 'F': 'False', # Fはシステム予約だが、compiler.py1でFalseとして使わないなら定義不要
    'Z': 'None',
    
    # --- パターンマッチ ---
    'M': 'match',
    'K': 'case',
    
    # 'w': 'with', # 小文字wをwithに逃がすか、今回は未定義にしておく
}

RESERVED_CHARS = set(RESERVED_MAP.keys())

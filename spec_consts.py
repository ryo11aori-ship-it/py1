# spec_consts.py
# Pythonの予約語とpy1の1文字トークンの固定マッピング
# ここに定義された文字はユーザー定義(@v)で使用できません。

RESERVED_MAP = {
    # 主要キーワードの割り当て（衝突しないように設計者が決める）
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
    'p': 'pass',
    'b': 'break',
    't': 'try',
    'x': 'except',  # eはelseで使ったのでx
    'l': 'lambda',
    'a': 'and',
    # 'o' is used for 'from', so 'or' needs another char?
    # ここでは仮に 'O' (大文字) を割り当てるなど工夫が必要
    'O': 'or', 
    'N': 'not',
    'I': 'is',
    'A': 'as',
    'W': 'with',
    'Y': 'yield',
    'G': 'global',
    'T': 'True',
    'F': 'False',
    'Z': 'None',   # Nはnotで使ったのでZ
    'S': 'assert',
    'U': 'async',
    'V': 'await',
    # ...必要に応じて追加
}

# 逆引き用（コンパイル時のチェック用）
RESERVED_CHARS = set(RESERVED_MAP.keys())

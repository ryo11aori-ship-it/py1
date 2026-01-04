import tokenize
import io
import keyword
import builtins

# py1.py の中身を解析対象とする
TARGET_FILE = 'py1.py'

def analyze():
    with open(TARGET_FILE, 'r', encoding='utf-8') as f:
        source = f.read()

    tokens = list(tokenize.tokenize(io.BytesIO(source.encode('utf-8')).readline))
    
    identifiers = set()
    
    # Pythonのキーワードや組み込み関数を除外するかどうかの判断
    # py1では「組み込み関数(print, len等)」も「属性(.split, .strip等)」も全て定義が必要
    
    for tok in tokens:
        if tok.type == tokenize.NAME:
            name = tok.string
            # キーワードは除外（if, def等は予約語マップで解決されるため）
            if keyword.iskeyword(name):
                continue
            identifiers.add(name)

    print(f"--- Analysis of {TARGET_FILE} ---")
    print(f"Total unique identifiers found: {len(identifiers)}")
    print("\n--- Proposed @v Definitions (Template) ---\n")
    
    # ソートして出力
    sorted_ids = sorted(list(identifiers))
    
    # 既存の予約語マップ(spec_consts)と衝突しないかチェックが必要だが、
    # まずは単純にリストアップする
    for name in sorted_ids:
        # とりあえず空の文字を割り当てて出力
        print(f"@v ? '{name}'")

if __name__ == '__main__':
    analyze()

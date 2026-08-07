"""入力途中の文字から食材候補を出す（仕様書 要件1「『トマ』と打ったら『トマト』が表示される」）。

リファクタリング前は app.py の中に直接書かれていた。画面とは無関係な純粋な計算なので、
ここに切り出して単体でテストできるようにしている。アルゴリズムは変更していない。

候補の探し方は3段階：
  1. 別名に完全一致するもの
  2. 正式名称または別名が入力で始まるもの（2文字以上入力されている場合）
  3. 別名との文字列類似度が0.7以上のもの（打ち間違いを拾う）
"""
from difflib import SequenceMatcher

from . import ingredients

SIMILARITY_THRESHOLD = 0.7
MAX_SUGGESTIONS = 3
MIN_LENGTH_FOR_PREFIX = 2  # 1文字だと候補が出すぎるため


def _aliases_of(row: dict) -> list[str]:
    return [alias.strip() for alias in row["aliases"].split(";") if alias.strip()]


def suggest(text: str, limit: int = MAX_SUGGESTIONS) -> list[str]:
    """カンマ区切りの入力欄の中身を受け取り、入力途中の最後の1つに対する候補を返す。

    すでに正式名称が入力しきられている場合は候補を出さない（空リスト）。
    """
    if not text:
        return []

    current_input = text.split(",")[-1].strip()
    if not current_input:
        return []

    rows = ingredients.load_rows()

    # すでに正式名称そのものが入力されているなら候補は不要
    for row in rows:
        if current_input == row["name"].strip():
            return []

    suggestions = []

    # 1. 別名に完全一致
    for row in rows:
        if current_input in _aliases_of(row):
            suggestions.append(row["name"].strip())

    if len(current_input) >= MIN_LENGTH_FOR_PREFIX:
        # 2. 正式名称または別名が入力で始まる
        for row in rows:
            name = row["name"].strip()
            if name.startswith(current_input):
                suggestions.append(name)
            for alias in _aliases_of(row):
                if alias.startswith(current_input):
                    suggestions.append(name)
                    break

        # 3. 別名との類似度がしきい値以上（打ち間違いを拾う）
        for row in rows:
            name = row["name"].strip()
            for alias in _aliases_of(row):
                if SequenceMatcher(None, current_input, alias).ratio() >= SIMILARITY_THRESHOLD:
                    suggestions.append(name)
                    break

    # 順序を保ったまま重複を除く
    return list(dict.fromkeys(suggestions))[:limit]

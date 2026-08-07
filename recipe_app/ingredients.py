"""ingredients.csv の読み込みを一元化する。

リファクタリング前は app.py・recognize.py・recommend.py の3箇所が
それぞれ別々に（csv モジュールと pandas で）このCSVを読んでいた。
列を1つ増やすだけで3箇所直す必要があった状態を、ここに集約している。

CSVは初回アクセス時に1回だけ読み、以降はキャッシュを返す。
"""
import pandas as pd

from . import config

_df = None


def load_df() -> pd.DataFrame:
    """ingredients.csv 全体（135行）。初回だけ読み込む。"""
    global _df
    if _df is None:
        _df = pd.read_csv(config.INGREDIENTS_CSV)
    return _df


def load_rows() -> list[dict]:
    """全行を dict のリストで返す。入力候補（もしかして…）の照合に使う。"""
    return load_df().to_dict(orient="records")


def load_labels() -> list[dict]:
    """CLIP に渡す候補ラベル（調味料を除く101件）。
    戻り値: [{"name": "玉ねぎ", "en_label": "onion"}, ...]
    """
    df = load_df()
    food = df[~df["is_seasoning"]]  # 調味料は写真に撮らないので候補から外す
    return food[["name", "en_label"]].to_dict(orient="records")


def load_seasonings() -> set[str]:
    """調味料の名前の集合（34件）。合致率・消費率の分母から除くのに使う。"""
    df = load_df()
    return set(df[df["is_seasoning"]]["name"])


def build_alias_map() -> dict[str, str]:
    """「別名 → 正式名称」の辞書（403キー）を作る。
    例: {"玉葱": "玉ねぎ", "たまねぎ": "玉ねぎ", "玉ねぎ": "玉ねぎ"}
    正式名称自身も入れておかないと、正しく入力されたときに未登録扱いになる。
    """
    alias_map = {}
    for _, row in load_df().iterrows():
        alias_map[row["name"]] = row["name"]
        for alias in row["aliases"].split(";"):
            alias_map[alias.strip()] = row["name"]
    return alias_map

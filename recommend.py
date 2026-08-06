"""
① 正規化 （玉葱みたいに万が一、ingredients.csvにある正式名称と別の名前で食材が追加された時に、正式名称に変換する）
② 事前準備 （recipes.csvの読み込み → TF-IDF 行列（最初の1回だけ））
③ 推薦 recommend（食材リスト） → 上位5件

仕様書通りに「合致率を第1優先、類似度を第2優先としてソート」する
つまり並び順はほぼ合致率に左右され、TF-IDFの類似度は合致率が同点の時の決着用
"""

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

# 合致率がこれ未満のレシピは表示しない（仕様書 テスト項目6「合致率が閾値未満 → 該当なし」）
# 0.5 =「主材料の半分以上が手元にある」。実測では典型的な入力で7〜20件が残り、
# 上位5件を埋めるのに十分。0.7 まで上げると0件になる入力が出てしまう。
MATCH_THRESHOLD = 0.5

_alias_map = None
_recipes = None
_tfidf = None
_seasonings = None
_vectorizer = None


def build_alias_map() -> tuple[dict[str, str], pd.DataFrame]:
    """
    食材名の正規化を行う関数
    例: 玉葱 → 玉ねぎ
    """
    ingredients_df = pd.read_csv("data/ingredients.csv")
    # {"玉葱": "玉ねぎ", "たまねぎ": "玉ねぎ", "オニオン": "玉ねぎ", "玉ねぎ": "玉ねぎ"} の形
    alias_map = {}
    for _, row in ingredients_df.iterrows():
        alias_map[row["name"]] = row["name"]
        for alias in row["aliases"].split(";"):
            alias_map[alias] = row["name"]

    return alias_map, ingredients_df


def _load():
    global _alias_map, _recipes, _tfidf, _seasonings, _vectorizer
    if _alias_map is not None: # すでに読み込まれている場合は何もしない（初回だけ読み込む）
        return

    _alias_map, ingredients_df = build_alias_map()  # 正規化マップを作る（読み込んだcsvも返すことで読み込み回数を減らす）
    _seasonings = set(ingredients_df[ingredients_df["is_seasoning"]]["name"])  # 調味料のセットを作る

    recipes_df = pd.read_csv("data/recipes.csv")
    _recipes = []
    for _, row in recipes_df.iterrows():
        items = [x.strip() for x in row["ingredients"].split(";")]
        recipe = row.to_dict() # csvの1行を辞書に変換
        recipe["items"] = items # item列を追加（全食材のリスト）
        recipe["main"] = [x for x in items if x not in _seasonings] # main列を追加（調味料を除いた食材のリスト）
        _recipes.append(recipe)    

    docs = [r["main"] for r in _recipes] # 主材料のリスト
    _vectorizer = TfidfVectorizer(analyzer=lambda items: items)
    _tfidf = _vectorizer.fit_transform(docs) # TF-IDF行列を作る


def text_normalization(ingredients: list[str]) -> tuple[list[str], list[str]]:
    """
    戻り値: (正規化できた食材, 未登録だった食材)
    """
    _load() # csvは初回だけ読み込む
    known, unknown = [], []
    for name in ingredients:
        canonical = _alias_map.get(name.strip())
        if canonical is None:
            unknown.append(name)
        elif canonical not in known:
            known.append(canonical)

    return known, unknown


def calc_match(have: set[str], main: list[str]) -> tuple[float, list[str]]:
    """
    合致率と不足食材を返す
    have: ユーザーが持っている食材（正規化済みの食材名）
    main: レシピの主材料
    """
    missing = [x for x in main if x not in have] # 不足食材のリスト
    rate = (len(main) - len(missing)) / len(main) # 合致率 = (持っている食材の数) / (主材料の数)　（主食材は常に1個以上あることは保証されている）
    return rate, missing


def recommend(ingredients: list[str], top_k: int = 5):
    _load()
    known, unknown = text_normalization(ingredients) # 正規化できた食材と未登録の食材に分ける
    have = set(known) # 正規化できた食材のセット

    query = _vectorizer.transform([known])
    sims = (query @ _tfidf.T).toarray()[0] # コサイン類似度（TF-IDFの類似度）

    results = []
    for recipe, sim in zip(_recipes, sims):
        rate, missing = calc_match(have, recipe["main"])

        """
        選択した食材の中から1つでも合っていたら検索に引っかかって、
        両方一気に消費するものを提案してくれるわけではない
        という問題点を解消する
        """
        # ① 消費率 = 手元の食材のうち、このレシピで使えるものの割合
        main_known = [x for x in known if x not in _seasonings] # 合致率と同じく、調味料は常備前提として分母から除く   
        used = [x for x in main_known if x in recipe["main"]]
        usage = len(used) / len(main_known) if main_known else 0.0
        # ② 合致率と消費率の調和平均。どちらかが低いと全体が下がる
        score = 0.0 if rate + usage == 0 else 2 * rate * usage / (rate + usage)

        results.append(
            {
                **recipe,
                "match_rate": rate,
                "usage_rate": usage,
                "used": used,
                "score": score,
                "similarity": float(sim),
                "missing": missing,
            }
        )

    # 合致率が閾値未満のものは候補から外す
    results = [r for r in results if r["match_rate"] >= MATCH_THRESHOLD]

    # 第1に合致率と消費率の調和平均で比較し、第2に類似度で比較
    results.sort(key=lambda r: (-r["score"], -r["similarity"]))
    return results[:top_k], unknown


if __name__ == "__main__":
    _load()
    oyakodon = next(r for r in _recipes if r["name"] == "親子丼")
    print("主材料:", oyakodon["main"])
    print(calc_match({"鶏もも肉", "卵", "玉ねぎ", "ご飯", "ねぎ"}, oyakodon["main"]))
    print(calc_match({"鶏もも肉", "卵", "玉ねぎ"}, oyakodon["main"]))
    print(_tfidf.shape)
    print(recommend(['鶏もも肉', '卵', '玉ねぎ'], 1))
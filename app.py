import streamlit as st
import csv
import io
from difflib import SequenceMatcher
from recognize import recognize
from recommend import recommend


@st.cache_data(show_spinner="画像を認識中...")
def recognize_image(data: bytes):
    return recognize(io.BytesIO(data), top_k=3)


SEARCH_SITES = [
    ("クックパッド", "https://cookpad.com/search/{}"),
    ("クラシル", "https://www.kurashiru.com/search?query={}"),
    ("デリッシュキッチン", "https://delishkitchen.tv/search?q={}"),
]

st.title("レシピ提案アプリ")
st.write("食材からレシピを提案します。")
st.write("食材をテキストで入力、または画像アップロードで食材を認識させることができます。")

# 入力候補（もしかして...）の元データ
ingredient_data = []
with open("data/ingredients.csv", "r", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    for row in reader:
        ingredient_data.append(row)

if "ingredients" not in st.session_state:          # 選択中の食材（テキスト・画像の共通の置き場）
    st.session_state.ingredients = []

if "ingredient_input" not in st.session_state:     # テキスト入力欄の中身
    st.session_state.ingredient_input = ""

if "selected_suggestion" not in st.session_state:  # 押された候補
    st.session_state.selected_suggestion = None

if "clear_input" not in st.session_state:          # 追加後に入力欄を空にするためのフラグ
    st.session_state.clear_input = False

if "image_queue" not in st.session_state:          # 認識待ちの画像 [{"id","name","data"}]
    st.session_state.image_queue = []

if "uploader_round" not in st.session_state:       # アップローダーを作り直すための世代番号
    st.session_state.uploader_round = 0

# st.session_state.ingredient_input を書き換えられるのは text_input を作る前だけ。
# ウィジェット生成後に書き換えると StreamlitAPIException になるため、この位置で行う。
if st.session_state.selected_suggestion:

    suggestion = st.session_state.selected_suggestion

    current_text = st.session_state.ingredient_input

    current_ingredients = [
        ingredient.strip()
        for ingredient in current_text.split(",")
        if ingredient.strip()
    ]

    # 入力途中の最後の1つを、押された候補で置き換える
    if current_ingredients:
        current_ingredients[-1] = suggestion
    else:
        current_ingredients.append(suggestion)

    st.session_state.ingredient_input = ", ".join(current_ingredients)

    st.session_state.selected_suggestion = None

if st.session_state.clear_input:
    st.session_state.ingredient_input = ""
    st.session_state.clear_input = False


st.subheader("食材を入力", anchor=False)

ingredient_text = st.text_input(
    "食材をカンマ区切りで入力してください",
    placeholder="例: 鶏肉, 玉ねぎ, にんじん",
    key="ingredient_input",
)

# 仕様書 要件1「『トマ』と打ったら『トマト』が表示される」
suggestions = []

if ingredient_text:

    current_input = ingredient_text.split(",")[-1].strip()

    if current_input:
        exact_name = False

        for row in ingredient_data:

            name = row["name"].strip()

            if current_input == name:
                exact_name = True
                break

        if not exact_name:

            for row in ingredient_data:

                name = row["name"].strip()

                aliases = [
                    alias.strip()
                    for alias in row["aliases"].split(";")
                    if alias.strip()
                ]

                if current_input in aliases:
                    suggestions.append(name)

            if len(current_input) >= 2:

                for row in ingredient_data:

                    name = row["name"].strip()
                    if name.startswith(current_input):

                        suggestions.append(name)

                    aliases = [
                        alias.strip()
                        for alias in row["aliases"].split(";")
                        if alias.strip()
                    ]

                    for alias in aliases:

                        if alias.startswith(current_input):
                            suggestions.append(name)
                            break

                for row in ingredient_data:

                    name = row["name"].strip()

                    aliases = [
                        alias.strip()
                        for alias in row["aliases"].split(";")
                        if alias.strip()
                    ]

                    for alias in aliases:

                        similarity = SequenceMatcher(None, current_input, alias).ratio()

                        if similarity >= 0.7:
                            suggestions.append(name)
                            break

        suggestions = list(dict.fromkeys(suggestions))

        suggestions = suggestions[:3]

if suggestions:

    st.write("もしかして...")

    for i, suggestion in enumerate(suggestions):

        if st.button(suggestion, key=f"suggestion_{i}_{suggestion}"):

            st.session_state.selected_suggestion = suggestion

            st.rerun()

# 入力欄の中身を「選択中の食材」に登録する
if st.button("追加", disabled=not ingredient_text.strip()):
    for name in [s.strip() for s in ingredient_text.split(",") if s.strip()]:
        if name not in st.session_state.ingredients:  # 重複防止
            st.session_state.ingredients.append(name)
    st.session_state.clear_input = True
    st.rerun()


st.subheader("食材の画像アップロード", anchor=False)

uploaded_files = st.file_uploader(
    "食材の画像をアップロードしてください",
    accept_multiple_files=True,
    type=["jpg", "jpeg", "png"],
    key=f"uploader_{st.session_state.uploader_round}",
)
# アップローダーからは1枚だけ取り除くことができないので、受け取ったら即座に
# 自前のキューへ移し、key を変えてアップローダーを空の状態に作り直す。
# 以降の表示はキューが元になるため、1枚ずつ消せるようになる。
if uploaded_files:
    known = {item["id"] for item in st.session_state.image_queue}
    for f in uploaded_files:
        if f.file_id not in known:
            st.session_state.image_queue.append(
                {"id": f.file_id, "name": f.name, "data": f.getvalue()}
            )
    st.session_state.uploader_round += 1
    st.rerun()

if st.session_state.image_queue:
    st.write("アップロードされた画像:")
    for item in st.session_state.image_queue:
        st.image(item["data"], caption=item["name"], width=250)

        results = recognize_image(item["data"])
        names = [r["name"] for r in results]

        choice = st.radio(
            "この画像の食材を選んでください",
            options=names,
            captions=[f"類似度 {r['score']:.2f}" for r in results],
            key=f"choice_{item['id']}",
        )

        col_add, col_skip = st.columns([1, 4])

        # 選んだ画像だけをキューから取り除く。直後の st.rerun() が実行を打ち切るので、
        # ループ中にリストを差し替えても続行されない。
        if col_add.button("食材に追加", key=f"add_{item['id']}"):
            if choice not in st.session_state.ingredients:
                st.session_state.ingredients.append(choice)
            st.session_state.image_queue = [
                q for q in st.session_state.image_queue if q["id"] != item["id"]
            ]
            st.rerun()

        if col_skip.button("この画像を削除", key=f"skip_{item['id']}"):
            st.session_state.image_queue = [
                q for q in st.session_state.image_queue if q["id"] != item["id"]
            ]
            st.rerun()


st.subheader("選択中の食材", anchor=False)

with st.container(border=True):
    if not st.session_state.ingredients:
        st.info("食材を入力するか、画像から選択してください")
    else:
        st.caption("✕ を押すと削除できます")
        # 外側の horizontal=True でチップが横に並び、幅に応じて折り返す
        with st.container(horizontal=True):
            for name in st.session_state.ingredients:
                # チップ1つ分。食材名はただの文字で、✕ だけをボタンにする。
                # width="content" が無いと、折り返した行のチップが横幅いっぱいに広がる。
                with st.container(horizontal=True, border=True, gap="xxsmall",
                                  width="content", vertical_alignment="center"):
                    st.markdown(name)
                    # remove() でループ中のリストを書き換えているが、直後の st.rerun() が
                    # 実行を打ち切るのでループは続行されない。この rerun は消さないこと。
                    if st.button("✕", key=f"del_{name}", type="tertiary"):
                        st.session_state.ingredients.remove(name)
                        st.rerun()


# 仕様書 要件2「食材が一つも選択されていないときは、検索開始ボタンは押せないようにする(disabled)」
if st.button("レシピを探す", disabled=not st.session_state.ingredients):

    found, unknown = recommend(st.session_state.ingredients, top_k=5)

    st.subheader("レシピ検索結果", anchor=False)

    # 仕様書 テスト項目4「データに存在しない食材を入力 → 無視され、未登録である旨を表示」
    if unknown:
        st.warning("次の食材は未登録のため、検索から除外しました: " + "、".join(unknown))

    # 仕様書 テスト項目6「合致率が閾値未満 → レシピを表示せず『該当なし』を表示」
    if not found:
        st.write("該当するレシピは見つかりませんでした。")
    else:
        st.write(f"{len(found)}件のレシピが見つかりました。")

        for recipe in found:
            st.markdown("---")

            col_img, col_info = st.columns([1, 2])
            col_img.image(f"data/images/{recipe['image']}", width="stretch")

            col_info.subheader(recipe["name"], anchor=False)
            col_info.write(
                f"合致率 {recipe['match_rate']:.0%}" 
                f" ／ 手元の食材を {recipe['usage_rate']:.0%} 使用"
                f" ／ {recipe['minutes']}分 ／ {recipe['servings']}人分"
            )
            col_info.write("使用する手元の食材：" + "、".join(recipe["used"]))
            col_info.write("使用食材：" + "、".join(recipe["items"]))
            if recipe["missing"]:
                col_info.warning("不足している食材：" + "、".join(recipe["missing"]))

            # 仕様書 要件4「詳細をタッチすると見れる」
            with st.expander("詳細（材料と作り方）"):
                st.write("**材料**")
                for name, amount in zip(recipe["items"], recipe["amounts"].split(";")):
                    st.write(f"・{name}　{amount}")

                st.write("**作り方**")
                for i, step in enumerate(recipe["steps"].split(";"), 1):
                    st.write(f"{i}. {step}")

                for col, (site, url) in zip(st.columns(len(SEARCH_SITES)), SEARCH_SITES):
                    col.link_button(f"{site}で検索", url.format(recipe["name"]), width="stretch")

import streamlit as st 
import io
from recognize import recognize

@st.cache_data(show_spinner="画像を認識中...")
def recognize_image(data: bytes):
    return recognize(io.BytesIO(data), top_k=3)



st.title("レシピ提案アプリ") 
st.write("食材からレシピを提案します。")
st.write("食材をテキストで入力、または画像アップロードで食材を認識させることができます。")

recipes = [
    {
        "name": "親子丼",
        "ingredients": ["鶏肉", "卵", "玉ねぎ"],
        "minutes": 20
    },
    {
        "name": "照り焼きチキン",
        "ingredients": ["鶏肉", "玉ねぎ"],
        "minutes": 15
    },
    {
        "name": "肉じゃが",
        "ingredients": ["鶏肉", "じゃがいも", "玉ねぎ", "にんじん"],
        "minutes": 30
    },
    {
        "name": "野菜炒め",
        "ingredients": ["キャベツ", "にんじん", "ピーマン", "玉ねぎ"],
        "minutes": 10
    },
    {
        "name": "オムライス",
        "ingredients": ["卵", "玉ねぎ", "鶏肉"],
        "minutes": 25
    }
]

if "ingredients" not in st.session_state:
    st.session_state.ingredients = [] 

st.subheader("食材を入力") 

# form にしているのは、Enterで送信できることと、追加後に入力欄が空になること
# （clear_on_submit）の2つのため。text_input を作った後に session_state を
# 書き換えてクリアする方法は Streamlit が禁止していて例外になる。
with st.form("add_text", clear_on_submit=True):
    ingredient_text = st.text_input("食材をカンマ区切りで入力してください", placeholder="例: 鶏肉, 玉ねぎ, にんじん")
    submitted = st.form_submit_button("追加")

if submitted:
    for name in [s.strip() for s in ingredient_text.split(",") if s.strip()]:
        if name not in st.session_state.ingredients:  # 重複防止
            st.session_state.ingredients.append(name)
    st.rerun()

st.subheader("食材の画像アップロード") 

uploaded_files = st.file_uploader("食材の画像をアップロードしてください", accept_multiple_files=True, type=["jpg", "jpeg", "png"])

if uploaded_files:
    st.write("アップロードされた画像:")
    for uploaded_file in uploaded_files:
        data = uploaded_file.getvalue()
        st.image(data, caption=uploaded_file.name, use_container_width=True)

        results = recognize_image(data)
        names = [r["name"] for r in results]

        choice = st.radio(
            "この画像の食材を選んでください",
            options=names,
            captions=[f"類似度 {r['score']:.2f}" for r in results],
            key=f"choice_{uploaded_file.file_id}",
        )

        if st.button("食材に追加", key=f"add_{uploaded_file.file_id}"):
            if choice not in st.session_state.ingredients:
                st.session_state.ingredients.append(choice)
            st.rerun()


st.subheader("選択中の食材")

if not st.session_state.ingredients:
    st.info("食材を入力するか、画像から選択してください")
else:
    for name in st.session_state.ingredients:
        col1, col2 = st.columns([4, 1])
        col1.write(f"・{name}")
        # remove() でループ中のリストを書き換えているが、直後の st.rerun() が
        # 実行を打ち切るのでループは続行されない。この rerun は消さないこと。
        if col2.button("削除", key=f"del_{name}"):
            st.session_state.ingredients.remove(name)
            st.rerun()


# 仕様書 要件2「食材が一つも選択されていないときは、検索開始ボタンは押せないようにする(disabled)」
if st.button("レシピを探す", disabled=not st.session_state.ingredients):

    found = []

    for recipe in recipes:
        matched = set(st.session_state.ingredients) & set(recipe["ingredients"])

        if matched:
            found.append(recipe)

    st.subheader("レシピ検索結果")

    if found:
        st.write(f"{len(found)}件のレシピが見つかりました。")

        for recipe in found:
            st.markdown("---")
            st.subheader(recipe["name"])
            st.write("材料："+"、".join(recipe["ingredients"]))
            st.write("調理時間：" + str(recipe["minutes"]) + "分")

    else:
        st.write("該当するレシピは見つかりませんでした。")
            


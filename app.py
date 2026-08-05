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

ingredient_text = st.text_input("食材をカンマ区切りで入力してください", placeholder="例: 鶏肉, 玉ねぎ, にんじん") 

ingredients = [ 
    ingredient.strip() 
    for ingredient in ingredient_text.split(",") 
    if ingredient.strip() ] 

st.subheader("食材の画像アップロード") 

uploaded_files = st.file_uploader("食材の画像をアップロードしてください", accept_multiple_files=True, type=["jpg", "jpeg", "png"]) 
if ingredient_text: 
    ingredients = [ingredient.strip() for ingredient in ingredient_text.split(",")] 
    st.write("入力された食材:") 
    for ingredient in ingredients:
        st.write("・", ingredient) 
        
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


if st.session_state.ingredients:
    st.subheader("選択された食材")
    for name in st.session_state.ingredients:
        col1, col2 = st.columns([4, 1])
        col1.write(f"・{name}")
        if col2.button("削除", key=f"del_{name}"):
            st.session_state.ingredients.remove(name)
            st.rerun()


if ingredients:
    
    if st.button("レシピを探す"):
        
        results = []
        
        for recipe in recipes:
            matched = set(ingredients) & set(recipe["ingredients"])
            
            if matched:
                results.append(recipe)
                
        st.subheader("レシピ検索結果")
               
        if results:
            st.write(f"{len(results)}件のレシピが見つかりました。")

            for recipe in results:
                st.markdown("---")
                st.subheader(recipe["name"])
                st.write("材料："+"、".join(recipe["ingredients"]))
                st.write("調理時間：" + str(recipe["minutes"]) + "分")
    
        else:
            st.write("該当するレシピは見つかりませんでした。")

else:
    st.write("食材を入力してください。")
            


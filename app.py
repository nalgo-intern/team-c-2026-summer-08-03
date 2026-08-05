import streamlit as st 

st.title("レシピ提案アプリ") 
st.write("食材からレシピを提案します。")
st.write("食材をテキストで入力、または画像アップロードで食材を認識させることができます。")

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
        st.image(uploaded_file, caption=uploaded_file.name, use_column_width=True)
if ingredients:
    if st.button("レシピを探す"):
        st.write("レシピを検索中...")
    
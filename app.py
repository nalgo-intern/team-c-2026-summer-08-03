import streamlit as st 

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
        st.image(uploaded_file, caption=uploaded_file.name, use_container_width=True)

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
            


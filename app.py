import streamlit as st 
import csv
from difflib import SequenceMatcher 

st.title("レシピ提案アプリ") 
st.write("食材からレシピを提案します。")
st.write("食材をテキストで入力、または画像アップロードで食材を認識させることができます。")

ingredient_data = []

with open("data/ingredients.csv", "r", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)

    for row in reader:
        ingredient_data.append(row)

if "ingredient_input" not in st.session_state:
    st.session_state.ingredient_input = ""

if "selected_suggestion" not in st.session_state:
    st.session_state.selected_suggestion = None

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

if "selected_ingredients" not in st.session_state:
    st.session_state.selected_suggestions = None

if st.session_state.selected_suggestion:

    suggestion = st.session_state.selected_suggestion

    current_text = st.session_state.ingredient_input

    current_ingredients = [
        ingredient.strip()
        for ingredient in current_text.split(",")
        if ingredient.strip()
    ]

    if current_ingredients:
        current_ingredients[-1] = suggestion
    else:
        current_ingredients.append(suggestion)

    st.session_state.ingredient_input = ", ".join(current_ingredients)

    st.session_state.selected_suggestion = None

st.subheader("食材を入力")

ingredient_text = st.text_input("食材をカンマ区切りで入力してください",placeholder="例: 鶏肉, 玉ねぎ, にんじん",key="ingredient_input")

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

                        similarity = SequenceMatcher(None,current_input,alias).ratio()

                        if similarity >= 0.7:
                            suggestions.append(name)
                            break

        suggestions = list(dict.fromkeys(suggestions))

        suggestions = suggestions[:3]

if suggestions:

    st.write("もしかして...")

    for i, suggestion in enumerate(suggestions):

        if st.button(suggestion,key=f"suggestion_{i}_{suggestion}"):

            st.session_state.selected_suggestion = suggestion

            st.rerun()
                
ingredients = [ 
    ingredient.strip() 
    for ingredient in ingredient_text.split(",") 
    if ingredient.strip() 
]

if ingredients:
    st.write("入力された食材:")
    for ingredient in ingredients:
        st.write("・", ingredient) 

st.subheader("食材の画像アップロード") 

uploaded_files = st.file_uploader("食材の画像をアップロードしてください", accept_multiple_files=True, type=["jpg", "jpeg", "png"]) 
        
if uploaded_files:
    st.write("アップロードされた画像:")
    for uploaded_file in uploaded_files:
        st.image(uploaded_file, caption=uploaded_file.name, use_container_width=True)

if ingredients:
    
    if st.button("レシピを探す"):
        
        results = []
        
        normalized_ingredients = []
        
        for ingredient in ingredients:
            normalized_name = ingredient
            for row in ingredient_data:
                name = row["name"]
                if ingredient == name:
                    normalized_name = row["name"]
                    break
                aliases = row["aliases"].split(";")

                if ingredient in aliases:

                    normalized_name = name
                    break

            normalized_ingredients.append(normalized_name)
        
        for recipe in recipes:
            matched = set(normalized_ingredients) & set(recipe["ingredients"])
            
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
            


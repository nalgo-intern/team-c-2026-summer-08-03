"""プロジェクト内のパスを一元管理する。

__file__ を起点にしているため、どのディレクトリから実行しても同じ場所を指す。
（"data/xxx.csv" のような相対パスだと、実行時のカレントディレクトリに依存して壊れる）
"""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"
INGREDIENTS_CSV = DATA_DIR / "ingredients.csv"
RECIPES_CSV = DATA_DIR / "recipes.csv"
RECIPE_IMAGES_DIR = DATA_DIR / "images"   # レシピの完成写真
EVAL_IMAGES_DIR = DATA_DIR / "eval_images"  # 画像認識の評価用

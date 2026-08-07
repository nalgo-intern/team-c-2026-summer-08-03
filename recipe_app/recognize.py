"""食材画像の認識（CLIP ViT-B/32 によるゼロショット画像分類）。"""
from transformers import CLIPModel, CLIPProcessor
import torch
from PIL import Image

from . import ingredients

_model = None
_processor = None
_labels = None
_label_features = None


def _load():
    # 初回だけモデルを読み込み、ラベル側のベクトルを計算する
    global _model, _processor, _labels, _label_features
    if _model is not None: # すでに読み込まれている場合は何もしない
        return
    
    MODEL_NAME = "openai/clip-vit-base-patch32"

    _model = CLIPModel.from_pretrained(MODEL_NAME) # CLIPモデル本体
    _processor = CLIPProcessor.from_pretrained(MODEL_NAME) # 文字列をトークンに変換したり、画像をリサイズ・正規化したりする（つまり前処理）

    _model.eval() # 推論モードにする（学習時の挙動を止める）

    _labels = ingredients.load_labels()
    texts = [f"a photo of {label['en_label']}" for label in _labels] # 英語ラベルを使って、CLIPのテキスト入力を作る（CLIPは英語のキャプションで学習されているので、日本語を入れると精度が落ちる）

    # ベクトル化する
    inputs = _processor(text=texts, return_tensors="pt", padding=True) 
    with torch.no_grad():
        features = _model.get_text_features(**inputs).pooler_output # テキストの特徴量を計算する

    # 正規化する
    _label_features = features / features.norm(dim=-1, keepdim=True) # ベクトルの長さを1にする　これによって後で内積を取るだけでコサイン類似度になる


def recognize(image, top_k: int = 3) -> list[dict]:
    """
    画像1枚 → 上位top_k件の食材ラベルを返す
    """
    _load() # 初回だけモデルを読み込む

    img = Image.open(image).convert("RGB") # 画像を読み込む

    # ベクトル化する
    inputs = _processor(images=img, return_tensors="pt")
    with torch.no_grad():
        feature = _model.get_image_features(**inputs).pooler_output # 画像の特徴量を計算する

    # 正規化する
    feature = feature / feature.norm(dim=-1, keepdim=True)

    # コサイン類似度を計算する
    sims = feature @ _label_features.T # 内積を取るだけでコサイン類似度になる (1, 512) @ (512, 101) → (1, 101) 食材101件分の類似度が並んだ行列

    # 上位を取り出す
    top = sims[0].topk(top_k)

    # dictのリストに戻す
    return [
        {"name": _labels[int(i)]["name"], "score": float(v)}
        for i, v in zip(top.indices, top.values)
    ]


if __name__ == "__main__":
    # 動作確認: python -m recipe_app.recognize
    from . import config

    for r in recognize(config.RECIPE_IMAGES_DIR / "curry_rice.jpg"):
        print(r)
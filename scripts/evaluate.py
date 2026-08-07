"""画像認識の評価スクリプト。

実行: python scripts/evaluate.py
"""
import sys
from collections import defaultdict
from pathlib import Path

# scripts/ から親の recipe_app を import できるようにする
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from recipe_app import config                  # noqa: E402
from recipe_app.recognize import recognize     # noqa: E402

EVAL_DIR = config.EVAL_IMAGES_DIR
IMAGE_EXTS = {".jpg", ".jpeg", ".png"}

# フォルダ名 → 正解とみなすラベルの集合
ALIASES = {
    "鶏肉": {"鶏もも肉", "鶏むね肉", "鶏ひき肉", "鶏手羽元"},
}


def acceptable(answer: str) -> set[str]:
    """
    正解とみなすラベルの集合を返す
    """
    return ALIASES.get(answer, {answer})

def load_eval_set() -> list[tuple[Path, str]]:
    """
    EVAL_DIR直下のフォルダを見て、(パス, フォルダ名)を返す
    """
    eval_set = []
    for folder in sorted(EVAL_DIR.iterdir()):
        if not folder.is_dir():
            continue
        for path in sorted(folder.iterdir()):
            if path.suffix.lower() in IMAGE_EXTS:
                eval_set.append((path, folder.name))
    return eval_set


stats = defaultdict(lambda: {"total": 0, "top1": 0, "top3": 0})
mistakes = []

for path, answer in load_eval_set():
    names = [p["name"] for p in recognize(path, top_k=3)]
    ok = acceptable(answer)

    hit1 = names[0] in ok
    hit3 = any(n in ok for n in names)

    s = stats[answer]
    s["total"] += 1
    s["top1"] += hit1
    s["top3"] += hit3

    if not hit1:
        mistakes.append((path, answer, names))

total = sum(s["total"] for s in stats.values())
top1  = sum(s["top1"]  for s in stats.values())
top3  = sum(s["top3"]  for s in stats.values())

# 画像を入れ忘れているとこの後の割り算でゼロ除算になるので、先に止める
if total == 0:
    raise SystemExit(f"{EVAL_DIR} に画像がありません")

print(f"評価枚数: {total}枚 / {len(stats)}種類")
print()

# 食材ごとの内訳
print(f"{'食材':<8}{'枚数':>4}{'Top-1':>8}{'Top-3':>8}")
print("-" * 32)

for name, s in stats.items():
    rate1 = s["top1"] / s["total"]
    rate3 = s["top3"] / s["total"]
    mark = "" if rate1 >= 0.60 else "  ← 目標60%未満"  # 食材ごとの目標値
    print(f"{name:<8}{s['total']:>4}{rate1:>8.0%}{rate3:>8.0%}{mark}")

print("-" * 32)
print()

# 全体（目標値は仕様書「画像認識の評価指標と目標値」より）
print(f"全体 Top-1: {top1 / total:>6.1%}  (目標 80%)  {'OK' if top1 / total >= 0.80 else 'NG'}")
print(f"全体 Top-3: {top3 / total:>6.1%}  (目標 95%)  {'OK' if top3 / total >= 0.95 else 'NG'}")
print()

# 誤認識の一覧（Step④のプロンプト調整で、どこを直すべきかの手がかりになる）
print(f"=== 誤認識 {len(mistakes)}件 ===")
for path, answer, names in mistakes:
    print(f"  {path.parent.name}/{path.name}  正解={answer}  予測={names}")

# データセット

日本の家庭料理 150 件と食材マスタ 135 件。アプリに同梱して使う参照データです。

## ファイル

| ファイル | 内容 |
|---|---|
| `data/recipes.csv` | レシピ 150 件 |
| `data/ingredients.csv` | 食材マスタ 135 件（調味料 34 / 画像認識の候補 101） |
| `data/images/` | 料理の完成写真 150 枚。`recipes.csv` の `image` 列と 1 対 1 で対応 |
| `data/eval_images/` | 画像認識の評価用 50 枚（10 種類 × 5 枚）。フォルダ名が正解ラベル |

文字コードは UTF-8、区切り文字は半角 `;` です。

## recipes.csv

| 列 | 必須 | 例 | 用途 |
|---|---|---|---|
| `id` | ✔ | `1` | 主キー |
| `name` | ✔ | `親子丼` | 表示。外部レシピサイトの検索語にも使う |
| `category` | ✔ | `丼物` | 絞り込み |
| `ingredients` | ✔ | `鶏もも肉;卵;玉ねぎ` | **照合・合致率・不足食材の算出対象** |
| `amounts` | ✔ | `200g;3個;1個` | 表示専用。`ingredients` と同数・同順 |
| `minutes` | ✔ | `20` | 所要時間の表示 |
| `servings` | ✔ | `2` | 何人分かの表示 |
| `steps` | ✔ | `玉ねぎを薄切りにする;...` | 調理手順の表示 |
| `image` | ✔ | `oyakodon.jpg` | `data/images/` 配下のファイル名 |

カテゴリ内訳: 主菜 45 / 副菜 30 / 麺類 18 / 汁物 15 / 丼物 15 / ご飯物 12 / 鍋物 8 / サラダ 7

## ingredients.csv

| 列 | 例 | 用途 |
|---|---|---|
| `name` | `玉ねぎ` | 正式表記。表示と照合に使う |
| `en_label` | `onion` | 画像認識（CLIP）に渡す英語ラベル |
| `is_seasoning` | `FALSE` | `TRUE` は合致率・消費率の計算から除外 |
| `aliases` | `玉葱;たまねぎ;オニオン` | 表記ゆれ。入力時に `name` へ変換 |

このファイル 1 つで **候補ラベルの供給・英語変換・調味料判定・表記の正規化** を兼ねます。

### `en_label` は単語ではなく「説明句」を書く

実装して分かった、このデータで最も重要な点です。

当初 `豆腐 → tofu` としていたところ、Top-1 正解率が 40% しか出ませんでした。
原因は、競合する食材のラベルがすべて `tofu` を含んでいて区別できていなかったことです。

```text
豆腐      → tofu                 ← 正解であるべきものが最も情報量が少ない
高野豆腐   → dried tofu
厚揚げ     → thick fried tofu
油揚げ     → fried tofu pouch
```

競合ラベルとの違いを言語化したところ、**40% → 100%** に改善しました。

```text
豆腐 → a block of plain white tofu
       plain（加工なし）／ white（高野豆腐の茶色と対比）／ block（油揚げの薄さと対比）
```

**似た食材を追加するときは、既存のラベルと何が違うのかを英文に含めてください。**
単語1つで済ませると、既存の食材の認識精度まで巻き添えで落ちます。
経緯の詳細は [開発メモ.md](開発メモ.md) の 1-1 を参照してください。

## eval_images/

画像認識の評価用データです。**フォルダ名がそのまま正解ラベル**になります。

```text
data/eval_images/
├── トマト/     1.jpg 2.jpg 3.jpg 4.jpg 5.jpg
├── 卵/        ...
└── 鶏肉/       ...
```

実際の利用環境に近づけるため、白背景の商品写真は避けて収集しています。
`scripts/evaluate.py` がこのフォルダを走査して正解率を算出します。

なお `鶏肉/` は `ingredients.csv` に「鶏肉」という行が存在しないため、
評価時のみ 4 部位（鶏もも肉・鶏むね肉・鶏ひき肉・鶏手羽元）のいずれでも正解とみなしています。
この対応表は `scripts/evaluate.py` の `ALIASES` にあります。

## 編集ルール

1. **区切り文字は半角 `;`。** 全角 `；` では分割されず、食材名がまるごと 1 つとして扱われます
2. **編集は Google Sheets で行い、CSV エクスポートしてコミット。** 複数人が同じ CSV を直接触るとコンフリクトで壊れます
3. **`recipes.csv` の食材名は、必ず `ingredients.csv` の `name` に存在させる。** マスタに無い名前は照合時に無視されます
4. **マスタに食材を足したら、その食材を使うレシピも 1 件以上足す。** 選べるのにヒットしない選択肢になります
5. **`amounts` は `ingredients` と個数・順序を揃える。** 画面で材料と分量を対にして表示しています
6. **`image` に書いたファイルは必ず `data/images/` に置く。** 存在しないと詳細表示でエラーになります

## 整合性チェック

CSV を編集したら、以下を実行して確認してください。

```bash
python -c "
import pandas as pd, os
r = pd.read_csv('data/recipes.csv'); m = pd.read_csv('data/ingredients.csv')
seas = set(m[m['is_seasoning']]['name']); known = set(m['name'])
used = {x.strip() for s in r['ingredients'] for x in s.split(';')}
print('マスタに無い食材      :', sorted(used - known) or 'なし')
print('どのレシピでも未使用    :', sorted(known - used) or 'なし')
print('画像の配置漏れ        :', [x for x in r['image'] if not os.path.exists(f'data/images/{x}')] or 'なし')
print('全角セミコロン        :', sum('；' in str(s) for s in [*r['ingredients'], *r['steps'], *m['aliases']]), '件')
print('amounts の個数不一致   :', sum(len(str(x).split(';')) != len(str(y).split(';')) for x, y in zip(r['ingredients'], r['amounts'])), '件')
print('主材料0件のレシピ      :', sum(not [x for x in s.split(';') if x.strip() not in seas] for s in r['ingredients']), '件')
print('name の重複          :', int(m['name'].duplicated().sum()), '件')
"
```

現在の状態はすべて問題なしです（未登録 0 / 未使用 0 / 画像漏れ 0 / 重複 0）。

## 判定ロジックでの使われ方

`ingredients` 列から調味料を除いたものを **主材料** と呼び、これが計算の対象になります。

```python
main = [x for x in recipe["ingredients"].split(";") if x not in seasonings]

missing = [x for x in main if x not in have]              # 不足食材
match   = (len(main) - len(missing)) / len(main)          # 合致率  … 作れるか
usage   = len(set(main) & have) / len(have_main)          # 消費率  … 使い切れるか

score = 2 * match * usage / (match + usage)               # 並び順（調和平均）
```

**調味料を除外するのが要点です。** 除外しないと「醤油がないので作れません」が量産されます。

合致率だけで並べると、主材料が 1 つの料理（じゃがバターなど）が必ず 100% になって上位を独占します。
手元の食材を使い切るという目的に合わせ、消費率との調和平均で並べ替えています。

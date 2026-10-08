# 滑走面と回転摩耗検証 第54巡

[報告本文](../GPT回答_多方向探索第54巡_雪に接する面の微細構造と回転摩耗_20261009.md)。物理試験0件、実物成功確率null。計算は粒自身の回転、面形状、仮の材料量と寿命費用の診断。

- inputs.json：仮定と前巡の数量
- calculate.py / results.json / validation.json：再計算と18項目照合
- rotation.csv / paths.csv：連続回転と離散方向の違い
- texture_wear.csv / same_Sa.csv：面Sa・段差・摩耗後の幾何
- cap_cost.csv / life_cost.csv：面積換算の接触材と機能寿命費用
- test_plan.json：未実施の順次試験。結果欄はnull
- model.md / sources.md：数式・原著の適用範囲
- draw.py / figure1〜3：計算図と概念図。生成画像や実試料写真ではない

~~~text
python calculate.py
python draw.py
~~~

数値計算はPython標準ライブラリのみ。図にmatplotlibを使用。draw.pyはリポジトリ直下.depsがあれば優先するが必須でない。再実行で結果を再生成する。スキー係数・寿命・成功確率の外挿は行っていない。

このフォルダの図・コード・計算結果はGitHubで共有する。保存バイトの照合後に作業用コピーとGit履歴を削除し、ルートの接続案内と利用設定を残す。

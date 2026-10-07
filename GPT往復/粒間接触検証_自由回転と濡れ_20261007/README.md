# 第13巡 再現資料

[報告本文](../GPT回答_多方向探索第13巡_粒間接触と三方向開口の比較_20261007.md)を先に読む。物理試験0件、success_probability=null。粒間の幾何・指定接点の剛体釣合い・液橋の比較尺度であり、粒群床や滑走の物理実証ではない。

## 保存した資料

- [入力](inputs.json)、[円弧支持関数と初回接触の上下限](pair_geometry.py)、[36条件・270方向の結果](pair_results.json)
- [三支持粒の配置と力・モーメント](cluster.py)、[配置・96摩擦条件の結果](cluster_results.json)
- [接触面の内外判定](contact_faces.py)、[面別摩擦の結果](face_results.json)
- [力学解の分離証拠と精度変更](audit_wrenches.py)、[数値監査](numerical_audit.json)
- [濡れと材料量・費用](wet_cost.py)、[その結果](wet_cost_results.json)
- [C3の形状ソース](C3_cyclic_open150.scad)、[描画コード](plot.py)
- [三形状](three_shapes.png)、[釣合いの一覧](fixture_balance.png)、[C3の小規模配置](C3_fixture.png)、[幅・液橋・費用](width_wet_cost.png)
- [検証コード](validate_delivery.py)、[検証結果](validation.json)、[検証記録](検証記録.md)
- [出典](sources.md)、[探索台帳](探索台帳.md)、[依存関係](requirements.txt)

## 実行順

Pythonとrequirements.txtのライブラリを用意し、pair_geometry.py → cluster.py → contact_faces.py → audit_wrenches.py → wet_cost.py → plot.py → validate_delivery.pyの順に実行する。リポジトリ直下に一時依存.depsがあれば優先し、図のキャッシュは.scratchへ置く。

湿潤時の自重は[第12巡](../接触配分検証_傾きと自整列_20261007/README.md)のgravity_results.json、費用の粒数は[第11巡](../荷重経路検証_直交輪と内部補強_20261007/README.md)のinputs.jsonを参照する。単独フォルダだけでなく、リポジトリの階層を保つ。

SCADはOpenSCADの形状ソースであり、今回コンパイル・STL出力はしていない。図はPythonの同じ円弧定義から描いた。R4/C3/S3は独立した粒であり、禁止されたマット・ブラシ・メッシュ床への置換ではない。

高さの上下限は接触位置と法線精度の保証とは別。指定接点モデルの釣合いは粒の強度・安定性・捕捉率と別。全結果にはモデルの範囲を記録する。初回接触36条件、配置9（うち幾何不成立1を除外）、摩擦96条件、面別摩擦8条件、液橋30条件を成功率の分母にしない。

開口150°は本巡の固定条件。別の角度へ変更する際は、入力だけでなく円弧定義・名称・形状ソース・全計算の整合も変更する。

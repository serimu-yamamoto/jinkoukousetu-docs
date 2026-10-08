# 第59巡 再計算資料

[報告書](../GPT回答_多方向探索第59巡_濡れた静摩擦を越える開離復帰と材料分担_20261009.md)を先に読む。物理試験0件、成功確率未算定。

- inputs.json：仮定とメーカー値の区別。
- published_static_water.csv：S2 Table3、13行・52係数の転記（今回の材料測定ではない）。
- calculate.py / results.json / validation.json：25の数式・転記照合。
- cam_material_bounds.csv / static_kinetic_separation.csv：静摩擦と動摩擦を分けた条件。
- opening_force_path.csv / bed_overburden.csv：開離全経路と45cm床の圧力反例。
- additional_opening_cost.csv：追加梁だけの原料費、仮税込額。
- draw.py / figure*.png / figure*.svg：再生成可能な3図。概念図は立体CADではない。
- sources.md / provenance.json：一次資料、確認範囲、参照PDFのハッシュ。原PDFは転載しない。
- model.md / test_plan.json：式と未実施の実験分岐。
- audit.py / document-audit.json：参照・転記・索引・成果範囲の確認。
- publication-manifest.json：成果と索引のSHA-256。自身は循環参照を避けて一覧から除く。

再計算はPython3標準ライブラリで calculate.py を実行。図だけmatplotlibとnumpyを要する。RTK環境では rtk summary python calculate.py、続いて rtk summary python draw.py とする。draw.pyはリポジトリ直下の一時.depsを任意で読み込むが、通常環境のライブラリでも実行可能。

一次資料数値の点検はPDF本文・原表画像で実施。計算照合、図の目視確認と実物性能検証を混同しない。

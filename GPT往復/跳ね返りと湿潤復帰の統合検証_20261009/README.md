# 第58巡・跳ね返りと湿潤復帰の統合検証

[報告書](../GPT回答_多方向探索第58巡_内部摩擦で雪の切れと復帰を両立する条件_20261009.md) / [入力](inputs.json) / [モデル](model.md) / [出典](sources.md) / [未実施の試験計画](test_plan.json)

実物試験0件。成功確率未算定。計算表は全て仮定したモデルの結果で、雪や試作品の測定値ではない。

- calculate.py: Python標準ライブラリで全11表・results.json・validation.jsonを生成。35項目は力・エネルギー・収支の照合。
- draw.py: matplotlibで3組のPNG/SVGを生成。必要ならリポジトリ直下の.depsを参照。
- audit.py: 文書・リンク・履歴・図・計算値を照合。

| CSV | 内容 |
|---|---|
| cam_regimes.csv | 摩擦・角度と固着の境界 |
| force_branches.csv | 45°カムの制御往復 |
| wet_return.csv | 液橋と戻り残留、予圧の負担 |
| bridge_splitting.csv | 同じ濡れ面積の細分化反例 |
| contact_pressure_tradeoff.csv | 液橋半径と荷重面を同時に縮める反例 |
| flexure_strain.csv | 梁の変形とひずみの目安 |
| prior_elastic_energy.csv | H57で未計算だった散逸の扱い |
| whole_grain_energy.csv | 部品と合算のエネルギー比の差 |
| damping_scale_cost.csv | 単純増設の収支と材料負担 |
| candidate_tolerance.csv | H58-Cの162感度ケース |
| additional_flexure_cost.csv | 基本形の追加梁だけの費用 |

候補Cの追加梁量と費用はresults.jsonのcandidate、比較図3、本文に保存。基本形の2倍の幅で2倍の梁材料量となるだけで、製造費が2倍に比例すると保証しない。

再計算: このフォルダで python calculate.py、python draw.py、python audit.py。文書監査の履歴比較は初回の作業用Git管理領域にある公開前スナップショットを使用。公開後の再実行では利用できない検査をスキップと記録する。

publication-manifest.jsonは自分以外の全公開対象のバイト数・SHA-256を保持。公開後、固定コミットからマニフェスト自身も含めて全件照合する。作業用複製とGit履歴は照合後に削除。

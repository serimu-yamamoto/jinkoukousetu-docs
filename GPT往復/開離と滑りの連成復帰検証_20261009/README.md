# 第60巡：開離と滑りの連成復帰

[本文](../GPT回答_多方向探索第60巡_戻る順序の反証と留め具を増やさない連成復帰_20261009.md)を先に読む。物理試験0件、成功確率未算定。前巡の「先に開く」は機構として未保証だったため、同時に動く2自由度を検証した。

|ファイル|内容|
|---|---|
|inputs.json|未測定のばね・付着・荷重・費用仮定|
|calculate.py / results.json|接触の釣り合いと経路を再計算|
|validation.json|30件の数式・釣り合い照合。実験ではない|
|coupled_unloading_path.csv|407状態。イベントの直前／直後を含む準静的枝|
|coupled_sensitivity.csv|162条件の感度。製造歩留まり・成功確率ではない|
|event_order.csv|16条件の滑り／開離順序|
|static_kinetic_jump.csv|静動摩擦差と未解決の過渡エネルギー5条件|
|cross_axis_coupling.csv|軸間干渉のある破断後平衡15条件。全経路ではない|
|latch_tradeoff.csv|荷重中の抜去抵抗12条件|
|partial_component_cost.csv|一部部材の原料費9行|
|draw.py / figure*.png / figure*.svg|3図の生成コードと画像|
|model.md|式、単位、立体化で満たすべき条件|
|sources.md / provenance.json|一次資料の確認範囲と前巡への追補|
|test_plan.json|未実施の比較試験と設計分岐|
|audit.py / document-audit.json|文章・リンク・数値・履歴の照合|
|publication-manifest.json|成果と変更した索引等のSHA-256。自身を除外|

再計算：Python3標準ライブラリで calculate.py。図はmatplotlib/numpyを要する。RTK環境では rtk summary python calculate.py、rtk summary python draw.py、rtk summary python audit.py。draw.pyは任意でリポジトリ直下の.depsを読む。監査の旧版保存データは作業用.gitの内部でのみ使用し、公開物の再計算ではそれ以外のチェックを実行する。

原著の図・本文や実験を転載した資料ではない。全曲線は明示した仮定の独立計算で、実物の時間波形・滑走試験結果ではない。

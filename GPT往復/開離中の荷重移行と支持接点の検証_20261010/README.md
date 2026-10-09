# 第100巡の再現入口

[報告書](../GPT回答_多方向探索第100巡_開離する粒から周囲へ荷重を渡す構造と復旧条件_20261010.md)。物理試験0件、成功確率null。単粒の固定接点釣合いと、粒群への荷重分散を別々の模型で調べる。両者を結合したDEMではない。

## 実行順

リポジトリ全体を取得し、このフォルダで実行する。Pythonと依存版はruntime_versions.json／requirements.txt。

```text
python -m pip install -r requirements.txt
python reproduce.py --check
python two_helpers.py
python load_sharing.py
python area_budget.py
python make_figures.py
```

reproduce.pyを--checkなしで実行するとresults.jsonとvalidation.jsonを再生成する。--checkは主出力の一致も確認する。他のスクリプトは対応する結果・図を再生成する。

- inputs.json：比較条件、基点、依存6ファイルのLF SHA256。
- reproduce.py／results.json／validation.json：主720条件、974照合。既存32条件との定式化比較、解析的支持反力、円錐分割、接点精密化も記録。
- two_helpers.py／two_helpers_results.json：二つの仮想補助接点。360条件・458照合。指定15状態を全て支える組合せなし。
- load_sharing.py／load_sharing_results.json：圧縮のみの25支持点と自由端梁。20条件・105照合。固定された接点幾何の640条件とは別の模型。
- area_budget.py／area_budget.json：仮名目圧力から必要面積を計算。36条件・38照合。
- 2図：固定接点と荷重分散。図の緑や解の存在を雪性能の合格と読まない。
- model.md／sources.md／test_plan.md／claude_handoff.md：定義、出典、未実施検証、反証依頼。
- research_state.json／publication_audit.json／manifest.json：状態と公開対象の照合。manifestは自身を除外。

第13巡C3の接点座標は近似。第99巡の初期微小重なりも未修復。追加接点の隣接粒は未構築。力が釣り合っても、変形の整合・安定性・実際の運動・50℃・濡れ・雪相当性能は未証明。

## 実行環境の移行記録

サーバー再実行はserver_recheck.json、判定差はmigration_differences.jsonを参照。runtime_versions.jsonは移行前の計算・作図環境。サーバーはPython 3.14.4、NumPy 2.5.3、SciPy 1.18.1。移行前のPythonは3.12.14。全数値の完全なバイト一致ではなく、判定差を開示した数値照合。主reproduce.pyの--checkは、保存結果を生成したサーバー環境で確認する。図を新しい環境で再作図した場合は見た目と元データを再確認する。

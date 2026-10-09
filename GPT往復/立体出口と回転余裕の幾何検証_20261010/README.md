# 第99巡の再現入口

[報告書](../GPT回答_多方向探索第99巡_立体接点の回転拘束と横へ逃がす開離設計_20261010.md)。物理試験0件、成功確率未算定。

## ファイルと実行

Python、依存版は requirements.txt と runtime_versions.json を参照。リポジトリ全体を取得し、このフォルダで以下を順に実行する。

```text
python -m pip install -r requirements.txt
python mobility.py --check
python probe_paths.py
python correct_path.py
python audit.py
python make_figures.py
```

mobility.py を --check なしで実行すると主計算結果を再生成する。--check は保存済みJSONとの一致も調べる。probe_paths.py と correct_path.py は既存の幾何関数を使うため数分以上かかる場合がある。audit.py は保存された有限距離区間・単位・製造量境界を照合する追加監査で、物理試験ではない。

- inputs.json：基点・仮定・第13巡依存5ファイルのLF正規化SHA256。
- mobility_results.json／validation.json：128 LP、32変位要求、36配向感度、208照合と独立12 LP比較。
- path_results.json：指定15終点、隣接距離45問。連続経路全体は未検証。
- correction_results.json：補正7終点、隣接距離21問、接点精密化6 LP、条件付き製造量。
- mobility_and_correction.png／fixture_and_path.png：図。線で結んだ途中の無衝突を保証しない。
- model.md／sources.md／test_plan.md／claude_handoff.md：定義、出典、未実施検証、共有依頼。
- research_state.json：実施状況。manifest.json：今回の成果・索引のサイズとSHA256（自己除外）。

計算形状は成形した枝状の候補。雪結晶の自発成長・雪相当性能の証明ではない。初期配置の微小重なりと有限終点だけの検証を省略しない。

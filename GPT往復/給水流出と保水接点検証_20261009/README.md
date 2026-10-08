# 第45巡の再計算資料

[受け渡し報告](../GPT回答_多方向探索第45巡_滑走中の水流出と保水接点への再設計_20261009.md) に目的・仮定・式・コード・Claude依頼を集約。

物理試験0件。実物成功確率は未算定。各JSONは理想模型の感度結果であり、材料性能や雪感の実証ではない。

- inputs.json：固定した入力。未測定値を採用材の実測としない。
- calculate.py：標準ライブラリで計算、matplotlibで2図を出力。
- transport/pressure/hydrostatic/retention/cost.json：全条件。
- results.json：代表値、checks.json：数値照合27件。
- sources.json：一次資料と取得範囲。exploration-ledger.json：比較案と採否。
- environment.json：実行環境。publication-manifest.json：公開ファイルのバイト数・SHA256。

再計算：Python環境にmatplotlibを用意して、このフォルダのcalculate.pyを実行する。リポジトリ直下の.depsが存在すればそこも参照する。ネットワーク接続や外部試験装置は使わない。出力はこのフォルダへ上書きする。

コードには円周流束・圧力分布の独立数値積分、力・質量・反復定常解の照合を含む。全項通過はモデル実装の確認に限る。

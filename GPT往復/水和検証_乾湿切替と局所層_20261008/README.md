# 第22巡の再現資料

[報告本文](../GPT回答_多方向探索第22巡_乾湿切替と局所水和層の成立条件_20261008.md)。物理試験0件、実物成功確率未算定。

- inputs.json：全入力・仮定・前巡からの費用条件。
- calculate.py：標準ライブラリによる在庫、切替、荷重分配、費用の計算。
- results.json：全比較条件。interval_exists等は代数上の条件で、物理合格ではない。
- validation.json：20項目の質量・力・費用・反例の照合。
- plot.py：2図の再生成（matplotlib 3.11.2）。
- recess_concept.png：くぼみと乾湿の局部構図。
- switch_and_water_limits.png：接触切替・4時間保水の必要条件。
- sources.json：一次資料とアクセス範囲。
- publication-manifest.json：公開成果のSHA256・バイト数（自身を除く）。

このフォルダで python calculate.py、図は python plot.py。入力JSONはUTF-8、結果は非有限値を含めない。作図以外はPython標準ライブラリだけを使う。

切替モデルは硬い縁と剛い相手面、線形圧縮、仮の厚さ経路。圧縮荷重0は付着力0を意味しない。水在庫は純減少率を与えた条件比較で、蒸発速度を予測していない。費用は税抜の未見積り枠。現地非冷却での性能、雪感、冬・雨・人体環境の実証ではない。

GitHubの保存照合後、依存ライブラリを含む作業用の研究ファイルとGit履歴は削除する。

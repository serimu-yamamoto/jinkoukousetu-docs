# 第43巡の再現資料

[報告書](../GPT回答_多方向探索第43巡_微粉を流さない材料と雨水回収の設計_20261009.md)の計算資料。物理試験0件、実物成功確率はnull。

- inputs.json：寸法・雨・粒子発生・費用の仮定。文献測定値から推定した分解速度ではない。
- calculate.py：枝の表面後退、雨水／粒子収支、理想沈降、理論酸素要求量、費用逆算。補助の粒径割合例と照合用基準値はコードにも明記。
- erosion.csv：12条件。幾何学的質量減少で、完全生分解ではない。
- rain.csv：36条件。流出率、全体捕集率、貯留、残余流出を保存。
- settling.csv：3粒径の球の沈降尺度。実粒の沈降測定ではない。
- annual_fines_value.csv／capital_budget.csv／bulk_processing.csv：年額価値・払える初期費・正味40分の処理量。
- results.json／checks.json：集計と22件の式・単位・保存則の照合。
- sources.json：一次資料4件、取得範囲、本文の利用範囲。著作物全文・図の再配布なし。
- exploration-ledger.json：今回の反証と次の識別条件。
- PNG／SVG：同じ2図。こちらで作図した仮定比較。
- environment.json：実行環境。publication-manifest.json：公開対象のバイト数・SHA256（自己参照は除く）。

再計算はPythonとMatplotlib 3.11.2を使用。図以外は標準ライブラリ。リポジトリ直下の .deps があればそこを参照し、なければ現在のPython環境を使う。

~~~powershell
python -m pip install matplotlib==3.11.2
python "GPT往復/微粉流出と使用後分解検証_20261009/calculate.py"
~~~

22件は実装照合で、材料の合格数ではない。固定の比較入力に対する回帰照合を含むため、入力変更後は期待値・図説明も見直す。物理モデルの妥当性や毒性を確認するテストではない。図の環境差によるバイト差と数値差は区別する。

GitHubのmainへ通常コミットし、固定コミットから全成果を読み戻してSHA256とバイト数を確認した後、依頼者指定に従ってローカル作業複製とGit履歴を削除する。rootの接続案内と利用設定を保護する。

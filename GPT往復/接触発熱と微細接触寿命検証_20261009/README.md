# 第41巡の再現資料

[受け渡し報告](../GPT回答_多方向探索第41巡_滑走接点の発熱と摩耗を両立させる設計_20261009.md)を入口にする。実物試験0件、実物成功確率はnull。

- inputs.json：仮定と文献パラメーターの区別。
- model.md：熱源・分割・摩耗・費用の導出と限界。
- reproduce.py：積分、相似比較、保存、図生成。
- contact_cases.csv：54条件。材料の達成値や物理成功数ではない。
- coefficient_convergence.csv：積分収束。掲載された重み平均係数との差はresults.jsonに明示。
- mean_heating.csv：板全体の平均発熱の別模型。局所ピークとの単純加算不可。
- cost_caps.csv：仮の材料年額から逆算した単価上限。
- results.json：25数値検証、未解決の文献係数差、主要値。
- splitting_tradeoff.png、contact_heat_profiles.png：仮定模型から作った図。原著の図を転載していない。
- sources.json：実際に確認した範囲・本文未取得・適用限界。
- environment.json、requirements.txt：実行環境。
- publication-manifest.json：今回の変更ファイルのバイト数とSHA256。自身は含めない。

Python 3.12とrequirements.txtの依存を利用する。RTK使用下では次のように実行する。

~~~text
rtk summary python -m pip install -r requirements.txt
rtk summary python reproduce.py
~~~

--no-plotsは図の再描画のみを省略する。隣接するリポジトリの .deps がある場合は優先する。一次論文PDFは一時取得し、出版社または著者URLとSHA256を出典台帳へ保存。全文・図の再配布はしていない。

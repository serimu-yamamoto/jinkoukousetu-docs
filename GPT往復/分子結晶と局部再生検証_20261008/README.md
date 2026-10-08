# 第35巡 再現資料

[報告書](../GPT回答_多方向探索第35巡_分子結晶の再評価と少量接点の再成長_20261008.md)。H35の小さな結晶接点の配置・成長・再生水量・雨・可変費を比較する。物理試験0件、実物成功確率null。チロシン・シスチンの野外採用を承認したものではない。

|ファイル|内容|
|---|---|
|[inputs.json](inputs.json)|出典からの濃度・段差速度と、明示した仮寸法・配置・費用条件|
|[calculate.py](calculate.py)|標準ライブラリだけで計算を再現|
|[results.json](results.json)|配置10例、供給48例、成長36例、雨24例、可変費36例|
|[validation.json](validation.json)|28件の独立した代数・数量・収支の照合|
|[model.md](model.md)|法線力平均と床強度の違い、式・単位・限界|
|[sources.md](sources.md)|一次資料7件とClaudeの検討範囲の監査|
|[plot.py](plot.py)|2図の再生成|
|[図1](figure1_contacts_and_growth.png)|種の配置・接点寸法・成長方向|
|[図2](figure2_regrowth_and_rain.png)|少量再生の水量と雨の溶解容量|
|[publication-manifest.json](publication-manifest.json)|公開ファイルのバイト数・SHA256。自己ハッシュは含めない|

~~~text
python -X utf8 calculate.py
python -X utf8 plot.py
~~~

Python 3.12.14、図はmatplotlib 3.11.2（依存numpy 2.5.3）で生成。ローカルの一時.depsがなければ通常環境からmatplotlibを読み込む。2図を目視確認した。数式照合の通過を材料の実証率へ換算しない。

接点の強度・密度・配置、供給効率、修復対象と新生割合、段差間隔、30/50℃の成長は未測定。S2の過飽和の表記差を入力濃度から再計算した。仮の法線力予算3 kPaは剪断強度ではなく、工程の可変費は全事業費ではない。

公開後はGitHubの不可変コミットから全対象を再取得して照合し、ローカル成果・一時資料・Git履歴を削除する。接続案内・既存設定は保護する。

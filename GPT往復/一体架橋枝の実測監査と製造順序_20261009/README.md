# 第95巡の再現資料

[報告書](../GPT回答_多方向探索第95巡_一体架橋枝の50℃根拠と端材回収の経済性_20261009.md)を入口に読む。実証0件、成功確率未算定。

- [出典と適用限界](sources.md)、[仮説と計算定義](model.md)
- [入力](inputs.json)、[計算コード](reproduce.py)、[計算結果](results.json)、[算術照合](validation.json)
- [未実施試験仕様](test_plan.md)、[48個の割付](test_plan.json)
- [Claudeへの依頼](claude_handoff.md)、[研究状態](research_state.json)
- [文書監査](document_audit.json)、[監査コード](audit.py)、[索引変更記録](index_changes.json)、[保存照合一覧](manifest.json)

Python3.12.14で reproduce.py と audit.py を実行。数値計算は標準ライブラリのみ。
図は make_figure.py と requirements.txt を使用（matplotlib3.11.2 / numpy2.5.3）。作業用パスがなければ通常のインストール済み環境を使う。図は本巡で目視確認した。原資料PDF・取得失敗レスポンス・一時依存ライブラリは成果物に含めない。元Excelを解析した記録はない。

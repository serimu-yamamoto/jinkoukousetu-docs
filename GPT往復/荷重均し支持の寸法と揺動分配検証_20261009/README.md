# 第78巡の再現資料

[研究報告](../GPT回答_多方向探索第78巡_支持ばねの実寸制約と揺動する荷重分配_20261009.md)。H78-Rは局所的な力学構想。物理試験0件、成功確率未算定。

- [入力](inputs.json)・[模型と式](model.md)・[再計算](reproduce.py)・[依存バージョン](requirements.txt)
- [集計](summary.json)・[28数式照合](checks.json)
- [円柱60行](axial_posts.csv)・[固定案内梁128行](fixed_guided_beams.csv)・[一軸容量72行](uniaxial_energy_bound.csv)
- [揺動240行](rocker_pairs.csv)・[共通移動12行](common_translation.csv)・[末端バー物量8行](lever_stock_cost.csv)・[横力モーメント72行](lateral_moment_budget.csv)
- [比較図](support_rocker_cost.png)・[機能図](rocker_concept.png)
- [出典と参照範囲](sources.json)・[判断](decision.json)・[7件の未実施仕様](test_plan.json)・[Claude依頼](claude_handoff.md)
- [文書監査コード](audit.py)・[文書監査結果](document_audit.json)・[索引差分](index_changes.json)・[成果ハッシュ](manifest.json)

Python 3、numpy、scipy、matplotlibで、このフォルダの python reproduce.py を実行。入力はinputs.json、出力は同フォルダへ上書き。検証用コピーで実行する。旧巡スクリプトのimportやネット接続は不要。図PNGは環境差があり得る。

文書監査audit.pyは旧mainとの履歴照合にGit履歴、またはGitHubの当該コミットの公開本文を使う。全592行と28照合は数学とコードの確認で、物理的成功件数ではない。元原著は取得範囲だけを参照し、取得できていない全文・図表を確認済みにしない。

公開ファイルをバイト照合後、作業クローン・依存環境・Git履歴を削除する。rootの接続案内・利用設定を保護する。

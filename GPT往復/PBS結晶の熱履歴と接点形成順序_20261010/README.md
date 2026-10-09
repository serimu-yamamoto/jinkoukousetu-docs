# PBS結晶の熱履歴と接点形成順序

2026-10-10、第134巡。[報告](../GPT回答_多方向探索第134巡_PBSの融点では決められない50度安定性と接点形成順序_20261010.md)。

- [入力](inputs.json)、[再現コード](reproduce.py)、[結果](results.json)、[実装整合確認](validation.json)
- [モデルの適用範囲](model.md)、[一次資料](sources.json)、[試験計画](test_plan.json)、[Claudeへの依頼](claude_handoff.md)
- [研究状態](research_state.json)。公開監査 publication_audit.json と保存目録 manifest.json は公開工程で生成する。
- [再利用部品](../../計算部品/crystal_thermal_ledger.py)

Python標準ライブラリのみ。リポジトリのこのフォルダで python3 -B reproduce.py --check を実行すると保存結果と照合する。--check を付けない実行はサーバー上でのみ行う。依存計算部品0。整合確認22件は物理実験ではない。物理実験0、成功確率未算定。

DSC収支の3例は未校正の反例。PBSの50℃での融解量や接点寿命を予測しない。27条件の費用感度は見積ではない。

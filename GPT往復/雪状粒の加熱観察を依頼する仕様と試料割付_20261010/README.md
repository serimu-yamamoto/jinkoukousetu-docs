# 雪状粒の加熱観察を依頼する仕様と試料割付

2026-10-10、第135巡。[報告](../GPT回答_多方向探索第135巡_雪状粒の50度形状保持を実測へつなぐ試験仕様_20261010.md)。

[詳細仕様](protocol.md)・[未送信照会文](inquiry_draft.md)・[Claudeへの依頼](claude_handoff.md)。
[入力](inputs.json)・[再現コード](reproduce.py)・[割付と時間感度](results.json)・[整合確認](validation.json)・[モデルの範囲](model.md)・[一次資料](sources.json)・[機械可読計画](test_plan.json)。
[再利用部品](../../計算部品/blocked_thermal_screen.py)。

Python標準ライブラリのみ。サーバー上で python3 -B reproduce.py --check を実行すると保存値を照合する。実物試験0、成功確率未算定。18物理試料、18DSC、63時点、3調製バッチは予定数であり、実施数・独立成功数ではない。

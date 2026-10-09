# 第111巡：結晶精製の選択性と洗浄順序

47件の数値確認、実物試験0件、成功確率null。結晶の先精製と後固定を比較する工程仮説。

- [報告](../GPT回答_多方向探索第111巡_結晶の精製と固定順序から残留物と費用を減らす_20261010.md)
- [模型と限界](model.md)
- [再計算コード](reproduce.py)
- [共通部品](../../計算部品/washing_selectivity.py)
- [結果](results.json)
- [数値確認](validation.json)
- [一次資料](sources.json)
- [未実施確認仕様](test_plan.json)
- [Claudeへの依頼](claude_handoff.md)

サーバー上でリポジトリを取得し、このフォルダのreproduce.pyに対し `python3 -B reproduce.py --check`。Python標準ライブラリのみ。--checkなしは結果を生成する。液中濃度と製品1kgあたり純度を分離する。数値確認数は実物成功率ではない。

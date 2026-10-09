# 第109巡の再計算

120仮条件、91解析・数値照合。物理試験0、成功確率null。

- [報告](../GPT回答_多方向探索第109巡_粒の配向と自由回転を踏まえた支持解放_20261010.md)
- [模型](model.md)
- [共通部品](../../計算部品/contact_fabric.py)
- [コード](reproduce.py)
- [結果](results.json)
- [照合](validation.json)
- [一次資料](sources.json)
- [Claude依頼](claude_handoff.md)

サーバーでリポジトリを取得し、PythonとNumPyを使い python3 -B reproduce.py --check を実行する。未生成なら--checkなしで生成。今回のNumPy版は2.5.0。接点密度×枝長²×kaで正規化し、実物のPaとしていない。記録した結果の再計算は実物の成功を意味しない。

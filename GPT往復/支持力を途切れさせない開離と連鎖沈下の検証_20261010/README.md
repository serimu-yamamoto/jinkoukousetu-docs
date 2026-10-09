# 第101巡：開離時の支持力急落と連鎖

[報告](../GPT回答_多方向探索第101巡_支持力を途切れさせない開離と連鎖沈下の防止_20261010.md) / [計算定義](model.md) / [出典](sources.md) / [試験仕様](test_plan.md) / [Claude依頼](claude_handoff.md)

Python 3.14.4（実行時に記録）、標準ライブラリのみ。サーバー上の作業コピーで、次をこのフォルダから実行する。

```text
python3 -B reproduce.py --check
python3 -B independent_checks.py --check
```

--checkは保存結果との一致を検査し、成果を上書きしない。新規再計算時は--checkを外す。別Python版で末尾浮動小数点が違う場合は物理結論と数値差を分け、保存結果を黙って上書きしない。

- inputs.json：仮定、探索条件、先行コード・Claude資料のハッシュ。
- results.json：70パラメータ組、各2法則、イベントの全波と支持点ID、連続分布への照合。
- validation.json：主計算の数値照合と実行環境。
- independent_checks.json：別解法490荷重条件と追加恒等式、相関、試験機、費用感度。
- research_state.json：物理試験0・成功確率null・未解決。
- manifest.json：公開対象のバイト数とSHA256。自己ハッシュは除外。
- index_preservation.json：既存案内の履歴保持検査。

「一斉切替」は同じ閾値への同時到達を含む。「二次連鎖」は荷重を受け直して別の閾値に達する追加切替。β=1の状態名切替は支持力の損失ではない。

本模型は剛な上板・全域荷重分配であり、粒床の局所集中や実スキーの曲げを計算していない。図・結果は雪状滑走、安全性、製造・受注・試験成功の証拠ではない。

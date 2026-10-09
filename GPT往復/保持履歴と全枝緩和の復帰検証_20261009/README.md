# 第96巡の再計算入口

[報告](../GPT回答_多方向探索第96巡_長時間荷重でも戻る粒形状と製造ばらつきの条件_20261009.md)／[模型](model.md)／[出典](sources.md)／[Claude依頼](claude_handoff.md)／[未実施試験](test_plan.md)。全て条件付き計算。物理試験0件・成功確率未算定。

- inputs.json：仮入力。PEの50℃同定値ではない。
- reproduce.py / results.json：72比較＋6候補、12公差、4組の別解法、残留力と仮費用。validation.jsonの173照合。
- event_audit.py / event_audit.json：報告4例を刻み上限0.0025で照合。
- finite_recovery.py / finite_recovery.json：6条件を各2解法で解き、自由状態の位置を有限範囲へ囲い込む条件を計算。
- make_figures.py：計算値から2図を描く。左の履歴は対数時間の疎な標本で、振動周期の推定に用いない。
- research_state.json / test_plan.json：0件・未確定・未実施を機械可読で保持。
- audit.py / document_audit.json：数値表・リンク・履歴・測定状態を監査。材料認証ではない。
- index_changes.json / manifest.json：既存索引の保存と成果のバイト照合。

Python 3と[requirements.txt](requirements.txt)の環境で、このフォルダを作業場所として実行する例：

```text
rtk summary python reproduce.py --check
rtk summary python event_audit.py
rtk summary python finite_recovery.py --check
rtk summary python make_figures.py
rtk summary python audit.py
```

通常実行のreproduce.pyとfinite_recovery.pyは結果を書き、--checkは再計算して保存バイトとの一致を確認する。同じ依存版・環境の厳密照合用であり、他OSでは最終桁の差を個別に確認する。reproduce.py --revalidate-savedは保存済みODE結果のチェックと派生算術だけで、ODEの再実行ではない。

全計算は数分かかる場合がある。finite_recovery.pyは --pair 0 から --pair 5 まで各条件を独立に実行し、--assembleでまとめられる。分割中間は作業クローンの.git内へ保存する。この巡では最初の全計算で12解を得ており、時間制限後の確認用に再実行したpair0/1とも同じ値だった。以後の文書監査では高価な全ODEを繰り返さず、既存結果・別解法・刻み幅照合を確認する。

.gitがない配布コピーでは分割モードを使わず通常の全計算を使う。作業用依存ライブラリの探索は任意で、公開コード自体に実行環境や第三者PDFを同梱していない。

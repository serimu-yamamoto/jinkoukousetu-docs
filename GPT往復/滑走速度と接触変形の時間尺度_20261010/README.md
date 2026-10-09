# 第112巡：滑走速度と接触変形の時間尺度

96仮条件と独立時間積分、122件の数値確認。物理試験0件、成功確率null。

- [報告](../GPT回答_多方向探索第112巡_滑走速度で変わる抵抗と雪らしい解放の分離_20261010.md)
- [模型と限界](model.md)
- [共通部品](../../計算部品/viscoelastic_glide.py)
- [再計算](reproduce.py)
- [結果](results.json)
- [数値確認](validation.json)
- [出典](sources.json)
- [未実施確認仕様](test_plan.json)
- [Claudeへの依頼](claude_handoff.md)

サーバー上のこのフォルダで `python3 -B reproduce.py --check`。Python標準ライブラリのみ。--checkなしは結果生成。表示する比は変形抵抗の一成分で、総摩擦係数や成功確率ではない。

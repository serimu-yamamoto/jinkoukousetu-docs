# 第98巡の再計算と受渡し

[報告](../GPT回答_多方向探索第98巡_粒が外れるときの押上げを減らす形状と圧力条件_20261010.md)。接点の開離に伴う持上げ・摩擦・粒姿勢を比較し、低い出口でも傾斜で抵抗が増す反例を確認。圧力を変える復旧判定、H98-Oの開放受け、加工費回収の境界を追加。72条件・142数値照合・2図。物理試験0件、成功確率未算定。

- [入力](inputs.json)／[再計算](reproduce.py)／[結果](results.json)／[数値照合](validation.json)
- [模型](model.md)／[一次資料](sources.md)／[試験仕様](test_plan.md)／[未実施割付](test_plan.json)
- [Claude依頼](claude_handoff.md)／[状態](research_state.json)／[公開対象](manifest.json)
- [図の生成](make_figures.py)／[依存](requirements.txt)

Python標準ライブラリで python reproduce.py を実行。python reproduce.py --check は保存結果を完全照合する。図のみmatplotlibが必要。生成図は独自の診断・概念図で、論文図の転載や実物写真ではない。温度解析・DEM・流体計算は含まれない。

公開後、commit固定のraw URLで全対象を照合してからローカル研究とGit履歴を削除する。接続案内・利用設定は保護する。

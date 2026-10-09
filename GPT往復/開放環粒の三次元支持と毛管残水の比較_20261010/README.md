# 第106巡の再現
サーバー上で実行する。Python 3.14.4、NumPy 2.5.0、SciPy 1.18.0。

```sh
OPENBLAS_NUM_THREADS=1 python3 -B GPT往復/開放環粒の三次元支持と毛管残水の比較_20261010/reproduce.py --check
```

初回生成は `--check` を外す。計算途中のpartial.jsonは終了時に削除する。数分程度かかる場合がある。共通部品は [rim_grain_hex.py](../../計算部品/rim_grain_hex.py)、幾何参照は第105巡の [formation_routes.py](../../計算部品/formation_routes.py)。参照ハッシュをresultsへ保存。

- [報告](../GPT回答_多方向探索第106巡_側面窓の支持損失と残水条件_20261010.md)
- [再現コード](reproduce.py)、[結果](results.json)、[76件の整合性とメッシュ判定](validation.json)
- [絶対剛性・水頭・加工量の補足](diagnostics.json)、[出典](sources.json)
- [Claude依頼](claude_handoff.md)、[研究状態](research_state.json)
- [旧本文保存](index_preservation.json)、[公開前確認](publication_audit.json)、[公開対象](manifest.json)

E=1、ν=0.3は仮定。Hex8に2×2×2ガウス積分。下端全固定、上端は一方向だけ同一変位、他方向自由。円弧は直線分割。大窓の最終横剛性比の差3.903％は3％基準未達として保存。基準を緩めていない。小窓の通過も連続体解の誤差保証ではない。

validationのstatusはalgebraic_checks_passedであり、mesh_acceptance_passedはfalse。これは物理試験の合否ではない。
毛管圧は円形／矩形一定断面の力尺度。実際の短い曲面窓、二相流、流速、接触角履歴、残水量を解いていない。S3は原著の要旨確認まで。
今回、途中でメッシュ基準未達を検出した実行1回と、未達を保持して全結果を保存した実行1回。修正後の保存値をさらに全再計算した照合は行っていない。

# 出典台帳・2026-10-10確認

## S1：回転と集団配向

Antonio Pol, Riccardo Artoni, Patrick Richard. Collective alignment controls rotation frustration in granular flows of elongated particles. Physical Review Fluids 11,064302 (2026), DOI 10.1103/ckmc-x152。

[出版社要旨](https://journals.aps.org/prfluids/abstract/10.1103/ckmc-x152)／[著者版HTML](https://arxiv.org/html/2606.13070v1)。出版社表示2026-06-10、arXiv v1提出表示2026-06-11。HTML内にAugust 24,2026の表示もあるが、改稿経緯は確認していない。

閲覧：要旨、HTML方法II、結果III.1–2を含む本文。3D DEM、細長い球集合粒、アスペクト比1.2～4。モデル式の定義はmodel.md参照。著者の元データ・計算コードの再実行はしていない。枝形C3、実スキー、50℃の検証根拠としては使わない。

## S2：星形粒の実験との距離

Zhaoら、Packings of 3D stars: Stability and structure. Granular Matter 18,24 (2016), DOI 10.1007/s10035-016-0606-4。

[著者版要旨](https://arxiv.org/abs/1511.06026)／[HTML本文](https://arxiv.org/html/1511.06026v1)。閲覧：方法2、結果3.1を含む本文。cm級の直交6枝、アクリル／ナイロン粒の集団安定性。微小枝や滑走・摩耗性能へ数値転用しない。元実験の追試は未実施。

## S3：内部で再利用した計算

[第13巡報告](../GPT回答_多方向探索第13巡_粒間接触と三方向開口の比較_20261007.md)。入力・配置・円弧幾何・接点精密化の5ファイルをinputs.jsonのLF SHA256で固定。既存C3を新形状と呼ばない。

[第98巡報告](../GPT回答_多方向探索第98巡_粒が外れるときの押上げを減らす形状と圧力条件_20261010.md)から、低い開離出口でも姿勢で抵抗が増す未較正模型を継承。今回は3Dの隣接粒と有限終点を追加。外部論文の実験と内部の仮定計算を混同しない。

Claudeの[物性値台帳](../../調査台帳/物性値照合_自律ループv2v3.md)は基点でLF SHA256 054c9388de3be3bd251c395059a9e02c9d3b336885236683ba3f528ff819d71f。前巡と不変。今回の新しい返答は未確認。

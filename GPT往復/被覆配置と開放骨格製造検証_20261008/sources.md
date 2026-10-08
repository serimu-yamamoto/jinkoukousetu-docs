# 第34巡 出典と証拠範囲

参照日：2026-10-08。原著の掲載結果、メーカーの装置仕様、特許の工程記載と、こちらの仮定計算を分離する。外部全文・図は再配布しない。以下の材料は研究対象例であり、スキー用採用や安全確認を意味しない。

## S1：乾式被覆の構造を3Dで測定

Friebel et al. (2024), Three-Dimensional Characterization of Dry Particle Coating Structures Originating from the Mechano-fusion Process. [出版社全文](https://academic.oup.com/mam/article/30/2/179/7624475)、[DOI](https://doi.org/10.1093/mam/ozae009)。Materials and Methods、式1〜3、Table 1/4を確認。

アルミナ母粒45.64 µm・密度3.95 g/cm³、架橋PS子粒3.5 µm・1.05 g/cm³。5000/4000/3000 rpm、10/10/20分の比較。式1/2へ掲載中央値を代入すると子粒8.6363 wt%となり、本文・Table 1の9.12 wt%とは一致しない。分布に基づく別の代表径等の可能性を否定できず、誤植とは断定しない。式3のcoating efficiencyは層の区別を含まない計数指標で、面積被覆率や滑走成功率に読み替えない。

同じ温度上昇の測定位置は蓋の外面。Table 4の5000 rpmは13.25 K。試料内部温度・工業装置のkWh/kgではない。今回の費用へ直接転用していない。

## S2：被覆粒子の変形測定

Gräfensteiner et al., An AFM-based approach for quantification of guest particle deformation during mechano-fusion. [著者プレプリント v1](https://arxiv.org/abs/2311.03851v1)、[掲載論文 DOI](https://doi.org/10.1016/j.powtec.2023.119293)、Powder Technology 434 (2024) 119293。

取得した15頁PDFのp3、p9〜13を確認。体積一定の楕円体フィットで、処理前40粒・処理後240粒、平均アスペクト比1.27→1.53。球対称性・既知体積の仮定とAFM測定誤差の議論がある。この平均から個々の粒が軸対称扁平体とは断定できない。

p3には5000 rpm・10分・蓋外面7.01 Kとあり、S1の5000 rpm・13.25 Kと整合しない。別試料・版差の特定は未了。温度値を混ぜて加工窓を作らない。今回の理想扁平体53.18という必要比は文献実測ではない。

確認PDF SHA256：b96795c2902e70468649f3e89814b0b49401af5aa201e313eb82753eb12dc81a（4,814,708 bytes）。PDFは一時参照後に削除する。

## S3：加工を強めた場合の限界

Seyffer et al., Guest particle deformation and powder flow behavior in mechano-fusion: Linking microscopic structure to macroscopic performance. Powder Technology 469 Part 3 (2026) 121853。[出版社本文・抄録](https://www.sciencedirect.com/science/article/abs/pii/S0032591025012483)、[DOI](https://doi.org/10.1016/j.powtec.2025.121853)。出版社が検索に返した本文、Fig. 4周辺と結論を確認。原データセットは[OPARA-933](https://doi.org/10.25532/OPARA-933)があるが、今回取得・再解析していない。

アルミナ／PS系では低強度側に混合のみ、高強度側に変形・粉砕・複雑な多層がある。6500 min⁻¹では32分から強い変形・粉砕を報告し、1 µm未満の破片も記載。分級で未付着分と弱い付着分が外れる影響を分けている。対象素材・機械の結果であり、軽量開放粒の限界回転数ではない。

## S4：小型装置の現行仕様

[Hosokawa Alpine Picobond](https://www.hosokawa-alpine.com/powder-particle-processing/technologies/special-solutions/picoline/picobond/)の公式仕様。AMSは約190 mL、630 W、ロータ40 mm、最高7300 rpm。NOBの220 mL・8000 rpmとは区別する。冷却・不活性ガス・バッチ処理の記載あり。630 Wは駆動仕様で実消費電力ではない。

今回の100 L／1000 Lは製品型式ではなく容量仮定。190 mLも2024年実験の機器構成と同一と断定しない。処理時間・充填率・かさ密度を仮定した処理量はメーカー保証ではない。

## S5：被覆装置の方式

[ホソカワミクロン AMS公式説明](https://www.hosokawamicron.co.jp/en/product/machines/detail/214.html)。圧縮・剪断・循環による乾式複合化、形状変更、冷却ジャケットを記載。開放骨格を壊さないこと、付着寿命、50℃での滑走、価格の証拠には使わない。

## S6：別の被覆方法と付着確認

Michelle Ramlakhan Mohan (2001), An experimental study of dry particle coating: devices, operating parameters and applications. [NJIT学位論文の著者抄録](https://digitalcommons.njit.edu/dissertations/480/)。MAIC・Mechanofusion・Hybridizerを比較し、セルロース／澱粉母粒の被覆、Fe/Ni/Cr汚染と超音波による脱離評価を記載。今回の参照は抄録まで。MAICなら本案の脆い枝が必ず保護されるとはしない。シリカの実験例は採用配合ではない。

## S7：別工程の技術的先行例

[US4206165A：Method of co-extrusion with foam core](https://patents.google.com/patent/US4206165A/en)、公開1980-06-03。発泡芯と緻密な表層を共押出しし、温度差で接合を制御する工程の記載。今回の部分被覆・開放粒・450 µm寸法・安全・雪感はこの特許で実証されていない。特許の記載は独立の性能検証ではなく、本案の新規性・実施自由を確認したものでもない。

## 継承資料

[第33巡](../GPT回答_多方向探索第33巡_局部圧力を抑える接点と接触材料の選び直し_20261008.md)：接触曲率・圧力上限・材料候補。R=500 µm等は仮定で、最適値ではない。
[第32巡](../GPT回答_多方向探索第32巡_板の走りとエッジの切れを分ける接点設計_20261008.md)：法線損失とエッジ解放。
[第31巡](../GPT回答_多方向探索第31巡_短距離拡散と微粒製造を両立する設計_20261008.md)：短距離発泡・開孔と製粒。
[回覧板](../../回覧板.md)：R39、保守条件、Claude v2/v3の共有状況。

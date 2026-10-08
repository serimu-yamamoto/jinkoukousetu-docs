# 第37巡 一次資料と採否

参照日2026-10-08。以下は発表された研究の確認で、本プロジェクトによる物理試験ではない。論文本文の再配布は行わず、リンク、必要な実験条件、記載の不一致と本案への適用限界を残す。

|ID|一次資料|今回利用する事実・適用限界|
|---|---|---|
|S1|Wei, Dao, Liu, Chen (2018), [Suspended polyhydroxyalkanoate microspheres as 3D carriers for mammalian cell growth](https://www.tandfonline.com/doi/full/10.1080/21691401.2018.1459635), DOI 10.1080/21691401.2018.1459635|PHBVHHxの開放多孔粒。Methodsの乳化・洗浄・吸水手順、Resultsの粒径・孔径・WURを使用。薬剤や培養試薬をスキー素材へ採用する提案ではない。人体・環境の全曝露安全、50℃荷重、摩擦は未立証。|
|S2|Zhang et al. (2022), [Supercritical CO2 Foaming of Poly(3-hydroxybutyrate-co-4-hydroxybutyrate)](https://pmc.ncbi.nlm.nih.gov/articles/PMC9144235/), Polymers 14, 2018, DOI [10.3390/polym14102018](https://doi.org/10.3390/polym14102018)|5×5 mmの原料片10 gを加圧発泡、保持60分。4HB割合によって発泡条件が変わる。30分圧縮後の厚さ回復の測定を、50℃・湿潤・反復滑走の耐久性には置き換えない。|
|S3|Xu et al. (2020), [Foaming of Poly(3-hydroxybutyrate-co-3-hydroxyvalerate) with Supercritical Carbon Dioxide: Foaming Performance and Crystallization Behavior](https://pubs.acs.org/doi/10.1021/acsomega.9b04501), ACS Omega 5, 9839–9845, DOI 10.1021/acsomega.9b04501|175℃30分の後、発泡温度でさらに90分保持。本文の実験方法まで確認し、30分だけの工程とは数えない。161℃近傍の一部開孔と、165℃での崩壊・合体を区別。発泡体から安全な枝粒を量産した証拠ではない。|
|S4|Calosi et al. (2026-08-10), [Study of the Biodegradation Properties of Amorphous Blends of Poly(Lactic Acid) and Poly(3-Hydroxybutyrate-co-4-Hydroxybutyrate) Foamed With Supercritical CO2](https://onlinelibrary.wiley.com/doi/full/10.1002/mame.70318), Macromolecular Materials and Engineering, DOI 10.1002/mame.70318|非晶性PLA/PHA混合発泡。50℃90 barで低密度でも、DSCのPLA相Tg約49℃。形成温度と使用耐熱性は別。海水中の選択的PHA損失、崩壊と無機化の違いを屋外寿命・微粉対策へ適用。|

## 読取上の注意

S1は出版社の検索索引にあるMethods、ResultsとPDF掲載部分を確認した。直接openの全文/PDF取得はエラーになり、PDF原本の全ページ画像照合は未完了。数値を実験追試で確認したとはしない。

- S1のAbstractの列挙順には製法との対応の不整合がある。PMS=気体/油/水、HMS=水/油/水、SMS=油/水というMethodsを採用した。
- S1の0.75 g/15 mLを体積当たり濃度として使う。「5 wt%」表記をそのまま質量分率の根拠にはしない。
- 洗浄4回と500 mL以上の記述は、総量と各回のどちらかが明確でない。モデルは合計0.5 Lと2.0 Lの二つの帳簿解釈。これは洗浄性能の上下限ではない。
- WURはMethodsの式とResultsの文章で定義が1ずれる。両方を計算し、どちらでも同じ採否となる点だけを使う。
- S2のDMA周波数は本文に1 MHzとある。未照会のまま1 Hzへ訂正せず、今回の50℃物性入力には使わない。70–100 barという全範囲が超臨界条件になるとも断定しない。
- S3の圧力範囲はResultsに最大29 MPaがあり、Methodsの10–20 MPaとの対応は照会事項。今回の計算は圧力別の性能を推定していない。
- S4 §3.3の密度0.04–0.07 g/Lは、同本文のg/cm³値・図・要旨と整合しない。1000倍の単位差があるため、当該記述をそのまま設計密度へ転記しない。本モデルの50/120/240/400 kg/m³は独立した仮定。

S2/S3はPMCの直接openにブラウザー確認が出る場合があったため、出版社又は公開一次本文の検索索引を併読した。S4は出版社全文のMethods、Tables、Discussionを確認。アクセス制限を回避していない。

## 継承資料

[第30巡](../GPT回答_多方向探索第30巡_浸水履歴と開放支持骨格の設計_20261008.md)の孔接続・浸水履歴、[第31巡](../GPT回答_多方向探索第31巡_短距離拡散と微粒製造を両立する設計_20261008.md)の拡散と外皮、[第36巡](../GPT回答_多方向探索第36巡_加圧で戻る材料と現地整地の分離_20261008.md)の粒単位工程能力を継承する。同じ公式を新規の材料実証として数えない。

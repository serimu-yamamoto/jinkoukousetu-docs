# 第36巡 出典と適用範囲

調査日：2026-10-08。一次論文4件。下記の性能は著者の試験条件に属し、本計画の試作・滑走結果ではない。レビューは一次論文を探す入口だけに使用し、候補の採用根拠にはしていない。

|ID|一次論文と参照箇所|設計へ残す事実|適用しない飛躍|
|---|---|---|---|
|S1|Taniguchi & Lovell (2012), *Low-Temperature Processable Degradable Polyesters*, Macromolecules 45, 7420–7428。[DOI](https://doi.org/10.1021/ma301230y)、[著者原稿](https://pmc.ncbi.nlm.nih.gov/articles/PMC3468741/)。Low-temperature processing節|PDXO/PmCL-PLLAの所定組成は25℃、34.5 MPa、5分で成形。PCL-PLLAは室温で同様に加工できず65℃を要した|低温加工可能性は50℃の床剛性・反復接点回復ではない|
|S2|Sharma et al. (2025), *Baroplastic Effect of Aliphatic Polyester Block Copolymers for Degradation-Free Multicycle Processing of Poly(l-lactide)*, ACS Macro Letters 14, 1716–1720。[DOI](https://doi.org/10.1021/acsmacrolett.5c00483)、[本文](https://pmc.ncbi.nlm.nih.gov/articles/PMC12632162/)。Experimental、Figures 2–5と本文|PmCL-PLLA添加でPLLAの流動温度を低下。50 MPa、昇温5℃/分、予備反復後の配合系列をinputsへ転記|流動開始温度は使用温度上限や50℃クリープの証拠ではない。別樹脂との相溶・接着へ外挿しない|
|S3|Xu et al. (2026), *Compostable and Recyclable Baroplastic Triblock Copolymers Enable Low-Energy Polymer Processing*, Small 22, e14939。[DOI](https://doi.org/10.1002/smll.202514939)、[本文](https://pmc.ncbi.nlm.nih.gov/articles/PMC13325701/)。2.1–2.3、Figures 2/4、4.8–4.11|PLLA-PEG-PLLAの所定鎖長。標準37℃/10 MPa、低条件22℃/5 MPaの記載。初期膜形成5分、Fig.4再圧縮1時間、初期比較膜14時間を分離。PEG融解は約50℃|薄膜・初期材料・再生膜・別配合の生物試験を一つの性能セットへ合成しない|
|S4|Ruiz-Franco & Giuntoli (2025), *Inducing mechanical self-healing in polymer glasses*, Nature Communications 16, 4085。[DOI](https://doi.org/10.1038/s41467-025-59426-6)、[本文](https://www.nature.com/articles/s41467-025-59426-6)、[公開コード・データ](https://doi.org/10.5281/zenodo.15170122)。Figure 2、Discussion、Methods|非晶質の粗視化分子モデルで振動による人工孔の閉鎖。著者の概略単位2 ps、0.5 nmとω=0.1、72周期を単位監査に使用|実材料の周波数較正ではなく、粒群や半結晶骨格の振動ローラー条件へ換算できない。本巡で著者MDを再実行していない|

S1はPMC直接取得が確認画面となったため、検索が返す一次本文の加工節と書誌を確認した。S2/S3/S4は公開本文を確認。S3補足docxはPMCがHTMLを返し、出版社側取得は403だったため未確認。アクセス制御を迂回していない。

S3の再生時間はFig.4の1時間とMethods 4.11の「同条件」（直前に14時間を記載）で読み取りが一致しない。両方を工程感度として残し、都合よく5分へ置き換えない。低条件22℃/5 MPaの保持時間はnull。

S3の環境評価は58℃の湿潤堆肥で60日、別配合の懸濁粒を用いた細胞・ミジンコの限られた試験。野外土壌、冬、吸入・皮膚、摩耗粉、長期生態影響の合格にはしない。再生例には低温粉砕が含まれる。実用化時の残留触媒・溶剤、用具摩耗、溶出、粒子捕集は未評価。論文に出る溶剤・NaOH・フッ素系離型材等を現地用材料へ採用する指示ではない。

S2の配合名40/50/60は公称値で、NMR由来のPLLA割合38/49/57 wt%とは違う。再現表は本文の公称系列を保存する。4回の予備加工を経た値を初回加工値として扱わない。

既存検討：[第26巡](../GPT回答_多方向探索第26巡_自己修復接点の保持時間と雪らしい解放_20261008.md)は自己修復・振動を既に調査済み。本巡での追加は加圧流動材料、加圧工程の在庫・力、再生と初期成形の条件分離、MD単位の具体監査。[第35巡](../GPT回答_多方向探索第35巡_分子結晶の再評価と少量接点の再成長_20261008.md)の水系結晶接点と比較する。

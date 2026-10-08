# 第38巡 一次資料と適用範囲

参照日2026-10-08。一次資料6件と、S4の訂正情報を確認した。原著全文は再配布せず、下記リンクと採否を共有する。ここにある研究は本プロジェクトの実験件数に含めない。

|ID|一次資料|今回の利用と限界|
|---|---|---|
|S1|Rizvi et al. (2018), [Non-crosslinked thermoplastic reticulated polymer foams from crystallization-induced structural heterogeneities](https://www.sciencedirect.com/science/article/abs/pii/S0032386117311618), Polymer 135, 185–192, DOI [10.1016/j.polymer.2017.12.006](https://doi.org/10.1016/j.polymer.2017.12.006)|PP/PTFEの連続押出し・CO₂発泡。密度0.07 g/cm³、開孔率97.7%という報告は当該配合のみ。膜の開孔と骨格保持を分ける機構の参考。フッ素相に依存する配合を本案へ採用せず、PHAや無添加PPへ数値を転用しない。出版社の要旨・導入部分を検索索引で確認、直接openは403。本文の全図表は未照合。|
|S2|Nathan et al. (2017), [Particulate Release From Nanoparticle-Loaded Shape Memory Polymer Foams](https://pmc.ncbi.nlm.nih.gov/articles/PMC5253671/), Journal of Medical Devices 11, 011009, DOI [10.1115/1.4035547](https://doi.org/10.1115/1.4035547)|膜の機械的開孔で粒子放出が増え、洗浄履歴が影響する比較。浮動ピンと振動の処理は4時間。10/25/50 µm以上という粒子計測区分は、より小さい摩耗粉がない証明ではない。SMP、充填剤、医療用の限度値を屋外スキー材へ移さない。PMC直接openはブラウザー確認、公開本文のMethods/Resultsを検索索引で確認。|
|S3|公開特許WO2003066298A1 (2003), [Process for grinding mixtures of polymeric foams](https://patents.google.com/patent/WO2003066298A1)|明細書¶0036等は、中心から長い部分が突出しない粉末を好ましい対象としている。つまり普通の粉砕工程の目的はH38の枝保持と一致しない場合がある。記載は出願人の技術開示で、第三者再現や本案の製造歩留まりの実証ではない。権利状態・実施自由性の判断は行っていない。|
|S4|Tucker & Spear (2019), [A Tool to Generate Grain-Resolved Open-Cell Metal Foam Models](https://mmm.mech.utah.edu/wp-content/uploads/2019/06/2019_TuckerSpear_IMMI_GrainMappedFoamModels.pdf), DOI [10.1007/s40192-019-00136-5](https://doi.org/10.1007/s40192-019-00136-5), [NSF掲載原稿](https://par.nsf.gov/servlets/purl/10101011)|節点、ストラットの厚み変化、断面形状を分ける形態生成の参考。金属泡のモデルで、PHA物性の根拠ではない。今回の放物線半径・diamond接続・分断モデルは独自の簡略化で、同論文のアルゴリズムを実装したものではない。公開PDFを取得して書誌・形態説明を確認。|
|S5|Bang et al. (2023), [Fluid Flow Templating of Polymeric Soft Matter with Diverse Morphologies](https://advanced.onlinelibrary.wiley.com/doi/10.1002/adma.202211438), Advanced Materials 35, 2211438, DOI 10.1002/adma.202211438|第27巡の資料を再参照。流れ、分子鎖の絡み、析出速度で枝・繊維・リボン・シートが変わる。高い剪断入力が強いゲル化に結び付いても、末端枝長との強い相関は確立されていない。直接粒形成の代替経路へ残すが、回転数だけで目的枝長や乾いた雪感を保証しない。出版社全文§2/Figs.1–5を確認。|
|S6|BlueQuartz Software, [DREAM.3D: Establish Foam Morphology](https://dream3d.bluequartz.net/Help/Filters/DREAM3DReviewFilters/EstablishFoamMorphology/)|公式ソフト文書。最小ストラット厚み、節点へ向かう厚み変化、断面形状は別の入力である。今回DREAM.3Dを実行したとはしない。|

S4には[2019年の訂正](https://link.springer.com/article/10.1007/s40192-019-00152-5)が存在する。出版社で存在・書誌・補足ファイルの掲示を確認したが、訂正本文は購読対象で未取得。訂正の中身を推測して「影響なし」としない。S4から実測パラメータやコードを転用せず、形状の区別はS6とも照合した。本巡の数式と入力はmodel.mdで独立定義している。

## 既出資料との違い

[第27巡](../GPT回答_多方向探索第27巡_枝状粒の形成と微細枝の熱仕上げ_20261008.md)の直接枝形成、[第28巡](../GPT回答_多方向探索第28巡_枝熱伝導の反証と噴出時の直接製粒_20261008.md)の熱仕上げの限界、[第37巡](../GPT回答_多方向探索第37巡_一括発泡による開放粒と雨後重量の設計_20261008.md)の一括製造案を継承した。本巡では切断位置・独立粒化・質量回収を初めてこの簡略骨格上で結び付けた。S5を新発見として数えない。

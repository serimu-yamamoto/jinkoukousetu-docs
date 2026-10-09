# 出典と調査記録

確認日：2026-10-10 JST。調査前に調査台帳/一般.md・計算部品索引.mdを検索。連鎖・fiber bundle・閾値分布・局在に関する該当する既存解析を見つけなかった。軟化に関する鉱物・熱の既存項目は別の現象として再利用範囲を分けた。全分野で新規という意味ではない。

| 資料 | 実際に確認した範囲 | 採用すること／採用しないこと |
|---|---|---|
| [Kun, Zapperi, Herrmann: Damage in fiber bundle models](https://arxiv.org/pdf/cond-mat/9908226) | 著者公開PDF、2節と3節の1回軟化式 | 剛性減少と荷重再分配の模型。人工雪での実測や可逆再生の根拠にしない |
| [Raischel, Kun, Herrmann: Failure process of a bundle of plastic fibers](https://arxiv.org/pdf/cond-mat/0601290) / [DOI](https://doi.org/10.1103/PhysRevE.73.066101) | 著者公開PDF、2節・3節、式(1)(2) | 破断時荷重の一定割合を保持するαと、本巡の剛性割合βを区別。同論文の臨界値を流用しない |
| [Karpas, Kun: Blending stiffness and strength disorder can stabilize fracture](https://arxiv.org/pdf/1604.01430) / [DOI](https://doi.org/10.1103/PhysRevE.93.033002) | 著者公開PDF、II節 | 強度/剛性の比と順序の関係。同論文の独立乱数条件を、本巡の相関付き分布と混同しない |
| [Hao, Yang, Liang: Catastrophic Failure and Critical Scaling Laws of Fiber Bundle Material](https://www.mdpi.com/1996-1944/10/5/515) / [DOI](https://doi.org/10.3390/ma10050515) | 出版社検索取得の結論本文。ページ直接取得は失敗、PMCは確認画面 | 直列機械剛性と負の接線の関係。文献の数値・指数を製品へ転用しない |

2000年論文の公開稿はarXiv v2（2000-04-15）、2006年論文はv2（2006-07-07）、2016年論文はv1（2016-04-05）。PDF内部の組版日が後年でも研究発表年として使わない。

第100巡の[梁模型](../開離中の荷重移行と支持接点の検証_20261010/load_sharing.py)は有限な板剛性での空間的荷重集中の根拠として既存成果を参照。今回の剛板はその代用ではない。

Claudeの[物性監査](../../調査台帳/物性値照合_自律ループv2v3.md)のLF正規化SHA256は054c9388de3be3bd251c395059a9e02c9d3b336885236683ba3f528ff819d71f。今回の確認時点で前巡と同じ。新しい全結果・元コード・返答・稼働は未確認。鉱物・噴霧案を採用済みに変更しない。

H101-Cの受渡し形状、重複余裕式、費用感度、数値例は本巡の仮説・計算であり、上記論文がその製品を実証したとの意味ではない。

# 第53巡 出典監査

確認日：2026-10-09。第三者本文・PDF・入力例ZIPは成果へ再配布せず、参照先と取得時の同一性を記録する。

|ID|資料|確認範囲と使い方|
|---|---|---|
|S1|Meuchelböck et al., Influence of temperature on the compression properties of expanded thermoplastic polyurethane (ETPU), 2024. DOI 10.1186/s40712-024-00149-9。[原著](https://link.springer.com/article/10.1186/s40712-024-00149-9)、[大学公開PDF](https://epub.uni-bayreuth.de/8758/1/s40712-024-00149-9-1.pdf)|本文とPDF全体のテキスト、図9・10の画像を確認。図の温度点、回復待ち時間、成形体・速度の範囲を記録。50℃への補間値を測定値として作らない。|
|S2|Hu et al., Self-Reinforced Thermoplastic Polyurethane Wrinkled Foams with High Energy Absorption Realized by Gas Cooling Assisted Supercritical CO2 Foaming, Ind. Eng. Chem. Res. 61 (2022), 4832–4841. DOI 10.1021/acs.iecr.2c00001。[出版社](https://pubs.acs.org/doi/abs/10.1021/acs.iecr.2c00001)、[著者稿PDF](https://publications.aston.ac.uk/id/document/85867)|著者稿を抽出、p.18と図7を画像確認。気泡径・密度・同一応力での軸ひずみを転記。回復率・エネルギー返還を滑走摩擦へ換算しない。|
|S3|Ellingham et al., Microcellular injection molding process for producing lightweight thermoplastic polyurethane with customizable properties, Front. Mech. Eng. 13 (2018), 96–106. DOI 10.1007/s11465-018-0498-6。[出版社](https://journal.hep.com.cn/fme/EN/10.1007/s11465-018-0498-6)|公開要旨と書誌を確認。局所密度を変える工程の存在まで。500µm粒の量産、価格、歩留まりを示す資料として扱わない。|
|S4|Maciariello, Lucchetta & Sorgato, Mechanical recycling of TPU foams via microcellular injection molding - effects on hard segments crystallization, cell structure, and mechanical properties, Int. J. Adv. Manuf. Technol. 144 (2026), 2155–2169. DOI 10.1007/s00170-026-18031-7。[原著](https://link.springer.com/article/10.1007/s00170-026-18031-7)|出版社の全文、材料・工場内回収材・疲労方法・結果を確認。小さい気泡だけで新品性能を保証できない反例。土砂を含むコース回収材の再生率へ移さない。|
|S5|Zhu et al., Fatigue behaviors and cellular damages of bead-welded foam of poly(ether-b-amide) under cyclic compression, Int. J. Fatigue 194 (2025), 108841. DOI 10.1016/j.ijfatigue.2025.108841。[出版社](https://www.sciencedirect.com/science/article/pii/S0142112325000386)|出版社の検索表示にある要旨・抜粋まで。直接本文取得は失敗。PEBAの対照候補を残すために使用し、数値モデルへ入力していない。|

## 記載差を解決したことにしない

S1：本文・結論は60℃までの回復を説明する一方、図9・10には50℃・60℃の測定点を確認できない。本文の高さ再測定は24時間、図注は72時間。第2回圧縮は72時間後23℃。この相違を保持し、いずれかへ勝手に統一しない。

S1が示す[公開解析リポジトリ](https://github.com/Polymer-Engineering-University-Bayreuth/MechanicalProps_Foams)も確認した。rootにはLICENSE、README.md、efficiency_absorption.ipynb、input_examples.zip。ZIP内はfile1〜file9、test_ASCII、test_excel等の形式例であり、今回確認した情報では50℃・60℃の試料に同定できない。ZIPのGit blob SHAは9f8b6b9c87934dc8c9a748114e90d17e9e33d50d。著者コードを今回の物理試験として実行していない。

S2：著者稿p.18は質量密度0.218g/cm³と空隙率0.788を記載するが、材料節の緻密相1.12g/cm³と空隙率の定義からは1−0.218/1.12=0.80536。約1.74百分率点の差がある。「cell density」という本文ラベルにもg/cm³が付いており、ここでは単位に従って質量密度として転記した。雨水計算は0.788と0.80536を別条件に保存し、測定精度や信頼区間とは呼ばない。

S2：p.18の弾性率低下率と図7cの点の比は視読で一致しない。図のデジタイズ精度を確定していないため、独自の訂正値を作らず、低下率を寿命・50℃での剛性保持へ代入しない。本文の強化率、回復率、エネルギー損失率もそれぞれ異なる載荷条件に属し、一つの性能値へ統合しない。

## 模型の入力を分離

- source-values.csv：資料から転記した7行。S1の圧縮成形体とS2の小試料を別の識別子で記録。
- 切断影響域の深さ0.5〜1気泡、皮膜厚2〜10µm、6枝形状、充填率、雨水アクセス・保持率、粒内体積比J、仮単価、工場速度等：独自の感度条件。
- 切断影響域は、破れた気泡率・開気泡率・吸水率ではない。
- 6枝の重量模型と連続異形材は別の形状。必要量と工程負荷を評価するための候補比較で、同時成立した製作図ではない。
- 50℃、雪同等の滑走、人体・環境への無害性、冬の固着、雨後復旧を証明する完成粒の試験データはない。

## 取得ファイルの同一性

- etpu2024.pdf：6881049 bytes／SHA-256 23f1ab44d1eaeb3a912372ccd9ee01c90522ea21e5f587d41ad50ffb5112a610
- wrinkled.pdf：1903177 bytes／SHA-256 1d43cf7af099c41db85a92b703d333ceaab0bc7772af15d3c8ec51ea51859a51
- input_examples.zip：1709294 bytes／SHA-256 a6237261c35c8d746f6615bdf4764a3af227e387b9bd5b03093fc4da41d3cbdb

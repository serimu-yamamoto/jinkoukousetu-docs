# 参照資料と適用範囲

確認日：2026-10-23。実測0件。一次資料の方法・環境値と、人工フィルンへの独自提案を区別する。

| 資料 | 使用した範囲・留保 |
|---|---|
| [一般排水基準](https://www.env.go.jp/water/impure/haisui.html) | pH海域以外5.8–8.6、BOD/COD160（日平均120）mg/L。施設・排水量・水域等の適用条件付き。製品の無害性基準ではない。 |
| [2026年掲載の水質環境基準一覧](https://www.pref.saitama.lg.jp/a0505/suisitukankyoukijun.html) | 河川AA：pH6.5–8.5、BOD≤1mg/L。湖沼AA：pH6.5–8.5、COD≤1mg/L。2026-09-02掲載。受水域の基準。 |
| [水質環境基準・河川](https://www.env.go.jp/kijun/wt2-1-1.html) | pH・BODの数値を確認。古い表記を含むページのため、最新の大腸菌項目等の根拠には用いない。 |
| [水質環境基準・湖沼](https://www.env.go.jp/kijun/wt2-1-2.html) | pH・CODの数値のみ参照。旧表記項目を現行値として引用しない。 |
| [第十八改正日本薬局方2.47](https://www.mhlw.go.jp/content/11120000/000788359.pdf) | 凝固点降下法、ΔT=K m、水のK=1.86。0.01Kはプロジェクト目標で法定環境上限ではない。 |
| [作業環境評価基準](https://www.mhlw.go.jp/web/t_doc?dataId=74088000) | 鉱物性粉じん等のE=3.0/(1.19Q+1)mg/m³。Qは遊離けい酸含有率。一般利用者の安全濃度への転用不可。 |
| [吸入性粉じんの分粒特性](https://www.mhlw.go.jp/content/11303000/2r9852000001xph4.pdf) | 空気力学径4µm、50%分粒の説明のみ使用。資料固有の別作業の濃度区分は転用しない。 |
| [大気の環境基準](https://www.env.go.jp/kijun/taiki.html) | SPM：1時間値の日平均0.10mg/m³、1時間値0.20mg/m³。評価時間と背景濃度を伴う。 |
| [PM2.5環境基準告示](https://www.env.go.jp/content/900479266.pdf) | 年平均15µg/m³、日平均35µg/m³。短時間試験で適合を認定しない。 |
| [粉状物質の有害性情報伝達等の通知](https://www.mhlw.go.jp/web/t_doc?dataId=00tc2991&dataType=1) | 粉体の危険有害性情報とばく露評価。食品用・未分類を吸入無害と同一視しない。 |
| [生物応答を用いた排水試験法（検討案）](https://www.env.go.jp/content/900541513.pdf) | 藻類・ミジンコ・魚類の枠組み、5–80%試験系列。NOEC≥80%を本材料の選別条件にすることは独自提案・未確認で、法定上限ではない。 |
| [環境リスク初期評価ガイドラインを含む資料](https://www.env.go.jp/content/900501350.pdf) | PEC/PNEC<0.1の区分は低い検討優先度を示す。無害の保証・法定認証ではない。PNEC等がなければ未確認。 |

## 再現

サーバー等の作業環境で、リポジトリ内の計算部品を同じ場所に保持して次を実行する。

    python3 -B 計算部品/stage2_ab_safety_audit.py

calculation_results.jsonは未測定の密度・価格等を置いた算術。13照合の通過は物性の検証ではない。入力のSHA256はinput_metadata.json、参照先の取得結果はlink_checks.jsonに保存。

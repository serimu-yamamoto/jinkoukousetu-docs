# Capillo-Firn v2.1の監査記録

2026-10-22。実物試験0件。成功確率未算定。添付された原案の検証であり、新配合の性能保証ではない。

- [監査報告](../GPT回答_Capillo-Firn_v2.1の感触台風採算監査_20261022.md)
- [Gemini等へ渡す回答文（未送信）](監査回答.txt)
- [提供Python](submitted_audit.py) と [その再実行出力](submitted_results.json)
- [独立物量・能力・費用監査](../../計算部品/capillo_v21_system_audit.py) と [結果](audit_results.json)
- [入力識別・SHA256](input_metadata.json)、[出典と確認範囲](sources.json)

提供Pythonはmath/jsonと算術・出力だけであることを目視とASTで確認して実行した。独立監査は既存のformulation_claim_audit.py、capillo_physics_audit.pyを再利用する。新しい10個の確認は質量保存・処理上限・境界条件等の算術整合で、材料試験10件という意味ではない。

実行は開発サーバー上の作業用チェックアウトで行う。リポジトリの計算部品ディレクトリをPython検索パスへ追加し、capillo_v21_system_audit.audit()の戻り値をJSON化すればaudit_results.jsonを再生成できる。提供コードはsubmitted_audit.pyをPython3で実行する。-Bを付けて不要なキャッシュを作らない。

標準の再生能力は「湿潤完成粒200kg/h、8h/日、220日」として計算した。乾燥完成粒200kg/hの場合も別に収録。入力能力、回収率、製造歩留まり、性能合格率は同じではない。全て原案の仮定への感度計算で、処理能力、損耗率、需要、価格、試験設備を実測・確保したものではない。

GitHubで各ファイルの公開内容を照合してから、この監査のサーバー作業コピーと当方が新規作成した共通部品コピーを削除する。既存の接続案内、他者のファイル、依頼者添付は削除対象にしない。

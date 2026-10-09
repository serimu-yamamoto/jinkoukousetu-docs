# 再利用する計算部品

- [flared_ligament.py](flared_ligament.py)：可変幅支柱のQ4平面応力、断面と局所流路の積分。[第104巡](../GPT往復/拡大流路と支持剛性の連成監査_20261010/README.md)。

- [graded_contact.py](graded_contact.py)：区分一次剛性と自由回転の片側接触。handover_contacts.pyの幾何を再利用。[第103巡](../GPT往復/受け面の剛性勾配と薄枝実現条件の検証_20261010/README.md)。

- [handover_contacts.py](handover_contacts.py)：第102巡の圧縮のみの局所接触・重なり面積・曲面受渡し。標準ライブラリのみ。50℃や実粒の物性は未較正。
- [入力・再現・限界](../GPT往復/曲面補償と面積受渡しの有限形状検証_20261010/README.md)。正本はこのGitHub。サーバーの ~/firn/lib へ展開して利用できる。今回の作業用コピーは公開照合後に削除する。

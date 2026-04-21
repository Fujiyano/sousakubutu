# other/

VHF 本体 (脆弱性ハンドリング) や DSL の動作には**直接必要ない**ファイルを
退避してあるフォルダ。必要になったらいつでもルートに戻せる。

## 中身

| ファイル | 分類 | 理由 |
|---|---|---|
| `origin_router.py` | 旧版 | `router.py` に置き換えられた昔のコピー。どこからも import されていない |
| `server.py` | デモサーバ (代替) | `from app import *` で立ち上げる旧デモエントリポイント |
| `server2.py` | デモサーバ (代替) | 同上。`bottle.jinja2_template` を使う版 |
| `preserver.py` | デモサーバ (代替) | 同上 |
| `xss_server.py` | デモサーバ (代替) | XSS 検証用のデモエントリポイント |

ルートに残したデモサーバは `my_server.py` のみ。
他のデモサーバを使いたいときは、このフォルダからルートに戻せば `from app import *`
がそのまま解決する (app.py 等はルートに置いたまま)。

## 以前ここに置く予定だったが、ユーザ判断で削除済みのもの

スクラッチ / メモ系 (a.py, aiueo.py, ast_test.py, "import ast.py", memo.py,
memo.c, cvefrtest.py, auth.py, sonota/) は既に削除済み。

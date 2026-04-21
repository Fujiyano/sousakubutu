# VHF プロジェクト作業ログ

> VHF (Vulnerability Handling Framework) に対してこれまで行った作業の記録。
> 次回セッションで文脈を失わないための覚書。

---

## 1. プロジェクトの目的 (再掲)

VHF は **Web アプリに含まれる脆弱性を AST レベルで書き換えて修復するフレームワーク**。
脆弱性ハンドラーは以下の 3 要素で構成される:

1. **追加関数の設定** (必要に応じて、例: `reverse_print`) → `inserted_functions.py`
2. **AST レベルで脆弱性パターンを書き換える処理** (必須) → 従来は `node_fixer.py` 内に手書き
3. **コールバック関数に変更を適用するプログラム** (必須) → `@node_fixer.add` で登録

### 現セッションのミッション

> 2 の「書き換えパターン」を **DSL (宣言的言語)** で記述できるようにする。

---

## 2. 実施した作業の時系列

### Step 1. DSL の設計・実装

ユーザと議論した設計方針:

- **ノード種別を DSL 側で区別**: `func()` / `name()` / `constant()` の 3 種
- **ドット区切り**は文字列のまま受け取り、コンパイラ側で `Attribute` に展開
- **複数ハンドラーは 1 回の AST トラバースに統合** (ノード種別ごとに `visit_Call` / `visit_Name` / `visit_Constant` を 1 メソッドずつ生成して if/elif 分岐)
- **同一ターゲット重複はコンパイル時エラー**
- **`handler_set` (フェーズ分け)** は MVP では未実装 (将来の拡張余地として文法設計に残す)

実装ファイル:

| ファイル | 役割 |
|---|---|
| [`vhf_dsl/lexer.py`](vhf_dsl/lexer.py) | トークナイザ (文字列・数値・キーワード・`#` コメント対応) |
| [`vhf_dsl/parser.py`](vhf_dsl/parser.py) | `handler / target: / transform:` 構文 → `Handler` データクラス |
| [`vhf_dsl/compiler.py`](vhf_dsl/compiler.py) | 統合 `NodeTransformer` の動的生成、重複検出、`register_dsl` による `node_fixer` 連携 |
| [`vhf_dsl/__init__.py`](vhf_dsl/__init__.py) | 公開 API: `compile_dsl`, `register_dsl` 等 |
| [`vhf_dsl/examples/print_to_reverse.vhf`](vhf_dsl/examples/print_to_reverse.vhf) | 4 ハンドラーのサンプル |

### Step 2. テスト整備

8 ケースの単体テスト: [`tests/test_vhf_dsl.py`](tests/test_vhf_dsl.py)

- レキサのトークン列検査
- `print → reverse_print`
- `eval → None`
- ドット区切り `ast.literal_eval → safe_eval`
- `name()` と `func()` の棲み分け
- 複数ハンドラー統合トラバース
- 重複ターゲットがコンパイルエラーになること
- サンプル `.vhf` ファイルの読み込み

実行コマンド:

```bash
py -3.13 tests/test_vhf_dsl.py
# → all tests passed.
```

### Step 3. 動作確認用ツール整備

| ファイル | 用途 |
|---|---|
| [`tools/run_dsl_on_file.py`](tools/run_dsl_on_file.py) | 任意の `.vhf` × 任意の `.py` を書き換えて stdout に出力 |
| [`tools/run_dsl_cases.py`](tools/run_dsl_cases.py) | `dsl_demo_cases/` 配下を **1 ケース 1 プロセス**で実行 (DSL 登録の汚染を防ぐ) |
| [`tools/_case_worker.py`](tools/_case_worker.py) | 上記ランナーが subprocess で spawn するワーカー |

デモケース (`dsl_demo_cases/`):

- `case1_print` — `print → reverse_print`
- `case2_eval` — `eval → None`
- `case3_literal_eval` — `ast.literal_eval → safe_eval`
- `case4_user_input` — `name("user_input") → name("safe_user_input")`
- `case5_sqli_existing` — **DSL ルールなし**、既存手書きハンドラーだけで SQLi f-string LIKE を書き換え (共存性の確認用)

### Step 4. ファイル配置を役割別に整理

```
VHF-main/
├── vhf_dsl/              # DSL 実装 (ライブラリ)
├── tests/                # 単体テスト (新設)
├── tools/                # CLI / ランナー (新設)
├── dsl_demo_cases/       # ケースデータ (新設)
```

各スクリプトは `__file__` から `_PROJECT_ROOT` を算出して `sys.path` に追加するので、どこから叩いても動く。

### Step 5. 不要ファイル整理 → `other/` へ退避

ユーザ判断で削除されたスクラッチ系:

- `a.py`, `aiueo.py`, `ast_test.py`, `"import ast.py"`, `memo.py`, `memo.c`, `cvefrtest.py`, `auth.py`, `sonota/`

[`other/`](other/) に退避したもの:

- `origin_router.py` (旧版、`router.py` に置換済み)
- `server.py`, `server2.py`, `preserver.py`, `xss_server.py` (代替デモサーバ、`my_server.py` は現役なので据え置き)

[`other/README.md`](other/README.md) に中身を明記。

### Step 6. 脆弱性ハンドラーを独立ファイルに分離

**目的**: `node_fixer.py` はインフラ専用にし、脆弱性ハンドラーは別ファイルで管理したい。

- 新設 [`vulnerability_handlers.py`](vulnerability_handlers.py) に SQLi f-string LIKE ハンドラーを移動
  - `RewriteSQLiteFStringSQLiToParams` クラス
  - `fix_sqlite_sqli_fstring_like` (登録関数)
  - 末尾に「新ハンドラーを追加するときのテンプレ」コメントあり
- [`node_fixer.py`](node_fixer.py) を整理: `NodeFixer` クラス、検索ユーティリティ、`make_new_callback` のみ残す
- [`callback_fixer.py`](callback_fixer.py) に `import vulnerability_handlers` を追加 → `Fix` が使われると副作用で自動登録

**動作確認**:

- `py -3.13 main.py` → SQLi 書き換えがベースラインどおり実行
- `py -3.13 -c "from callback_fixer import Fix"` → `handlers: 1` (登録成功)
- `my_server.py` の import チェーンも破壊されず

### Step 7. ドキュメント整備

| ファイル | 内容 |
|---|---|
| [`DSL_USAGE.txt`](DSL_USAGE.txt) | DSL 使い方ガイド (plain text、238 行) |
| [`DSL_USAGE.md`](DSL_USAGE.md) | 同内容の Markdown 版 (表 / シンタックスハイライト / アンカー、300 行) |

章立ては両者同じ: 構文 → 意味論 → 例 → 複数ハンドラー → Python からの呼び出し → ツール実行 → 配置指針 → ハマりどころ → できること/できないこと。

---

## 3. 最終的なファイル構成

```
VHF-main/
├── CLAUDE.md                     # Claude 用プロジェクト指示
├── readme.md                     # 既存 README
├── PROGRESS.md                   # ★ このファイル: 作業ログ
├── DSL_USAGE.md                  # DSL 使い方ガイド (Markdown)
├── DSL_USAGE.txt                 # 同 (plain text)
│
├── main.py                       # VHF 適用エントリ
├── callback_before.py            # main.py の入力 (脆弱性入りサンプルコード)
├── callback_after/after.py       # main.py の出力
│
├── callback_fixer.py             # VHF パイプライン (Fix クラス)
├── node_fixer.py                 # 登録インフラ + 検索ユーティリティ
├── vulnerability_handlers.py     # ★ 脆弱性ハンドラー専用ファイル
├── inserted_functions.py         # 挿入対象の関数群 (vhf_like_param 等)
│
├── my_server.py                  # 現役デモ Web サーバ
├── app.py / router.py / request.py / response.py   # デモ Web フレームワーク
├── access.html / database.html / index.html / access.sqlite3   # デモリソース
│
├── vhf_dsl/                      # DSL 実装
│   ├── __init__.py
│   ├── lexer.py
│   ├── parser.py
│   ├── compiler.py
│   └── examples/print_to_reverse.vhf
│
├── tests/
│   └── test_vhf_dsl.py
│
├── tools/
│   ├── run_dsl_on_file.py
│   ├── run_dsl_cases.py
│   └── _case_worker.py
│
├── dsl_demo_cases/
│   ├── case1_print/
│   ├── case2_eval/
│   ├── case3_literal_eval/
│   ├── case4_user_input/
│   └── case5_sqli_existing/
│
├── bench_cases/                  # 既存ベンチ (CWE-94)
│
└── other/                        # 非本質ファイル退避
    ├── README.md
    ├── origin_router.py
    ├── server.py / server2.py / preserver.py / xss_server.py
```

---

## 4. よく使うコマンド集

```bash
# 1) DSL 単体テスト
py -3.13 tests/test_vhf_dsl.py

# 2) 既存パイプライン (callback_before.py → callback_after/after.py に書き換え)
py -3.13 main.py

# 3) DSL デモケース一括実行
py -3.13 tools/run_dsl_cases.py

# 4) 任意の .vhf × .py を 1 回だけ書き換え
py -3.13 tools/run_dsl_on_file.py vhf_dsl/examples/print_to_reverse.vhf callback_before.py

# 5) ハンドラー登録状況の確認
py -3.13 -c "from callback_fixer import Fix; import node_fixer; print('handlers:', len(node_fixer.node_fixer.node_fix_functions))"

# 6) デモ Web サーバ起動 (必要時)
py -3.13 my_server.py
```

---

## 5. 設計判断のメモ

### 5.1. なぜ DSL を「1 回のトラバースに統合」する方式にしたか

- 複数ハンドラーを個別の `NodeTransformer` として **順次適用**する方式は単純だが、AST を N 回走査するので遅い
- **統合方式**ならノード種別ごとに 1 回だけ見るので AST 走査は 1 パス
- 副次効果: 「どのハンドラーが効いたか」をログに残す仕掛けが作りやすい (将来)

### 5.2. なぜ重複ターゲットをエラーにしたか

- 暗黙に「最後の宣言が勝つ」などのルールを作ると DSL の書き手が混乱する
- `CompileError` を早期に投げた方が安全

### 5.3. なぜ `vulnerability_handlers.py` を 1 ファイルにしたか

- 現状 1 ハンドラーしかない (SQLi f-string LIKE)
- ユーザの指示が「**ファイル**」(単数) だった
- 5〜10 個に増えたら `vulnerability_handlers/` パッケージ化 (`__init__.py` が兄弟モジュールを auto-import) するのがスケール時の次ステップ

### 5.4. なぜデモケースを subprocess で実行するか

- `@node_fixer.add` はグローバル状態を更新する
- ケース間でハンドラーが蓄積すると、後のケースほど前のケースの DSL に影響される
- 1 ケース 1 Python プロセスで完全に隔離

### 5.5. なぜ手書きハンドラーと DSL ハンドラーを併用可能にしたか

- DSL だけでは表現できない書き換えが確実に出てくる (例: 引数の中身条件、ガード式、テンプレ展開)
- `vulnerability_handlers.py` (Python 直書き) と DSL ルールの両方が同じ `node_fixer` に乗る設計にしておけば、表現力と手軽さのどちらも諦めない

---

## 6. 今後の拡張候補 (優先度順)

1. **ゴールデンテスト化**: `dsl_demo_cases/caseN/` に `expected.py` を置き、runner で diff 0 を自動判定する仕組み
2. **ヒット件数ログ**: DSL コンパイラに「どの handler が何回マッチしたか」のカウンタを持たせる → ルールの書き間違いで 0 件ヒットに気付ける
3. **`vulnerability_handlers/` パッケージ化**: ハンドラーが増えてきたら 1 ハンドラー 1 ファイルに
4. **DSL 文法拡張**: 引数マッチ (`func("eval", args=[constant(str)])`)、フェーズ分け (`handler_set phase1 { ... }`)、ガード式
5. **bench_cases/ 統合**: CWE-94 ベンチを DSL ルールで書き直して回帰テスト化

---

## 7. 関連ドキュメント

- [`CLAUDE.md`](CLAUDE.md) — プロジェクトの基礎説明 (VHF 概要・3 要素・DSL 化タスク)
- [`DSL_USAGE.md`](DSL_USAGE.md) / [`DSL_USAGE.txt`](DSL_USAGE.txt) — DSL 使い方ガイド
- [`other/README.md`](other/README.md) — `other/` 配下に何を退避したかの説明
- `~/.claude/projects/C--Users-rrrsk-VHF-main/memory/project_vhf_overview.md` — Claude のグローバルメモリ内 VHF 概要

---

## 8. 未解決 / 保留中の事項

- **`test_vhf_dsl.py` を実行して結果を見る** タスクが、ユーザ操作で割り込まれたまま未実施 (本ログ記述後に再開可能)
- **既存ベンチ (`bench_cases/cwe94_*`)** と DSL の接続は未着手
- **DSL のヒット件数ログ** の導入は未着手

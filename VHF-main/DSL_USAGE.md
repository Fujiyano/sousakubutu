# VHF DSL 使い方ガイド

VHF の「脆弱性のある AST パターンを書き換える処理」を、Python の `ast.NodeTransformer` を直接書かずに、宣言的なミニ言語 (DSL) で記述するための仕組みです。

|  | コスト |
|---|---|
| 手書きハンドラーを書く | 1 ファイルに数十〜数百行の Python |
| DSL でハンドラーを書く | 1 ハンドラー = 4 行 |

---

## 1. DSL の最小構文

```
handler <名前> {
  target:    <matchExpr>
  transform: <replaceExpr>
}
```

- `handler` の `<名前>` は識別子。Python の関数名と同じ命名規則。
- `<matchExpr>` と `<replaceExpr>` には 3 種類の「ノード指定式」が書ける。

| 式 | 対象 AST ノード |
|---|---|
| `func("foo")` | 関数呼び出し (`ast.Call`) |
| `name("x")` | 変数参照 (`ast.Name`) |
| `constant(None)` / `constant(0)` / `constant("abc")` / `constant(True)` | 定数 (`ast.Constant`) |

### ドット区切り

ドットを含む名前は `Attribute` (モジュール参照) として自動展開される:

```vhf
func("ast.literal_eval")    # ast.literal_eval(...) にマッチ
name("request.args")        # request.args にマッチ
```

---

## 2. 書き換えの意味論 (一覧)

### target: `func("X")` (Call.func が X のもの)

| transform | 挙動 |
|---|---|
| `func("Y")` | `node.func` を Y に差し替える (引数は維持) |
| `name("Y")` | 同上 (Name と Func は等価に扱う) |
| `constant(V)` | Call 全体を定数 V に置換する (**引数ごと消える**) |

### target: `name("X")` (Name ノード X 、Call.func は除外)

| transform | 挙動 |
|---|---|
| `name("Y")` | Name を Y に差し替え |
| `constant(V)` | Name を定数 V に置換 |

### target: `constant(V)` (Constant ノード、値が厳密一致)

| transform | 挙動 |
|---|---|
| `constant(W)` | 別の定数に置換 |
| `name("Y")` | 定数を変数参照に差し替え |

---

## 3. 使い方: 最小の例

### 例 1: `print` を `reverse_print` に置き換える

`my_rules.vhf`:

```vhf
handler rewrite_print {
  target:    func("print")
  transform: func("reverse_print")
}
```

適用結果:

```python
# before
print("hello")

# after
reverse_print('hello')
```

### 例 2: `eval` を根こそぎ `None` に置換 (= 実質削除)

```vhf
handler remove_eval {
  target:    func("eval")
  transform: constant(None)
}
```

```python
# before
x = eval("1+1")

# after
x = None
```

### 例 3: ドット区切り — `ast.literal_eval` → `safe_eval`

```vhf
handler safe_literal_eval {
  target:    func("ast.literal_eval")
  transform: func("safe_eval")
}
```

```python
# before
parsed = ast.literal_eval(s)

# after
parsed = safe_eval(s)
```

### 例 4: 変数参照の置換 (SQLi 対策の入口としてよく使うパターン)

```vhf
handler wrap_user_input {
  target:    name("user_input")
  transform: name("safe_user_input")
}
```

```python
# before
query = "..." + user_input

# after
query = "..." + safe_user_input
```

> ⚠️ **注意**: 関数定義の引数名 (`def f(user_input):` の `user_input`) は `ast.arg` であり `ast.Name` ではないので書き換わらない。これは仕様どおり — 呼び出し側 / 参照側だけを書き換える。

---

## 4. 複数ハンドラーを 1 ファイルに書く

```vhf
# コメントは # から行末まで
handler a { target: func("print")  transform: func("reverse_print") }
handler b { target: func("eval")   transform: constant(None) }
handler c { target: name("danger") transform: name("safe") }
```

- DSL コンパイラはこれらを **1 個の NodeTransformer クラスに統合**する (AST を何度もなめない = 高速)。
- 同じターゲットを 2 個以上の handler で指定するとコンパイル時エラー:

```vhf
handler h1 { target: func("print") transform: func("a") }
handler h2 { target: func("print") transform: func("b") }
# -> CompileError: duplicate target ('FUNC', ('print',)) ...
```

---

## 5. Python から呼ぶ

### パターン A: コードに埋め込んだ DSL 文字列から一度だけ使う

```python
from vhf_dsl import compile_dsl
import ast

dsl = '''
handler h { target: func("print") transform: func("reverse_print") }
'''
Transformer = compile_dsl(dsl)

tree = ast.parse('print("hi")')
new_tree = Transformer().visit(tree)
ast.fix_missing_locations(new_tree)
print(ast.unparse(new_tree))   # -> reverse_print('hi')
```

### パターン B: VHF 本体 (Fix / node_fixer) に登録して使う

```python
from vhf_dsl import register_dsl
from callback_fixer import Fix

register_dsl(
    open('my_rules.vhf', encoding='utf-8').read(),
    name='my_rules',
)

fixed_source = Fix().fixStatic(original_source_code_string)
```

- `register_dsl` は DSL をコンパイルして `node_fixer` にハンドラーを追加する。
- 以後 `Fix().fix()` / `fixStatic()` を呼ぶと自動適用される。
- `my_server.py` / `main.py` の既存フローにも、この `register_dsl` を起動時に呼ぶだけで組み込める。

---

## 6. 既存ツールから試す (手を動かす順序)

### 単体テスト (DSL 自体の健全性確認)

```bash
py -3.13 tests/test_vhf_dsl.py
```

### `.vhf` ファイル × Python ファイルを 1 回だけ書き換え

```bash
py -3.13 tools/run_dsl_on_file.py \
         vhf_dsl/examples/print_to_reverse.vhf callback_before.py
```

### ケースごと独立実行 (before/after を並べて目視)

```bash
py -3.13 tools/run_dsl_cases.py
# dsl_demo_cases/ 配下の各サブフォルダを 1 ケース 1 プロセスで実行
```

---

## 7. ファイル配置の指針

```
vhf_dsl/                DSL 実装 (lexer / parser / compiler)
  examples/             サンプル .vhf ファイル
dsl_demo_cases/         1 DSL ルールごとの before/rule.vhf セット (デモ & 回帰)
tests/                  DSL 自体のテスト
tools/                  CLI ランナー
```

自作の DSL ルールを置く場所:

- **試しに 1 本**: `vhf_dsl/examples/` に置けば見つけやすい
- **回帰テスト込みで管理**: `dsl_demo_cases/caseN_xxx/rule.vhf` + `before.py`
- **本番適用用**: プロジェクトのどこでも OK (文字列として `register_dsl` に渡すだけ)

---

## 8. よくあるハマりどころ

<table>
<tr><th>症状</th><th>原因 / 対処</th></tr>
<tr>
<td><code>name("print")</code> と書いたのに <code>print(...)</code> が置換されない</td>
<td><code>Call.func</code> の位置にある <code>print</code> は <code>func()</code> ハンドラーでしか拾えない。<code>name()</code> は <code>Call.func</code> を除外した Name を見る設計。</td>
</tr>
<tr>
<td>const 比較が型まで厳密</td>
<td><code>constant(0)</code> は <code>int</code> の <code>0</code> だけにマッチ、<code>False</code> にはマッチしない。<code>is</code> チェックではなく「値相等 + 型同一」。</td>
</tr>
<tr>
<td>関数の引数定義が書き換わらない</td>
<td><code>def f(user_input):</code> の <code>user_input</code> は <code>ast.arg</code> で <code>Name</code> ではない。呼び出し側 / 参照側だけが対象。</td>
</tr>
<tr>
<td><code>ast.unparse</code> でコメント/元のクォートが消える</td>
<td>DSL の責任ではなく Python 標準 <code>ast</code> の仕様。ダブルクォート <code>"hi"</code> が <code>'hi'</code> になるのもこのため。</td>
</tr>
<tr>
<td>Windows のコンソールが文字化けする</td>
<td>Python 側で stdout を UTF-8 再構成するか、<code>chcp 65001</code> を実行。</td>
</tr>
</table>

---

## 9. 参考: DSL で書ける範囲 / 書けない範囲 (現行 MVP)

### ✅ 書ける

- 名前 1 個の `Call` / `Name` / `Constant` へのマッチ
- 名前 1 個への差し替え
- `Call` 丸ごと定数へ置換
- ドット区切り (`ast.literal_eval` など)

### ❌ 書けない (今後の拡張候補)

- 引数の中身を条件にしたマッチ (例: `eval` の第 1 引数が文字列リテラルの時のみ)
- 複数パス (`phase1 → phase2`) の分割適用
- ガード式 (「呼び出し位置が特定の関数の中のとき」など)
- 書き換え後ノードに元の子ノードを再利用する (テンプレ展開)

こうした高度な書き換えは、現時点では [`vulnerability_handlers.py`](vulnerability_handlers.py) に Python の `ast.NodeTransformer` として書く。**DSL と手書きハンドラーは併用できる** (両方 `node_fixer` に乗る)。

---

## 関連ファイル

- 同じ内容の plain text 版: [`DSL_USAGE.txt`](DSL_USAGE.txt)
- DSL 実装本体: [`vhf_dsl/`](vhf_dsl/)
- サンプル DSL: [`vhf_dsl/examples/print_to_reverse.vhf`](vhf_dsl/examples/print_to_reverse.vhf)
- デモケース: [`dsl_demo_cases/`](dsl_demo_cases/)
- 手書きハンドラー置き場: [`vulnerability_handlers.py`](vulnerability_handlers.py)

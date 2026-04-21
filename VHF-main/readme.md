## 使い方
このフレームワーク(vhf)は，アプリケーション開発者が実装したソースコードを自動で解析して修正するWebアプリケーションフレームワークです．

## vhfでwebアプリケーションを作って，ローカルで実行する
webアプリケーションをvhfで作成してローカルで実行します．

```sh:
#vhf-dirで
cd vhf

# アプリケーションを作成する
touch my_server.py

# 好きなエディタでmy_server.pyを編集する
vi my_server.py
```

my_server.pyを記述します．
実行環境はPython3.7です．

リクエストパスとメソッド，コールバック関数を対応づけます．

下の例ではリクエストパスが/helloでリクエストメソッドがGETの時，helloという関数が呼び出されます．

このリクエストパスとリクエストメソッドに応じて呼び出される関数をコールバック関数と言います．

vhfの仕様でコールバック関数の引数にはrequestが必要です．

```py:my_server.py
# vhfをimportする
from app import *

# @app.route("パスの正規表現",  "リクエストメソッド")
# def コールバック関数(request):
#   コールバック関数内の処理
#   return "webブラウザに返却するページ"
@app.route("^/hello$", "GET")
def hello(request):
  return "Hello"

if __name__=="__main__":
  app.run(port=8000)
```

vhfを実行します．
my_server.pyがあるディレクトリで以下を実行します．

```sh: ローカルで実行
python3 my_server.py
```
ターミナルで"Serving HTTP on port 8000"が出力されたら，webブラウザでlocalhost:8000/helloを実行します．
ブラウザにHelloと表示されていたらOK．

終了する時は，ターミナルでctrl（コントロールボタン） + c　で終了します．

## アプリケーションを修正する
vhfはnode_fixer.py内でコールバック関数を修正します．

node_fixer.pyの21行目以降にコールバック関数を修正する関数を追加します．

記述例は下です．

```py:node_fixer.py
@node_fixer.add
def fix_hoge(ast_callbacks):
  new_ast_callbacks = ...
  ...
  ...
  return new_ast_callbacks
```
node_fixer.addデコレータがコールバック関数を修正する関数をvhfに追加します．

node_fixer.addの下の関数がコールバック関数を修正する関数（今回の場合，fix_hoge関数）です．

この関数の引数はast_callbacksというリストを持っています．

この引数はリストで，要素はそれぞれコールバック関数とリクエストパス，リクエストメソッドです．
引数ast_callbacksは以下のようになっています．
```py:
ast_callbacks = [
  {"callback_name": "hello", "method": "GET", "path": "^/hello$", "path_compiled":r'^/hello$', "ast": ast状態のコールバック関数},
  {...},
  ...
]
```

astとは抽象構文木（Abstract Syntax Tree）の略です．

このastを修正することで，コールバック関数を修正します．
今回は修正の例としてrewrite_print_to_reverse_print()関数を参考にします．

この関数はコールバック関数内のprint()関数をreverse_print()関数に変更します．
reverse_print()関数はprint関数の文字列を逆から出力する関数で，inserted_functions.pyに記述されています．
reverse_print()関数の具体的なソースコードは以下のようになっています．
```py:inserted_functions.py
def reverse_print(s, *args, **kwargs):
    if isinstance(s, str):
        print(s[::-1], *args, **kwargs)
    else:
        print("Not Str")
        print(s, *args, **kwargs)
```
 rewrite_print_to_reverse_print()関数は，コールバック関数内部でprint()関数を見つけるとreverse_print()に変更します．

以下がrewrite_print_to_reverse_print()関数とその内部で利用される関数です．
```py:node_fixer.py
from inserted_functions import *
import ast #pythonが提供しているastに関するモジュール

# (中略)

@node_fixer.add
def rewrite_print_to_reverse_print(ast_callbacks):
    new_ast_callbacks = []
    for ast_callback in ast_callbacks:
        node = ast_callback.get('ast') # ast_callback = {"callback_name": ..., ..., "ast": ast_callback} だから nodeにast_callbackを代入
        new_node = RewriteReversePrint().visit(node) # ast状態のコールバック関数を修正するメソッド
        new_ast_callbacks.append(make_new_callback(ast_callback, new_node=new_node)) # 修正されたコールバック関数をnew_ast_callbacksに格納
    return new_ast_callbacks

# (中略)

# ast.NodeTransformerの子クラス
# visit_ノード属性()メソッドは，引数にast状態の変数を取ってノードを探索する
# 引数のノードとvisit_ノード属性が一致する場合，visit_ノード属性()メソッドが実行される
class RewriteReversePrint(ast.NodeTransformer):
    #visit_Name()メソッドなのでName属性のノードの時に実行される
    def visit_Name(self, node):
        # nodeの名前が"print"の時に"reverse_print"に変更するノードを作成
        if node.id is 'print':
            new_node = ast.Name(
                id='reverse_print',
                ctx=ast.Load()
            )
            return ast.copy_location(new_node, node) # ast.copy_location()メソッドによって，nodeのprintの部分をnew_nodeに変更する
        return node

# (中略)

def make_new_callback(callback, new_node=None):
    new_callback = {}
    if new_node:
        new_callback = {
            'callback_name': callback.get('callback_name'),
            'method': callback.get('method'),
            'path': callback.get('path'),
            'path_compiled': callback.get('path_compiled'),
            'ast': new_node
        }
        return new_callback
    return callback

```

このようにして，コールバック関数が修正されます．
コールバック関数を修正しているか確認するために，my_server.pyに以下を追加します．
```py:my_server.py
from app import *

@app.route("^/hello$", "GET")
def hello(request):
  print("hoge") #追加部分
  return "Hello"

if __name__=="__main__":
  app.run(port=8000)
```

その後実行します．
```sh:再実行
python3 my_server.py
```

webブラウザでlocalhost:8000/helloを実行して，その時にターミナル上で"egoh"と出力されていたらOKです．


# 参考URL
## git
[Gitの一部のディレクトリだけ取得する方法](https://qiita.com/ponsuke0531/items/1e0ab0d6845ec93a0dc0)


## python ast関連
[ast --- 抽象構文木](https://docs.python.org/ja/3/library/ast.html)

[Pythonのastモジュール入門](https://qiita.com/t2y/items/c8877cf5d3d22cdcf2a8)

[ast.NodeTransformerによるコード書き換えの例](https://qiita.com/wonderful_panda/items/dfb12a7de244033aae85)


## webアプリケーションフレームワーク関連
[Webアプリケーションフレームワークの作り方 in Python](https://c-bata.link/webframework-in-python/#)

[Bottle: Python Web Framework](https://bottlepy.org/docs/dev/)

[Bottleのソースコード(github)](https://github.com/bottlepy/bottle/blob/master/bottle.py)

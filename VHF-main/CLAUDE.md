# VHF(Vulnerbility Handling Framework)
- Webアプリに含まれる脆弱性を修復するフレームワーク。

## 脆弱性ハンドラー
- VHFを動作させるために必要なプログラム群。大きく分けて3つ

- 1.追加の関数の設定(必要に応じて)
- 下はpythonのreverse_print関数: 
"""
def reverse_print(s, *args, **kwargs):
    if isinstance(s, str):
        print(s[::-1], *args, **kwargs)
    else:
        print("Not Str")
        print(s, *args, **kwargs)
"""
- 2.ASTレベルで脆弱性のあるパターンを書き換える処理
- 以下はprint関数を発見しreverse_printに修正する関数(必須):
"""
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
"""
- 3.コールバック関数に変更を適用させるプログラム(必須):
"""
@node_fixer.add
def rewrite_print_to_reverse_print(ast_callbacks):
    new_ast_callbacks = []
    for ast_callback in ast_callbacks:
        node = ast_callback.get('ast') # ast_callback = {"callback_name": ..., ..., "ast": ast_callback} だから nodeにast_callbackを代入
        new_node = RewriteReversePrint().visit(node) # ast状態のコールバック関数を修正するメソッド
        new_ast_callbacks.append(make_new_callback(ast_callback, new_node=new_node)) # 修正されたコールバック関数をnew_ast_callbacksに格納
    return new_ast_callbacks
"""


## やること1
- 脆弱性ハンドラーにおいて、もっとも重要な点は2.の脆弱性のある部分を書き換えるパターンを作成する点である。したがって、そのパターンをDSL等の宣言的な言語を作成することである。
- DSLの設計を練りたい。


## 指針
- 会話履歴を圧縮した後はVHF-main直下のPROGRESS.mdを読むこと。
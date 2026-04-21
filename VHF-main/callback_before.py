import ast
import sqlite3


def search_product(keyword, user_input, s):
    # 1) print() が残っている
    print("searching...")
    print(user_input)  # name("user_input") も同時にヒット

    # 2) eval が使われている (まるごと除去したい)
    threshold = eval("1 + 1")

    # 3) ast.literal_eval を safe_eval に差し替えたい
    parsed = ast.literal_eval(s)

    # 4) LIKE f-string SQLi (既存ハンドラが捕捉)
    con = sqlite3.connect('store.db')
    cur = con.cursor()
    sql = f"SELECT * FROM products WHERE name LIKE '%{keyword}%'"
    cur.execute(sql)
    rows = cur.fetchall()
    con.close()
    return rows, threshold, parsed

import ast
import sqlite3

def search_product(keyword, user_input, s):
    reverse_print('searching...')
    reverse_print(user_input)
    threshold = None
    parsed = safe_eval(s)
    con = sqlite3.connect('store.db')
    cur = con.cursor()
    sql = 'SELECT * FROM products WHERE name LIKE ?'
    cur.execute(sql, (vhf_like_param(keyword),))
    rows = cur.fetchall()
    con.close()
    return (rows, threshold, parsed)
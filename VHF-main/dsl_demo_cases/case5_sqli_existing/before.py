import sqlite3

def search_product(keyword):
    con = sqlite3.connect('store.db')
    cur = con.cursor()
    sql = f"SELECT * FROM products WHERE name LIKE '%{keyword}%'"
    cur.execute(sql)
    rows = cur.fetchall()
    con.close()
    return rows

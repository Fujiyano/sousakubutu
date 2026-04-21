from app import *
from bottle import jinja2_template as tmpl

@app.route("^/$")
def index(request):
    return tmpl("index.html", name="hoge")

@app.route("^/access$", "GET")
def access(request):
    return tmpl("access.html", action="None",name="None", password="None")

@app.route("^/access$", "POST")
def access(request):
    import sqlite3
    conn = sqlite3.connect("test.sqlite3")
    cur = conn.cursor()
    action = request.forms.get('action')
    name = request.forms.get('name')
    password = request.forms.get('password')
    query = '{action} * from user'.format(action=action)
    if name and password:
        query += " where name = '{name}' and password = 'password'".format(name=name, password=password)
        print(query)
        cur.execute(query)
        data = cur.fetchone()
        return tmpl("access.html", action=action,name=name, password=password)
    return tmpl("access.html", action=action,name=name, password=password)

if __name__=="__main__":
    app.run(port=8888)

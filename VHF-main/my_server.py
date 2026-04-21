# vhfをimportする
from app import *

# @app.route("パスの正規表現",  "リクエストメソッド")
# def コールバック関数(request):
#   コールバック関数内の処理
#   return "webブラウザに返却するページ"
@app.route("^/$")
def index(request):
  from bottle import jinja2_template as tmpl
  return tmpl("index.html")

@app.route("^/database$", "GET")
def database(request):
  from bottle import jinja2_template as tmpl
  return tmpl("database.html", action="None", result="None")

@app.route("^/database$", "POST")
def database(request):
  from bottle import jinja2_template as tmpl
  import sqlite3 as sql3
  import time
  start = time.time()
  conne = sql3.connect("database.sqlite3")
  curs = conne.cursor()
  action = request.forms.get("action")
  query = "{action}".format(action=action[0])
  curs.execute(query)
  data = curs.fetchall()
  conne.commit()
  conne.close()
  end = time.time() - start
  print("elapsed time is {} sec".format(end))
  return tmpl("database.html", action=action, result=data)

if __name__=="__main__":
  app.run(port=8000)
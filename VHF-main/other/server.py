from app import *

@app.route("^/$", "GET")
def index(request):
    return """
<form action="http://localhost:8000/login" method="post">
<input type="textarea" name="id" value="">
<input type="textarea" name="password" value="">
<input type="submit" value="送信">
</form>
    """
@app.route("^/login$", "GET")
def login(request):
    return """
<form action="http://localhost:8000/login" method="post">
<input type="textarea" name="id" value="">
<input type="textarea" name="password" value="">
<input type="submit" value="送信">
</form>
    """
@app.route("^/login2$", "GET")
def login2(request):
    return """
<form action="http://localhost:8000/login2" method="post">
<input type="textarea" name="id" value="">
<input type="textarea" name="password" value="">
<input type="submit" value="送信">
</form>
    """

@app.route("^/login$", "POST")
def do_login(request):
    id, password = None, None
    if request.forms.get("id"):
        id = str(request.forms.get("id")[0])
    if request.forms.get("password"):
        password = str(request.forms.get("password")[0])
    if is_admin(id, password):
        return "ADMIN_PAGE"
    else:
        return """
<form action="http://localhost:8000/login" method="post">
<input type="textarea" name="id" value="">
<input type="textarea" name="password" value="">
<input type="submit" value="送信">
</form>
        """

@app.route("^/login2$", "POST")
def do_login2(request):
    id, password = None, None
    if request.forms.get("id"):
        id = str(request.forms.get("id")[0])
    if request.forms.get("password"):
        password = str(request.forms.get("password")[0])
    if is_admin(id, password):
        return "ADMIN_PAGE2"
    else:
        return """
<form action="http://localhost:8000/login2" method="post">
<input type="textarea" name="id" value="">
<input type="textarea" name="password" value="">
<input type="submit" value="送信">
</form>
        """

@app.route("^/home$", "GET")
def home(request):
    return "ADMIN_PAGE"

if __name__=="__main__":
    app.run(port=8000)

from app import *

#external module
from bottle import jinja2_template

@app.route("^/$")
def callback1(request):
    return escape_xss_characters("hogehogecall1")

@app.route("^/two$")
def callback2(request):
    def reverse(s):
        return s[::-1]
    return '''
        <html>
            <head>
                <title>page2 for xss</title>
                </head>
                <body>
                Hello, {content2}
                </body>
                </html>
    '''.format(content2=reverse(request.query["content2"][0]))

@app.route("^/three$")
def callback3(request):
    html = '''
    <html>
        <head>
            <title>page3 for xss</title>
        </head>
        <body>
            Hello, {}
            Content is {}.
        </body>
    </html>
    '''
    return html.format("sobasoba", "subusubu")

# func(html.format(...))を取り扱ってくれない修正
@app.route("^/four$")
def callback4(request):
    html = '''
    <html>
        <head>
            <title>page4 for xss</title>
        </head>
        <body>
            Hello, {}
            Content is {}.
        </body>
    </html>
    '''
    def reverse(s):
        return s[::-1]

    return reverse(html.format(reverse(request.query["name"][0]), reverse(reverse(request.query["content"][0]))))


if __name__=="__main__":
    app.run(port=8888)

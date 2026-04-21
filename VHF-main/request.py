import cgi
import json
from http.cookies import SimpleCookie, Morsel, CookieError
from urllib.parse import parse_qs, urljoin, unquote as urlunquote
from io import BytesIO
from tempfile import TemporaryFile

class Request:
    MEMFILE_MAX = 102400
    def __init__(self, environ=None, charset='utf-8'):
        self.environ = environ
        self.charset = charset
        self.forms = self.make_forms()
        self.query = self.make_query()

    @property
    def path(self):
        return self.environ['PATH_INFO'] or '/'

    @property
    def client_ip_addr(self):
        return self.environ['REMOTE_ADDR']

    @property
    def client_user_agent(self):
        return self.environ['HTTP_USER_AGENT']

    @property
    def method(self):
        return self.environ['REQUEST_METHOD'].upper()

    def make_forms(self):
        if not self.environ['REQUEST_METHOD'].upper() == "POST":
            return {}
        else:
            body = self.body
            forms = parse_qs(body)
            return forms

    def make_query(self):
        return parse_qs(urlunquote(self.environ['QUERY_STRING']))

    @property
    def body(self):
        if self.environ['REQUEST_METHOD'].upper() == "POST":
            content_length = int(self.environ.get('CONTENT_LENGTH', 0))
            body = self.environ.get('wsgi.input').read(content_length)
            return body.decode()

        else:
            return ""

    @property
    def text(self):
        return self.body.decode(self.charset)

    @property
    def json(self):
        return json.loads(self.body)

    @property
    def cookies(self):
        # return Set-Cookie: key=value
        cookies = SimpleCookie(self.environ.get('HTTP_COOKIE', ''))
        return cookies

    @property
    def content_type(self):
        return self.environ.get("CONTENT_TYPE", "").lower()

from wsgiref.headers import Headers
from datetime import date as datedate, datetime, timedelta
import calendar, email
from http.client import responses as http_responses
from http.cookies import SimpleCookie, CookieError

class Response:
    default_status = 200
    default_charset = 'utf-8'
    default_content_type = 'text/html; charset=UTF-8'

    def __init__(self):
        #self._body = body
        self.body = ''
        self.status = self.default_status
        self.status_code = None
        self.headers = Headers()
        self.content_type = self.default_content_type
        self.charset = self.default_charset
        self.cookies = None

    def makeStatusCode(self, status):
        if isinstance(status, str):
            status = int(status)
        self.status = status
        self.status_code = http_responses[status]

    def addBody(self, body):
        self.body = body

    def setCookies(self, name=None, value=None, **options):
        self.cookies = SimpleCookie()
        self.cookies[name] = value
        for key, value in options.items():
            if key in('max_age', 'maxage'):
                key = 'max-age'
                if isinstance(value, timedelta):
                    value = value.seconds + value.days * 24 * 3600
            if key == 'expires':
                value = http_date(value)
            if key in ('same_site', 'samesite'):
                key = 'samesite'
                value = (value or "none").lower()
                if value not in('lax', 'strict' 'none'):
                    raise CookieError("Invalid value for SameSite")
            if key in('secure', 'httponly') and not value:
                continue
            self.cookies[name][key] = value

    def makeResponse(self):
        status_code = "{} {}".format(self.status, self.status_code)
        if isinstance(self.body, str):
            encoded_body = [self.body.encode(self.charset)]
        else:
            #### ボディがないことに対するエラーを吐く必要がある ####
            pass
        self.headers.add_header('Content-Type', self.content_type)
        if self.cookies:
            for cookie in self.cookies.values():
                self.headers.add_header('Set-Cookie', cookie.OutputString())
        headers = self.headers
        self.__init__()
        return status_code, headers.items(), encoded_body


def http_date(value):
    if isinstance(value, str):
        return value
    if isinstance(value, datetime):
        # aware datetime.datetime is converted to UTC time
        # naive datetime.datetime is treated as UTC time
        value = value.utctimetuple()
    elif isinstance(value, datedate):
        # datetime.date is naive, and is treated as UTC time
        value = value.timetuple()
    if not isinstance(value, (int, float)):
        # convert struct_time in UTC to UNIX timestamp
        value = calendar.timegm(value)
    return email.utils.formatdate(value, usegmt=True)



if __name__=="__main__":
    response = Response()
    list = [200, 201, 404, 405, 500]
    dict = {
        'max_age': 3600,
        'httponly': 'yes',
        'samesite': 'yes',
        'max_age': 3600,
        'httponly': 'yes',
    }
    bodies = ["Hello1", "Hello2", "Hello3", "Hello4", "Hello5"]
    for status, body in zip(list, bodies):
        response.makeStatusCode(status)
        response
        response.addBody(body)
        response.setCookies('name', 'value', secure='yes', httponly='yes', max_age=3600, domain='/')
        status_code, header, encoded_body = response.makeResponse()
        print(header,end=", ")
        print(encoded_body)

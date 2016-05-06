from gramex import conf, __version__ as version
from tornado.web import RequestHandler
from tornado.escape import json_decode

server_header = 'Gramex/%s' % version


class BaseHandler(RequestHandler):
    '''
    BaseHandler provides auth, caching and other services common to all request
    handlers. All RequestHandlers must inherit from BaseHandler.
    '''

    def initialize(self, cache=None, **kwargs):
        if cache is not None:
            self.cachefile = cache(self)
            self.original_get = self.get
            self.get = self._cached_get

    def set_default_headers(self):
        self.set_header('Server', server_header)

    def _cached_get(self, *args, **kwargs):
        cached = self.cachefile.get()
        headers_written = set()
        if cached is not None:
            self.set_status(cached['status'])
            for name, value in cached['headers']:
                if name in headers_written:
                    self.add_header(name, value)
                else:
                    self.set_header(name, value)
                    headers_written.add(name)
            self.write(cached['body'])
        else:
            self.cachefile.wrap(self)
            self.original_get(*args, **kwargs)

    def get_current_user(self):
        app_auth = conf.app.settings.get('auth', False)
        route_auth = self.params.get('auth', app_auth)
        if not route_auth:
            return 'static'
        user_json = self.get_secure_cookie('user')
        if not user_json:
            return None
        return json_decode(user_json)

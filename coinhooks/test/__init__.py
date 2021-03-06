import json
import os
import paste.deploy
import redis

from unittest import TestCase

from coinhooks import web

_DEFAULT = object()

ENV_TEST_INI = os.environ.get('TEST_INI', 'test.ini')

HERE_DIR = os.path.dirname(os.path.abspath(__file__))
CONF_DIR = os.path.dirname(os.path.dirname(HERE_DIR))
TEST_INI = os.path.join(CONF_DIR, ENV_TEST_INI)

settings = paste.deploy.appconfig('config:' + TEST_INI)


class TestApp(TestCase):
    def setUp(self):
        super(TestApp, self).setUp()

        self.config = web.environment.setup_testing(**settings)
        self.wsgi_app = self.config.make_wsgi_app()
        self.redis = redis.Redis(connection_pool=self.config.registry.redis_pool)

    def tearDown(self):
        self.redis.flushdb()
        #testing.tearDown()

        super(TestApp, self).tearDown()


class TestWeb(TestApp):
    def setUp(self):
        super(TestWeb, self).setUp()

        from webtest import TestApp
        self.app = TestApp(self.wsgi_app)
        self.csrf_token = settings['session.constant_csrf_token']
        self.request = self.app.RequestClass.blank('/')

    def call_api(self, method, format='json', csrf_token=_DEFAULT, _status=None, _extra_params=None, **params):
        "Helpers for calling our @exposed_api(...) methods."
        if csrf_token is _DEFAULT:
            csrf_token = self.csrf_token

        p = {
            'method': method,
            'csrf_token': csrf_token,
            'format': format,
        }
        p.update(params)
        if _extra_params:
            p.update(_extra_params)

        r = self.app.post('/api', params=p, status=_status)

        return json.loads(r.body)


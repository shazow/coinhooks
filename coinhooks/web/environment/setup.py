from urlparse import urlparse
from pyramid import tweens
from pyramid import httpexceptions

import jsonrpclib
import redis
import sqlalchemy.pool

from coinhooks.lib.exceptions import APIError
from coinhooks.lib import helpers


## Service connection helpers.
# TODO: Move this into respective model modules?

def _redis_pool(url):
    p = urlparse()
    return redis.ConnectionPool(
        host=p.hostname,
        port=p.port,
        password=p.password,
        db=int(p.path[1:] or 0),
    )

def _bitcoin_pool(url, max_overflow=10, pool_size=5):
    def conn_factory():
        return jsonrpclib.Server(url)

    # jsonrpclib doesn't come with connectionpooling, so we use SQLAlchemy's generic pool.
    return sqlalchemy.pool.QueuePool(conn_factory, max_overflow=max_overflow, pool_size=pool_size)


def _redis_model(request):
    # http://redis-py.readthedocs.org/en/latest/#redis.ConnectionPool.release
    pool = request.registry.redis_pool
    conn = redis.Redis(connection_pool=pool)

    def cleanup(request):
        pool.release(conn)
    request.add_finished_callback(cleanup)

    return conn


def _bitcoin_model(request):
    # http://docs.sqlalchemy.org/en/rel_0_7/core/pooling.html#constructing-a-pool
    conn = request.registry.bitcoin_pool.connect()

    def cleanup(request):
        conn.close()
    request.add_finished_callback(cleanup)

    return conn

##


def _setup_models(config):
    """ Attach connection to model modules. """
    settings = config.get_settings()

    # Attach request.redis property:
    config.registry.redis_pool = _redis_pool(settings['redis.url'])
    config.add_request_method(_redis_model, name='redis', reify=True)

    # Attach request.bitcoind property:
    config.registry.bitcoin_pool = _bitcoin_pool(settings['bitcoind.url'])
    config.add_request_method(_bitcoin_model, name='bitcoin', reify=True)



def _template_globals_factory(system):
    """ Default namespace provided for our templates. """
    return {'h': helpers}


def _login_tween(handler, registry):
    """ Handle our own exceptions a little more intelligently. """
    def _login_handler(request):
        try:
            return handler(request)
        except APIError, e:
            raise httpexceptions.HTTPBadRequest(detail=e.message)

    return _login_handler


def make_config(settings):
    from pyramid.config import Configurator
    return Configurator(settings=settings)


def setup_config(config):
    """ Called by setup with a config instance. Or used for initializing tests
    environment."""
    from .request import Request
    config.set_request_factory(Request)
    config.add_tween('coinhooks.web.environment.setup._login_tween', over=tweens.MAIN)

    # Add Pyramid plugins
    config.include('pyramid_handlers') # Handler-based routes
    config.include('pyramid_mailer') # Email

    # Globals for templates
    config.set_renderer_globals_factory(_template_globals_factory)

    # Beaker sessions
    from pyramid_beaker import session_factory_from_settings
    config.set_session_factory(session_factory_from_settings(config.get_settings()))

    # Routes
    config.add_renderer(".mako", "pyramid.mako_templating.renderer_factory")
    config.add_static_view("static", "coinhooks.web:static")

    # More routes
    from .routes import add_routes
    add_routes(config)

    # Module-level model global setup
    _setup_models(config)

    # Need more setup? Do it here.
    # ...

    return config


def setup_wsgi(global_config, **settings):
    """ This function returns a Pyramid WSGI application. """
    settings.update(global_config)
    config = setup_config(make_config(settings=settings))
    config.commit()

    return config.make_wsgi_app()


def setup_testing(**settings):
    from pyramid import testing

    # FIXME: Remove the Registry-related stuff once
    # https://github.com/Pylons/pyramid/issues/856 is fixed.
    from pyramid.registry import Registry
    registry = Registry('testing')
    config = testing.setUp(registry=registry, settings=settings)
    config.registry = registry
    config.setup_registry(settings=settings)

    return setup_config(config)


def setup_shell(env):
    """ Called by pshell. """
    from webtest import TestApp
    env['testapp'] = TestApp(env['app'])

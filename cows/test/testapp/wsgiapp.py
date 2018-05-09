# BSD Licence
# Copyright (c) 2009, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

"""The TestApp WSGI application"""
import os

from paste.cascade import Cascade
from paste.registry import RegistryManager
from paste.urlparser import StaticURLParser
from paste.deploy.converters import asbool

import pylons
from pylons.error import error_template
from pylons.middleware import error_mapper, ErrorDocuments, ErrorHandler, \
    StaticJavascripts
from pylons.wsgiapp import PylonsApp

import cows.test.testapp.helpers
from cows.test.testapp.routing import make_map

def load_environment(global_conf, app_conf):
    """Configure the Pylons environment via the ``pylons.config``
    object
    """
    # Pylons paths
    root = os.path.dirname(os.path.abspath(__file__))
    paths = dict(root=root,
                 controllers=os.path.join(root, 'controllers'),
                 static_files=os.path.join(root, 'public'),
                 templates=[os.path.join(root, 'templates')])

    # Initialize config with the basic options
    pylons.config.init_app(global_conf, app_conf, package='cows.test.testapp',
                    template_engine='mako', paths=paths)

    pylons.config['routes.map'] = make_map()
    pylons.config['pylons.g'] = Globals()
    pylons.config['pylons.h'] = cows.test.testapp.helpers

    # Customize templating options via this variable
    tmpl_options = pylons.config['buffet.template_options']

    # CONFIGURATION OPTIONS HERE (note: all config options will override
    # any Pylons config options)


def make_app(global_conf, full_stack=True, **app_conf):
    """Create a Pylons WSGI application and return it

    ``global_conf``
        The inherited configuration for this application. Normally from
        the [DEFAULT] section of the Paste ini file.

    ``full_stack``
        Whether or not this application provides a full WSGI stack (by
        default, meaning it handles its own exceptions and errors).
        Disable full_stack when this application is "managed" by another
        WSGI middleware.

    ``app_conf``
        The application's local configuration. Normally specified in the
        [app:<name>] section of the Paste ini file (where <name>
        defaults to main).
    """
    # Configure the Pylons environment
    load_environment(global_conf, app_conf)

    # The Pylons WSGI app
    app = PylonsApp()

    # CUSTOM MIDDLEWARE HERE (filtered by error handling middlewares)

    if pylons.__version__ >= '0.9.7':
        # Routing/Session/Cache Middleware
        from beaker.middleware import CacheMiddleware, SessionMiddleware
        from routes.middleware import RoutesMiddleware
        app = RoutesMiddleware(app, pylons.config['routes.map'])
        app = SessionMiddleware(app, pylons.config)
        app = CacheMiddleware(app, pylons.config)

    if asbool(full_stack):
        # Handle Python exceptions
        app = ErrorHandler(app, global_conf, error_template=error_template,
                           **pylons.config['pylons.errorware'])

        # Display error documents for 401, 403, 404 status codes (and
        # 500 when debug is disabled)
        app = ErrorDocuments(app, global_conf, mapper=error_mapper, **app_conf)

    # Establish the Registry for this application
    app = RegistryManager(app)

    # Static files
    javascripts_app = StaticJavascripts()
    static_app = StaticURLParser(pylons.config['pylons.paths']['static_files'])
    app = Cascade([static_app, javascripts_app, app])
    return app


class Globals(object):
    """Globals acts as a container for objects available throughout the
    life of the application
    """

    def __init__(self):
        """One instance of Globals is created during application
        initialization and is available during requests via the 'g'
        variable.
        """
        pass

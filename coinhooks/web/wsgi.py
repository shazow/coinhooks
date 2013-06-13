import os
here = os.path.dirname(__file__)

ini_path = os.path.join(here, '../../production.ini')

from paste.deploy import loadapp
actual_application = loadapp('config:%s' % ini_path, relative_to='.')

import logging
import logging.config
logging.config.fileConfig(ini_path)


def wrapper_application(environ, start_response):
    if environ["SCRIPT_NAME"] == "/":
        environ["SCRIPT_NAME"] = ""
    return actual_application(environ, start_response)

application = actual_application

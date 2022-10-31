from os import environ, path
import logging, sys
from dotenv import load_dotenv
from distutils.util import strtobool



basedir = path.abspath(path.dirname(__file__))
load_dotenv(path.join(basedir, '.env'))
log = logging.getLogger(__name__)


conf =  { 'DEBUG': bool(strtobool(environ.get('DEBUG', 'False'))),
         'HOSTNAME': environ.get('HOSTNAME', '10.0.60.101'),
         'USERNAME': environ.get('USERNAME', 'Administrator'),
         'PASSWORD': environ.get('PASSWORD', 'Administrator'),
         }

class Settings(object):
    

    def __init__(self):
        self._config = conf

        for key, value in conf.items():
            setattr(self, key, value)
        self.set_debug()
        
        log.debug(f'{__name__} loaded')
        
    def get_property(self, property_name):
        if property_name not in self._config.keys(): # we don't want KeyError
            return None  # just return None if not found
        return self._config[property_name]

    def set_debug(self):
        logging.basicConfig(format='%(asctime)s %(name)s.%(funcName)s(%(lineno)s): %(message)s', stream=sys.stderr)
        if self.DEBUG:
            logging.getLogger().setLevel(logging.DEBUG)
        else:
            logging.getLogger().setLevel(logging.INFO)
        log.info(f'set debug = {self.DEBUG}')
    

gira_settings = Settings()
            

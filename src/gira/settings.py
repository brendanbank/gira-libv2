from os import environ, path
import logging, sys
from distutils.util import strtobool


from dotenv import load_dotenv
load_dotenv()

basedir = path.abspath(path.dirname(__file__))
log = logging.getLogger(__name__)


conf =  { 'DEBUG': bool(strtobool(environ.get('DEBUG', 'False'))),
         'HOSTNAME': environ.get('HOSTNAME'),
         'USERNAME': environ.get('USERNAME'),
         'PASSWORD': environ.get('PASSWORD'),
         'SQLALCHEMY_DATABASE_URI': environ.get('SQLALCHEMY_DATABASE_URI'),
         }

class Settings(object):
    

    def __init__(self):
        self._config = conf
        self.DEBUG = conf['DEBUG']
        self.set_debug()

        for key, value in conf.items():
            log.debug(f'set {key} = {value}')
            setattr(self, key, value)
        
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
            

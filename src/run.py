import gira, logging, sys
from os import environ, path
from distutils.util import strtobool

from gira.device import GiraServer
import logging
from dotenv import load_dotenv

log = logging.getLogger(__name__)
load_dotenv()

# from attic_settings import gira_settings

conf =  { 'DEBUG': bool(strtobool(environ.get('DEBUG', 'False'))),
         'HOSTNAME': environ.get('HOSTNAME'),
         'USERNAME': environ.get('USERNAME'),
         'PASSWORD': environ.get('PASSWORD'),
         'GIRA_USERNAME': environ.get('GIRA_USERNAME'),
         'GIRA_PASSWORD': environ.get('GIRA_PASSWORD'),
         'SQLALCHEMY_DATABASE_URI': environ.get('SQLALCHEMY_DATABASE_URI'),
         }
logging.basicConfig(format='%(asctime)s %(name)s.%(funcName)s(%(lineno)s): %(message)s', stream=sys.stderr)
logging.getLogger().setLevel(logging.DEBUG)

if __name__ == '__main__':
    log.debug(f'started')
    
    from gira.servercache import CacheObject
    cache = CacheObject(dburi=conf['SQLALCHEMY_DATABASE_URI'], instance=conf['HOSTNAME'])
    # cache.invalidate()


    vpn = 'https://http.httpaccess.net/GIS1YYYCJD/httpu://10.0.60.101'
    vpn=None
    server = GiraServer(cache=cache, 
                        password=conf['USERNAME'],
                        username=conf['PASSWORD'],
                        gira_username=conf['GIRA_USERNAME'],
                        gira_password=conf['GIRA_PASSWORD'],
                        hostname=conf['HOSTNAME'],
                        vpn=vpn
                        )
    server.authenticate()
    server.get_device_config()
    log.debug(server.functions.uids['a019'].get())
    
    log.debug(server.functions.uids['a01c'].set(20))

    log.debug(f'ended')
    
    # server.authenticate()
    # server.version()
    #
    # print (vars(server.cache))
    # print (server.cache._token)
    #
    # server.invalidate_cache()
        

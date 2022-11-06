import gira, logging, sys, time
from os import environ, path
from distutils.util import strtobool

from gira.device import GiraServer
import logging
from dotenv import load_dotenv

log = logging.getLogger(__name__)
load_dotenv()

# from attic_settings import gira_settings

conf =  { 'DEBUG': bool(strtobool(environ.get('DEBUG', 'False'))),
         }
logging.basicConfig(format='%(asctime)s %(name)s.%(funcName)s(%(lineno)s): %(message)s', stream=sys.stderr)
logging.getLogger().setLevel(logging.INFO)

if __name__ == '__main__':
    log.debug(f'started')
    
    from gira.servercache import CacheObject
    cache = CacheObject(dburi=environ.get('SQLALCHEMY_DATABASE_URI'), instance=environ.get('HOSTNAME'))
    # cache.invalidate()

    vpn = 'https://http.httpaccess.net/GIS1YYYCJD/httpu://10.0.60.101'
    # vpn=None
    server = GiraServer(cache=cache, 
                        password=environ.get('USERNAME'),
                        username=environ.get('PASSWORD'),
                        gira_username=environ.get('GIRA_USERNAME'),
                        gira_password=environ.get('GIRA_PASSWORD'),
                        hostname=environ.get('HOSTNAME'),
                        vpn=vpn
                        )
    server.vpn_login(refresh=False)
    server.authenticate(refresh=False)
    server.get_device_config()
    
    
    # log.debug(server.functions.get_all())
    
    # log.debug(server.functions.uids['a01c'].location)

    # serviceCallback =  'https://10.0.20.210:5001/giraapi/function'
    # valueCallback = 'https://10.0.20.210:5001/giraapi/value'
    
    # server.set_callaback(serviceCallback,valueCallback)

    # time.sleep(3)
    server.delete_callback()
    log.debug(f'ended')
    
    # server.authenticate()
    # server.version()
    #
    # print (vars(server.cache))
    # print (server.cache._token)
    #
    # server.invalidate_cache()
        

'''
Disables the Callback to the server

    python ./disableCallback.py

'''
import logging, sys
from os import environ
from distutils.util import strtobool

from gira.device import GiraServer
from dotenv import load_dotenv

log = logging.getLogger(__name__)
load_dotenv()

# from attic_settings import gira_settings

conf =  { 'DEBUG': bool(strtobool(environ.get('DEBUG', 'False'))),
         }
logging.basicConfig(format='%(asctime)s %(name)s.%(funcName)s(%(lineno)s): %(message)s', stream=sys.stderr)
logging.getLogger().setLevel(logging.DEBUG)




def main():
    """
    main_exec
    """
    log.debug(f'started')
    
    from gira.cache import CacheObject
    cache = CacheObject(dburi=environ.get('SQLALCHEMY_DATABASE_URI'), instance=environ.get('INSTANCE_NAME'))
    # cache.invalidate()

    vpn = environ.get('VPN_HOST')

    server = GiraServer(cache=cache, 
                        password=environ.get('USERNAME'),
                        username=environ.get('PASSWORD'),
                        gira_username=environ.get('GIRA_USERNAME'),
                        gira_password=environ.get('GIRA_PASSWORD'),
                        hostname=environ.get('HOSTNAME'),
                        vpn=vpn
                        )
    refresh=False
    server.vpn_login(refresh=refresh)
    server.authenticate(refresh=refresh)
    logging.getLogger().setLevel(logging.INFO)
    
    server.delete_callback()

    log.debug(f'ended')
            
if __name__ == '__main__':
    main()

"""Enables the Callback to the server

    python ./enableCallback.py
"""

import logging, sys
from os import environ

from gira import GiraServer, CacheObject
from dotenv import load_dotenv

log = logging.getLogger(__name__)
load_dotenv()

# from attic_settings import gira_settings

logging.basicConfig(format='%(asctime)s %(name)s.%(funcName)s(%(lineno)s): %(message)s', stream=sys.stderr)
logging.getLogger().setLevel(logging.DEBUG)

    
def main_exec():
    log.debug(f'started')
    
    cache = CacheObject(dburi=environ.get('SQLALCHEMY_DATABASE_URI'), instance=environ.get('INSTANCE_NAME'))
    # cache.invalidate()

    vpn = environ.get('VPN_HOST')
    # vpn = None
    server = GiraServer(cache=cache, 
                        password=environ.get('USERNAME'),
                        username=environ.get('PASSWORD'),
                        gira_username=environ.get('GIRA_USERNAME'),
                        gira_password=environ.get('GIRA_PASSWORD'),
                        hostname=environ.get('HOSTNAME'),
                        vpn=vpn
                        )
    refresh=True
    server.vpn_login(refresh=refresh)
    server.authenticate(refresh=refresh)
    logging.getLogger().setLevel(logging.INFO)

    server.get_device_config(refresh=refresh)
    
    
    callback_server = environ.get('CALLBACK_SERVER')
    serviceCallback =  'https://{callback_server}/giraapi/function'.format(callback_server=callback_server)
    valueCallback = 'https://{callback_server}/giraapi/value'.format(callback_server=callback_server)
    
    server.set_callaback(serviceCallback,valueCallback)
    # server.delete_callback()
    log.debug(f'ended')
            
if __name__ == '__main__':
    main_exec()

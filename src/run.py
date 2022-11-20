import logging, sys, time
from os import environ
log = logging.getLogger(__name__)

import gira
from dotenv import load_dotenv
load_dotenv()

logging.basicConfig( 
        format='%(asctime)s %(name)s.%(funcName)s(%(lineno)s): %(message)s',
        stream=sys.stderr)
logging.getLogger().setLevel(logging.DEBUG)

    
def main_exec():
    log.debug(f'started')
    
    cache = gira.CacheObject(dburi=environ.get('SQLALCHEMY_DATABASE_URI'),
        instance=environ.get('INSTANCE_NAME'))

    vpn = environ.get('VPN_HOST')

    server = gira.GiraServer(cache=cache, 
                        password=environ.get('USERNAME'),
                        username=environ.get('PASSWORD'),
                        gira_username=environ.get('GIRA_USERNAME'),
                        gira_password=environ.get('GIRA_PASSWORD'),
                        hostname=environ.get('HOSTNAME'),
                        vpn=vpn,
                        refresh=True)
    
    server.vpn_login()
    server.authenticate()
    logging.getLogger().setLevel(logging.INFO)

    server.get_device_config()
    
    callbackserver = environ.get('CALLBACK_SERVER')
    
    
    # log.debug(server.functions.get_all())
    
    # log.debug(server.functions.uids['a01c'].location)

    serviceCallback =  'https://{callbackserver}/giraapi/function'.format(callbackserver=callbackserver)
    valueCallback = 'https://{callbackserver}/giraapi/value'.format(callbackserver=callbackserver)
    server.set_callaback(serviceCallback,valueCallback)

    time.sleep(3)
    server.delete_callback()
    log.debug(f'ended')
        
if __name__ == '__main__':
    main_exec()

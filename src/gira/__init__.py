'''
The Gira module is a module to interact with a Gira X1 or Homeserver's REST API.

.. highlight:: python
.. code-block:: python

    """
    This code block expects the following environment variables
    to be set. You can create a .env file including the 
    format below main directory where this script is run to load
    the environment variables.

    DEBUG=<True|False>
    HOSTNAME=<local LAN IP address of your X1>
    USERNAME=<username of the X1>
    PASSWORD=<password of the X1>
    SQLALCHEMY_DATABASE_URI=<database URI>
    GIRA_USERNAME=<username of the https://geraeteportal.gira.de/ portal>
    GIRA_PASSWORD=<pasword of the https://geraeteportal.gira.de/ portal>
    VPN_HOST=<url to your X1 link through the Gira S1>
    INSTANCE_NAME=<instance name, used for storing your key variables 
        (cookies, authorization keys) in your persistent cache>
    
    The VPN_HOST has the following sturcture
    https://http.httpaccess.net/[serviceId]/httpu://[local LAN ip address of your X1]
    
    It can be found in your S1 configuration on https://geraeteportal.gira.de/

    """


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
        server.invalidate_cache()
        log.debug(f'ended')
            
    if __name__ == '__main__':
        main_exec()

'''

from gira.cache import CacheObject
from gira.device import GiraServer
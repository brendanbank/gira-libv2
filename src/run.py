import gira
from gira.server import GiraServer
from gira.servercache import CacheObject
import logging

from gira.settings import gira_settings
log = logging.getLogger(__name__)

if __name__ == '__main__':
    
    cache = CacheObject(gira_settings.get_property('SQLALCHEMY_DATABASE_URI'), 'srv1.bgwlan.nl')

    server = GiraServer(cache=cache)
    server._token = None
    server.authenticate()
    server.version()
    
    print (vars(server.cache))
    print (server.cache._token)
    
    server.invalidate_cache()
        

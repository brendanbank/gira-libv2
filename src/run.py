import gira
from gira.server import GiraServer
import logging

from gira.settings import gira_settings
log = logging.getLogger(__name__)

if __name__ == '__main__':
    server = GiraServer()
    server.identity()
    server.authenticate()
        

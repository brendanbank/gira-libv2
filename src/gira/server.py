
from gira.settings import gira_settings
import logging
import requests
from requests.auth import HTTPBasicAuth
import urllib3
import uuid
import socket

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

log = logging.getLogger(__name__)
log.debug(f'{__name__} loaded')
Headers = {'Content-type': 'application/json'}

IdentityURl = 'https://{host}/api/v2'
DeviceTypes = {
    'GIGSRVKX02': {
        "AUTHENTICATION_URL": 'https://{host}/api/v2/clients',
        "DELETE_CLIENT_URL": 'https://{host}/api/clients/{token}',
        "CALLBACK_URL": 'https://{host}/api/clients/{token}/callbacks',
        "CONFIG_URL": 'https://{host}/api/v2/uiconfig?token={token}&expand=dataPointFlags,parameters,locations,trades',
        "CONFIG_URL_SHORT": 'https://{host}/api/v2/uiconfig?token={token}',
        "CONFIG_URL_UID": 'https://{host}/api/uiconfig/uid?token={token}',
        "GET_URL": 'https://{host}/api/v2/values/%s?token={token}',
        "PUT_URL": 'https://{host}/api/v2/values?token={token}',
        }
    }

class GiraServer(object):

    def __init__(self, hostname=None, username=None, password=None, cookie=None):
        log.debug(f'{__name__} started')

        self.hostname = hostname or gira_settings.get_property('HOSTNAME')
        self.username = username or gira_settings.get_property('USERNAME')
        self.password = password or gira_settings.get_property('PASSWORD')

        self.DEVICETYPE = None
        self.DEVICEURL = None
        self.cookie = cookie
        self.name = f'de.python.{uuid.getnode()}.{socket.gethostname()}' 
        self.errors = []
        
        if self.hostname == None or self.username == None or self.password == None:
            log.critical('Hostname, username and/or password cannot be None')
            return (False)

    def authenticate(self, test_token=False):
        
        """authenticate the app at the gira server"""
        
        if not 'AUTHENTICATION_URL' in self.DEVICEURLS:
            log.critical('AUTHENTICATION_URL not in devices URLS???')
            return(False)
        
        url = self.DEVICEURLS['AUTHENTICATION_URL'].format(host=self.hostname)
        
        data = {"client": self.name}
        
        log.debug(f'post: {data}')
        http_session = requests.Session()


        r = http_session.post(url,
                    json=data, headers=Headers,
                    verify=False,
                    cookies=self.cookie,
                    auth=HTTPBasicAuth(self.username, self.password))

        if (r.status_code == 201):
            self._auth = r.json()
            log.debug(f'received: {self._auth}')

            self._token = self._auth['token']
                
            return(self._token)

        log.critical(f'Error logging into server {url}: {r.json()}')
        self.errors.append(f'Error logging into server{url}: {r.json()}')
        return(False)
    
    
    def identity(self):
        url = IdentityURl.format(host=self.hostname)
        (jdata, status_code) = self._get(url)
        if status_code != 200:
            return (False)
        
        log.debug(f'Received: {jdata}')
        
        self.DEVICETYPE = jdata
        
        if self.DEVICETYPE['deviceType'] in DeviceTypes:
            log.info (f'Devicetype found: {self.DEVICETYPE["deviceType"]} ({self.DEVICETYPE["deviceName"]})')
            self.DEVICEURLS = DeviceTypes[self.DEVICETYPE['deviceType']]
            return (True)
        else:
            log.critical(f'Could not find devictype for: {self.DEVICETYPE["deviceType"]} ({self.DEVICETYPE["deviceName"]})')
            return(False)


    def _get(self, url):
        log.debug(f'connect to {url}')
        
        http_session = requests.Session()
        
        r = http_session.get(url, headers=Headers, verify=False, cookies=self.cookie)
        
        if (r.headers['Content-Type'] == 'application/json'):
            if len(r.text) < 500:
                log.debug('Received status_code: %s with data %s' % (r.status_code, r.json()))
            else:
                log.debug('Received status_code: %s with longdata' % (r.status_code))
            return(r.json(), r.status_code)
        if (r.status_code < 300):
            log.debug('Received status_code: %s with non json data and data: %s' % (r.status_code, r.text))
        else:
            log.error('Received status_code: %s with non json data and data: %s' % (r.status_code, r.text))
            self.errors.append('Received status_code: %s with non json data and data: %s' % (r.status_code, r.text))

        return(None, r.status_code)


                
        
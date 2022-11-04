
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

    def __init__(self, hostname=None, username=None, password=None, cookie=None, vpn=True, cache=None):
               
        print (cache)
        if (cache == None):
            raise ValueError(f'cache cannot not be None')
            
        self.cache=cache
        
        
        cache.set_ignore(['username','password'])
        
        log.debug(f'{__name__} started')

        self.cache.hostname = hostname or gira_settings.get_property('HOSTNAME')
        self.cache.username = username or gira_settings.get_property('USERNAME')
        self.cache.password = password or gira_settings.get_property('PASSWORD')

        
        self.DEVICETYPE = self.DEVICEURLS = None
        self.cache.cookie = cookie
        self.cache.name = f'de.python.{uuid.getnode()}.{socket.gethostname()}' 
        self.errors = []
        
        if self.cache.hostname == None or self.cache.username == None or self.cache.password == None:
            log.critical('Hostname, username and/or password cannot be None')
            return (False)

    def vpn_connect(self):
        # re-login to refresh cookie
        if self.cache.cookie_jar:
            return(self.cache.cookie_jar)
        
        url = f'https://{self.cache.hostname}/httpaccess.net/{self.cache.cookie}/'
        
        login_request = requests.get(url)
        cookies = requests.utils.dict_from_cookiejar(login_request.cookies)
        self.cache.cookie_jar = cookies
        return cookies

    def invalidate_cache(self):
        if (self.cache):
            self.cache.invalidate()
        
    def version(self):
        
        
        version = self.cache.config_version
        if (version):
            log.debug(f'config_version found in cache {version}')
            return(version)

        
        if not self.DEVICEURLS and not self.identity():
            return(False)
            
        if not self.cache._token and not self.authenticate():
            return (False)
        
        if not 'CONFIG_URL_UID' in self.DEVICEURLS:
            log.critical('CONFIG_URL_UID not in devices URLS???')
            return(False)
                
        url = self.DEVICEURLS['CONFIG_URL_UID'].format(host=self.cache.hostname, token=self.cache._token )
        
        (json_data, result_code) = self._get(url)
        
        if (result_code != 200):
            return False
        
        self.cache.config_version = json_data['uid']
        return (self.cache.config_version)
        
    def authenticate(self):
        
        """authenticate the app at the gira server"""
        
        if (self.cache._token):
            log.debug(f'token found in cache {self.cache._token}')
            return(self.cache._token)
        
        if not self.DEVICEURLS:
            self.identity()
            
        if not 'AUTHENTICATION_URL' in self.DEVICEURLS:
            log.critical('AUTHENTICATION_URL not in devices URLS???')
            return(False)
        
        url = self.DEVICEURLS['AUTHENTICATION_URL'].format(host=self.cache.hostname)
        
        data = {"client": self.cache.name}
        
        log.debug(f'post: {data}')
        http_session = requests.Session()


        r = http_session.post(url,
                    json=data, headers=Headers,
                    verify=False,
                    cookies=self.cache.cookie,
                    auth=HTTPBasicAuth(self.cache.username, self.cache.password))

        if (r.status_code == 201):

            self.cache._token = r.json()['token']
            log.debug(f'received: {self.cache._token}')
                
            return(self.cache._token)

        log.critical(f'Error logging into server {url}: {r.json()}')
        self.errors.append(f'Error logging into server{url}: {r.json()} authentication failed')
        return(False)
    
    
    def identity(self):
        url = IdentityURl.format(host=self.cache.hostname)
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
        
        r = http_session.get(url, headers=Headers, verify=False, cookies=self.cache.cookie)
        
        if (r.headers['Content-Type'] == 'application/json'):
            if len(r.text) < 500:
                log.debug(f'Received status_code: {r.status_code} with data {r.json()}')
            else:
                log.debug(f'Received status_code: {r.status_code}')
            return(r.json(), r.status_code)
        
        log.debug(f'Received status_code: {r.status_code} with non json data and data: {r.text}')
        
        if not (r.status_code < 300):
            log.error('Received status_code: %s with non json data and data: %s' % (r.status_code, r.text))
            self.errors.append('Received status_code: %s with non json data and data: %s' % (r.status_code, r.text))

        return(None, r.status_code)


                
        
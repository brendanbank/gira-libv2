
import logging
import requests
from requests.auth import HTTPBasicAuth
from gira.device_config import DeviceConfig
import urllib3
import uuid
import socket
from urllib.parse import urljoin, urlparse
import json

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
        "GET_UID": 'https://{host}/api/v2/values/{uid}?token={token}',
        "PUT_UID": 'https://{host}/api/v2/values?token={token}',
        }
    }    

class GiraServer(object):

    def __init__(self, hostname, 
                 username,
                 password, 
                 cache,
                 cookie=None, 
                 vpn=False, 
                 gira_username=None,
                 gira_password=None,
                 ):
               
        log.debug(f'{__name__} started')

        if (cache == None):
            raise ValueError(f'cache cannot not be None')
            
        self.cache=cache
        
        
        cache.set_ignore(['username','password', 'gira_username', 'gira_password', 'vpn'])
        

        self.cache.hostname = hostname 
        self.cache.username = username 
        self.cache.password = password 
        self.cache.gira_username = gira_username 
        self.cache.gira_password = gira_password
        
        if (vpn):
            self.cache.vpn = vpn

        if cookie:
            self.cache.cookie = cookie
        
        self.DEVICETYPE = self.DEVICEURLS = None
        
        self.cache.name = f'de.python.{uuid.getnode()}.{socket.gethostname()}' 
        self.errors = []
        
        if self.cache.hostname == None or self.cache.username == None or self.cache.password == None:
            log.critical('Hostname, username and/or password cannot be None')
            return (False)
        
        self.identity()
        
    def invalidate_cache(self):
        if (self.cache):
            self.cache.invalidate()
            
    def get_device_config(self, refresh=False):
        
        
        self.authenticate()
        
        device_config_json = self.cache.device_config_json
        if (device_config_json and not refresh):
            log.info(f'device_config found in cache')
        
        else:
            url = self.DEVICEURLS['CONFIG_URL'].format(host=self.cache.vpn_hostname or self.cache.hostname, token=self.cache.token )
            
            (json_data, result_code) = self._get(url)
            
            if (result_code != 200):
                return False
            
            self.cache.device_config_json = json.dumps(json_data)
            
            log.info(f'device_config fetched from server')
            
        self.functions = DeviceConfig(cache=self.cache,device=self)
        
        return(self.functions)
            
    def version(self, refresh=False):
        
        version = self.cache.config_version
        
        if (version and not refresh):
            log.debug(f'config_version found in cache {version}')
            return(version)

        
        if not self.DEVICEURLS and not self.identity():
            return(False)
            
        if not self.cache.token and not self.authenticate():
            return (False)
        
        if not 'CONFIG_URL_UID' in self.DEVICEURLS:
            log.critical('CONFIG_URL_UID not in devices URLS???')
            return(False)
                
        url = self.DEVICEURLS['CONFIG_URL_UID'].format(host=self.cache.vpn_hostname or self.cache.hostname, token=self.cache.token )
        
        (json_data, result_code) = self._get(url)
        
        if (result_code != 200):
            return False
        
        self.cache.config_version = json_data['uid']
        return (self.cache.config_version)


    def authenticate(self,refresh=False):
        
        """authenticate the app at the gira server"""
        
        if (self.cache.vpn and not self.cache.cookie):
            self.vpn_login(refresh=True)
        
        if (self.cache.vpn and self.cache.cookie):
            hostname = self.cache.vpn_hostname
            cookie = self.vpn_connect()            
        else:
            hostname = self.cache.hostname
            cookie = None
        
        if (self.cache.token and not refresh):
            log.debug(f'token found in cache {self.cache.token}')
            return(self.cache.token)
        
        if not self.DEVICEURLS:
            self.identity(refresh=refresh)
            
        if not 'AUTHENTICATION_URL' in self.DEVICEURLS:
            log.critical('AUTHENTICATION_URL not in devices URLS???')
            return(False)
        
        url = self.DEVICEURLS['AUTHENTICATION_URL'].format(host=hostname)
        
        data = {"client": self.cache.name}
        
        log.debug(f'post: {data}')
        http_session = requests.Session()      
        
        log.debug (cookie)      
        
        log.info(f'connect to {url}')

        r = http_session.post(url,
                    json=data,
                    headers=Headers,
                    verify=False,
                    cookies=cookie,
                    auth=HTTPBasicAuth(self.cache.username, self.cache.password))

        if (r.status_code == 201 ):

            self.cache.token = r.json()['token']
            log.info(f'token received')
                
            return(self.cache.token)

        log.critical(f'Error logging into server {url}: {vars(r)}')
        self.errors.append(f'Error logging into server{url}: {vars(r)} authentication failed')
        return(False)
    
    
    def identity(self, refresh=False):
        
        if (not refresh and self.cache.devicetype):
            self.DEVICEURLS = DeviceTypes[self.cache.devicetype]
            return (True)
        
        url = IdentityURl.format(host=self.cache.vpn_hostname or self.cache.hostname)
        (jdata, status_code) = self._get(url)
        if status_code != 200:
            return (False)
        
        log.debug(f'Received: {jdata}')
        
        self.DEVICETYPE = jdata
        
        if self.DEVICETYPE['deviceType'] in DeviceTypes:
            log.info (f'Devicetype found: {self.DEVICETYPE["deviceType"]} ({self.DEVICETYPE["deviceName"]})')
            self.DEVICEURLS = DeviceTypes[self.DEVICETYPE['deviceType']]
            self.cache.devicetype = self.DEVICETYPE['deviceType']
            return (True)
        else:
            log.critical(f'Could not find devictype for: {self.DEVICETYPE["deviceType"]} ({self.DEVICETYPE["deviceName"]})')
            return(False)

    def _put(self, url, data):
        if (self.cache.vpn and not self.cache.cookie):
            self.vpn_login()
        
        if (self.cache.vpn and self.cache.cookie):
            cookie = self.vpn_connect()            
        else:
            cookie = None
            

        http_session = requests.Session()      

        r = http_session.put(url, json=data, headers=Headers, verify=False, cookies=cookie)

        if (r.status_code < 300):
            log.debug('Received status_code: %s with non json data and data: %s' % (r.status_code, r.text))
        else:
            log.error('Received status_code: %s with non json data and data: %s' % (r.status_code, r.text))
            self.errors.append('Received status_code: %s with non json data and data: %s' % (r.status_code, r.text))

        return(None, r.status_code)

    def put_uid(self,uid,value):
        url = self.DEVICEURLS['PUT_UID'].format(host=self.cache.vpn_hostname or self.cache.hostname, token=self.cache.token)
        data = {"values": [
                {"uid": uid,
                 "value": value
                    }
            
            ]}
        log.debug(f'set {uid} to {value}')
        (data,status_code) = self._put(url, data)
        if (status_code < 300):
            return (True)
        else:
            return(False)

    def get_uid(self,uid):
        log.debug(f'try to fetch {uid}')
        url = self.DEVICEURLS['GET_UID'].format(host=self.cache.vpn_hostname or self.cache.hostname, uid=uid, token=self.cache.token)
        (data,status_code) = self._get(url)


        if (status_code == 200):
            return(data)
        else:
            return (None)

    def _get(self, url):
        log.debug(f'connect to {url}')
        
        http_session = requests.Session()
        
        if (self.cache.cookie):
            cookie = json.loads(self.cache.cookie)
        else:
            cookie = None
        
        log.info(f'get {url}')
        r = http_session.get(url, headers=Headers, verify=False, cookies=cookie)
        
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

    def vpn_login(self,refresh = False):
        
        if not self.cache.vpn:
            log.info(f'vpn not configured!')
            return(True)

        if not refresh and self.cache.vpn and self.cache.cookie:
            return(True)
        
        from lxml import etree
        from io import StringIO
        # 
        log.info(f'try to connect to {self.cache.vpn}')
        
        r = requests.get(self.cache.vpn)
        
        post_items = {'user': self.cache.gira_username,
                      'password': self.cache.gira_password}
    
        parser = etree.HTMLParser()
        tree = etree.parse(StringIO(r.content.decode()), parser)
        root = tree.getroot()
    
        for form in root.xpath('//form'):
            action_path = form.get('action')
            
            for field in form.iterchildren():
                if field.get('name') in ['serviceId', 'url']:
                    post_items[field.get('name') ] = field.get('value')
    
        post_url = urljoin(r.url, action_path)
        
        log.info(f'post credentials to {post_url}')
        
        log.debug(post_items)
        
        login_request = requests.post(post_url, data=post_items)
        
        log.info(f'received {login_request.status_code}')
    
        cookie = { k:v for (k, v) in login_request.cookies.items()}
        self.cache.cookie = json.dumps(cookie)
        self.cache.vpn_hostname = urlparse(login_request.url).netloc
        
        if (self.cache.cookie):
            log.info(f'Authentication succeeded received cookie! {self.cache.cookie}')
            return True
        
        return False
    
    
    def vpn_connect(self, refresh=False):
        # re-login to refresh cookie
        
        if not (self.cache.cookie):
            return None
        
        if (not refresh):
            return (json.loads(self.cache.cookie))
        
        key = list(json.loads(self.cache.cookie).values())[0]
        
        url = f'https://{self.cache.vpn_hostname}/httpaccess.net/{key}/'
        
        login_request = requests.get(url)
        cookie = requests.utils.dict_from_cookiejar(login_request.cookies)
        self.cache.cookie = json.dumps(cookie)
        log.debug(f'new cookie {self.cache.cookie}')
                
        return cookie

    def post(self, url, data):
        if (self.cache.vpn and not self.cache.cookie):
            self.vpn_login()
        
        if (self.cache.vpn and self.cache.cookie):
            cookie = self.vpn_connect()            
        else:
            cookie = None
            
        http_session = requests.Session()      
        
        log.debug(f'posting {data}')

        r = http_session.post(url, json=data, headers=Headers, verify=False, cookies=cookie)
        
        if (hasattr(r.headers, 'content-type')):
            if (r.headers['Content-Type'] == 'application/json'):
                log.debug('Received status_code: %s with data %s' % (r.status_code, r.json()))
                return(r.json(), r.status_code)
        
        if (r.status_code < 300):
            log.debug('Received status_code: %s with non json data and data: %s' % (r.status_code, r.text))
        else:
            log.error('Error status_code: %s and data: %s' % (r.status_code, r.text))
            self.errors.append(f'Error trying to set callback with {data} status_code: {r.status_code} and data: {r.text}')

        return(None, r.status_code)

    def set_callaback(self, serviceCallback, valueCallback, testCallbacks=True):

        url = self.DEVICEURLS['CALLBACK_URL'].format(host=self.cache.vpn_hostname or self.cache.hostname, token=self.cache.token)

        jdata = {
                'serviceCallback': serviceCallback,
                'valueCallback': valueCallback,
                "testCallbacks": testCallbacks
                }
        
        print (jdata)

        (data, status_code) = self.post(url, jdata)

        if (status_code == 200):
            log.info('Callback was successfully registered.')
            return(True)

        log.critical('Error logging when communicating to the server %s' % (url))

        return(False)

    def delete_callback(self):
        if (self.cache.vpn and not self.cache.cookie):
            self.vpn_login()
        
        if (self.cache.vpn and self.cache.cookie):
            cookie = self.vpn_connect()            
        else:
            cookie = None

        url = self.DEVICEURLS['CALLBACK_URL'].format(host=self.cache.vpn_hostname or self.cache.hostname, token=self.cache.token)
        
        http_session = requests.Session()

        r = http_session.delete(url,
                    headers=Headers,
                    verify=False ,
                    cookies=cookie)
        
        if (r.status_code == 200):
            log.info('Callback was successfully deleted.')
            return(True)

        log.critical(f'Error delete client from  server {url}: {r.text}')
        return(False)
        
"""Module to interact with the X1 Rest API
"""

import logging
import requests
from requests.auth import HTTPBasicAuth
import urllib3
import uuid
import socket
from urllib.parse import urljoin, urlparse
import json
from lxml import etree
from io import StringIO

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
    '''
    class to interact with the REST API.
    
    :param hostname: Hostname of the X1 or Home server on the local LAN
    :param username: Gira Server (X1 or Home server) username
    :param password: Gira Server (X1 or Home server) password
    :param cache: gira.cache.CacheObject object
    :param cookie: Cookie DICT
    :param vpn: url to your X1 link through the Gira S1  has the following structure
        https://http.httpaccess.net/[serviceId]/httpu://[local LAN ip address of your X1]
        Ensure "httpu" is used to allow the untrusted certificate on the X1/Homeserver
    :param gira_username: username of the https://geraeteportal.gira.de/ portal
    :param gira_password: pasword of the https://geraeteportal.gira.de/ portal
    :param refresh: boolean if True it will delete the cached settings.

    '''

    def __init__(self,
                 hostname,
                 username,
                 password,
                 cache,
                 cookie=None,
                 vpn=False,
                 gira_username=None,
                 gira_password=None,
                 refresh=False):
               
        log.debug(f'{__name__} started')
        
        log.debug(vars(self))

        if (cache == None):
            raise ValueError(f'cache cannot not be None')
        
        if refresh:
            cache.invalidate()

        self.cache = cache
        
        
        cache.set_ignore(['username','password', 'gira_username', 'gira_password', 'vpn'])
        """Set the ingore vairables that will not be stored in the cache object"""
        

        self.cache.hostname = hostname 
        self.cache.username = username 
        self.cache.password = password 
        self.cache.gira_username = gira_username 
        self.cache.gira_password = gira_password
        self.functions = None
        
        if (vpn):
            self.cache.vpn = vpn
            self.vpn_login()
    

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
        '''
        This will delete the cache items of database.
        '''
        if (self.cache):
            self.cache.invalidate()
            
    def get_device_config(self, refresh=False):
        '''
        GiraServer.get_device_config retrieves the configuration from the server or from the cache.
        
        :param refresh: boolean if True it will ignore the cache in the database and fetch the configuration from the server and store it in the cache.
        '''
        
        
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
        '''
        GiraServer.version retrieves the configuration version from the server or from the cache.

        :param refresh: boolean if True it will ignore the cache in the database and fetch the version from the server and store it in the cache.
        '''
        
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
        '''
        authenticate the app at the gira server

        :param refresh: boolean if True it will ignore the cache in the database and fetch the setting from the server and store it in the cache.
        :returns: Authentication Token or false if the it's not possible authenticate. 
        '''
            
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
        '''
        Get the type of server (identity) from the X1/Home server.
        
        :param refresh: boolean if True it will ignore the cache in the database and fetch the setting from the server and store it in the cache.
        '''
        
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


    def vpn_login(self,refresh = False):
        '''
        VPN login (see separate documentation)
        
        :param refresh: boolean if True it will ignore the cache in the database and fetch the setting from the server and store it in the cache.
        '''
        
        if not self.cache.vpn:
            log.info(f'vpn not configured!')
            return(True)

        if not refresh and self.cache.vpn and self.cache.cookie:
            return(True)
        
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

    def set_callaback(self, serviceCallback, valueCallback, testCallbacks=True):
        '''
        Create a callback for events on the KNX bus on the Gira X1/Homeserver.
        
        :param serviceCallback: Callback url for service callback's.
        :param valueCallback: Callback url for datapoint callback's.
        :param testCallbacks: Test the callback server.
        :returns: True of False
        
        '''

        url = self.DEVICEURLS['CALLBACK_URL'].format(host=self.cache.vpn_hostname or self.cache.hostname, token=self.cache.token)

        jdata = {
                'serviceCallback': serviceCallback,
                'valueCallback': valueCallback,
                "testCallbacks": testCallbacks
                }
        
        (data, status_code) = self._post(url, jdata)

        if (status_code == 200):
            log.info('Callback was successfully registered.')
            return(True)

        log.critical('Error logging when communicating to the server %s' % (url))

        return(False)

    def delete_callback(self):
        '''
        Deletes the call back settings on the Gira X1/Homeserver.
        
        :returns: True of False

        '''
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

    def _post(self, url, data):
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


class Datapoint(object):
    def __init__(self, dp):
        self.value = None
        self.function = None
        self.location = None
        
        for key in dp.keys():
            setattr(self, key, dp[key])
            if key == 'uid':
                self.uid = dp[key]
        
    def __repr__(self):
        return f"<Datapoint(name='{self.name}', uid='{self.uid}, value='{self.value}, function='{self.function}')>"

    def get(self):
        data = self.function.device.get_uid(self.uid)
        if 'values' in data:
            for dp in data['values']:
                self.value = dp['value']
                log.debug(f"fetched: {self.uid} to {dp['value']} on {self}")
                
    def set(self,value):
        return self.function.device.put_uid(self.uid, str(value))

class Function(object):
    
    def __init__(self,config,device):

        self.functionType = config['functionType']
        self.channelType = config['channelType']
        self.displayName = config['displayName']
        self.uid = config['uid']
        self.dp_uids = {}
        self.location = None
        self.proc_datapoints(config['dataPoints'])
        self.trade = None
        self.device = device

    def __repr__(self):
        return f"<Function(functionType='{self.functionType}' channelType='{self.channelType}' displayName='{self.displayName}', " \
                        f"uid='{self.uid}')>"
    
    def get(self):
        data = self.device.get_uid(self.uid)
        if 'values' in data:
            for dp in data['values']:
                self.dp_uids[dp['uid']].value = dp['value']
                log.debug(f"fetched: {self.dp_uids[dp['uid']]} to {dp['value']}")

    def proc_datapoints(self,datapoints):
        self.dataPoints = []
        for dp in datapoints:
            datapoint = Datapoint(dp)
            self.dataPoints.append(datapoint)
            datapoint.function = self
            self.dp_uids[datapoint.uid] = datapoint
            log.debug(f'datapoint added {datapoint}')

class Location(object):
    def __init__(self,config,parent=None):
        self.displayName = config['displayName']
        self.locationType = config['locationType']
        self.children = []
        self.functions = None
        self.parent = parent
        self.uids = {}
        
        if 'locations' in config.keys():
            for location in config['locations']:
                self.children.append(Location(location,self))
        
        if 'functions' in config.keys():
            self.functions = config['functions']
            
    def location_string(self):
        string = ""
        if (self.parent):
            string = f'{self.parent.location_string()}/{self.displayName}({self.locationType})'
        else:
            string = f'{self.displayName} ({self.locationType})'
            
        return(string)
                
    def __repr__(self):
        return f"<Location(displayName='{self.displayName}', locationType='{self.locationType}')>"

class Trades(object):
    def __init__(self, config):
        self.uids = {}
        self.tradeName = config['displayName']
        self.tradeType = config['tradeType']
        
    def tradestring(self):
        return(f'{self.tradeName}({self.tradeType})')
        
    def __repr__(self):
        return f"<Trades(tradeName='{self.tradeName}', tradeType='{self.tradeType}')>"
        
        
class DeviceConfig(object):
    '''
    This class is creating a device configuration based on the the cached device configuration.
    
    :param cache: gira.cache.CacheObject object
    :param device: gira.GiraServer object
    '''

    def __init__(self, cache, device):

        log.debug(f'started')
        self.cache = cache
        self.locations=[]
        
        self.device = device
        
        self.device_config = json.loads(self.cache.device_config_json)
        
        self.function_uids = {}
        self.dataPiont_uids = {}
        self.trades = []
        
        if 'functions' in self.device_config.keys():
            self._proc_functions()
        
        if 'locations' in self.device_config.keys():
            self._proc_location()
            
        if 'trades' in self.device_config.keys():
            self._proc_trades()
        
        self.uids = {}
        self.uids.update(self.function_uids)
        self.uids.update(self.dataPiont_uids)
        

    def uid(self,uid):
        """returns the gira.device.Datapoint or gira.device.Function based on the uid.
        """
        return self.uids[uid]


    def get_all (self):
        """Fetch all gira.device.Datapoint from the X1 server
        """
        for function_uid in self.function_uids:
            self.function_uids[function_uid].get()

    def update_uid (self,uid,data):
        """update gira.device.Datapoint with a value.
        """
        if uid in self.uids:
            self.uids[uid].update(data)
        
    def _proc_location(self):
        log.debug(f'started')
        for  location in self.device_config['locations']:
            location = Location(location)
            self.locations.append(location)

            
            def set_location(self,location):
                if location.functions:
                    for uid in location.functions:
                        function = self.function_uids[uid]
                        function.location = location
                        location.uids[uid] = function

                for loc in location.children:
                    set_location(self,loc)
                    
                log.debug (f'location added: {location}')
                
            log.debug (f'location added: {location}')
            if location.functions:
                set_location(self,location)
                
            for loc in location.children:
                set_location(self,loc)

    def _proc_trades(self):
        log.debug(f'started')
        
        
        for trades_conf in self.device_config['trades']:
            trade = Trades(trades_conf)
            log.debug (f'trade added: {trade}')
            
            if 'functions' in trades_conf:
                for uid in trades_conf['functions']:
                    function = self.function_uids[uid]
                    trade.uids[uid] = function
                    function.trade = trade
                    
            self.trades.append(trade)

        
    def _proc_functions(self):
        log.debug(f'started')
        
        for  function in self.device_config['functions']:
            function = Function(function, self.device)
            log.debug (f'function added: {function}')
            self.function_uids[function.uid] = function
            for dp in function.dataPoints:
                self.dataPiont_uids[dp.uid] = dp
            
            
            
        
        
        


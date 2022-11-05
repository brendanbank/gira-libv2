'''
Created on 5 Nov 2022

@author: brendan
'''

import json
import logging

log = logging.getLogger(__name__)
log.debug(f'{__name__} loaded')


# Binary
# Brightness
# Current
# DWord
# Heating
# Mode
# OnOff
# Percent
# Scene
# Set-Point
# Shift
# Status
# Step-Up-Down
# Trigger
# Up-Down


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
        return f"<Datapoint(name='{self.name}', uid='{self.uid}, value='{self.value}, function='{self.function}'>"

    def get(self):
        data = self.function.device.get_uid(self.uid)
        if 'values' in data:
            for dp in data['values']:
                self.value = dp['value']
                log.debug(f"fetched: {self.uid} to {dp['value']} on {self}")
                
    def set(self,value):
        data = self.function.device.put_uid(self.uid, str(value))
        log.debug(data)


class Function(object):
    
    def __init__(self,config,device):

        self.functionType = config['functionType']
        self.channelType = config['channelType']
        self.displayName = config['displayName']
        self.uid = config['uid']
        self.dp_uids = {}
        self.location = None
        self.proc_datapoints(config['dataPoints'])
        self.tradeName = None
        self.tradeType = None
        self.device = device

    def __repr__(self):
        return f"<Function(functionType='{self.functionType}' channelType='{self.channelType}' displayName='{self.displayName}', " \
                        f"uid='{self.uid}' location='{self.location}' tradeName='{self.tradeName}' " \
                        f"tradeType='{self.tradeType}'>"
    
    def get(self):
        data = self.device.get_uid(self.uid)
        if 'values' in data:
            for dp in data['values']:
                self.dp_uids[dp['uid']].value = dp['value']
                log.debug(f"fetched: {self.dp_uids[dp['uid']]} to {dp['value']} on {self}")

    def proc_datapoints(self,datapoints):
        self.dataPoints = []
        for dp in datapoints:
            datapoint = Datapoint(dp)
            self.dataPoints.append(datapoint)
            datapoint.function = self
            self.dp_uids[datapoint.uid] = datapoint

class Location(object):
    def __init__(self,config,parent=None):
        self.displayName = config['displayName']
        self.locationType = config['locationType']
        self.children = []
        self.functions = None
        self.parent = parent
        
        if 'locations' in config.keys():
            for location in config['locations']:
                self.children.append(Location(location,self))
        
        if 'functions' in config.keys():
            self.functions = config['functions']
                
    def __repr__(self):
        return f"<Location(displayName='{self.displayName}', locationType='{self.locationType}, parent='{self.parent}'>"

class DeviceConfig(object):

    def __init__(self, cache, device):
        '''
        Constructor
        '''
        log.debug(f'started')
        self.cache = cache
        
        self.device = device
        
        self.device_config = json.loads(self.cache.device_config_json)
        
        self.function_uids = {}
        self.dataPiont_uids = {}
        
        print (self.device_config.keys())
        if 'functions' in self.device_config.keys():
            self.proc_functions()
        
        if 'locations' in self.device_config.keys():
            self.proc_location()
            
        if 'trades' in self.device_config.keys():
            self.proc_trades()
        
        self.uids = {}
        self.uids.update(self.function_uids)
        self.uids.update(self.dataPiont_uids)
        

    def update_uid (self,uid,data):
        if uid in self.uids:
            self.uids[uid].update(data)
        
    def proc_location(self):
        log.debug(f'started')
        for  location in self.device_config['locations']:
            location = Location(location)

            
            def set_location(self,location):
                if location.functions:
                    for uid in location.functions:
                        function = self.function_uids[uid]
                        function.location = location

                for loc in location.children:
                    set_location(self,loc)
                    
                log.debug (f'location added: {location}')
                
            log.debug (f'location added: {location}')
            if location.functions:
                set_location(self,location)
            for loc in location.children:
                set_location(self,loc)
                



    def proc_trades(self):
        log.debug(f'started')
        
        for trades in self.device_config['trades']:
            tradeName = trades['displayName']
            tradeType = trades['tradeType']
            if 'functions' in trades:
                for uid in trades['functions']:
                    function = self.function_uids[uid]
                    function.tradeName = tradeName
                    function.tradeType = tradeType
            
            

    def proc_functions(self):
        log.debug(f'started')
        
        for  function in self.device_config['functions']:
            function = Function(function, self.device)
            self.function_uids[function.uid] = function
            for dp in function.dataPoints:
                self.dataPiont_uids[dp.uid] = dp
            
            
            
        
        
        

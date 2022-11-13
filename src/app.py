"""
This is a flask test server to demonstrate how to receive call-backs from an X1 Gira Server.

To start this flask test server

  python ./app.py
  

It expects the following environment variables to be set.

DEBUG=<True|False>
HOSTNAME=<local LAN IP address of your X1>
USERNAME=<username of the X1>
PASSWORD=<password of the X1>
SQLALCHEMY_DATABASE_URI=<database URI>
GIRA_USERNAME=<>
GIRA_PASSWORD=<>
VPN_HOST=<url to your X1 link through the Gira S1>
INSTANCE_NAME=<instance name, used for storing your key variables (cookies, authorization keys) in your persistent cache> 

The VPN_HOST has the following sturcture

    https://http.httpaccess.net/[serviceId]/httpu://[local LAN ip address of your X1]
    
It can be found in your S1 configuration on https://geraeteportal.gira.de/

You can add these variables to the .env file in the root of your project, the load_dotenv command will read them.

You will have to run GiraServer.set_callaback after the server has started.

"""

import logging, sys
from flask import Flask, request
from gira.device import GiraServer
from distutils.util import strtobool
from gira.cache import CacheObject


log = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s %(name)s.%(funcName)s(%(lineno)s): %(message)s', stream=sys.stderr)

from dotenv import load_dotenv
from os import environ

load_dotenv()

if bool(strtobool(environ.get('DEBUG', 'False'))):              
    logging.getLogger().setLevel(logging.DEBUG)
else:
    logging.getLogger().setLevel(logging.INFO)

app = Flask(__name__)

@app.route("/giraapi/value",methods=['GET', 'POST'])
def giraapi_value():
    jdata = request.get_json()
    # log.debug(f'data received: {jdata}')    
    if 'events' in jdata:
        for event in jdata['events']:
            uid = event['uid']
            log.debug(f"uid='{uid}'")
            dp = server.functions.uids[uid]
            dp.value = event['value']
            log.debug (f"Data point: name='{dp.name}' value='{dp.value}' function='{dp.function.displayName}' " \
                       f"location='{dp.function.location.location_string()}' "\
                       f"type='{dp.function.trade.tradestring()}'")
            
    return '{"status":"OK"}'

@app.route("/giraapi/function",methods=['GET', 'POST'])
def giraapi_function():
    log.debug(request)
    
    jdata = request.get_json()
    log.info(f'data received: {jdata}')
    return '{"status":"OK"}'

@app.route("/giraapi/test",methods=['GET', 'POST'])
def giraapi_test():
    jdata = request.get_json()
    log.info(f'data received: {jdata}')
    return '{"status":"OK"}'

if __name__ == '__main__':
    
    cache = CacheObject(dburi=environ.get('SQLALCHEMY_DATABASE_URI'), instance=environ.get('HOSTNAME'))
    # cache.invalidate()

    vpn=environ.get('VPN_HOST')    
    server = GiraServer(cache=cache, 
                        password=environ.get('USERNAME'),
                        username=environ.get('PASSWORD'),
                        gira_username=environ.get('GIRA_USERNAME'),
                        gira_password=environ.get('GIRA_PASSWORD'),
                        hostname=environ.get('HOSTNAME'),
                        vpn=vpn
                        )
    server.authenticate()
    server.get_device_config()
    
    app.run(app.run(host='0.0.0.0',ssl_context='adhoc', debug=True, port=5001))


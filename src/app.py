import logging, sys
from flask import Flask, request
from gira.device import GiraServer

from gira.cache import CacheObject


log = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s %(name)s.%(funcName)s(%(lineno)s): %(message)s', stream=sys.stderr)
logging.getLogger().setLevel(logging.DEBUG)
from dotenv import load_dotenv
from os import environ

load_dotenv()

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

    vpn = 'https://http.httpaccess.net/GIS1YYYCJD/httpu://10.0.60.101'
    vpn=None
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


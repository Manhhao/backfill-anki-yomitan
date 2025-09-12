import json
import socket
import urllib
from aqt import mw
from . import logger
from urllib.error import HTTPError, URLError

request_url = ""
request_timeout = 10
ping_timeout = 5

max_entries = 0
reading_handlebar = ""

def read_config():
    global request_url
    global max_entries
    global reading_handlebar
    cfg = mw.addonManager.getConfig(__name__)

    request_url = f"http://{cfg['yomitan_api_ip']}:{cfg['yomitan_api_port']}"
    max_entries = cfg["max_entries"]
    reading_handlebar = cfg["reading_handlebar"]

# https://github.com/Kuuuube/yomitan-api/blob/master/docs/api_paths/ankiFields.md
def request_handlebar(expression, reading, handlebars):
    markers = list(handlebars)
    if reading:
        markers.append(reading_handlebar)

    body = {
        "text": expression,
        "type": "term",
        "markers": markers,
        "maxEntries": max_entries if reading else 1,
        "includeMedia": True
    }

    req = urllib.request.Request(
        request_url + "/ankiFields",
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        response = urllib.request.urlopen(req, timeout=request_timeout)  
        data = json.loads(response.read())
    except HTTPError as e:
        if e.code == 500:
            logger.log.error(f"http 500: request using {markers}")
            return None
        else:
            logger.log.error(e)
            raise
    except socket.timeout:
        logger.log.error(f"request using '{markers}' timed out for '{expression}'")
        return None
    except URLError as e:
        logger.log.error(e.reason)
        raise ConnectionRefusedError(f"Request to Yomitan API failed: {e.reason}")
    
    return data

def ping_yomitan(): 
    read_config()
    req = urllib.request.Request(request_url + "/yomitanVersion", method="POST")
    try:
        response = urllib.request.urlopen(req, timeout=ping_timeout)  
        data = json.loads(response.read())
        return data
    except Exception:
        return False
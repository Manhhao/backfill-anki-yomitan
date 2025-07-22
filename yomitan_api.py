import json
import urllib
from urllib.error import HTTPError, URLError

request_url = "http://127.0.0.1:8766"
request_timeout = 10
ping_timeout = 5

# https://github.com/Kuuuube/yomitan-api/blob/master/docs/api_paths/ankiFields.md
def request_handlebar(expression, reading, handlebar):
    body = {
        "text": expression,
        "type": "term",
        "markers": [handlebar, "reading"],
        "maxEntries": 4 if reading else 1, # should probably be configurable
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
            # this throws if the handlebar does not exist for specified term
            return None
        else:
            raise
    except URLError as e:
        raise ConnectionRefusedError(f"Request to Yomitan API failed: {e.reason}")
    
    return data

def ping_yomitan(): 
    req = urllib.request.Request(request_url + "/yomitanVersion", method="POST")
    try:
        response = urllib.request.urlopen(req, timeout=ping_timeout)  
        data = json.loads(response.read())
        return data
    except Exception:
        return False
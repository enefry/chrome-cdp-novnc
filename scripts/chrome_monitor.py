import requests
import time
import os
import signal

DEBUG_PORT = int(os.environ.get("DEBUG_PORT", "9222"))
CHECK_URL = f"http://127.0.0.1:{DEBUG_PORT}/json/version"


while True:
    try:
        r = requests.get(CHECK_URL, timeout=5)
        if r.status_code != 200:
            raise RuntimeError(f"Bad status: {r.status_code}")
    except Exception:
        os.kill(1, signal.SIGTERM)
        break
    time.sleep(30)

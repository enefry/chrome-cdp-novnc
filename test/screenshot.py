#!/usr/bin/env python3
import base64
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cdp_client import connect_page, open_target


def main():
    url = sys.argv[1] if len(sys.argv) > 1 else "https://example.com"
    output = sys.argv[2] if len(sys.argv) > 2 else "screenshot.png"

    target = open_target(url)
    ws = connect_page(target["webSocketDebuggerUrl"])
    try:
        ws.call("Page.enable")
        ws.call("Page.navigate", {"url": url}, msg_id=2)
        ws.call("Runtime.enable", msg_id=3)
        ws.call("Runtime.evaluate", {"expression": "document.readyState", "returnByValue": True}, msg_id=4)
        shot = ws.call("Page.captureScreenshot", {"format": "png", "fromSurface": True}, msg_id=5)
    finally:
        ws.close()

    with open(output, "wb") as f:
        f.write(base64.b64decode(shot["data"]))

    print("Saved:", output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

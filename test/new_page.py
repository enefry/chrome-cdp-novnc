#!/usr/bin/env python3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cdp_client import connect_page, open_target


def main():
    url = sys.argv[1] if len(sys.argv) > 1 else "https://example.com"
    target = open_target(url)
    print("Opened:", url)
    print("Target ID:", target["id"])
    print("Page WS:", target["webSocketDebuggerUrl"])

    ws = connect_page(target["webSocketDebuggerUrl"])
    try:
        ws.call("Page.enable")
        result = ws.call("Runtime.evaluate", {"expression": "document.title", "returnByValue": True}, msg_id=2)
        print("Title:", result["result"].get("value"))
    finally:
        ws.close()


if __name__ == "__main__":
    raise SystemExit(main())

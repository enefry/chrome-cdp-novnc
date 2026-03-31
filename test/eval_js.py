#!/usr/bin/env python3
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cdp_client import connect_page, list_targets


def main():
    expression = sys.argv[1] if len(sys.argv) > 1 else "document.title"

    targets = [t for t in list_targets() if t.get("type") == "page"]
    if not targets:
        raise SystemExit("No page targets available")

    target = targets[0]
    print("Target:", target["title"], target["url"])

    ws = connect_page(target["webSocketDebuggerUrl"])
    try:
        ws.call("Runtime.enable")
        result = ws.call(
            "Runtime.evaluate",
            {"expression": expression, "returnByValue": True, "awaitPromise": True},
            msg_id=2,
        )
    finally:
        ws.close()

    print(json.dumps(result["result"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

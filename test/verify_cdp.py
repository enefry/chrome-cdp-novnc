#!/usr/bin/env python3
import argparse
import base64
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cdp_client import HTTP_BASE, browser_version, connect_browser, connect_page, list_targets, open_target


def print_base_info(version: dict, targets: list):
    print("CDP HTTP:", HTTP_BASE)
    print("Browser:", version["Browser"])
    print("Protocol-Version:", version["Protocol-Version"])
    print("Browser WS:", version["webSocketDebuggerUrl"])
    print("Targets:", len(targets))


def verify_browser(version: dict):
    ws = connect_browser()
    try:
        result = ws.call("Browser.getVersion")
    finally:
        ws.close()

    print("CDP command:", "Browser.getVersion")
    print("Product:", result.get("product"))
    print("Revision:", result.get("revision"))
    print("User-Agent:", result.get("userAgent"))


def open_page(url: str):
    target = open_target(url)
    print("Opened:", url)
    print("Target ID:", target["id"])
    print("Page WS:", target["webSocketDebuggerUrl"])
    return target


def eval_on_target(target: dict, expression: str):
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

    print("Eval Target:", target["title"], target["url"])
    print(json.dumps(result["result"], ensure_ascii=False, indent=2))


def screenshot_target(target: dict, path: str):
    ws = connect_page(target["webSocketDebuggerUrl"])
    try:
        ws.call("Page.enable")
        shot = ws.call("Page.captureScreenshot", {"format": "png", "fromSurface": True}, msg_id=2)
    finally:
        ws.close()

    with open(path, "wb") as f:
        f.write(base64.b64decode(shot["data"]))

    print("Saved:", path)


def choose_existing_page(targets: list):
    pages = [t for t in targets if t.get("type") == "page"]
    if not pages:
        raise RuntimeError("no page targets available")
    return pages[0]


def parse_args():
    parser = argparse.ArgumentParser(description="Verify and exercise a Chrome CDP endpoint.")
    parser.add_argument("--url", default="https://example.com", help="URL used with --new-page")
    parser.add_argument("--new-page", action="store_true", help="Create a new page target using --url")
    parser.add_argument("--eval", dest="expression", help="Evaluate JavaScript on a page target")
    parser.add_argument("--screenshot", metavar="PATH", help="Capture a PNG screenshot to PATH")
    return parser.parse_args()


def main():
    args = parse_args()
    version = browser_version()
    targets = list_targets()
    print_base_info(version, targets)
    verify_browser(version)

    target = None
    if args.new_page:
        target = open_page(args.url)
    elif args.expression or args.screenshot:
        target = choose_existing_page(targets)

    if args.expression:
        eval_on_target(target, args.expression)

    if args.screenshot:
        screenshot_target(target, args.screenshot)

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"verify_cdp.py failed: {exc}", file=sys.stderr)
        raise SystemExit(1)

#!/usr/bin/env python3
import argparse
import base64
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cdp_client import browser_version, connect_browser, connect_page, list_targets, open_target


def ok(name: str, detail: str):
    print(f"[OK] {name}: {detail}")


def fail(name: str, detail: str):
    print(f"[FAIL] {name}: {detail}")


def check_http(url: str, name: str):
    with urllib.request.urlopen(url, timeout=10) as resp:
        status = getattr(resp, "status", 200)
        if status >= 400:
            raise RuntimeError(f"HTTP {status}")
        body = resp.read(256)
    ok(name, f"{url} -> HTTP {status}, {len(body)} bytes")


def check_browser_ws():
    version = browser_version()
    ws = connect_browser()
    try:
        result = ws.call("Browser.getVersion")
    finally:
        ws.close()
    ok("CDP Browser WS", result.get("product", "unknown"))
    return version


def check_targets():
    targets = list_targets()
    ok("CDP Targets", str(len(targets)))
    return targets


def check_page_flow(url: str, screenshot_path: str):
    target = open_target(url)
    ok("Open Page", f"{target['id']} {url}")

    ws = connect_page(target["webSocketDebuggerUrl"])
    try:
        ws.call("Page.enable")
        ws.call("Runtime.enable", msg_id=2)
        title = ws.call(
            "Runtime.evaluate",
            {"expression": "document.title", "returnByValue": True, "awaitPromise": True},
            msg_id=3,
        )
        shot = ws.call("Page.captureScreenshot", {"format": "png", "fromSurface": True}, msg_id=4)
    finally:
        ws.close()

    title_value = title["result"].get("value", "")
    ok("Runtime.evaluate", repr(title_value))

    data = base64.b64decode(shot["data"])
    with open(screenshot_path, "wb") as f:
        f.write(data)
    ok("Page.captureScreenshot", f"{screenshot_path} ({len(data)} bytes)")


def parse_args():
    parser = argparse.ArgumentParser(description="Run an end-to-end health check for chrome-cdp.")
    parser.add_argument("--novnc-url", default="http://127.0.0.1:9600", help="noVNC base URL")
    parser.add_argument("--test-url", default="https://example.com", help="URL opened for page checks")
    parser.add_argument(
        "--screenshot-path",
        default="/tmp/chrome-cdp-test-all.png",
        help="Where to save the verification screenshot",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    failures = []

    checks = [
        ("noVNC HTTP", lambda: check_http(args.novnc_url, "noVNC HTTP")),
        ("CDP Version HTTP", lambda: ok("CDP Version HTTP", browser_version()["Browser"])),
        ("CDP Browser WS", check_browser_ws),
        ("CDP Targets", check_targets),
        ("Page Flow", lambda: check_page_flow(args.test_url, args.screenshot_path)),
    ]

    for name, fn in checks:
        try:
            fn()
        except Exception as exc:
            failures.append((name, str(exc)))
            fail(name, str(exc))

    if failures:
        print()
        print("Environment check failed.")
        return 1

    print()
    print("Environment check passed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"test_all.py failed: {exc}", file=sys.stderr)
        raise SystemExit(1)

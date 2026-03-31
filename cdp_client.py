#!/usr/bin/env python3
import base64
import hashlib
import json
import os
import socket
import urllib.request
from urllib.parse import quote, urlparse


HTTP_BASE = os.environ.get("CDP_HTTP_BASE", "http://127.0.0.1:9601")


def http_get_json(path: str):
    with urllib.request.urlopen(f"{HTTP_BASE}{path}", timeout=10) as resp:
        return json.load(resp)


def http_put_json(path: str):
    req = urllib.request.Request(f"{HTTP_BASE}{path}", method="PUT")
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.load(resp)


def open_target(url: str):
    return http_put_json(f"/json/new?{quote(url, safe=':/?&=#')}")


def list_targets():
    return http_get_json("/json/list")


def browser_version():
    return http_get_json("/json/version")


class WebSocketClient:
    def __init__(self, ws_url: str):
        self.ws_url = ws_url
        self.sock = None

    def connect(self):
        parsed = urlparse(self.ws_url)
        host = parsed.hostname or "127.0.0.1"
        port = parsed.port or 80
        path = parsed.path or "/"
        if parsed.query:
            path = f"{path}?{parsed.query}"

        sock = socket.create_connection((host, port), timeout=10)
        key = base64.b64encode(os.urandom(16)).decode("ascii")
        request = (
            f"GET {path} HTTP/1.1\r\n"
            f"Host: {host}:{port}\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\n"
            "Sec-WebSocket-Version: 13\r\n"
            "\r\n"
        )
        sock.sendall(request.encode("ascii"))

        response = b""
        while b"\r\n\r\n" not in response:
            chunk = sock.recv(4096)
            if not chunk:
                raise RuntimeError("websocket handshake failed: empty response")
            response += chunk

        header_block = response.split(b"\r\n\r\n", 1)[0].decode("latin1")
        lines = header_block.split("\r\n")
        if "101" not in lines[0]:
            raise RuntimeError(f"websocket handshake failed: {lines[0]}")

        headers = {}
        for line in lines[1:]:
            if ":" in line:
                k, v = line.split(":", 1)
                headers[k.strip().lower()] = v.strip()

        expected = base64.b64encode(
            hashlib.sha1((key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode("ascii")).digest()
        ).decode("ascii")
        if headers.get("sec-websocket-accept") != expected:
            raise RuntimeError("websocket handshake failed: invalid accept key")

        self.sock = sock
        return self

    def close(self):
        if self.sock is not None:
            self.sock.close()
            self.sock = None

    def _recv_exact(self, n: int) -> bytes:
        data = bytearray()
        while len(data) < n:
            chunk = self.sock.recv(n - len(data))
            if not chunk:
                raise RuntimeError("websocket read failed: connection closed")
            data.extend(chunk)
        return bytes(data)

    def send_json(self, payload: dict):
        body = json.dumps(payload).encode("utf-8")
        mask = os.urandom(4)
        header = bytearray([0x81])
        length = len(body)
        if length < 126:
            header.append(0x80 | length)
        elif length < (1 << 16):
            header.append(0x80 | 126)
            header.extend(length.to_bytes(2, "big"))
        else:
            header.append(0x80 | 127)
            header.extend(length.to_bytes(8, "big"))

        masked = bytes(b ^ mask[i % 4] for i, b in enumerate(body))
        self.sock.sendall(bytes(header) + mask + masked)

    def recv_json(self):
        first = self._recv_exact(2)
        opcode = first[0] & 0x0F
        masked = (first[1] & 0x80) != 0
        length = first[1] & 0x7F

        if length == 126:
            length = int.from_bytes(self._recv_exact(2), "big")
        elif length == 127:
            length = int.from_bytes(self._recv_exact(8), "big")

        mask = self._recv_exact(4) if masked else b""
        payload = bytearray(self._recv_exact(length))
        if masked:
            payload = bytearray(b ^ mask[i % 4] for i, b in enumerate(payload))

        if opcode == 0x8:
            raise RuntimeError("websocket closed by peer")
        if opcode != 0x1:
            raise RuntimeError(f"unexpected websocket opcode: {opcode}")

        return json.loads(payload.decode("utf-8"))

    def call(self, method: str, params=None, msg_id: int = 1):
        self.send_json({"id": msg_id, "method": method, "params": params or {}})
        while True:
            message = self.recv_json()
            if message.get("id") == msg_id:
                if "error" in message:
                    raise RuntimeError(f"{method} failed: {message['error']}")
                return message["result"]


def connect_browser():
    version = browser_version()
    return WebSocketClient(version["webSocketDebuggerUrl"]).connect()


def connect_page(ws_url: str):
    return WebSocketClient(ws_url).connect()

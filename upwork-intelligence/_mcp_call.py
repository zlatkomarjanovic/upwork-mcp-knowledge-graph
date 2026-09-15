#!/usr/bin/env python3
"""Invoke Upwork find_jobs via Cursor dynamic tools HTTP bridge (when available)."""
import json
import os
import socket
import sys


def http_post(path: str, body: dict) -> tuple[int, str]:
    sock_path = os.environ.get("CURSOR_AGENT_SOCKET", "/run/cursor/api.sock")
    payload = json.dumps(body)
    req = (
        f"POST {path} HTTP/1.1\r\n"
        f"Host: localhost\r\n"
        f"Content-Type: application/json\r\n"
        f"Content-Length: {len(payload)}\r\n"
        f"Connection: close\r\n\r\n"
        f"{payload}"
    )
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.connect(sock_path)
    sock.sendall(req.encode())
    data = b""
    while True:
        chunk = sock.recv(65536)
        if not chunk:
            break
        data += chunk
    sock.close()
    text = data.decode("utf-8", errors="replace")
    if "\r\n\r\n" in text:
        header, body_text = text.split("\r\n\r\n", 1)
        status = int(header.split()[1]) if header.startswith("HTTP") else 0
        return status, body_text
    return 0, text


def call_find_jobs(payload: dict) -> dict:
    paths = (
        "/v1/dynamic-tools/invoke",
        "/v1/mcp/invoke",
        "/v1/tools/invoke",
    )
    for path in paths:
        status, body = http_post(
            path,
            {
                "namespace": "Upwork",
                "toolName": "upwork__find_jobs",
                "arguments": payload,
            },
        )
        if status == 200:
            try:
                return json.loads(body)
            except json.JSONDecodeError:
                return {"status": "error", "error": body[:500]}
    return {"status": "error", "error_code": "NO_BRIDGE"}


def main() -> None:
    payload = json.loads(sys.argv[1])
    print(json.dumps(call_find_jobs(payload)))


if __name__ == "__main__":
    main()

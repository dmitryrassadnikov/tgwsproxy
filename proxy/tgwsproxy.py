from __future__ import annotations

import argparse
import asyncio
import base64
import logging
import os
import socket as _socket
import ssl
import struct
import sys
import time
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from typing import Dict, List, Optional, Set, Tuple

DEFAULT_PORT = 1080
log = logging.getLogger('tg-ws-proxy')

_TCP_NODELAY = True
_RECV_BUF = 64 * 1024
_SEND_BUF = 64 * 1024
_WS_POOL_SIZE = 8
_WS_POOL_MAX_AGE = 60.0

# --- Telegram IP ranges ---
_TG_RANGES = [(struct.unpack('!I', _socket.inet_aton('185.76.151.0'))[0],
               struct.unpack('!I', _socket.inet_aton('185.76.151.255'))[0]),
    (struct.unpack('!I', _socket.inet_aton('149.154.160.0'))[0],
     struct.unpack('!I', _socket.inet_aton('149.154.175.255'))[0]),
    (struct.unpack('!I', _socket.inet_aton('91.105.192.0'))[0],
     struct.unpack('!I', _socket.inet_aton('91.105.193.255'))[0]),
    (struct.unpack('!I', _socket.inet_aton('91.108.0.0'))[0],
     struct.unpack('!I', _socket.inet_aton('91.108.255.255'))[0]), ]

_IP_TO_DC: Dict[str, Tuple[int, bool]] = {'149.154.175.50': (1, False), '149.154.175.52': (1, True),
    '149.154.167.41': (2, False), '149.154.167.151': (2, True), '149.154.175.100': (3, False),
    '149.154.175.102': (3, True), '149.154.167.91': (4, False), '149.154.164.250': (4, True),
    '91.108.56.100': (5, False), '91.108.56.102': (5, True), '91.105.192.100': (203, False), }

_DC_OVERRIDES: Dict[int, int] = {203: 2}
_dc_opt: Dict[int, Optional[str]] = {}

_ws_blacklist: Set[Tuple[int, bool]] = set()
_dc_fail_until: Dict[Tuple[int, bool], float] = {}

_DC_FAIL_COOLDOWN = 30.0
_WS_FAIL_TIMEOUT = 2.0

_ssl_ctx = ssl.create_default_context()
_ssl_ctx.check_hostname = False
_ssl_ctx.verify_mode = ssl.CERT_NONE


# ---------------- utils ----------------

def _set_sock_opts(transport):
    sock = transport.get_extra_info('socket')
    if sock is None:
        return
    try:
        sock.setsockopt(_socket.IPPROTO_TCP, _socket.TCP_NODELAY, 1)
    except Exception:
        pass


def _xor_mask(data: bytes, mask: bytes) -> bytes:
    if not data:
        return data
    return bytes(b ^ mask[i % 4] for i, b in enumerate(data))


def _is_telegram_ip(ip: str) -> bool:
    try:
        n = struct.unpack('!I', _socket.inet_aton(ip))[0]
        return any(lo <= n <= hi for lo, hi in _TG_RANGES)
    except OSError:
        return False


def _ws_domains(dc: int, is_media: Optional[bool]) -> List[str]:
    dc = _DC_OVERRIDES.get(dc, dc)
    if is_media:
        return [f'kws{dc}-1.web.telegram.org', f'kws{dc}.web.telegram.org']
    return [f'kws{dc}.web.telegram.org', f'kws{dc}-1.web.telegram.org']


# ---------------- WebSocket ----------------

class WsHandshakeError(Exception):
    def __init__(self, status_code: int, status_line: str):
        self.status_code = status_code
        self.status_line = status_line
        super().__init__(status_line)


class RawWebSocket:
    OP_BINARY = 2

    def __init__(self, reader, writer):
        self.reader = reader
        self.writer = writer
        self._closed = False

    @staticmethod
    async def connect(ip: str, domain: str, timeout=10):
        reader, writer = await asyncio.open_connection(ip, 443, ssl=_ssl_ctx, server_hostname=domain)

        key = base64.b64encode(os.urandom(16)).decode()

        req = (f"GET /apiws HTTP/1.1\r\n"
               f"Host: {domain}\r\n"
               f"Upgrade: websocket\r\n"
               f"Connection: Upgrade\r\n"
               f"Sec-WebSocket-Key: {key}\r\n"
               f"Sec-WebSocket-Version: 13\r\n\r\n")

        writer.write(req.encode())
        await writer.drain()

        line = await reader.readline()
        if b"101" not in line:
            raise WsHandshakeError(0, line.decode())

        while True:
            if await reader.readline() in (b"\r\n", b""):
                break

        return RawWebSocket(reader, writer)

    async def send(self, data: bytes):
        if self._closed:
            return
        frame = b'\x82' + bytes([len(data)]) + data
        self.writer.write(frame)
        await self.writer.drain()

    async def recv(self):
        hdr = await self.reader.readexactly(2)
        length = hdr[1] & 0x7F
        return await self.reader.readexactly(length)

    async def close(self):
        self._closed = True
        self.writer.close()
        await self.writer.wait_closed()


# ---------------- bridge ----------------

async def _bridge_ws(reader, writer, ws: RawWebSocket):
    async def a():
        while True:
            d = await reader.read(65536)
            if not d:
                break
            await ws.send(d)

    async def b():
        while True:
            d = await ws.recv()
            if not d:
                break
            writer.write(d)
            await writer.drain()

    await asyncio.gather(a(), b())


# ---------------- handler ----------------

async def _handle_client(reader, writer):
    try:
        hdr = await reader.readexactly(2)
        if hdr[0] != 5:
            writer.close()
            return

        n = hdr[1]
        await reader.readexactly(n)

        writer.write(b'\x05\x00')
        await writer.drain()

        req = await reader.readexactly(4)
        atyp = req[3]

        if atyp == 1:
            dst = _socket.inet_ntoa(await reader.readexactly(4))
        else:
            writer.close()
            return

        port = struct.unpack('!H', await reader.readexactly(2))[0]

        if not _is_telegram_ip(dst):
            writer.close()
            return

        writer.write(b'\x05\x00\x00\x01\x00\x00\x00\x00\x00\x00')
        await writer.drain()

        init = await reader.readexactly(64)

        dc, is_media = _IP_TO_DC.get(dst, (2, False))
        domains = _ws_domains(dc, is_media)
        target = _dc_opt.get(dc)

        for d in domains:
            try:
                ws = await RawWebSocket.connect(target, d)
                break
            except Exception:
                ws = None

        if not ws:
            writer.close()
            return

        await ws.send(init)
        await _bridge_ws(reader, writer, ws)

    except Exception as e:
        log.error("client error: %s", e)
        writer.close()


# ---------------- run ----------------

async def _run(port, dc_opt):
    global _dc_opt
    _dc_opt = dc_opt

    server = await asyncio.start_server(_handle_client, '0.0.0.0', port)

    log.info("Listening on %d", port)

    async with server:
        await server.serve_forever()


def parse_dc_ip_list(lst):
    out = {}
    for e in lst:
        dc, ip = e.split(":")
        out[int(dc)] = ip
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=1080)
    ap.add_argument("--dc-ip", action="append", default=["2:149.154.167.220"])
    args = ap.parse_args()

    logging.basicConfig(level=logging.INFO)

    dc_opt = parse_dc_ip_list(args.dc_ip)

    asyncio.run(_run(args.port, dc_opt))


if __name__ == "__main__":
    main()

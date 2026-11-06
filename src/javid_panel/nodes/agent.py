#!/usr/bin/env python3
"""Standalone Javid Node health agent (stdlib only).

Mutually authenticates heartbeat using HMAC over verified HTTPS. This agent does
NOT create a VPN tunnel or manage firewall rules; it reports machine health only.
"""
from __future__ import annotations

import argparse
import base64
import getpass
import hashlib
import hmac
import json
import os
from pathlib import Path
import platform
import socket
import ssl
import sys
import time
import urllib.error
import urllib.request
from urllib.parse import urlsplit

DEFAULT_CONFIG = '/etc/javid-node/agent.json'


class AgentError(Exception):
    pass


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise AgentError('Redirects are forbidden for node credentials')


def validate_panel_url(url: str) -> str:
    parsed = urlsplit(url)
    if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise AgentError('Panel URL must be HTTPS with no query, userinfo or fragment')
    if parsed.path not in ('', '/'):
        raise AgentError('Panel URL must be the site origin (no path)')
    return url.rstrip('/')


def request_json(panel: str, path: str, payload: dict, timeout: int = 15) -> dict:
    data = json.dumps(payload, sort_keys=True, separators=(',', ':')).encode('utf-8')
    req = urllib.request.Request(panel + path, data=data, method='POST',
                                 headers={'Content-Type': 'application/json', 'Accept': 'application/json'})
    opener = urllib.request.build_opener(NoRedirect(), urllib.request.HTTPSHandler(context=ssl.create_default_context()))
    try:
        with opener.open(req, timeout=timeout) as response:
            if response.status != 200:
                raise AgentError('Unexpected response status')
            body = response.read(4097)
            if len(body) > 4096:
                raise AgentError('Response too large')
            value = json.loads(body)
            if not isinstance(value, dict):
                raise AgentError('Invalid response')
            return value
    except (urllib.error.URLError, ssl.SSLError, ValueError) as exc:
        raise AgentError('Connection or API request failed') from exc


def private_write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    if path.is_symlink():
        raise AgentError('Refusing symlink target')
    temporary = path.with_name('.' + path.name + '.pending')
    if temporary.exists() or temporary.is_symlink():
        raise AgentError('Temporary config path already exists')
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as out:
            json.dump(data, out, sort_keys=True)
            out.flush()
            os.fsync(out.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def load(path: Path) -> dict:
    if path.stat().st_mode & 0o077:
        raise AgentError('Agent config permissions must be 0600')
    return json.loads(path.read_text())


def sign(key_b64: str, node_id: str, counter: int, at: int, payload: dict) -> str:
    secret = base64.urlsafe_b64decode(key_b64 + '=' * (-len(key_b64) % 4))
    message = json.dumps({'node_id': node_id, 'counter': counter, 'timestamp': at,
                          'payload': payload}, sort_keys=True, separators=(',', ':'),
                         ensure_ascii=True).encode('ascii')
    return hmac.new(secret, message, hashlib.sha256).hexdigest()


def health_payload() -> dict:
    load_1m = None
    try:
        load_1m = round(os.getloadavg()[0], 2)
    except (AttributeError, OSError):
        pass
    return {'hostname': socket.gethostname()[:100], 'platform': platform.system(),
            'machine': platform.machine(), 'load_1m': load_1m, 'agent': '0.1.0'}


def enroll(panel: str, enrollment_id: str, path: Path) -> None:
    if path.exists() or path.is_symlink():
        raise AgentError('Node is already enrolled; refusing to replace credentials')
    token = getpass.getpass('Paste one-time enrollment token (hidden): ')
    result = request_json(panel, '/api/v1/nodes/claim',
                          {'enrollment_id': enrollment_id, 'token': token})
    if not result.get('node_id') or not result.get('node_key'):
        raise AgentError('Invalid enrollment response')
    private_write(path, {'panel': panel, 'node_id': result['node_id'],
                         'key': result['node_key'], 'counter': 0})
    print('Node enrolled and private credentials saved; heartbeat service may now be started.')


def send_heartbeat(path: Path) -> None:
    cfg = load(path)
    at = int(time.time())
    counter = int(cfg.get('counter', 0)) + 1
    payload = health_payload()
    signature = sign(cfg['key'], cfg['node_id'], counter, at, payload)
    # Reserve counter BEFORE send; if the server receives an answer but the
    # network drops it, we must never replay this counter on retry.
    cfg['counter'] = counter
    private_write(path, cfg)
    request_json(validate_panel_url(cfg['panel']),
                 '/api/v1/nodes/' + cfg['node_id'] + '/heartbeat',
                 {'counter': counter, 'timestamp': at,
                  'payload': payload, 'signature': signature})
    print('Heartbeat accepted')


def main(argv=None):
    parser = argparse.ArgumentParser(description='Javid Node experimental health agent')
    parser.add_argument('--config', default=DEFAULT_CONFIG)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--enroll', action='store_true')
    group.add_argument('--once', action='store_true')
    group.add_argument('--run', action='store_true')
    parser.add_argument('--panel')
    parser.add_argument('--enrollment-id')
    parser.add_argument('--interval', type=int, default=30)
    args = parser.parse_args(argv)
    try:
        path = Path(args.config)
        if args.enroll:
            if not args.panel or not args.enrollment_id:
                parser.error('--panel and --enrollment-id are required to enroll')
            enroll(validate_panel_url(args.panel), args.enrollment_id, path)
        elif args.once:
            send_heartbeat(path)
        else:
            if not 15 <= args.interval <= 3600:
                raise AgentError('Interval must be 15..3600 seconds')
            while True:
                try:
                    send_heartbeat(path)
                except (AgentError, OSError, KeyError, ValueError) as exc:
                    print('Heartbeat failed; will retry later', file=sys.stderr)
                time.sleep(args.interval)
        return 0
    except (AgentError, OSError, KeyError, ValueError) as exc:
        print('Javid Node: ' + str(exc), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())

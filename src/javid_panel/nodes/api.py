"""Standalone JavaidPanel node-control API (experimental, JSON-only).

Requires HTTPS (reverse proxy or native TLS) when reached over the network.
Never proxy public traffic to a plain HTTP listener bound to 0.0.0.0.
"""
from __future__ import annotations

import argparse
import hmac
import json
import os
import secrets
import ssl
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from .runtime import NodeError, NodeRegistry


class API:
    def __init__(self, registry: NodeRegistry, admin_token: str):
        if not isinstance(admin_token, str) or len(admin_token) < 32:
            raise ValueError('Admin token must be 32+ characters')
        self.registry = registry
        self.admin_token = admin_token
        self._attempts: dict[str, list[float]] = {}
        self._attempts_lock = threading.Lock()

    def authenticated(self, header: str | None) -> bool:
        if not header or not header.startswith('Bearer '):
            return False
        return hmac.compare_digest(header[7:].encode(), self.admin_token.encode())

    def claim_allowed(self, remote_ip: str) -> bool:
        # An in-process limit supplements (does not replace) rate limits in the TLS proxy.
        now = self.registry.clock()
        with self._attempts_lock:
            if len(self._attempts) > 5000:
                self._attempts.clear()  # Upstream per-IP limiting is still required.
            recent = [t for t in self._attempts.get(remote_ip, []) if now-t < 60]
            if len(recent) >= 12:
                self._attempts[remote_ip] = recent
                return False
            recent.append(now)
            self._attempts[remote_ip] = recent
            return True


def make_handler(app: API):
    class Handler(BaseHTTPRequestHandler):
        server_version = 'JavaidPanelNodeAPI'
        sys_version = ''

        def setup(self):
            super().setup()
            self.connection.settimeout(15)

        def log_message(self, fmt, *args):
            # Do not log bearer tokens or request bodies.
            sys.stderr.write('Node API: request handled\n')

        def respond(self, status: int, payload: dict | list):
            body = json.dumps(payload, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
            self.send_response(status)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('X-Frame-Options', 'DENY')
            self.send_header('Referrer-Policy', 'no-referrer')
            self.end_headers()
            self.wfile.write(body)

        def unauthorized(self):
            self.respond(401, {'error': 'Unauthorized'})

        def require_admin(self) -> bool:
            if not app.authenticated(self.headers.get('Authorization')):
                self.unauthorized()
                return False
            return True

        def read_body(self):
            raw = self.headers.get('Content-Length', '')
            if not raw.isascii() or not raw.isdigit() or int(raw) > 4096:
                raise NodeError('JSON request body missing or too large')
            data = self.rfile.read(int(raw))
            if not data:
                raise NodeError('Empty request')
            try:
                obj = json.loads(data.decode('utf-8'))
            except (UnicodeError, json.JSONDecodeError) as exc:
                raise NodeError('Invalid JSON') from exc
            if not isinstance(obj, dict):
                raise NodeError('Expected JSON object')
            return obj

        def serve_admin_dashboard(self, path: str) -> bool:
            """Read-only static UI, restricted to the loopback management listener.

            It is intentionally NOT exposed on a public domain. Administrators
            use SSH -L to reach the loopback API from their own browser.
            API calls still require the separately entered admin bearer token.
            """
            import ipaddress
            import re
            host = self.headers.get('Host', '')
            if (self.server.server_address[0] not in ('127.0.0.1', '::1', 'localhost')
                    or not ipaddress.ip_address(self.client_address[0]).is_loopback
                    or not re.fullmatch(r'(?:127\\.0\\.0\\.1|localhost|\\[::1\\])(?::[0-9]{1,5})?', host)):
                self.respond(403, {'error': 'Admin dashboard is loopback-only'})
                return True
            names = {
                '/admin/nodes': ('dashboard.html', 'text/html; charset=utf-8'),
                '/admin/assets/dashboard.js': ('dashboard.js', 'text/javascript; charset=utf-8'),
                '/admin/assets/dashboard.css': ('dashboard.css', 'text/css; charset=utf-8'),
            }
            if path not in names:
                self.respond(404, {'error': 'Not found'})
                return True
            filename, mime = names[path]
            try:
                data = Path(__file__).with_name(filename).read_bytes()
            except OSError:
                self.respond(503, {'error': 'Dashboard assets not installed'})
                return True
            self.send_response(200)
            self.send_header('Content-Type', mime)
            self.send_header('Content-Length', str(len(data)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('X-Frame-Options', 'DENY')
            self.send_header('Referrer-Policy', 'no-referrer')
            self.send_header('Content-Security-Policy',
                "default-src 'none'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
                "connect-src 'self'; img-src 'self'; form-action 'none'; "
                "base-uri 'none'; frame-ancestors 'none'")
            self.end_headers()
            self.wfile.write(data)
            return True

        def do_GET(self):
            path = urlsplit(self.path).path
            if path == '/admin/nodes' or path.startswith('/admin/'):
                return self.serve_admin_dashboard(path)
            if path == '/healthz':
                return self.respond(200, {'status': 'ok', 'service': 'javid-node-control'})
            if path == '/api/v1/nodes':
                if not self.require_admin(): return
                return self.respond(200, {'nodes': app.registry.list_nodes()})
            return self.respond(404, {'error': 'Not found'})

        def do_POST(self):
            path = urlsplit(self.path).path
            admin_path = path == '/api/v1/nodes/enrollments' or path.endswith('/revoke')
            if admin_path and not self.require_admin(): return
            if path == '/api/v1/nodes/claim' and not app.claim_allowed(self.client_address[0]):
                return self.respond(429, {'error': 'Too many attempts'})
            if not (admin_path or path == '/api/v1/nodes/claim' or path.endswith('/heartbeat')):
                return self.respond(404, {'error': 'Not found'})
            try:
                data = self.read_body()
                if path == '/api/v1/nodes/enrollments':
                    invite = app.registry.create(data.get('name'), data.get('host'), data.get('ttl', 600))
                    return self.respond(201, {'node_id': invite.node_id,
                        'enrollment_id': invite.enrollment_id,
                        'token': invite.token, 'expires_at': invite.expires_at})
                if path == '/api/v1/nodes/claim':
                    credential = app.registry.claim(data.get('enrollment_id'), data.get('token'))
                    return self.respond(200, {'node_id': credential.node_id, 'node_key': credential.key})
                parts = path.strip('/').split('/')
                if len(parts) != 5 or parts[:3] != ['api', 'v1', 'nodes']:
                    return self.respond(404, {'error': 'Not found'})
                node_id, action = parts[3], parts[4]
                if action == 'heartbeat':
                    app.registry.heartbeat(node_id, data.get('counter'), data.get('timestamp'),
                                           data.get('payload'), data.get('signature'))
                    return self.respond(200, {'accepted': True})
                if action == 'revoke':
                    if not self.require_admin(): return
                    ok = app.registry.revoke(node_id)
                    return self.respond(200 if ok else 404, {'revoked': ok})
                return self.respond(404, {'error': 'Not found'})
            except NodeError as exc:
                # Avoid an oracle for enrollment secrets.
                status = 403 if path.endswith('/claim') or path.endswith('/heartbeat') else 400
                return self.respond(status, {'error': 'Claim or heartbeat rejected' if status == 403 else str(exc)})
            except (KeyError, TypeError, ValueError) as exc:
                return self.respond(400, {'error': 'Invalid request fields'})
            except Exception:
                # No stack traces, secrets, or database content in HTTP responses.
                return self.respond(500, {'error': 'Internal failure'})
    return Handler


def load_config(path: str) -> dict:
    st = os.stat(path)
    if st.st_mode & 0o077:
        raise ValueError('Config permissions must be 0600')
    result = json.loads(Path(path).read_text(encoding='utf-8'))
    if len(result.get('admin_token','')) < 32 or len(result.get('master_key','')) < 64:
        raise ValueError('Invalid control-plane credentials')
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description='JavaidPanel experimental node API')
    sub = parser.add_subparsers(dest='command', required=True)
    init = sub.add_parser('init', help='Create private credentials and SQLite database')
    init.add_argument('--config', required=True)
    serve = sub.add_parser('serve', help='Run API on loopback HTTP or explicitly enabled HTTPS')
    serve.add_argument('--config', required=True)
    serve.add_argument('--host', default='127.0.0.1')
    serve.add_argument('--port', type=int, default=9443)
    serve.add_argument('--cert')
    serve.add_argument('--key')
    args = parser.parse_args(argv)
    if args.command == 'init':
        config = Path(args.config).resolve()
        config.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        if config.parent.stat().st_mode & 0o077:
            raise SystemExit('Config directory must have mode 0700')
        if config.exists():
            raise SystemExit('Config already exists; refusing to overwrite it')
        database = str(config.parent / 'nodes.sqlite3')
        payload = {'database': database, 'admin_token': secrets.token_urlsafe(40),
                   'master_key': secrets.token_hex(48)}
        flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
        fd = os.open(config, flags, 0o600)
        with os.fdopen(fd, 'w', encoding='utf-8') as out:
            json.dump(payload, out)
        NodeRegistry(database, bytes.fromhex(payload['master_key']))
        print('Created private config and database. Admin token is stored in the config file.')
        return 0
    conf = load_config(args.config)
    registry = NodeRegistry(conf['database'], bytes.fromhex(conf['master_key']))
    if not 1 <= args.port <= 65535:
        raise SystemExit('Invalid TCP port')
    if (args.cert is None) != (args.key is None):
        raise SystemExit('Both --cert and --key are required for TLS')
    if args.host not in ('127.0.0.1', 'localhost') and args.cert is None:
        raise SystemExit('Non-loopback bind requires TLS (--cert and --key)')
    server = ThreadingHTTPServer((args.host, args.port), make_handler(API(registry, conf['admin_token'])))
    if args.cert:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        context.load_cert_chain(args.cert, args.key)
        server.socket = context.wrap_socket(server.socket, server_side=True)
    print('Javid Node control API listening; use HTTPS for all remote access.', flush=True)
    server.serve_forever()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

#!/usr/bin/env python3
"""Local-only JavaidPanel node management CLI.

Reads private admin token from a 0600 file; token is not part of shell args.
"""
import argparse
import json
import os
import re
from pathlib import Path
import sys
import urllib.error
import urllib.request
from urllib.parse import urlsplit


def admin_call(url, token, method, endpoint, payload=None):
    parsed = urlsplit(url)
    if parsed.scheme != 'http' or parsed.hostname not in ('127.0.0.1','localhost'):
        raise ValueError('Admin CLI must use loopback HTTP only (local machine)')
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url.rstrip('/')+endpoint, data=data, method=method,
        headers={'Authorization':'Bearer '+token,'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=10) as reply:
        return json.loads(reply.read(100000))


def main(argv=None):
    parser = argparse.ArgumentParser(description='JavaidPanel local node management CLI')
    parser.add_argument('--config',required=True,help='Local 0600 control-plane JSON config')
    parser.add_argument('--api',default='http://127.0.0.1:9443')
    sub = parser.add_subparsers(dest='action',required=True)
    create=sub.add_parser('create',help='Generate one-time enrollment + install command')
    create.add_argument('--name',required=True)
    create.add_argument('--host',required=True)
    create.add_argument('--panel',required=True,help='Public HTTPS panel origin')
    create.add_argument('--ttl',type=int,default=600)
    sub.add_parser('list',help='List nodes and verified heartbeat status')
    revoke=sub.add_parser('revoke',help='Revoke node credentials')
    revoke.add_argument('node_id')
    args=parser.parse_args(argv)
    st=os.stat(args.config)
    if st.st_mode & 0o077:
        raise SystemExit('Refusing config with insecure permissions; expected 0600')
    cfg=json.loads(Path(args.config).read_text())
    token=cfg['admin_token']
    try:
        if args.action=='create':
            # Validate public origin without adding secrets to command or URL.
            url=urlsplit(args.panel)
            if (url.scheme!='https' or not url.hostname or url.username or url.password or url.query or url.fragment
                    or url.path not in ('','/') or not re.fullmatch(r'https://[A-Za-z0-9.-]+(?::[0-9]{1,5})?/?', args.panel)):
                raise ValueError('Public panel URL must be HTTPS origin only')
            item=admin_call(args.api,token,'POST','/api/v1/nodes/enrollments',
                           {'name':args.name,'host':args.host,'ttl':args.ttl})
            cmd=('curl -fsSL https://raw.githubusercontent.com/wisealii/JavaidPanel/main/node-agent-install.sh '
                 '| sudo bash -s -- --panel '+args.panel.rstrip('/')+' --enrollment-id '+item['enrollment_id'])
            print('Node ID: '+item['node_id'])
            print('Enrollment expires (Unix): '+str(item['expires_at']))
            print('Run on the node VPS (review script first):\n'+cmd)
            print('\nPaste this ONE-TIME token at the password prompt; it is never part of the command:')
            print(item['token'])
            print('\nProtect this terminal output; token is not recoverable from storage.')
        elif args.action=='list':
            nodes=admin_call(args.api,token,'GET','/api/v1/nodes')['nodes']
            for node in nodes:
                print('{state:<8} {name:<22} {host:<30} {id}'.format(**node))
        else:
            result=admin_call(args.api,token,'POST','/api/v1/nodes/'+args.node_id+'/revoke',{})
            print('Revoked' if result.get('revoked') else 'Not found')
        return 0
    except (urllib.error.HTTPError, urllib.error.URLError, KeyError, ValueError) as exc:
        print('Javidctl: operation failed; check API, permissions, node ID and input.',file=sys.stderr)
        return 2


if __name__=='__main__':raise SystemExit(main())

"""Executable offline API and agent integration tests, no external services."""
from __future__ import annotations
import base64
import hashlib
import hmac
import http.client
import json
import os
from pathlib import Path
import socket
import stat
import sys
import tempfile
import threading
import time
import unittest
from unittest import mock

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from javid_panel.nodes.runtime import NodeRegistry, NodeError, canonical_message, validate_host
from javid_panel.nodes.api import API, make_handler, ThreadingHTTPServer, load_config, main
from javid_panel.nodes.agent import sign, validate_panel_url, private_write, load

class NodeAPIIntegration(unittest.TestCase):
    def setUp(self):
        self.td=tempfile.TemporaryDirectory()
        self.addCleanup(self.td.cleanup)
        basedir=Path(self.td.name)/'private'
        basedir.mkdir(mode=0o700)
        self.clock=[1800000000]
        self.registry=NodeRegistry(basedir/'node.db',b'M'*48,clock=lambda:self.clock[0])
        self.admin='A'*44
        self.api=API(self.registry,self.admin)
        self.server=ThreadingHTTPServer(('127.0.0.1',0), make_handler(self.api))
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True)
        self.thread.start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)

    def req(self, path, obj=None, token=None, method=None):
        conn=http.client.HTTPConnection('127.0.0.1',self.server.server_address[1],timeout=5)
        data=json.dumps(obj).encode() if obj is not None else None
        headers={'Content-Type':'application/json'}
        if token: headers['Authorization']='Bearer '+token
        conn.request(method or ('POST' if data is not None else 'GET'), path, body=data, headers=headers)
        response=conn.getresponse()
        body=response.read()
        status=response.status
        cache=response.getheader('Cache-Control')
        conn.close()
        return status,json.loads(body),cache

    def issue(self):
        status,res,_=self.req('/api/v1/nodes/enrollments',{'name':'DE-1','host':'203.0.113.10'},self.admin)
        self.assertEqual(status,201,res)
        return res

    def test_health_and_admin_auth(self):
        self.assertEqual(self.req('/healthz')[0],200)
        self.assertEqual(self.req('/api/v1/nodes')[0],401)
        self.assertEqual(self.req('/api/v1/nodes',token='wrong')[0],401)
        self.assertEqual(self.req('/api/v1/nodes',token=self.admin)[0],200)

    def test_end_to_end_claim_and_heartbeat(self):
        inv=self.issue()
        self.assertEqual(self.req('/api/v1/nodes/claim',{'enrollment_id':inv['enrollment_id'],'token':'X'*44})[0],403)
        status,creds,cache=self.req('/api/v1/nodes/claim',{'enrollment_id':inv['enrollment_id'],'token':inv['token']})
        self.assertEqual(status,200,creds)
        self.assertEqual(cache,'no-store')
        self.assertEqual(self.req('/api/v1/nodes/claim',{'enrollment_id':inv['enrollment_id'],'token':inv['token']})[0],403)
        node_id=creds['node_id']
        nodes=self.req('/api/v1/nodes',token=self.admin)[1]['nodes']
        self.assertEqual(nodes[0]['state'],'claimed')
        payload={'agent':'0.1.0','cpu':1.2}
        counter=1
        stamp=self.clock[0]
        signature=sign(creds['node_key'],node_id,counter,stamp,payload)
        url=f'/api/v1/nodes/{node_id}/heartbeat'
        msg={'counter':counter,'timestamp':stamp,'payload':payload,'signature':signature}
        self.assertEqual(self.req(url,msg)[0],200)
        self.assertEqual(self.req(url,msg)[0],403,'Replay must be rejected')
        self.assertEqual(self.req(url,{**msg,'counter':2})[0],403,'Tamper without signing must fail')
        self.assertEqual(self.req('/api/v1/nodes',token=self.admin)[1]['nodes'][0]['state'],'online')
        self.clock[0]+=100
        self.assertEqual(self.req('/api/v1/nodes',token=self.admin)[1]['nodes'][0]['state'],'offline')
        self.clock[0]-=100
        self.assertEqual(self.req(f'/api/v1/nodes/{node_id}/revoke',{},self.admin)[0],200)
        self.assertEqual(self.req(url,{**msg,'counter':2,'signature':sign(creds['node_key'],node_id,2,stamp,payload)})[0],403)
        self.assertEqual(self.req('/api/v1/nodes',token=self.admin)[1]['nodes'][0]['state'],'revoked')

    def test_expiry_and_single_use(self):
        inv=self.issue()
        self.clock[0]+=601
        self.assertEqual(self.req('/api/v1/nodes/claim',{'enrollment_id':inv['enrollment_id'],'token':inv['token']})[0],403)

    def test_reject_non_json_body(self):
        self.assertEqual(self.req('/api/v1/nodes/enrollments',{},self.admin)[0],400)
        self.assertEqual(self.req('/api/v1/nodes/enrollments',{'name':'bad','host':'127.0.0.999'},self.admin)[0],400)

    def test_limit_claim_attempts(self):
        for i in range(12):
            self.req('/api/v1/nodes/claim',{'enrollment_id':'x','token':'y'})
        self.assertEqual(self.req('/api/v1/nodes/claim',{'enrollment_id':'x','token':'y'})[0],429)

    def test_tls_required_for_non_loopback(self):
        base=Path(self.td.name)/'private'
        path=base/'config.json'
        path.write_text(json.dumps({'database':str(base/'nodes.db'),'admin_token':self.admin,'master_key':(b'M'*48).hex()}))
        path.chmod(0o600)
        with self.assertRaises(SystemExit):
            main(['serve','--config',str(path),'--host','0.0.0.0','--port','0'])
        with self.assertRaises(SystemExit):
            main(['serve','--config',str(path),'--host','0.0.0.0','--port','9443'])

    def test_agent_signatures_and_no_redirect(self):
        self.assertEqual(validate_panel_url('https://panel.example.org'), 'https://panel.example.org')
        for value in ['http://panel.example.org','https://user:pass@example.org',
                      'https://panel.example.org/secret','https://panel.example.org/?token=x']:
            with self.assertRaises(Exception):validate_panel_url(value)
        p=Path(self.td.name)/'private'/'agent.json'
        private_write(p,{'key':'secret','counter':0})
        self.assertEqual(load(p)['counter'],0)
        self.assertEqual(p.stat().st_mode & 0o777,0o600)
        private_write(p,{'key':'secret','counter':1})
        self.assertEqual(load(p)['counter'],1)

if __name__=='__main__':unittest.main()

"""Local-only dashboard integration tests. No external network or root access."""
from __future__ import annotations
import http.client
import pathlib
import sys
import tempfile
import threading
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from javid_panel.nodes.api import API, make_handler, ThreadingHTTPServer
from javid_panel.nodes.runtime import NodeRegistry

class DashboardTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        parent=pathlib.Path(self.temp.name)/'protected'
        parent.mkdir(mode=0o700)
        self.admin='Z'*48
        self.store=NodeRegistry(parent/'nodes.db', b'K'*48)
        self.server=ThreadingHTTPServer(('127.0.0.1',0),make_handler(API(self.store,self.admin)))
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True)
        self.thread.start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)

    def fetch(self,route,host=None):
        conn=http.client.HTTPConnection('127.0.0.1',self.server.server_address[1],timeout=4)
        headers={'Host':host} if host else {}
        conn.request('GET',route,headers=headers)
        response=conn.getresponse()
        body=response.read()
        fields=dict(response.getheaders())
        result=(response.status,body,fields)
        conn.close()
        return result

    def test_assets_and_csp(self):
        for route,mime in [
            ('/admin/nodes','text/html'),
            ('/admin/assets/dashboard.js','text/javascript'),
            ('/admin/assets/dashboard.css','text/css'),
        ]:
            with self.subTest(route=route):
                status,data,headers=self.fetch(route)
                self.assertEqual(status,200)
                self.assertIn(mime,headers.get('Content-Type',''))
                self.assertEqual(headers.get('Cache-Control'),'no-store')
                self.assertIn("default-src 'none'",headers.get('Content-Security-Policy',''))
                self.assertGreater(len(data),100)
                self.assertNotIn(self.admin.encode(),data)

    def test_dashboard_has_real_api_binding_not_demo(self):
        _,page,_=self.fetch('/admin/nodes')
        _,js,_=self.fetch('/admin/assets/dashboard.js')
        self.assertIn(b'/admin/assets/dashboard.js',page)
        self.assertIn(b'/api/v1/nodes/enrollments',js)
        self.assertIn(b'/api/v1/nodes',js)
        self.assertIn(b'Bearer ',js)
        self.assertIn(b'textContent',js)
        self.assertNotIn(b'localStorage',js)
        self.assertNotIn(b'innerHTML',js)

    def test_public_host_refused(self):
        status,_,_=self.fetch('/admin/nodes',host='panel.example.org')
        self.assertEqual(status,403)
        status,_,_=self.fetch('/admin/assets/dashboard.js',host='panel.example.org')
        self.assertEqual(status,403)

    def test_path_traversal_refused(self):
        status,_,_=self.fetch('/admin/does-not-exist')
        self.assertEqual(status,404)

    def test_admin_data_is_still_protected(self):
        status,_,_=self.fetch('/api/v1/nodes')
        self.assertEqual(status,401)

    def test_installer_copies_dashboard_assets(self):
        installer=(ROOT/'tools/install-control-plane.sh').read_text()
        for name in ['dashboard.html','dashboard.css','dashboard.js']:
            self.assertIn('src/javid_panel/nodes/'+name,installer)

if __name__=='__main__':
    unittest.main()

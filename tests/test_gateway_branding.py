"""Regression tests for the embedded presentation layer; no VPS mutations."""
import ast
import hashlib
import pathlib
import re
import subprocess
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


def embedded(name):
    source = (ROOT / 'installer/core.sh').read_text()
    match = re.search(r'cat > "\$STAGE/' + re.escape(name) + r'" <<\'([^\']+)\'\n(.*?)\n\1', source, re.S)
    return match.group(2)


class GatewayBrandingTests(unittest.TestCase):
    def test_installed_health_check_accepts_javaid_login_and_rejects_missing_adapter(self):
        module = ast.parse(embedded('manage.py'))
        check = next(n for n in module.body if isinstance(n, ast.FunctionDef) and n.name == 'check')
        assertion = next(n for n in ast.walk(check) if isinstance(n, ast.Assert))
        compiled = compile(ast.Module(body=[assertion], type_ignores=[]), '<health assertion>', 'exec')
        page = '<html><title>JavaidPanel</title><script src="/existing/_alireza/brand.js?v=javaid-1"></script></html>'
        exec(compiled, {'text': page})
        with self.assertRaises(AssertionError):
            exec(compiled, {'text': '<title>JavaidPanel</title>'})

    def test_adapter_preserves_user_and_legal_text(self):
        # Execute the real DOM visitor without polling, network or a live panel.
        prefix = embedded('brand.js').split('  function identity() {', 1)[0]
        program = '''const assert = require('node:assert/strict');
global.window = {ALIREZA: {base: '/existing/'}};
global.Node = {TEXT_NODE: 3, ELEMENT_NODE: 1};
const visit = ''' + prefix + ''' return visit; })();
function text(value, protectedArea = false) {
  return {nodeType: 3, nodeValue: value,
    parentElement: {closest: () => protectedArea ? {} : null}};
}
let heading = text('[alirezapanel]'); visit(heading);
assert.equal(heading.nodeValue, '[JavaidPanel]');
let legal = text('VPN-UI / AlirezaPanel', true); visit(legal);
assert.equal(legal.nodeValue, 'VPN-UI / AlirezaPanel');
let user = text('alirezapanel', true); visit(user);
assert.equal(user.nodeValue, 'alirezapanel');
let partial = text('customer-alirezapanel'); visit(partial);
assert.equal(partial.nodeValue, 'customer-alirezapanel');
'''
        proc = subprocess.run(['node', '-e', program], capture_output=True, text=True, timeout=10)
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_gateway_branding_preserves_configuration_and_native_dns(self):
        import html
        import json
        module = ast.parse(embedded('gateway.py'))
        gateway = next(n for n in module.body if isinstance(n, ast.ClassDef) and n.name == 'Gateway')
        method = next(n for n in gateway.body if isinstance(n, ast.FunctionDef) and n.name == 'brand_html')
        namespace = {'re': re, 'html': html, 'json': json}
        exec(compile(ast.Module(body=[method], type_ignores=[]), '<brand_html>', 'exec'), namespace)
        class Stub:
            def fix_restart_html(self, value):
                return value
        original = '<html><head><title>VPN-UI</title></head><body><input value="alirezapanel"><script>const key="alirezapanel";</script></body></html>'
        branded = namespace['brand_html'](Stub(), original, '/existing/')
        self.assertIn('<title>JavaidPanel</title>', branded)
        self.assertIn('input value="alirezapanel"', branded)
        self.assertIn('const key="alirezapanel";', branded)
        self.assertIn('/existing/_alireza/brand.js?v=javaid-1', branded)
        self.assertEqual(namespace['brand_html'](Stub(), original, '/existing/', True), original)

    def test_existing_brand_adapter_and_nodes_use_javaid_identity(self):
        adapter = embedded('brand.js')
        self.assertIn("const brand = 'JavaidPanel';", adapter)
        self.assertIn('footer', adapter)
        self.assertIn('.ant-table', adapter)
        self.assertIn("window.ALIREZA", adapter)
        self.assertIn('X-Alirezapanel-Request', embedded('nodes.html'))
        self.assertIn('<title>JavaidPanel · Nodes</title>', embedded('nodes.html'))
        self.assertIn('JavaidPanel', embedded('logo.svg'))
        self.assertIn('#f04452', embedded('theme.css'))
        self.assertIn("'profile': 'alirezapanel', 'label': 'JavaidPanel · '", embedded('features.py'))

    def test_bootstrap_and_ci_pin_exact_core(self):
        digest = hashlib.sha256((ROOT / 'installer/core.sh').read_bytes()).hexdigest()
        self.assertIn('CORE_SHA256="' + digest + '"', (ROOT / 'install.sh').read_text())
        self.assertIn(digest, (ROOT / '.github/workflows/verify.yml').read_text())


if __name__ == '__main__':
    unittest.main()

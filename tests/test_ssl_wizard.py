"""Regression checks for the non-destructive SSL wizard validation paths."""
import pathlib
import subprocess
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
SSL=ROOT/'tools'/'ssl-wizard.sh'

class SSLWizardTests(unittest.TestCase):
    def test_shell_syntax(self):
        for p in [SSL,ROOT/'tools'/'install-control-plane.sh',ROOT/'node-agent-install.sh']:
            r=subprocess.run(['bash','-n',str(p)],capture_output=True,text=True)
            self.assertEqual(r.returncode,0,r.stderr)

    def test_help(self):
        r=subprocess.run(['bash',str(SSL),'--help'],capture_output=True,text=True)
        self.assertEqual(r.returncode,0)
        self.assertIn("Let's Encrypt",r.stdout)

    def test_invalid_domain_refused(self):
        for value in ['-evil.example.org','a..example.org','example.com;id','localhost','a/b.com','127.0.0.1']:
            with self.subTest(value=value):
                r=subprocess.run(['bash',str(SSL),'--check',value],capture_output=True,text=True,timeout=10)
                self.assertNotEqual(r.returncode,0)
                self.assertIn('Invalid domain',r.stderr)

    def test_invalid_email_refused_before_certbot(self):
        r=subprocess.run(['bash',str(SSL),'--issue','panel.example.org','bad'],capture_output=True,text=True,timeout=10)
        self.assertNotEqual(r.returncode,0)
        self.assertIn('Valid email required',r.stderr)

    def test_control_plane_check_needs_source(self):
        r=subprocess.run(['bash',str(ROOT/'tools'/'install-control-plane.sh'),'--check'],cwd=ROOT,
                         capture_output=True,text=True,timeout=10)
        self.assertEqual(r.returncode,0,r.stderr)

if __name__=='__main__': unittest.main()

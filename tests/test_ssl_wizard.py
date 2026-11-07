"""Regression checks for the non-destructive SSL wizard validation paths."""
import pathlib
import subprocess
import tempfile
import os
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

    def _check_with_mocked_dns(self, ipv4="", ipv6="", occupied=False):
        """Replace only DNS and socket-inspection commands; never call ACME."""
        with tempfile.TemporaryDirectory() as root:
            bin_dir = pathlib.Path(root)
            getent = bin_dir / "getent"
            getent.write_text(
                "#!/bin/sh\n"
                "case \"$1\" in\n"
                "  ahostsv4) if [ -n \"$MOCK_A\" ]; then printf '%s STREAM panel.example.org\\n' \"$MOCK_A\"; fi;;\n"
                "  ahostsv6) if [ -n \"$MOCK_AAAA\" ]; then printf '%s STREAM panel.example.org\\n' \"$MOCK_AAAA\"; fi;;\n"
                "esac\n"
            )
            getent.chmod(0o755)
            ss = bin_dir / "ss"
            ss.write_text("#!/bin/sh\n[ \"$MOCK_BUSY\" = yes ] && echo 'LISTEN 0 128 *:80' || true\n")
            ss.chmod(0o755)
            env = os.environ.copy()
            env["PATH"] = str(bin_dir) + os.pathsep + env["PATH"]
            env["MOCK_A"] = ipv4
            env["MOCK_AAAA"] = ipv6
            env["MOCK_BUSY"] = "yes" if occupied else "no"
            return subprocess.run(
                ["bash", str(SSL), "--check", "panel.example.org"],
                env=env, capture_output=True, text=True, timeout=10,
            )

    def test_missing_dns_is_blocking_not_just_warning(self):
        result = self._check_with_mocked_dns()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("no A or AAAA address", result.stderr)

    def test_ipv4_dns_is_accepted(self):
        result = self._check_with_mocked_dns(ipv4="203.0.113.12")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Resolved IPv4", result.stdout)

    def test_ipv6_only_dns_is_accepted(self):
        result = self._check_with_mocked_dns(ipv6="2001:db8::12")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Resolved IPv6", result.stdout)

    def test_occupied_port_blocks_certificate_preflight(self):
        result = self._check_with_mocked_dns(ipv4="203.0.113.12", occupied=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("already has a listener", result.stderr)

    def test_control_plane_check_needs_source(self):
        r=subprocess.run(['bash',str(ROOT/'tools'/'install-control-plane.sh'),'--check'],cwd=ROOT,
                         capture_output=True,text=True,timeout=10)
        self.assertEqual(r.returncode,0,r.stderr)

if __name__=='__main__': unittest.main()

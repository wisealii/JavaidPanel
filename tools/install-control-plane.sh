#!/usr/bin/env bash
# Install standalone JavaidPanel node-control API on the LOCAL control VPS.
# No TLS/web-server configuration is changed. A verified HTTPS reverse proxy
# must be configured by the operator before exposing the enrollment API.
set -Eeuo pipefail
umask 077
usage(){
cat <<'HELP'
JavaidPanel node-control API setup (experimental)

  sudo bash tools/install-control-plane.sh --install
  bash tools/install-control-plane.sh --check

Run from the root of a checked-out JavaidPanel repository.
API binds ONLY to http://127.0.0.1:9443 (admin token never in public URL).
Use a dedicated HTTPS reverse proxy to expose /api/v1/nodes/* securely.
This does not install a VPN engine or alter existing panel services.
HELP
}
fail(){ echo "JavaidPanel node API ERROR: $*" >&2; exit 2; }
mode="${1:---help}"
if [[ "$mode" == --help || "$mode" == -h ]]; then usage; exit 0; fi
if [[ "$mode" == --check ]]; then
  command -v python3 >/dev/null || fail 'Python 3 required'
  python3 -c 'import sys; assert sys.version_info >= (3,10)' || fail 'Python >= 3.10 required'
  [[ -r src/javid_panel/nodes/runtime.py && -r src/javid_panel/nodes/api.py ]] || fail 'Run from repository root'
  bash -n tools/ssl-wizard.sh
  echo 'Source and Python prerequisites: OK (not a live server test)'
  exit 0
fi
[[ "$mode" == --install && $# -eq 1 ]] || fail 'Use --install or --check'
(( EUID==0 )) || fail 'Run with sudo/root'
[[ -r src/javid_panel/nodes/runtime.py && -r src/javid_panel/nodes/api.py ]] || fail 'Run from cloned repository root'
[[ -d /run/systemd/system ]] || fail 'A running systemd host is required'
python3 -c 'import sys; assert sys.version_info >= (3,10)' || fail 'Python >= 3.10 required'
for cmd in useradd runuser systemctl install; do command -v "$cmd" >/dev/null || fail "$cmd required"; done
[[ ! -e /etc/systemd/system/javid-node-control.service && ! -e /etc/javid-panel/node-control.json ]] || fail 'Existing API detected; refusing to overwrite credentials'
if ! id -u javidpanel >/dev/null 2>&1; then
  useradd --system --home-dir /var/lib/javid-panel --shell /usr/sbin/nologin --create-home javidpanel
fi
install -d -m 0700 -o javidpanel -g javidpanel /etc/javid-panel
install -d -m 0755 /opt/javid-control/src/javid_panel/nodes
install -m 0644 src/javid_panel/__init__.py /opt/javid-control/src/javid_panel/__init__.py
install -m 0644 src/javid_panel/nodes/__init__.py /opt/javid-control/src/javid_panel/nodes/__init__.py
install -m 0644 src/javid_panel/nodes/runtime.py /opt/javid-control/src/javid_panel/nodes/runtime.py
install -m 0644 src/javid_panel/nodes/api.py /opt/javid-control/src/javid_panel/nodes/api.py
runuser -u javidpanel -- env PYTHONPATH=/opt/javid-control/src \
  /usr/bin/python3 -m javid_panel.nodes.api init --config /etc/javid-panel/node-control.json
cat > /etc/systemd/system/javid-node-control.service <<'UNIT'
[Unit]
Description=JavaidPanel node control API (loopback only)
After=network-online.target
Wants=network-online.target
[Service]
Type=simple
User=javidpanel
Group=javidpanel
Environment=PYTHONPATH=/opt/javid-control/src
ExecStart=/usr/bin/python3 -m javid_panel.nodes.api serve --config /etc/javid-panel/node-control.json --host 127.0.0.1 --port 9443
Restart=on-failure
RestartSec=3
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/etc/javid-panel
CapabilityBoundingSet=
RestrictAddressFamilies=AF_UNIX AF_INET AF_INET6
[Install]
WantedBy=multi-user.target
UNIT
systemctl daemon-reload
systemctl enable --now javid-node-control.service
printf '\nJavid Node control-plane installed on LOOPBACK port 9443.\n'
printf 'Run: curl http://127.0.0.1:9443/healthz\n'
printf 'NEXT: configure verified HTTPS reverse proxy for your domain BEFORE enrolling nodes.\n'
printf 'Create a token and install command with: python3 tools/javidctl.py --config /etc/javid-panel/node-control.json create --name NODE --host NODE_IP --panel https://YOUR_DOMAIN\n'
printf 'The CLI requires root (or protected config access), never publish its output.\n'

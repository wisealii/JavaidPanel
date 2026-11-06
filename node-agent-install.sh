#!/usr/bin/env bash
# Javid Node experimental health agent installer.
# Does not deploy VPN engines, tunnels, or mTLS certificates.
set -Eeuo pipefail
umask 077
AGENT_SHA256='4759d9d1032db3788df9566f1f2bffd29972c84474d97af555e4fbc7852b3266'
AGENT_URL='https://raw.githubusercontent.com/wisealii/JavaidPanel/main/src/javid_panel/nodes/agent.py'
usage(){
cat <<'HELP'
Javid Node experimental agent installer

  curl -fsSL https://raw.githubusercontent.com/wisealii/JavaidPanel/main/node-agent-install.sh |
    sudo bash -s -- --panel https://panel.example.org --enrollment-id YOUR_UUID

  bash node-agent-install.sh --check     # read-only
  bash node-agent-install.sh --help

IMPORTANT: Obtain a one-time token from the administrator API before install.
The installer prompts for this token through the terminal; do NOT embed it in
shell history, URL query parameters, command-line arguments or screenshots.
Requires verified HTTPS, Python 3.10+, systemd and root on a fresh node VPS.
The current agent reports health only; no VPN tunnel is installed.
HELP
}
fail(){ printf 'Javid Node ERROR: %s\n' "$*" >&2; exit 2; }
check(){
  echo 'Javid Node system check (no changes)'
  uname -m
  if [[ -r /etc/os-release ]]; then (. /etc/os-release; printf '%s %s\n' "${ID:-unknown}" "${VERSION_ID:-unknown}"); fi
  for command in python3 curl systemctl useradd runuser sha256sum; do
    if command -v "$command" >/dev/null; then echo "$command OK"; else echo "$command MISSING"; fi
  done
  echo 'This command does not check real VPN tunnels.'
}
if [[ "${1:-}" == --check ]]; then [[ $# -eq 1 ]] || fail 'Extra arguments'; check; exit 0; fi
if [[ "${1:-}" == --help || "${1:-}" == -h ]]; then usage; exit 0; fi
panel=''; enrollment_id=''
while [[ $# -gt 0 ]]; do
  case "$1" in
    --panel) [[ $# -ge 2 ]] || fail '--panel needs URL'; panel="$2"; shift 2;;
    --enrollment-id) [[ $# -ge 2 ]] || fail '--enrollment-id needs UUID'; enrollment_id="$2"; shift 2;;
    *) usage; fail "Unknown option: $1";;
  esac
done
[[ -n "$panel" && -n "$enrollment_id" ]] || { usage; fail 'Panel URL and enrollment ID are required'; }
[[ "$panel" =~ ^https://[a-zA-Z0-9.:-]+/?$ ]] || fail 'Panel URL must be a HTTPS origin without paths'
[[ "$enrollment_id" =~ ^[a-fA-F0-9-]{36}$ ]] || fail 'Enrollment ID format invalid'
(( EUID == 0 )) || fail 'Use sudo on the node VPS'
command -v python3 >/dev/null || fail 'Python 3 required'
python3 -c 'import sys; assert sys.version_info >= (3, 10)' || fail 'Python >= 3.10 required'
for command in curl sha256sum systemctl useradd runuser; do command -v "$command" >/dev/null || fail "$command required"; done
[[ -d /run/systemd/system ]] || fail 'Running systemd required'
[[ ! -e /etc/javid-node/agent.json && ! -e /etc/systemd/system/javid-node-agent.service ]] || fail 'Existing Javid Node installation detected; refusing overwrite'
( : </dev/tty ) 2>/dev/null || fail 'A real interactive terminal is required for hidden token prompt'
[[ ! -e /opt/javid-node/agent.py ]] || fail 'Existing agent detected; refusing overwrite'
work="$(mktemp -d)"
cleanup(){ rm -rf -- "$work"; }
trap cleanup EXIT
curl -fLSs --retry 3 --connect-timeout 15 --max-time 120 "$AGENT_URL" -o "$work/agent.py" || fail 'Unable to download node agent'
printf '%s  %s\n' "$AGENT_SHA256" "$work/agent.py" | sha256sum -c --status || fail 'Agent SHA mismatch; aborted'
python3 -m py_compile "$work/agent.py" || fail 'Invalid downloaded Python code'
if ! id -u javidnode >/dev/null 2>&1; then
  useradd --system --home-dir /var/lib/javid-node --shell /usr/sbin/nologin --create-home javidnode
fi
install -d -m 0755 /opt/javid-node
install -d -m 0700 -o javidnode -g javidnode /etc/javid-node
install -m 0644 "$work/agent.py" /opt/javid-node/agent.py
printf '\nJavid Node: enter your one-time token at the hidden prompt.\n'
if ! runuser -u javidnode -- python3 /opt/javid-node/agent.py \
  --enroll --panel "$panel" --enrollment-id "$enrollment_id" --config /etc/javid-node/agent.json; then
  echo 'Enrollment failed. No systemd unit has been enabled; inspect TLS and token settings.' >&2
  exit 2
fi
cat > /etc/systemd/system/javid-node-agent.service <<'UNIT'
[Unit]
Description=Javid Node authenticated health agent
After=network-online.target
Wants=network-online.target
[Service]
Type=simple
User=javidnode
Group=javidnode
ExecStart=/usr/bin/python3 /opt/javid-node/agent.py --run --interval 30
Restart=always
RestartSec=10
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/etc/javid-node
CapabilityBoundingSet=
AmbientCapabilities=
RestrictAddressFamilies=AF_UNIX AF_INET AF_INET6
[Install]
WantedBy=multi-user.target
UNIT
systemctl daemon-reload
systemctl enable --now javid-node-agent.service
printf '\nJavid Node agent registered. Check state with: systemctl status javid-node-agent.service\n'
printf 'Agent reports health only. Check node status in the API; no VPN tunnel is installed.\n'

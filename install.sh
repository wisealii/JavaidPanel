#!/usr/bin/env bash
# JavaidPanel installation entrypoint (guarded bootstrap, 1.1.102-dev)
# IMPORTANT: Not a full VPN installation until backend and node runtime are shipped.
set -Eeuo pipefail
VERSION="1.1.102-dev"
red=$'\e[31m'; green=$'\e[32m'; yellow=$'\e[33m'; reset=$'\e[0m'
say(){ printf '%s\n' "$*"; }
error(){ printf '%sERROR: %s%s\n' "$red" "$*" "$reset" >&2; }
info(){ printf '%s%s%s\n' "$green" "$*" "$reset"; }
help_text(){
cat <<'HELP'
JavaidPanel guarded installer v1.1.102-dev

Usage:
  sudo bash install.sh --doctor        Inspect system without modifying it
  sudo bash install.sh --ssl DOMAIN    Request a Let's Encrypt certificate for a domain
  sudo bash install.sh --install       Check readiness for full installation
  bash install.sh --help               Show this help

STATUS: No working panel backend or node daemon is included in the current GitHub
repository. The old installer launched 'sleep infinity' instead of a real panel.
A full installation is intentionally blocked until a tested runtime is available.
HELP
}
require_root(){ if (( EUID != 0 )); then error 'Run this action with sudo/root.'; exit 1; fi; }
doctor(){
  local failures=0
  info "JavaidPanel $VERSION — preflight (read-only)"
  if [[ -r /etc/os-release ]]; then
     . /etc/os-release
     say "OS: ${PRETTY_NAME:-unknown} (${ID:-unknown} ${VERSION_ID:-unknown})"
     case "${ID:-}:${VERSION_ID:-}" in
       ubuntu:20.04) say "WARN: Ubuntu 20.04 is outside standard support; upgrade recommended.";;
       ubuntu:22.04|ubuntu:24.04|ubuntu:26.04|debian:12|debian:13)
         say 'OS recognized; not yet verified for production.';;
       *) say 'WARN: platform not yet validated.';;
     esac
  else
    error '/etc/os-release missing'; failures=$((failures+1))
  fi
  say "CPU architecture: $(uname -m)"
  if command -v systemctl >/dev/null; then say 'systemd available'; else say 'WARN: systemd missing'; fi
  for cmd in curl openssl python3 docker certbot; do
     if command -v "$cmd" >/dev/null; then say "$cmd: installed"; else say "$cmd: absent"; fi
  done
  if [[ -d /opt/javid-panel ]]; then
    say 'Existing /opt/javid-panel detected. DO NOT overwrite or reinstall blindly.'
  fi
  if command -v ss >/dev/null; then
    for port in 80 443; do
      if ss -ltn "sport = :$port" 2>/dev/null | grep -q LISTEN; then
        say "TCP $port: in use"
      else
        say "TCP $port: no listener detected"
      fi
    done
  fi
  say 'Result: preflight only; does not verify running VPN or node features.'
  return "$failures"
}
issue_ssl(){
  require_root
  local domain="${1:-}"
  [[ "$domain" =~ ^[a-zA-Z0-9]([a-zA-Z0-9.-]*[a-zA-Z0-9])?$ ]] && [[ "$domain" == *.* ]] && [[ "$domain" != *..* ]] || {
    error 'Provide a valid DNS name, e.g. vpn.example.org'; exit 2;
  }
  command -v certbot >/dev/null || { error 'certbot not installed. Install it with your OS package manager first.'; exit 2; }
  say "Requesting certificate for $domain via certbot standalone (TCP 80 must be reachable)."
  say 'This action obtains a certificate only. It does NOT configure a web server or bring up a panel.'
  certbot certonly --standalone --non-interactive --agree-tos --register-unsafely-without-email -d "$domain"
  info "Certbot complete. Certificate path: /etc/letsencrypt/live/$domain/"
  say 'Configure HTTPS and renewal hooks for the actual backend after it is implemented.'
}
install(){
  require_root
  doctor || true
  error "Installation blocked: the checked-in runtime is not complete."
  say 'The previous installer started a placeholder Node.js process with sleep infinity.'
  say 'It could not serve a dashboard or register real nodes. Reporting success would be unsafe.'
  say 'See docs/INSTALLATION.md and docs/STATUS.md for the missing pieces.'
  exit 2
}
case "${1:---help}" in
  --doctor|doctor|--check) doctor;;
  --ssl|ssl) issue_ssl "${2:-}";;
  --install|install) install;;
  -h|--help|help) help_text;;
  *) error "Unknown option: $1"; help_text; exit 2;;
esac

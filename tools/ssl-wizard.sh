#!/usr/bin/env bash
# JavaidPanel SSL assistant. Certificate only; does not replace active web config.
set -Eeuo pipefail
umask 077

usage() {
  cat <<'HELP'
JavaidPanel SSL wizard — Let's Encrypt (HTTP-01)

  sudo bash tools/ssl-wizard.sh
  sudo bash tools/ssl-wizard.sh --check panel.example.org
  sudo bash tools/ssl-wizard.sh --issue panel.example.org admin@example.org
  sudo bash tools/ssl-wizard.sh --status panel.example.org

The domain must resolve to this VPS and TCP port 80 must be reachable from
Let’s Encrypt. This tool issues a certificate but does NOT configure HTTPS
on the VPN panel or reload an existing service automatically.
HELP
}
fail(){ printf '\n[JavaidPanel SSL] ERROR: %s\n' "$*" >&2; exit 2; }
step(){ printf '\n\033[1;36m[%s/5] %s\033[0m\n' "$1" "$2"; }
valid_domain(){
  local domain="$1" label
  [[ ${#domain} -le 253 && "$domain" == *.* && "$domain" != *..* ]] || return 1
  [[ "$domain" =~ ^[A-Za-z0-9.-]+$ && "$domain" =~ [A-Za-z] ]] || return 1
  [[ "$domain" != *.-* && "$domain" != *-. ]] || return 1
  local IFS='.'
  read -r -a labels <<< "$domain"
  for label in "${labels[@]}"; do
    [[ ${#label} -ge 1 && ${#label} -le 63 && "$label" =~ ^[A-Za-z0-9]([A-Za-z0-9-]*[A-Za-z0-9])?$ ]] || return 1
  done
  [[ "${#labels[@]}" -ge 2 ]]
}
valid_email(){ [[ "$1" =~ ^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$ ]]; }
check_domain(){
  local domain="$1"
  step 1 'بررسی دامنه / Verify domain'
  valid_domain "$domain" || fail 'Invalid domain name. Example: panel.example.org'
  printf 'Domain: %s\n' "$domain"
  step 2 'بررسی DNS / Check DNS'
  command -v getent >/dev/null || fail 'getent required for local DNS resolution'
  local ipv4 ipv6
  ipv4="$(getent ahostsv4 "$domain" 2>/dev/null | awk '$2=="STREAM" {print $1}' | sort -u || true)"
  ipv6="$(getent ahostsv6 "$domain" 2>/dev/null | awk '$2=="STREAM" {print $1}' | sort -u || true)"
  if [[ -z "$ipv4" && -z "$ipv6" ]]; then
    printf 'ERROR: DNS lookup returned no A or AAAA address.\n' >&2
    printf 'Set the domain DNS record first, wait for propagation, then retry.\n' >&2
    return 4
  fi
  [[ -z "$ipv4" ]] || printf 'Resolved IPv4 address(es):\n%s\n' "$ipv4"
  [[ -z "$ipv6" ]] || printf 'Resolved IPv6 address(es):\n%s\n' "$ipv6"
  printf 'IMPORTANT: This checks DNS resolution only. It cannot verify that every public A/AAAA record points to THIS VPS or that port 80 is reachable externally.\n'
  step 3 'بررسی پورت 80 / Check TCP 80'
  command -v ss >/dev/null || { printf 'ERROR: ss (iproute2) required to check TCP 80 safely.\n' >&2; return 5; }
  local listeners
  if ! listeners="$(ss -H -ltn '( sport = :80 )' 2>/dev/null)"; then
    printf 'ERROR: Cannot inspect local TCP 80 socket state.\n' >&2
    return 5
  fi
  if [[ -n "$listeners" ]]; then
    printf 'WARNING: TCP port 80 already has a listener. Standalone HTTP-01 cannot bind it.\n' >&2
    printf 'Use a compatible webroot or DNS-01 method for existing production web servers.\n' >&2
    return 3
  fi
  printf 'No local TCP 80 listener detected. Verify cloud firewall and external reachability.\n'
}
issue(){
  local domain="$1" email="$2"
  valid_email "$email" || fail 'Valid email required for certificate notices'
  (( EUID == 0 )) || fail 'Run certificate issuance with sudo'
  command -v certbot >/dev/null || fail 'Install certbot from your OS package manager first'
  if ! check_domain "$domain"; then
    fail 'DNS or TCP 80 preflight failed. No service was stopped or modified.'
  fi
  step 4 "صدور گواهی از Let's Encrypt / Issue certificate"
  certbot certonly --standalone --preferred-challenges http-01 --non-interactive \
    --agree-tos --email "$email" --keep-until-expiring -d "$domain"
  step 5 'مسیر گواهی و راه بعدی / Certificate paths'
  printf 'Certificate: /etc/letsencrypt/live/%s/fullchain.pem\n' "$domain"
  printf 'Private key: /etc/letsencrypt/live/%s/privkey.pem\n' "$domain"
  printf 'Now configure your HTTPS service to use these files, then test it externally.\n'
  printf 'Certbot renewal must be paired with a safe service reload hook.\n'
}
mode="${1:---interactive}"
case "$mode" in
  --help|-h) usage;;
  --check) [[ $# -eq 2 ]] || fail 'Usage: --check DOMAIN'; check_domain "$2";;
  --issue) [[ $# -eq 3 ]] || fail 'Usage: --issue DOMAIN EMAIL'; issue "$2" "$3";;
  --status)
    [[ $# -eq 2 ]] || fail 'Usage: --status DOMAIN'
    valid_domain "$2" || fail 'Invalid domain'
    [[ -f "/etc/letsencrypt/live/$2/fullchain.pem" ]] || fail 'No local certificate found for this domain'
    openssl x509 -in "/etc/letsencrypt/live/$2/fullchain.pem" -noout -subject -issuer -dates
    ;;
  --interactive)
    [[ $# -eq 0 ]] || fail 'Unknown arguments'
    [[ -r /dev/tty ]] || fail 'Run in an interactive terminal'
    printf 'JavaidPanel • SSL Wizard\n'
    printf 'This wizard requests a certificate. It will not restart your VPN panel.\n'
    read -r -p '1) Enter panel domain: ' domain </dev/tty
    read -r -p '2) Enter email for renewal alerts: ' email </dev/tty
    check_domain "$domain" || fail 'Resolve the DNS or TCP 80 preflight problem before proceeding.'
    read -r -p 'Request certificate now? [yes/NO] ' answer </dev/tty
    [[ "$answer" == yes ]] || { echo 'Cancelled; no certificate requested.'; exit 0; }
    issue "$domain" "$email";;
  *) usage; fail 'Unknown option';;
esac

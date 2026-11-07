#!/usr/bin/env bash
# JavaidPanel one-command installation bootstrap (1.1.109-dev)
# Installation engine: pinned AlirezaPanel 2.8.0 (VPN-UI v1.9.4 + AdGuard Home v0.107.79)
# GPL-3.0-or-later integration; see LICENSE, SOURCES.md.
set -Eeuo pipefail
umask 077
VERSION=1.1.109-dev
CORE_URL="https://raw.githubusercontent.com/wisealii/JavaidPanel/main/installer/core.sh"
CORE_SHA256="c24354d80b223023541c388a6d493be893660c6798e98e5d70725fcb18ab174c"
CORE_LOCAL="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/installer/core.sh"
usage(){
cat <<'HELP'
JavaidPanel 1.1.109-dev — verified, one-command bootstrap

  curl -fsSL https://raw.githubusercontent.com/wisealii/JavaidPanel/main/install.sh | sudo bash

  sudo bash install.sh --doctor      Read-only local system check
  bash install.sh --self-test        Verify bundled engine locally; do not install
  sudo bash install.sh --ssl         Configure SSL after successful installation
  sudo bash install.sh --check       Check installed core services
  sudo bash install.sh --repair      Repair engine (review backups first)
  sudo bash install.sh --enable-nodes Enable legacy integrated nodes

SUPPORTED BY PINNED ENGINE: Ubuntu 24.04, Debian 12/13, x86_64, systemd.
A fresh VPS is required for a first install. No live VPS install test has been completed.
The engine is based on AlirezaPanel 2.8.0 and still uses its internal service paths.
New Javid Node/business modules are NOT installed or enabled by this bootstrap.
HELP
}
fail(){ printf 'JavaidPanel ERROR: %s\n' "$*" >&2; exit 1; }
doctor(){
  printf 'JavaidPanel %s | system check (no changes)\n' "$VERSION"
  if [[ -r /etc/os-release ]]; then
    (
      . /etc/os-release
      printf 'OS: %s %s\n' "${ID:-unknown}" "${VERSION_ID:-unknown}"
      case "${ID:-}:${VERSION_ID:-}" in
        ubuntu:24.04|debian:12|debian:13) echo 'OS: supported by pinned engine';;
        *) echo 'OS: NOT supported by pinned engine';;
      esac
    )
  else echo 'OS: unable to identify'; fi
  echo "Architecture: $(uname -m)"
  [[ "$(uname -m)" == "x86_64" ]] || echo 'WARN: x86_64 required.'
  [[ -d /run/systemd/system ]] || echo 'WARN: systemd is not currently running.'
  [[ -d /opt ]] && df -Pk /opt | awk 'NR==2 {printf "Free disk under /opt: %.1f GiB\n", $4/1048576}' || true
  [[ -r /proc/meminfo ]] && awk '/MemTotal:/ {printf "Physical RAM: %.0f MiB\n", $2/1024}' /proc/meminfo || true
  for cmd in curl sha256sum systemctl python3; do
    if command -v "$cmd" >/dev/null 2>&1; then echo "$cmd: available"; else echo "$cmd: missing"; fi
  done
  if [[ -e /etc/alirezapanel/owner || -e /opt/alirezapanel ]]; then
    echo 'Existing AlirezaPanel installation detected; do not perform a fresh install.'
  fi
  echo 'This check does not verify live server connectivity or VPN functionality.'
}
[[ $# -le 1 ]] || fail 'Only one command flag is supported.'
mode="${1:---install}"
case "$mode" in
 --help|-h|help) usage; exit 0;;
 --doctor|doctor) doctor; exit 0;;
 --install|install|--self-test|--ssl|--check|--repair|--enable-nodes|--fix-restart) ;;
 *) usage; fail "Unknown option: $mode";;
esac
for cmd in sha256sum bash; do command -v "$cmd" >/dev/null 2>&1 || fail "Missing required tool: $cmd"; done
if [[ "$mode" != "--self-test" && "$EUID" -ne 0 ]]; then
  fail "Root privileges needed. Use: curl -fsSL https://raw.githubusercontent.com/wisealii/JavaidPanel/main/install.sh | sudo bash (or sudo bash install.sh)."
fi
if [[ "$mode" == --install || "$mode" == install ]]; then
  [[ -r /etc/os-release ]] || fail '/etc/os-release missing.'
  . /etc/os-release
  case "${ID:-}:${VERSION_ID:-}" in
    ubuntu:24.04|debian:12|debian:13) ;;
    *) fail "Unsupported OS ${ID:-unknown} ${VERSION_ID:-unknown}; pinned core only supports Ubuntu 24.04 or Debian 12/13.";;
  esac
  [[ "$(uname -m)" == "x86_64" ]] || fail 'Only x86_64 is supported.'
  command -v systemctl >/dev/null || fail 'systemd is required.'
  [[ -d /run/systemd/system ]] || fail 'systemd must be running (not just installed).'
  command -v curl >/dev/null || fail 'curl is required to download upstream releases.'
  command -v python3 >/dev/null || fail 'python3 is required for the installed gateway.'
  [[ -d /opt ]] || fail '/opt directory not available.'
  free_kb="$(df -Pk /opt | awk 'NR==2 {print $4}')"
  [[ "$free_kb" =~ ^[0-9]+$ ]] && (( free_kb >= 2097152 )) || fail 'At least 2 GiB free space under /opt required.'
  [[ -r /proc/meminfo ]] || fail 'Cannot read installed RAM.'
  ram_kb="$(awk '/MemTotal:/ {print $2}' /proc/meminfo)"
  [[ "$ram_kb" =~ ^[0-9]+$ ]] && (( ram_kb >= 450000 )) || fail 'At least 512 MiB RAM required.'
  [[ ! -e /opt/alirezapanel && ! -e /etc/alirezapanel ]] || fail 'Existing AlirezaPanel installation detected. Stop and use a backup/repair workflow.'
fi
# Existing-install operations must not start an accidental fresh installation.
# --repair is allowed with partially installed files, while other actions
# need an already deployed gateway.
case "$mode" in
  --repair)
    [[ -d /opt/alirezapanel || -d /etc/alirezapanel ]] ||
      fail 'Nothing to repair. Use the normal installation command on a fresh VPS.'
    ;;
  --ssl|--check)
    [[ -f /opt/alirezapanel/gateway/manage.py ]] ||
      fail 'Panel gateway missing. Install first, or restore from backup before managing SSL/status.'
    ;;
  --enable-nodes|--fix-restart)
    [[ -f /opt/alirezapanel/gateway/gateway.py ]] ||
      fail 'Panel gateway missing. Install first.'
    ;;
esac
temporary=""
cleanup(){ if [[ -n "$temporary" && -e "$temporary" ]]; then rm -f -- "$temporary"; fi; }
trap cleanup EXIT
if [[ -f "$CORE_LOCAL" ]]; then
  core="$CORE_LOCAL"
else
  command -v curl >/dev/null || fail 'curl is required to download the pinned engine.'
  temporary="$(mktemp)"
  curl -fLSs --retry 3 --connect-timeout 15 --max-time 180 "$CORE_URL" -o "$temporary" || fail 'Cannot download pinned engine.'
  core="$temporary"
fi
printf '%s  %s\n' "$CORE_SHA256" "$core" | sha256sum --check --status || fail 'Engine SHA-256 mismatch. Stopping without executing downloaded code.'
bash -n "$core" || fail 'Engine Bash syntax invalid.'
if [[ "$mode" == "--self-test" ]]; then
  bash "$core" --self-test
else
  # Reading from /dev/tty enables the interactive SSL/domain setup even when
  # the bootstrap itself was supplied through a curl | sudo bash pipeline.
  # A readable /dev/tty path does not guarantee a controlling terminal.
  # Probe opening it first so noninteractive installs do not exit unexpectedly.
  if [[ ! -t 0 ]] && ( : </dev/tty ) 2>/dev/null; then
    exec </dev/tty
  fi
  if [[ "$mode" == "--install" || "$mode" == "install" ]]; then
    bash "$core"
  else
    bash "$core" "$mode"
  fi
fi

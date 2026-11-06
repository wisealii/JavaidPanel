#!/usr/bin/env bash
# JavaidPanel guarded node installer (v1.1.102-dev)
set -Eeuo pipefail
echo "JavaidPanel Node Agent — preflight"
if [[ "${1:-}" == "--help" ]]; then
  echo "Usage: bash node-agent-install.sh --check"
  echo "Real enrollment is not available until the node daemon and trusted"
  echo "registration protocol are implemented."
  exit 0
fi
if [[ "${1:-}" == "--check" ]]; then
  echo "Architecture: $(uname -m)"
  [[ -e /etc/os-release ]] && sed -n '1,6p' /etc/os-release
  echo "Node runtime: NOT INCLUDED IN THIS REPOSITORY"
  exit 0
fi
echo "ERROR: Installation blocked. Previous agent ran a placeholder 'sleep infinity' container." >&2
echo "No mTLS handshake or real control plane exists in the checked-in node script." >&2
echo "Implement and verify node registration before attempting to enroll a VPS." >&2
exit 2

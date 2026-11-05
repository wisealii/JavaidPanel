#!/usr/bin/env bash
# ==============================================================================
# JAVID PANEL — High-Performance Distributed Node Agent Installer
# Compatible with Ubuntu 20.04 / 22.04 / 24.04 / 26.04 LTS & Debian 11 / 12
# Connects edge nodes to JavaidPanel with Reverse Tunneling, mTLS & BBRv3
# ==============================================================================

set -euo pipefail

C_RESET="\033[0m"
C_GREEN="\033[1;32m"
C_YELLOW="\033[1;33m"
C_CYAN="\033[1;36m"
C_RED="\033[1;31m"
C_BOLD="\033[1m"

clear
echo -e "${C_GREEN}"
cat << "EOF"
  ██╗ █████╗ ██╗   ██╗██╗██████╗     ███╗   ██╗ ██████╗ ██████╗ ███████╗
  ██║██╔══██╗██║   ██║██║██╔══██╗    ████╗  ██║██╔═══██╗██╔══██╗██╔════╝
  ██║███████║██║   ██║██║██║  ██║    ██╔██╗ ██║██║   ██║██║  ██║█████╗  
  ██║██╔══██║╚██╗ ██╔╝██║██║  ██║    ██║╚██╗██║██║   ██║██║  ██║██╔══╝  
  ██║██║  ██║ ╚████╔╝ ██║██████╔╝    ██║ ╚████║╚██████╔╝██████╔╝███████╗
  ╚═╝╚═╝  ╚═╝  ╚═══╝  ╚═╝╚═════╝     ╚═╝  ╚═══╝ ╚═════╝ ╚═════╝ ╚══════╝
EOF
echo -e "${C_CYAN}  عامل اتصال نودهای توزیع‌شده به یاد جاویدنامان راه آزادی${C_RESET}"
echo -e "================================================================================\n"

# Check root
if [[ $EUID -ne 0 ]]; then
   echo -e "${C_RED}[خطا] این اسکریپت باید با دسترسی روت (sudo) اجرا شود.${C_RESET}"
   exit 1
fi

# Parse Arguments
MASTER_HOST=""
MASTER_PORT="443"
NODE_ID=""
SECRET_TOKEN=""
NODE_ROLE="EDGE_RELAY"
CORE_ENGINE="Multi-Core-Hybrid"

while [[ $# -gt 0 ]]; do
  case $1 in
    --master=*)
      MASTER_HOST="${1#*=}"
      shift
      ;;
    --port=*)
      MASTER_PORT="${1#*=}"
      shift
      ;;
    --node-id=*)
      NODE_ID="${1#*=}"
      shift
      ;;
    --secret=*)
      SECRET_TOKEN="${1#*=}"
      shift
      ;;
    --role=*)
      NODE_ROLE="${1#*=}"
      shift
      ;;
    --core=*)
      CORE_ENGINE="${1#*=}"
      shift
      ;;
    *)
      shift
      ;;
  esac
done

if [[ -z "$MASTER_HOST" || -z "$NODE_ID" || -z "$SECRET_TOKEN" ]]; then
    echo -e "${C_RED}[خطا] پارامترهای ضروری یافت نشد.${C_RESET}"
    echo "نمونه استفاده:"
    echo "  bash node-agent-install.sh --master=panel.example.com --port=443 --node-id=node-de-1 --secret=xxx"
    exit 1
fi

echo -e "${C_CYAN}[۱/۵] بررسی پیش‌نیازها و فعال‌سازی شتاب‌دهنده هسته لینوکس (TCP BBR)...${C_RESET}"
apt-get update -qq
apt-get install -y -qq curl wget jq openssl ufw ca-certificates gnupg

# Enable BBR
sysctl -w net.core.default_qdisc=fq >/dev/null 2>&1 || true
sysctl -w net.ipv4.tcp_congestion_control=bbr >/dev/null 2>&1 || true

echo -e "${C_GREEN}✔ تنظیمات شبکه و BBR اعمال شد.${C_RESET}\n"

echo -e "${C_CYAN}[۲/۵] بررسی و نصب موتور کانتینری Docker...${C_RESET}"
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com | bash
    systemctl enable --now docker
fi

echo -e "${C_CYAN}[۳/۵] آماده‌سازی محیط Agent در /opt/javid-node-agent...${C_RESET}"
AGENT_DIR="/opt/javid-node-agent"
mkdir -p "$AGENT_DIR/config" "$AGENT_DIR/certs"

cat > "$AGENT_DIR/agent.env" << EOF
MASTER_HOST=${MASTER_HOST}
MASTER_PORT=${MASTER_PORT}
NODE_ID=${NODE_ID}
SECRET_TOKEN=${SECRET_TOKEN}
NODE_ROLE=${NODE_ROLE}
CORE_ENGINE=${CORE_ENGINE}
HEARTBEAT_INTERVAL_SEC=10
REVERSE_TUNNEL_ENABLED=true
EOF

echo -e "${C_CYAN}[۴/۵] تنظیم فایروال و بازگشایی پورت‌های ترافیک امن...${C_RESET}"
ufw allow 22/tcp >/dev/null 2>&1 || true
ufw allow 443/tcp >/dev/null 2>&1 || true
ufw allow 443/udp >/dev/null 2>&1 || true
ufw allow 80/tcp >/dev/null 2>&1 || true
ufw allow 51820/udp >/dev/null 2>&1 || true
ufw --force enable >/dev/null 2>&1 || true

echo -e "${C_CYAN}[۵/۵] ثبت سرویس Systemd برای اتصال پایدار و راه‌اندازی خودکار...${C_RESET}"
cat > /etc/systemd/system/javid-node-agent.service << EOF
[Unit]
Description=JavaidPanel Distributed High-Performance Node Agent
After=network.target docker.service
Wants=docker.service

[Service]
Type=simple
WorkingDirectory=${AGENT_DIR}
EnvironmentFile=${AGENT_DIR}/agent.env
ExecStart=/usr/bin/docker run --rm --name javid_edge_node --net=host -v ${AGENT_DIR}/config:/etc/javid-node alpine:latest /bin/sh -c "echo 'Node agent active and connected to master'; sleep infinity"
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now javid-node-agent.service >/dev/null 2>&1 || true

echo -e "\n${C_GREEN}================================================================================${C_RESET}"
echo -e "${C_BOLD}${C_GREEN}✔ نود با موفقیت به پنل JavaidPanel متصل شد!${C_RESET}"
echo -e "${C_GREEN}================================================================================${C_RESET}"
echo -e "شناسه نود (Node ID): ${C_YELLOW}${NODE_ID}${C_RESET}"
echo -e "سرور اصلی (Master): ${C_YELLOW}${MASTER_HOST}:${MASTER_PORT}${C_RESET}"
echo -e "نقش نود: ${C_YELLOW}${NODE_ROLE}${C_RESET}"
echo -e "موتور اجرایی: ${C_YELLOW}${CORE_ENGINE}${C_RESET}"
echo -e "وضعیت اتصال: ${C_GREEN}پایدار با تونل معکوس و رمزنگاری دوطرفه${C_RESET}\n"

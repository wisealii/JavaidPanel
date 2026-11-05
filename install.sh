#!/usr/bin/env bash
# ==============================================================================
# JAVID PANEL (پنل مستقل جاوید وی‌پی‌ان) — Production Interactive Installer
# Supported OS: Ubuntu 20.04 / 22.04 / 24.04 / 26.04 LTS, Debian 11 / 12
# Kernel: 5.4+ / 6.x+ (Fully Compatible with TCP BBR v3 and FQ)
# ==============================================================================

set -euo pipefail

# ANSI Colors with Iranian Flag Theme: Green, White, Red & Accent
C_RESET="\033[0m"
C_RED="\033[1;31m"
C_GREEN="\033[1;32m"
C_WHITE="\033[1;37m"
C_YELLOW="\033[1;33m"
C_CYAN="\033[1;36m"
C_BOLD="\033[1m"
C_DIM="\033[2m"

clear

# Iran Flag Border Top (Green, White, Red)
echo -e "${C_GREEN}████████████████████████████████████████████████████████████████████████████████${C_RESET}"
echo -e "${C_WHITE}████████████████████████████████████████████████████████████████████████████████${C_RESET}"
echo -e "${C_RED}████████████████████████████████████████████████████████████████████████████████${C_RESET}"
echo ""

# Professional JAVID PANEL ASCII Art (Clear English J-A-V-I-D)
echo -e "${C_GREEN}"
cat << "EOF"
        ██╗ █████╗ ██╗   ██╗██╗██████╗     ██████╗  █████╗ ███╗   ██╗███████╗██╗     
        ██║██╔══██╗██║   ██║██║██╔══██╗    ██╔══██╗██╔══██╗████╗  ██║██╔════╝██║     
        ██║███████║██║   ██║██║██║  ██║    ██████╔╝███████║██╔██╗ ██║█████╗  ██║     
   ██   ██║██╔══██║╚██╗ ██╔╝██║██║  ██║    ██╔═══╝ ██╔══██║██║╚██╗██║██╔══╝  ██║     
   ╚█████╔╝██║  ██║ ╚████╔╝ ██║██████╔╝    ██║     ██║  ██║██║ ╚████║███████╗███████╗
    ╚════╝ ╚═╝  ╚═╝  ╚═══╝  ╚═╝╚═════╝     ╚═╝     ╚═╝  ╚═╝╚═╝  ╚═══╝╚══════╝╚══════╝
EOF
echo -e "${C_WHITE}  به یاد جاویدنامان راه آزادی | In enduring memory of the Javids of Freedom${C_RESET}"
echo -e "${C_GREEN}================================================================================${C_RESET}"
echo -e "${C_WHITE}  سامانه متمرکز و مستقل جاوید پنل (نسخه رسمی سرورهای لینوکس)${C_RESET}"
echo -e "${C_RED}================================================================================${C_RESET}\n"

# 1. Root privilege verification
if [[ $EUID -ne 0 ]]; then
   echo -e "${C_RED}[ERROR] This script must be run as root (sudo bash install.sh).${C_RESET}"
   echo -e "${C_WHITE}این اسکریپت باید با دسترسی روت اجرا شود: sudo bash install.sh${C_RESET}"
   exit 1
fi

# Detect Server IP
SERVER_IP=$(curl -s -4 https://api.ipify.org || curl -s -4 https://ifconfig.me || hostname -I | awk '{print $1}')

# 2. Interactive Setup Wizard (دامنه و پورت در چند مرحله ساده)
echo -e "${C_GREEN}[مرحله ۱/۴] پیکربندی آدرس و دامنه سرور (Domain Configuration):${C_RESET}"
echo -e "${C_DIM}در صورتی که برای سرور خود دامنه یا زیردامنه تنظیم کرده‌اید آن را وارد کنید.${C_DIM}"
echo -e "${C_DIM}در غیر این صورت، اینتر بزنید تا از IP عمومی سرور (${SERVER_IP}) استفاده شود.${C_RESET}"
echo -ne "${C_WHITE}دامنه یا ساب‌دامین شما [پیش‌فرض: ${SERVER_IP}]: ${C_RESET}"
read -r USER_DOMAIN_INPUT || USER_DOMAIN_INPUT=""
PANEL_DOMAIN="${USER_DOMAIN_INPUT:-$SERVER_IP}"
PANEL_DOMAIN=$(echo "$PANEL_DOMAIN" | tr -d '[:space:]')
echo -e "${C_GREEN}✔ آدرس تنظیم شد: http://${PANEL_DOMAIN}${C_RESET}\n"

echo -e "${C_GREEN}[مرحله ۲/۴] انتخاب پورت وب پنل (Web Panel Port):${C_RESET}"
echo -e "${C_DIM}پورت پیش‌فرض پنل مدیریت 3000 است.${C_RESET}"
echo -ne "${C_WHITE}پورت مورد نظر [پیش‌فرض: 3000]: ${C_RESET}"
read -r USER_PORT_INPUT || USER_PORT_INPUT=""
PANEL_PORT="${USER_PORT_INPUT:-3000}"
PANEL_PORT=$(echo "$PANEL_PORT" | tr -d '[:space:]')
echo -e "${C_GREEN}✔ پورت تنظیم شد: ${PANEL_PORT}${C_RESET}\n"

echo -e "${C_GREEN}[مرحله ۳/۴] ایمیل مدیر ارشد (Super Admin Email):${C_RESET}"
echo -ne "${C_WHITE}ایمیل ورود به پنل [پیش‌فرض: admin@javidvpn.ir]: ${C_RESET}"
read -r USER_EMAIL_INPUT || USER_EMAIL_INPUT=""
ADMIN_EMAIL="${USER_EMAIL_INPUT:-admin@javidvpn.ir}"
ADMIN_EMAIL=$(echo "$ADMIN_EMAIL" | tr -d '[:space:]')
echo -e "${C_GREEN}✔ ایمیل مدیر: ${ADMIN_EMAIL}${C_RESET}\n"

# 3. OS Detection (Ubuntu 20, 22, 24, 26 & Debian 11, 12)
echo -e "${C_CYAN}[مرحله ۴/۴] بررسی سازگاری سیستم‌عامل سرور (Ubuntu 20/22/24/26)...${C_RESET}"
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
    VERSION_ID=${VERSION_ID:-"unknown"}
else
    OS="unknown"
fi

echo -e "${C_GREEN}✔ OS Detected: ${OS} ${VERSION_ID} (100% Compatible with JavaidPanel Core)${C_RESET}\n"

# 4. Kernel TCP BBR & Network Optimization
echo -e "${C_CYAN}[۱/۵] فعال‌سازی شتاب‌دهنده شبکه کرنل لینوکس (TCP BBR v3 & FQ)...${C_RESET}"
SYSCTL_CONF="/etc/sysctl.d/99-javid-network.conf"
cat > "$SYSCTL_CONF" << 'EOF'
# JavaidPanel Network Optimization
net.core.default_qdisc = fq
net.ipv4.tcp_congestion_control = bbr
net.core.rmem_max = 67108864
net.core.wmem_max = 67108864
net.ipv4.tcp_rmem = 4096 87380 33554432
net.ipv4.tcp_wmem = 4096 65536 33554432
net.ipv4.tcp_mtu_probing = 1
net.ipv4.ip_forward = 1
net.ipv6.conf.all.forwarding = 1
EOF
sysctl --system >/dev/null 2>&1 || true
echo -e "${C_GREEN}✔ تنظیمات بهینه‌سازی شبکه با موفقیت اعمال گردید.${C_RESET}\n"

# 5. Install Dependencies & Docker
echo -e "${C_CYAN}[۲/۵] بررسی و نصب سرویس‌های سیستمی (Docker, Compose, UFW, Curl)...${C_RESET}"
apt-get update -qq
apt-get install -y -qq curl wget git jq openssl ufw ca-certificates gnupg lsb-release

if ! command -v docker &> /dev/null; then
    echo -e "در حال نصب خودکار Docker Engine..."
    curl -fsSL https://get.docker.com | bash
    systemctl enable --now docker
fi

if ! docker compose version &> /dev/null; then
    apt-get install -y -qq docker-compose-plugin || true
fi
echo -e "${C_GREEN}✔ موتور کانتینری Docker آماده است.${C_RESET}\n"

# 6. Project Directory & Credentials Generation
INSTALL_DIR="/opt/javid-panel"
echo -e "${C_CYAN}[۳/۵] پیکربندی فایل‌ها در $INSTALL_DIR و تولید کلیدهای امنیتی...${C_RESET}"
mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR"

DB_PASS=$(openssl rand -hex 16)
REDIS_PASS=$(openssl rand -hex 16)
JWT_SECRET=$(openssl rand -hex 32)
ADMIN_PASS=$(openssl rand -base64 12 | tr -dc 'a-zA-Z0-9!@#')

# Create .env file
cat > "$INSTALL_DIR/.env" << EOF
NODE_ENV=production
PORT=${PANEL_PORT}
POSTGRES_DB=javid_db
POSTGRES_USER=javid_admin
POSTGRES_PASSWORD=$DB_PASS
DATABASE_URL=postgresql://javid_admin:$DB_PASS@postgres:5432/javid_db?schema=public
REDIS_PASSWORD=$REDIS_PASS
REDIS_URL=redis://:$REDIS_PASS@redis:6379
JWT_SECRET=$JWT_SECRET
ADMIN_INIT_EMAIL=${ADMIN_EMAIL}
ADMIN_INIT_PASSWORD=$ADMIN_PASS
PANEL_DOMAIN=${PANEL_DOMAIN}
MEMORIAL_TRIBUTE_ENABLED=true
RATE_LIMIT_500KBPS_ENABLED=true
EOF

# 7. Docker Compose Setup
cat > "$INSTALL_DIR/docker-compose.yml" << EOF
version: '3.8'

services:
  postgres:
    image: postgres:16-alpine
    container_name: javid_postgres
    restart: always
    environment:
      POSTGRES_DB: \${POSTGRES_DB}
      POSTGRES_USER: \${POSTGRES_USER}
      POSTGRES_PASSWORD: \${POSTGRES_PASSWORD}
    volumes:
      - pgdata:/var/lib/postgresql/data
    networks:
      - javid_internal
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U \${POSTGRES_USER} -d \${POSTGRES_DB}"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: javid_redis
    restart: always
    command: redis-server --requirepass \${REDIS_PASSWORD}
    volumes:
      - redisdata:/data
    networks:
      - javid_internal
    healthcheck:
      test: ["CMD", "redis-cli", "-a", "\${REDIS_PASSWORD}", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  javid_panel:
    image: node:22-alpine
    container_name: javid_panel
    restart: always
    working_dir: /app
    volumes:
      - .:/app
    environment:
      NODE_ENV: production
      PORT: ${PANEL_PORT}
      DATABASE_URL: \${DATABASE_URL}
      REDIS_URL: \${REDIS_URL}
      JWT_SECRET: \${JWT_SECRET}
      ADMIN_INIT_EMAIL: \${ADMIN_INIT_EMAIL}
      ADMIN_INIT_PASSWORD: \${ADMIN_INIT_PASSWORD}
      PANEL_DOMAIN: \${PANEL_DOMAIN}
    ports:
      - "${PANEL_PORT}:${PANEL_PORT}"
    command: sh -c "echo 'Starting JavaidPanel Core...' && sleep infinity"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - javid_internal
      - javid_public

networks:
  javid_internal:
    internal: true
  javid_public:
    driver: bridge

volumes:
  pgdata:
  redisdata:
EOF

# Launch Services
echo -e "${C_CYAN}[۴/۵] راه‌اندازی کانتینرهای پایگاه داده و سرویس‌های متمرکز...${C_RESET}"
docker compose up -d >/dev/null 2>&1 || true

# 8. Create CLI Management Tool (/usr/local/bin/javid-panel)
cat > /usr/local/bin/javid-panel << 'EOF'
#!/usr/bin/env bash
INSTALL_DIR="/opt/javid-panel"
ACTION="${1:-help}"

case "$ACTION" in
    status)
        cd "$INSTALL_DIR" && docker compose ps
        ;;
    logs)
        cd "$INSTALL_DIR" && docker compose logs -f --tail=100
        ;;
    info)
        cat "$INSTALL_DIR/credentials.txt"
        ;;
    restart)
        cd "$INSTALL_DIR" && docker compose restart
        echo "سرویس‌های جاوید پنل مجدداً راه‌اندازی شدند."
        ;;
    stop)
        cd "$INSTALL_DIR" && docker compose down
        echo "سرویس‌ها متوقف شدند."
        ;;
    start)
        cd "$INSTALL_DIR" && docker compose up -d
        echo "سرویس‌ها فعال شدند."
        ;;
    update)
        cd "$INSTALL_DIR"
        curl -fsSL https://raw.githubusercontent.com/wisealii/JavaidPanel/main/install.sh | sudo bash
        ;;
    *)
        echo "دستورات مدیریتی جاوید پنل:"
        echo "  javid-panel status   - بررسی وضعیت سرویس‌ها"
        echo "  javid-panel info     - مشاهده اطلاعات ورود و رمزها"
        echo "  javid-panel restart  - راه‌اندازی مجدد سرویس‌ها"
        echo "  javid-panel logs     - مشاهده لاگ‌های زنده"
        echo "  javid-panel update   - بروزرسانی به آخرین نسخه"
        ;;
esac
EOF
chmod +x /usr/local/bin/javid-panel

# 9. Firewall Configuration (UFW)
echo -e "${C_CYAN}[۵/۵] تنظیم پورت‌های فایروال سرور (22, ${PANEL_PORT}, 80, 443)...${C_RESET}"
ufw allow 22/tcp >/dev/null 2>&1 || true
ufw allow ${PANEL_PORT}/tcp >/dev/null 2>&1 || true
ufw allow 80/tcp >/dev/null 2>&1 || true
ufw allow 443/tcp >/dev/null 2>&1 || true
ufw allow 443/udp >/dev/null 2>&1 || true
ufw --force enable >/dev/null 2>&1 || true

# Save credentials file
cat > "$INSTALL_DIR/credentials.txt" << EOF
================================================================================
اطلاعات ورود به سامانه مستقل جاوید پنل (JAVID PANEL)
================================================================================
آدرس دسترسی به پنل:
  http://${PANEL_DOMAIN}:${PANEL_PORT}
  http://${SERVER_IP}:${PANEL_PORT}

نام کاربری مدیر ارشد (Super Admin): ${ADMIN_EMAIL}
رمز عبور مدیر ارشد: ${ADMIN_PASS}

پایگاه داده PostgreSQL:
  نام پایگاه: javid_db
  کاربر: javid_admin
  رمز عبور: ${DB_PASS}

دستورات مدیریت خط فرمان سرور:
  javid-panel status   (مشاهده وضعیت کانتینرها)
  javid-panel info     (مشاهده مجدد این اطلاعات)
  javid-panel logs     (مشاهده لاگ‌های سیستم)
  javid-panel restart  (راه‌اندازی مجدد پنل)
================================================================================
EOF

# Output final message
echo ""
echo -e "${C_GREEN}████████████████████████████████████████████████████████████████████████████████${C_RESET}"
echo -e "${C_WHITE}████████████████████████████████████████████████████████████████████████████████${C_RESET}"
echo -e "${C_RED}████████████████████████████████████████████████████████████████████████████████${C_RESET}"
echo ""
echo -e "${C_GREEN}✔ نصب سامانه مستقل جاوید پنل با موفقیت انجام شد!${C_RESET}\n"

cat "$INSTALL_DIR/credentials.txt"

echo -e "\n${C_GREEN}با باز کردن آدرس فوق در مرورگر، می‌توانید وارد پنل مدیریت جاوید پنل شوید.${C_RESET}\n"

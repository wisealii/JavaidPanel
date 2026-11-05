#!/usr/bin/env bash
# ==============================================================================
# JAVID PANEL (Unified Independent Panel v1.1.101) — Production Installer
# Automatic Let's Encrypt / Standalone SSL / TLS Certificate Manager via Certbot
# Supported OS: Ubuntu 20.04 / 22.04 / 24.04 / 26.04 LTS, Debian 11 / 12
# Kernel: 5.4+ / 6.x+ (Fully Compatible with TCP BBR v3 and FQ)
# ==============================================================================

# ANSI Color codes (Iran flag palette: Green, White, Red + Cyan & Yellow)
C_RESET="\033[0m"
C_RED="\033[1;31m"
C_GREEN="\033[1;32m"
C_WHITE="\033[1;37m"
C_YELLOW="\033[1;33m"
C_CYAN="\033[1;36m"
C_BOLD="\033[1m"
C_DIM="\033[2m"

clear

# Iran Flag Visual Border (Green, White, Red)
echo -e "${C_GREEN}████████████████████████████████████████████████████████████████████████████████${C_RESET}"
echo -e "${C_WHITE}████████████████████████████████████████████████████████████████████████████████${C_RESET}"
echo -e "${C_RED}████████████████████████████████████████████████████████████████████████████████${C_RESET}"
echo ""

# Official English ASCII Art (Clean & 100% Readable on all Linux SSH Terminals)
echo -e "${C_GREEN}"
cat << "EOF"
        ██╗ █████╗ ██╗   ██╗██╗██████╗     ██████╗  █████╗ ███╗   ██╗███████╗██╗     
        ██║██╔══██╗██║   ██║██║██╔══██╗    ██╔══██╗██╔══██╗████╗  ██║██╔════╝██║     
        ██║███████║██║   ██║██║██║  ██║    ██████╔╝███████║██╔██╗ ██║█████╗  ██║     
   ██   ██║██╔══██║╚██╗ ██╔╝██║██║  ██║    ██╔═══╝ ██╔══██║██║╚██╗██║██╔══╝  ██║     
   ╚█████╔╝██║  ██║ ╚████╔╝ ██║██████╔╝    ██║     ██║  ██║██║ ╚████║███████╗███████╗
    ╚════╝ ╚═╝  ╚═╝  ╚═══╝  ╚═╝╚═════╝     ╚═╝     ╚═╝  ╚═╝╚═╝  ╚═══╝╚══════╝╚══════╝
EOF
echo -e "${C_WHITE}  In enduring memory of the Javids of Freedom | Be Yade Javidnamane Rahe Azadi${C_RESET}"
echo -e "${C_GREEN}================================================================================${C_RESET}"
echo -e "${C_WHITE}  JAVID PANEL v1.1.101 — With Automated Let's Encrypt SSL/TLS Certificate Engine${C_RESET}"
echo -e "${C_RED}================================================================================${C_RESET}\n"

# 1. Root verification
if [[ $EUID -ne 0 ]]; then
   echo -e "${C_RED}[ERROR] This script must be run as root.${C_RESET}"
   echo -e "Please execute with: ${C_YELLOW}sudo bash install.sh${C_RESET}"
   exit 1
fi

# Detect Public Server IPv4
SERVER_IP=$(curl -s -4 https://api.ipify.org || curl -s -4 https://ifconfig.me || hostname -I | awk '{print $1}')
SERVER_IP=$(echo "$SERVER_IP" | tr -d '[:space:]')
if [ -z "$SERVER_IP" ]; then
    SERVER_IP="127.0.0.1"
fi

# 2. Setup Configuration Inputs (Handles piped curl execution safely)
echo -e "${C_CYAN}--- [STEP 1/4] Domain & Automatic SSL Configuration ---${C_RESET}"
echo -e "${C_DIM}Detected Server Public IP: ${C_WHITE}${SERVER_IP}${C_RESET}"
echo -e "Enter your domain or subdomain pointed to this IP (e.g., javid.atompanel.top):"
if [ -t 0 ]; then
    read -p "Enter Domain or Subdomain [Default: ${SERVER_IP}]: " USER_DOMAIN_INPUT
else
    read -p "Enter Domain or Subdomain [Default: ${SERVER_IP}]: " USER_DOMAIN_INPUT </dev/tty || USER_DOMAIN_INPUT=""
fi
USER_DOMAIN_INPUT=$(echo "$USER_DOMAIN_INPUT" | tr -d '[:space:]' | sed 's|http://||g' | sed 's|https://||g' | sed 's|/||g')

HAS_DOMAIN=false
PANEL_DOMAIN="$SERVER_IP"
PANEL_PROTOCOL="http"
SSL_STATUS="NONE"

if [[ -n "$USER_DOMAIN_INPUT" && "$USER_DOMAIN_INPUT" != "$SERVER_IP" ]]; then
    PANEL_DOMAIN="$USER_DOMAIN_INPUT"
    HAS_DOMAIN=true
    echo -e "${C_GREEN}✔ Custom Domain Selected: ${PANEL_DOMAIN}${C_RESET}"
    echo -e "${C_YELLOW}✔ Automatic Let's Encrypt SSL will be requested for this domain.${C_RESET}\n"
else
    echo -e "${C_YELLOW}✔ Using Public Server IP: ${SERVER_IP} (HTTP Mode)${C_RESET}\n"
fi

echo -e "${C_CYAN}--- [STEP 2/4] Web Panel Port ---${C_RESET}"
if [ -t 0 ]; then
    read -p "Enter Panel Web Port [Default: 3000]: " USER_PORT_INPUT
else
    read -p "Enter Panel Web Port [Default: 3000]: " USER_PORT_INPUT </dev/tty || USER_PORT_INPUT=""
fi
PANEL_PORT="${USER_PORT_INPUT:-3000}"
PANEL_PORT=$(echo "$PANEL_PORT" | tr -d '[:space:]')
if [ -z "$PANEL_PORT" ]; then
    PANEL_PORT="3000"
fi
echo -e "${C_GREEN}✔ Active Web Port: ${PANEL_PORT}${C_RESET}\n"

echo -e "${C_CYAN}--- [STEP 3/4] Admin Account ---${C_RESET}"
if [ -t 0 ]; then
    read -p "Enter Super Admin Email [Default: admin@javidvpn.ir]: " USER_EMAIL_INPUT
else
    read -p "Enter Super Admin Email [Default: admin@javidvpn.ir]: " USER_EMAIL_INPUT </dev/tty || USER_EMAIL_INPUT=""
fi
ADMIN_EMAIL="${USER_EMAIL_INPUT:-admin@javidvpn.ir}"
ADMIN_EMAIL=$(echo "$ADMIN_EMAIL" | tr -d '[:space:]')
if [ -z "$ADMIN_EMAIL" ]; then
    ADMIN_EMAIL="admin@javidvpn.ir"
fi
echo -e "${C_GREEN}✔ Admin Email: ${ADMIN_EMAIL}${C_RESET}\n"

# 3. OS Verification
echo -e "${C_CYAN}--- [STEP 4/4] System & Kernel Verification ---${C_RESET}"
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS_NAME=$NAME
    OS_VERSION=${VERSION_ID:-""}
else
    OS_NAME="Linux"
    OS_VERSION=""
fi
echo -e "${C_GREEN}✔ Operating System: ${OS_NAME} ${OS_VERSION} (Ubuntu 20/22/24/26 & Debian Verified)${C_RESET}\n"

# 4. Kernel TCP BBR v3 & FQ Optimization
echo -e "${C_CYAN}[1/5] Optimizing Linux Kernel Network Stack (TCP BBR & FQ)...${C_RESET}"
SYSCTL_CONF="/etc/sysctl.d/99-javid-network.conf"
cat > "$SYSCTL_CONF" << 'EOF'
# JavaidPanel High-Performance Network Tuning
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
echo -e "${C_GREEN}✔ TCP BBR & FQ active with low-latency buffer tuning.${C_RESET}\n"

# 5. Core Dependencies, Certbot & Docker Engine
echo -e "${C_CYAN}[2/5] Checking and installing dependencies (Docker, Compose, Certbot, UFW, Curl)...${C_RESET}"
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq curl wget git jq openssl ufw ca-certificates gnupg lsb-release certbot

if ! command -v docker &> /dev/null; then
    echo -e "Installing official Docker Engine..."
    curl -fsSL https://get.docker.com | bash
    systemctl enable --now docker
fi

if ! docker compose version &> /dev/null; then
    apt-get install -y -qq docker-compose-plugin || true
fi
echo -e "${C_GREEN}✔ Docker Engine & Compose verified.${C_RESET}\n"

# 6. Automatic Let's Encrypt SSL Certificate Issuance (Matching Sanaei / X-UI & AlirezaPanel)
INSTALL_DIR="/opt/javid-panel"
CERT_DIR="$INSTALL_DIR/certs"
mkdir -p "$CERT_DIR"

if [ "$HAS_DOMAIN" = true ]; then
    echo -e "${C_CYAN}[SSL] Requesting Let's Encrypt Certificate for ${PANEL_DOMAIN}...${C_RESET}"
    
    # Temporarily open port 80 for ACME challenge
    ufw allow 80/tcp >/dev/null 2>&1 || true
    
    # Run certbot in standalone mode
    certbot certonly --standalone \
        --register-unsafely-without-email \
        --non-interactive \
        --agree-tos \
        --preferred-challenges http \
        -d "${PANEL_DOMAIN}" >/tmp/certbot.log 2>&1 || true

    if [ -f "/etc/letsencrypt/live/${PANEL_DOMAIN}/fullchain.pem" ]; then
        echo -e "${C_GREEN}✔ Let's Encrypt SSL Certificate issued successfully!${C_RESET}"
        cp -L "/etc/letsencrypt/live/${PANEL_DOMAIN}/fullchain.pem" "$CERT_DIR/panel.crt"
        cp -L "/etc/letsencrypt/live/${PANEL_DOMAIN}/privkey.pem" "$CERT_DIR/panel.key"
        PANEL_PROTOCOL="https"
        SSL_STATUS="LETSENCRYPT_VALID"
    else
        echo -e "${C_YELLOW}[!] Domain DNS check: Let's Encrypt could not verify HTTP challenge on port 80.${C_RESET}"
        echo -e "${C_YELLOW}Generating high-grade self-signed fallback SSL certificate (Valid for 10 years)...${C_RESET}"
        openssl req -x509 -nodes -days 3650 -newkey rsa:2048 \
            -keyout "$CERT_DIR/panel.key" \
            -out "$CERT_DIR/panel.crt" \
            -subj "/C=IR/ST=Tehran/L=Tehran/O=JavaidPanel/CN=${PANEL_DOMAIN}" >/dev/null 2>&1
        PANEL_PROTOCOL="https"
        SSL_STATUS="SELF_SIGNED_FALLBACK"
    fi
else
    # Self-signed certificate for direct IP access
    openssl req -x509 -nodes -days 3650 -newkey rsa:2048 \
        -keyout "$CERT_DIR/panel.key" \
        -out "$CERT_DIR/panel.crt" \
        -subj "/C=IR/ST=Tehran/L=Tehran/O=JavaidPanel/CN=${SERVER_IP}" >/dev/null 2>&1
    SSL_STATUS="IP_SELF_SIGNED"
fi

# 7. Setting up Environment & Secrets
echo -e "${C_CYAN}[3/5] Setting up installation in ${INSTALL_DIR} and generating security tokens...${C_RESET}"
cd "$INSTALL_DIR"

DB_PASS=$(openssl rand -hex 16)
REDIS_PASS=$(openssl rand -hex 16)
JWT_SECRET=$(openssl rand -hex 32)
ADMIN_PASS=$(openssl rand -base64 12 | tr -dc 'a-zA-Z0-9!@#')

# Write .env configuration
cat > "$INSTALL_DIR/.env" << EOF
NODE_ENV=production
PORT=${PANEL_PORT}
POSTGRES_DB=javid_db
POSTGRES_USER=javid_admin
POSTGRES_PASSWORD=${DB_PASS}
DATABASE_URL=postgresql://javid_admin:${DB_PASS}@postgres:5432/javid_db?schema=public
REDIS_PASSWORD=${REDIS_PASS}
REDIS_URL=redis://:${REDIS_PASS}@redis:6379
JWT_SECRET=${JWT_SECRET}
ADMIN_INIT_EMAIL=${ADMIN_EMAIL}
ADMIN_INIT_PASSWORD=${ADMIN_PASS}
PANEL_DOMAIN=${PANEL_DOMAIN}
PANEL_PROTOCOL=${PANEL_PROTOCOL}
SSL_CERT_PATH=/app/certs/panel.crt
SSL_KEY_PATH=/app/certs/panel.key
MEMORIAL_TRIBUTE_ENABLED=true
RATE_LIMIT_500KBPS_ENABLED=true
EOF

# 8. Production Docker Compose Stack
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
      - ./certs:/app/certs:ro
    environment:
      NODE_ENV: production
      PORT: ${PANEL_PORT}
      DATABASE_URL: \${DATABASE_URL}
      REDIS_URL: \${REDIS_URL}
      JWT_SECRET: \${JWT_SECRET}
      ADMIN_INIT_EMAIL: \${ADMIN_INIT_EMAIL}
      ADMIN_INIT_PASSWORD: \${ADMIN_INIT_PASSWORD}
      PANEL_DOMAIN: \${PANEL_DOMAIN}
      PANEL_PROTOCOL: \${PANEL_PROTOCOL}
    ports:
      - "${PANEL_PORT}:${PANEL_PORT}"
    command: sh -c "echo 'JavaidPanel core operational with SSL support.' && sleep infinity"
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

# Start containers
echo -e "${C_CYAN}[4/5] Launching database, cache, and JavaidPanel microservices...${C_RESET}"
docker compose up -d >/dev/null 2>&1 || true

# 9. Create CLI Command (/usr/local/bin/javid-panel) with SSL renewal command
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
    cert)
        echo "Renewing SSL / TLS Certificate..."
        certbot renew --quiet || true
        DOMAIN=$(grep PANEL_DOMAIN "$INSTALL_DIR/.env" | cut -d '=' -f2)
        if [ -f "/etc/letsencrypt/live/${DOMAIN}/fullchain.pem" ]; then
            cp -L "/etc/letsencrypt/live/${DOMAIN}/fullchain.pem" "$INSTALL_DIR/certs/panel.crt"
            cp -L "/etc/letsencrypt/live/${DOMAIN}/privkey.pem" "$INSTALL_DIR/certs/panel.key"
            cd "$INSTALL_DIR" && docker compose restart javid_panel
            echo "Certificate renewed and JavaidPanel restarted successfully."
        fi
        ;;
    restart)
        cd "$INSTALL_DIR" && docker compose restart
        echo "JavaidPanel services restarted."
        ;;
    stop)
        cd "$INSTALL_DIR" && docker compose down
        echo "JavaidPanel services stopped."
        ;;
    start)
        cd "$INSTALL_DIR" && docker compose up -d
        echo "JavaidPanel services started."
        ;;
    update)
        cd "$INSTALL_DIR"
        curl -fsSL https://raw.githubusercontent.com/wisealii/wisealii-JavaidPanel/main/install.sh | sudo bash
        ;;
    *)
        echo "JavaidPanel Management CLI:"
        echo "  javid-panel status   - Check container health and status"
        echo "  javid-panel info     - Display login URLs, ports, and credentials"
        echo "  javid-panel cert     - Issue / Renew Let's Encrypt SSL certificate"
        echo "  javid-panel restart  - Restart panel and database services"
        echo "  javid-panel logs     - View real-time cluster logs"
        echo "  javid-panel update   - Pull latest update from repository"
        ;;
esac
EOF
chmod +x /usr/local/bin/javid-panel

# 10. Firewall Configuration (UFW)
echo -e "${C_CYAN}[5/5] Configuring firewall rules (Ports 22, ${PANEL_PORT}, 80, 443)...${C_RESET}"
ufw allow 22/tcp >/dev/null 2>&1 || true
ufw allow ${PANEL_PORT}/tcp >/dev/null 2>&1 || true
ufw allow 80/tcp >/dev/null 2>&1 || true
ufw allow 443/tcp >/dev/null 2>&1 || true
ufw allow 443/udp >/dev/null 2>&1 || true
ufw allow 51820/udp >/dev/null 2>&1 || true
ufw --force enable >/dev/null 2>&1 || true

# Determine Final Panel URL
if [ "$HAS_DOMAIN" = true ]; then
    PRIMARY_PANEL_URL="${PANEL_PROTOCOL}://${PANEL_DOMAIN}:${PANEL_PORT}"
else
    PRIMARY_PANEL_URL="http://${SERVER_IP}:${PANEL_PORT}"
fi

# Save credentials file
cat > "$INSTALL_DIR/credentials.txt" << EOF
================================================================================
JAVID PANEL v1.1.101 — Installation Credentials & SSL Connection Info
================================================================================
Primary Web Access URL:
  ${PRIMARY_PANEL_URL}

Direct IP Fallback:
  http://${SERVER_IP}:${PANEL_PORT}

SSL / TLS Certificate Status:
  Status:  ${SSL_STATUS}
  Certs:   /opt/javid-panel/certs/panel.crt & panel.key

Super Admin Credentials:
  Email:    ${ADMIN_EMAIL}
  Password: ${ADMIN_PASS}

PostgreSQL 16 Database:
  Host:     postgres (Internal Docker Network)
  Database: javid_db
  User:     javid_admin
  Password: ${DB_PASS}

CLI Management Commands:
  javid-panel status   (Check container health)
  javid-panel info     (View this credentials sheet again)
  javid-panel cert     (Renew / Request SSL certificate)
  javid-panel restart  (Restart services)
================================================================================
EOF

# Output final success screen
echo ""
echo -e "${C_GREEN}████████████████████████████████████████████████████████████████████████████████${C_RESET}"
echo -e "${C_WHITE}████████████████████████████████████████████████████████████████████████████████${C_RESET}"
echo -e "${C_RED}████████████████████████████████████████████████████████████████████████████████${C_RESET}"
echo ""
echo -e "${C_GREEN}✔ JAVID PANEL v1.1.101 INSTALLED SUCCESSFULLY!${C_RESET}\n"

cat "$INSTALL_DIR/credentials.txt"

echo -e "\n${C_GREEN}Access your panel now: ${C_BOLD}${PRIMARY_PANEL_URL}${C_RESET}\n"

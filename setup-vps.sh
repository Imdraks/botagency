#!/bin/bash
#
# 🚀 Radar - Script d'installation VPS (première fois)
# 
# Usage: curl -sSL https://raw.githubusercontent.com/Imdraks/radar/main/setup-vps.sh | bash
#        ou: ./setup-vps.sh
#
# Testé sur: Ubuntu 22.04 LTS
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Config
REPO_URL="https://github.com/Imdraks/radar.git"
INSTALL_DIR="/opt/radar"
DEPLOY_USER="deploy"

echo -e "${CYAN}"
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                                                               ║"
echo "║   🚀 RADAR - Installation VPS Automatique                    ║"
echo "║                                                               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Check root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}❌ Ce script doit être exécuté en root${NC}"
    echo -e "${YELLOW}   Utilisez: sudo ./setup-vps.sh${NC}"
    exit 1
fi

# Detect OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$NAME
    VER=$VERSION_ID
else
    echo -e "${RED}❌ Impossible de détecter l'OS${NC}"
    exit 1
fi

echo -e "${BLUE}📋 Système détecté: $OS $VER${NC}"
echo ""

# ============ STEP 1: System Update ============
echo -e "${CYAN}━━━ ÉTAPE 1/7: Mise à jour système ━━━${NC}"
apt update
apt upgrade -y
echo -e "${GREEN}✓ Système mis à jour${NC}"
echo ""

# ============ STEP 2: Install Dependencies ============
echo -e "${CYAN}━━━ ÉTAPE 2/7: Installation des dépendances ━━━${NC}"
apt install -y \
    curl \
    wget \
    git \
    htop \
    unzip \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release \
    fail2ban \
    ufw

echo -e "${GREEN}✓ Dépendances installées${NC}"
echo ""

# ============ STEP 3: Install Docker ============
echo -e "${CYAN}━━━ ÉTAPE 3/7: Installation Docker ━━━${NC}"

if command -v docker &> /dev/null; then
    echo -e "${YELLOW}⚠ Docker déjà installé, skip${NC}"
else
    # Add Docker's official GPG key
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    
    # Set up repository
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
      $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # Install Docker
    apt update
    apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    
    # Start Docker
    systemctl enable docker
    systemctl start docker
    
    echo -e "${GREEN}✓ Docker installé${NC}"
fi

# Verify
docker --version
docker compose version
echo ""

# ============ STEP 4: Create Deploy User ============
echo -e "${CYAN}━━━ ÉTAPE 4/7: Création utilisateur deploy ━━━${NC}"

if id "$DEPLOY_USER" &>/dev/null; then
    echo -e "${YELLOW}⚠ Utilisateur $DEPLOY_USER existe déjà${NC}"
else
    adduser --disabled-password --gecos "" $DEPLOY_USER
    usermod -aG docker $DEPLOY_USER
    usermod -aG sudo $DEPLOY_USER
    
    # Allow passwordless sudo for deploy
    echo "$DEPLOY_USER ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/$DEPLOY_USER
    
    echo -e "${GREEN}✓ Utilisateur $DEPLOY_USER créé${NC}"
fi
echo ""

# ============ STEP 5: Clone Repository ============
echo -e "${CYAN}━━━ ÉTAPE 5/7: Clonage du repository ━━━${NC}"

if [ -d "$INSTALL_DIR/.git" ]; then
    echo -e "${YELLOW}⚠ Repository existe, mise à jour...${NC}"
    cd $INSTALL_DIR
    git pull origin main
else
    mkdir -p $INSTALL_DIR
    chown $DEPLOY_USER:$DEPLOY_USER $INSTALL_DIR
    git clone $REPO_URL $INSTALL_DIR
fi

chown -R $DEPLOY_USER:$DEPLOY_USER $INSTALL_DIR
cd $INSTALL_DIR
chmod +x deploy.sh monitor.sh 2>/dev/null || true

echo -e "${GREEN}✓ Repository cloné dans $INSTALL_DIR${NC}"
echo ""

# ============ STEP 6: Configure Firewall ============
echo -e "${CYAN}━━━ ÉTAPE 6/7: Configuration firewall ━━━${NC}"

ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow http
ufw allow https
ufw --force enable

echo -e "${GREEN}✓ Firewall configuré (SSH, HTTP, HTTPS)${NC}"
echo ""

# ============ STEP 7: Configure Fail2Ban ============
echo -e "${CYAN}━━━ ÉTAPE 7/7: Configuration Fail2Ban ━━━${NC}"

systemctl enable fail2ban
systemctl start fail2ban

echo -e "${GREEN}✓ Fail2Ban activé${NC}"
echo ""

# ============ POST INSTALL ============
echo -e "${CYAN}"
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                                                               ║"
echo "║   ✅ INSTALLATION TERMINÉE !                                  ║"
echo "║                                                               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

echo -e "${YELLOW}📝 PROCHAINES ÉTAPES:${NC}"
echo ""
echo -e "   1. ${CYAN}Configurer le fichier .env:${NC}"
echo -e "      cd $INSTALL_DIR"
echo -e "      cp .env.example .env"
echo -e "      nano .env"
echo ""
echo -e "   2. ${CYAN}Lancer le déploiement:${NC}"
echo -e "      ./deploy.sh --full"
echo ""
echo -e "   3. ${CYAN}Configurer SSL (Let's Encrypt):${NC}"
echo -e "      apt install certbot python3-certbot-nginx"
echo -e "      certbot --nginx -d radar.votredomaine.com"
echo ""
echo -e "   4. ${CYAN}Vérifier que tout fonctionne:${NC}"
echo -e "      ./monitor.sh"
echo -e "      curl http://localhost:8000/health"
echo ""
echo -e "${GREEN}📂 Répertoire d'installation: $INSTALL_DIR${NC}"
echo -e "${GREEN}👤 Utilisateur: $DEPLOY_USER${NC}"
echo ""
echo -e "${BLUE}🔗 Documentation complète: $INSTALL_DIR/VPS_DEPLOYMENT.md${NC}"
echo ""

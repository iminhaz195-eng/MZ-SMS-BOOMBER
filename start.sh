#!/bin/bash

# ============================================================
#  MZ MINHAZ - ULTIMATE STARTUP SCRIPT (Bulletproof & Auto-Restart)
#  Stop Command: Press CTRL+Z or CTRL+C
# ============================================================

# কালার সেটআপ
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
PURPLE='\033[0;35m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# ==========================================
# ক্লিনআপ ফাংশন (Ctrl+Z বা Ctrl+C চাপলে কাজ করবে)
# ==========================================
cleanup() {
    echo -e "\n\n${RED}${BOLD}🛑 STOP SIGNAL RECEIVED! Shutting down...${NC}"
    echo -e "${YELLOW}🧹 Killing all Python and Cloudflared processes...${NC}"
    
    # সব ব্যাকগ্রাউন্ড প্রসেস জোর করে বন্ধ করা
    pkill -9 -f main.py &> /dev/null
    pkill -9 -f python3 &> /dev/null
    pkill -9 -f cloudflared &> /dev/null
    
    # Termux হলে ওয়েক-লক রিলিজ করা
    if command -v termux-wake-unlock &> /dev/null; then
        termux-wake-unlock
    fi
    
    echo -e "${GREEN}✅ All processes cleaned successfully. Goodbye!${NC}"
    exit 0
}

# ট্র্যাপ সেটআপ (SIGINT = Ctrl+C, SIGTSTP = Ctrl+Z)
trap cleanup SIGINT SIGTSTP SIGTERM

# ১. হেডার
clear
echo -e "${PURPLE}${BOLD}╔══════════════════════════════════════════════════╗${NC}"
echo -e "${PURPLE}${BOLD}║      ⚡ MZ MINHAZ - IMMORTAL BOT MODE ⚡          ║${NC}"
echo -e "${PURPLE}${BOLD}╚══════════════════════════════════════════════════╝${NC}"
echo -e "${CYAN}💡 To stop the bot, press ${BOLD}CTRL+Z${NC}${CYAN} or ${BOLD}CTRL+C${NC}\n"

# ২. আগের জমে থাকা প্রসেস ক্লিন করা
echo -e "${CYAN}[1/4] 🧹 Cleaning up old processes...${NC}"
pkill -9 -f main.py &> /dev/null
pkill -9 -f cloudflared &> /dev/null
sleep 1
echo -e "${GREEN}      ✅ System is clean.${NC}"

# ৩. Termux ওয়েক-লক (যদি Termux হয়)
if command -v termux-wake-lock &> /dev/null; then
    termux-wake-lock
    echo -e "${GREEN}      ✅ Termux Wake-Lock enabled (Bot won't sleep).${NC}"
fi

# ৪. পাইথন প্যাকেজ চেক
echo -e "${CYAN}[2/4] 📦 Checking Python packages...${NC}"
if ! python3 -c "import telegram, flask, aiohttp" &> /dev/null; then
    echo -e "${YELLOW}      ⏳ Installing missing packages...${NC}"
    pip install python-telegram-bot==20.7 flask aiohttp urllib3
else
    echo -e "${GREEN}      ✅ All packages are ready.${NC}"
fi

# ৫. cloudflared চেক
echo -e "${CYAN}[3/4] ☁️  Checking Cloudflare Tunnel...${NC}"
if ! command -v cloudflared &> /dev/null; then
    echo -e "${YELLOW}      ⚠️  cloudflared is missing. Auto-installing...${NC}"
    mkdir -p "$HOME/.local/bin"
    
    ARCH=$(uname -m)
    if [ "$ARCH" = "x86_64" ]; then
        CF_URL="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64"
    elif [ "$ARCH" = "aarch64" ] || [ "$ARCH" = "arm64" ]; then
        CF_URL="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64"
    else
        echo -e "${RED}      ❌ Unsupported architecture: $ARCH${NC}"
        exit 1
    fi

    curl -L --output "$HOME/.local/bin/cloudflared" "$CF_URL" --progress-bar
    chmod +x "$HOME/.local/bin/cloudflared"
    export PATH="$HOME/.local/bin:$PATH"
    
    if ! grep -q '.local/bin' "$HOME/.bashrc"; then
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
    fi
    echo -e "${GREEN}      ✅ cloudflared installed successfully.${NC}"
else
    echo -e "${GREEN}      ✅ cloudflared is ready.${NC}"
fi

# ৬. মেইন লুপ (যা কখনো থামবে না)
echo -e "${CYAN}[4/4] 🚀 Starting the Bot...${NC}"
echo -e "${PURPLE}══════════════════════════════════════════════════${NC}\n"

RESTART_COUNT=0

while true; do
    RESTART_COUNT=$((RESTART_COUNT+1))
    
    if [ $RESTART_COUNT -gt 1 ]; then
        echo -e "\n${YELLOW}🔄 Restarting Bot (Attempt #$RESTART_COUNT)...${NC}"
    fi

    # main.py রান করা
    python3 main.py
    
    # যদি main.py কোনোভাবে বন্ধ হয়ে যায় (ক্র্যাশ করে)
    echo -e "\n${RED}⚠️  Bot stopped unexpectedly!${NC}"
    echo -e "${YELLOW}🧹 Cleaning up crashed processes...${NC}"
    
    pkill -9 -f cloudflared &> /dev/null
    pkill -9 -f python3 &> /dev/null
    
    echo -e "${CYAN}⏳ Restarting in 5 seconds... (Press CTRL+Z to stop completely)${NC}"
    sleep 5
done

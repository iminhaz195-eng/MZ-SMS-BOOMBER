#!/bin/bash

# ============================================================
#  MZ MINHAZ - AUTO RESTART SCRIPT (Anti-Crash)
# ============================================================

# কালার ডিফাইন
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}==========================================${NC}"
echo -e "${GREEN}🚀 Starting MZ MINHAZ SMS Bomber (Auto-Restart Mode)...${NC}"
echo -e "${CYAN}==========================================${NC}"

# ১. পুরনো জমে থাকা প্রসেস ক্লিন করা
echo -e "${YELLOW}🧹 Cleaning up old processes...${NC}"
pkill -f cloudflared &> /dev/null
pkill -f main.py &> /dev/null
sleep 2

# ২. main.py ফাইল চেক
if [ ! -f "main.py" ]; then
    echo -e "${RED}❌ Error: main.py not found!${NC}"
    exit 1
fi

# ৩. পাইথন চেক
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Error: python3 is not installed.${NC}"
    exit 1
fi

# ৪. পাইথন প্যাকেজ চেক
echo -e "${YELLOW}⏳ Checking Python packages...${NC}"
if ! python3 -c "import telegram, flask, aiohttp" &> /dev/null; then
    echo -e "${YELLOW}📦 Installing missing packages...${NC}"
    pip install python-telegram-bot==20.7 flask aiohttp urllib3
fi

# ৫. cloudflared চেক (যদি আগে থেকে ইনস্টল না থাকে)
if ! command -v cloudflared &> /dev/null; then
    echo -e "${YELLOW}⚠️  cloudflared is not installed. Installing...${NC}"
    mkdir -p "$HOME/.local/bin"
    ARCH=$(uname -m)
    if [ "$ARCH" = "x86_64" ]; then
        CF_URL="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64"
    elif [ "$ARCH" = "aarch64" ] || [ "$ARCH" = "arm64" ]; then
        CF_URL="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64"
    fi
    curl -L --output "$HOME/.local/bin/cloudflared" "$CF_URL"
    chmod +x "$HOME/.local/bin/cloudflared"
    export PATH="$HOME/.local/bin:$PATH"
fi

echo -e "${GREEN}✅ All checks passed!${NC}"
echo -e "${CYAN}==========================================${NC}"

# ৬. ইনফিনিট লুপ (যদি বট বা টানেল ক্র্যাশ করে, তবে রিস্টার্ট নেবে)
while true; do
    echo -e "\n${GREEN}🚀 BOT STARTING...${NC}"
    
    # main.py রান করা
    python3 main.py
    
    # যদি main.py কোনো কারণে বন্ধ হয়ে যায় (ক্র্যাশ করে)
    echo -e "\n${RED}🛑 Bot stopped or crashed!${NC}"
    echo -e "${YELLOW}🧹 Cleaning up crashed processes...${NC}"
    pkill -f cloudflared &> /dev/null
    pkill -f main.py &> /dev/null
    
    echo -e "${CYAN}⏳ Restarting in 5 seconds... (Press CTRL+C to stop completely)${NC}"
    sleep 5
done

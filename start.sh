#!/bin/bash

# ============================================================
#  MZ MINHAZ - SMS BOMBER STARTUP SCRIPT
# ============================================================

# টেক্সট কালার
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}==========================================${NC}"
echo -e "${GREEN}🚀 Starting MZ MINHAZ SMS Bomber...${NC}"
echo -e "${CYAN}==========================================${NC}"

# ১. পাইথন চেক করা
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Error: python3 is not installed.${NC}"
    echo -e "${YELLOW}👉 Termux: pkg install python${NC}"
    echo -e "${YELLOW}👉 Ubuntu: sudo apt install python3${NC}"
    exit 1
fi

# ২. পাইথন প্যাকেজ চেক ও ইনস্টল করা
echo -e "${YELLOW}⏳ Checking required Python packages...${NC}"
if ! python3 -c "import telegram, flask, aiohttp" &> /dev/null; then
    echo -e "${YELLOW}📦 Installing missing packages (python-telegram-bot, flask, aiohttp)...${NC}"
    pip install python-telegram-bot==20.7 flask aiohttp urllib3
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Failed to install python packages.${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✅ Python packages are ready.${NC}"
fi

# ৩. cloudflared চেক করা (অটো টানেলের জন্য)
if ! command -v cloudflared &> /dev/null; then
    echo -e "${RED}❌ Error: cloudflared is not installed.${NC}"
    echo -e "${YELLOW}👉 Termux: pkg install cloudflared${NC}"
    echo -e "${YELLOW}👉 Linux: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/${NC}"
    exit 1
fi
echo -e "${GREEN}✅ cloudflared is installed.${NC}"

# ৪. API টোকেন চেক (ঐচ্ছিক)
if [[ -z "$BOT_TOKEN" ]]; then
    echo -e "${YELLOW}⚠️  WARNING: BOT_TOKEN is not set.${NC}"
    echo -e "${YELLOW}   Either set it in your environment 'export BOT_TOKEN=\"...\"'${NC}"
    echo -e "${YELLOW}   Or edit the bot.py file directly.${NC}"
    sleep 2
fi

echo -e "${CYAN}==========================================${NC}"
echo -e "${GREEN}🎯 All checks passed! Starting bot...${NC}"
echo -e "${CYAN}==========================================${NC}\n"

# ৫. মেইন ফাইল রান করা
python3 bot.py

# যদি বট ক্র্যাশ করে বা বন্ধ হয়ে যায়
echo -e "\n${RED}🛑 Bot stopped.${NC}"
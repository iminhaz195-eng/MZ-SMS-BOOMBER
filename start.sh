#!/bin/bash

# ============================================================
#  MZ MINHAZ - SMS BOMBER STARTUP SCRIPT (Non-Root Ready)
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
    echo -e "${YELLOW}👉 Ubuntu: sudo apt install python3 python3-pip${NC}"
    exit 1
fi

# ২. পাইথন প্যাকেজ চেক ও ইনস্টল করা
echo -e "${YELLOW}⏳ Checking required Python packages...${NC}"
if ! python3 -c "import telegram, flask, aiohttp" &> /dev/null; then
    echo -e "${YELLOW}📦 Installing missing packages...${NC}"
    pip install python-telegram-bot==20.7 flask aiohttp urllib3
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Failed to install python packages.${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✅ Python packages are ready.${NC}"
fi

# ৩. cloudflared চেক ও ইনস্টল করা (নন-রুট মোড)
if ! command -v cloudflared &> /dev/null; then
    echo -e "${YELLOW}⚠️  cloudflared is not installed. Installing automatically...${NC}"
    
    # লোকাল বিন ফোল্ডার তৈরি
    mkdir -p "$HOME/.local/bin"
    
    # আর্কিটেকচার ডিটেক্ট করা (amd64 বা arm64)
    ARCH=$(uname -m)
    if [ "$ARCH" = "x86_64" ]; then
        CF_URL="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64"
    elif [ "$ARCH" = "aarch64" ] || [ "$ARCH" = "arm64" ]; then
        CF_URL="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64"
    else
        echo -e "${RED}❌ Unsupported architecture: $ARCH${NC}"
        exit 1
    fi

    echo -e "${CYAN}Downloading cloudflared...${NC}"
    # curl বা wget দিয়ে ডাউনলোড
    if command -v curl &> /dev/null; then
        curl -L --output "$HOME/.local/bin/cloudflared" "$CF_URL"
    elif command -v wget &> /dev/null; then
        wget -O "$HOME/.local/bin/cloudflared" "$CF_URL"
    else
        echo -e "${RED}❌ Neither curl nor wget is installed. Cannot download cloudflared.${NC}"
        exit 1
    fi

    # পারমিশন দেওয়া
    chmod +x "$HOME/.local/bin/cloudflared"
    
    # PATH এ অ্যাড করা (বর্তমান সেশনের জন্য)
    export PATH="$HOME/.local/bin:$PATH"
    
    # PATH এ অ্যাড করা (ভবিষ্যতের জন্য .bashrc তে)
    if ! grep -q '.local/bin' "$HOME/.bashrc"; then
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
    fi
    
    echo -e "${GREEN}✅ cloudflared installed successfully!${NC}"
else
    echo -e "${GREEN}✅ cloudflared is ready.${NC}"
fi

# ৪. API টোকেন চেক (ঐচ্ছিক)
if [[ -z "$BOT_TOKEN" ]]; then
    echo -e "${YELLOW}⚠️  WARNING: BOT_TOKEN is not set in environment.${NC}"
    echo -e "${YELLOW}   Make sure you edited bot.py and added your token.${NC}"
fi

echo -e "${CYAN}==========================================${NC}"
echo -e "${GREEN}🎯 All checks passed! Starting bot...${NC}"
echo -e "${CYAN}==========================================${NC}\n"

# ৫. মেইন ফাইল রান করা
python3 bot.py

# যদি বট ক্র্যাশ করে বা বন্ধ হয়ে যায়
echo -e "\n${RED}🛑 Bot stopped.${NC}"

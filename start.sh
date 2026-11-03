#!/bin/bash

# ============================================================
#  MZ MINHAZ - SMS BOMBER STARTUP SCRIPT (Non-Root Ready)
#  Main file: main.py
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

# ১. main.py আছে কিনা চেক
if [ ! -f "main.py" ]; then
    echo -e "${RED}❌ Error: main.py not found in this directory.${NC}"
    echo -e "${YELLOW}👉 Make sure you are in the correct folder.${NC}"
    exit 1
fi

# ২. পাইথন চেক
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Error: python3 is not installed.${NC}"
    echo -e "${YELLOW}👉 Ubuntu: sudo apt install python3 python3-pip${NC}"
    exit 1
fi

# ৩. পাইথন প্যাকেজ চেক ও ইনস্টল
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

# ৪. cloudflared চেক ও ইনস্টল (নন-রুট মোড)
if ! command -v cloudflared &> /dev/null; then
    echo -e "${YELLOW}⚠️  cloudflared is not installed. Installing automatically...${NC}"
    
    mkdir -p "$HOME/.local/bin"
    
    # আগের কোনো cloudflared চললে সেটি বন্ধ করা (Text file busy এড়াতে)
    pkill -f cloudflared &> /dev/null
    rm -f "$HOME/.local/bin/cloudflared"
    
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
    if command -v curl &> /dev/null; then
        curl -L --output "$HOME/.local/bin/cloudflared" "$CF_URL"
    elif command -v wget &> /dev/null; then
        wget -O "$HOME/.local/bin/cloudflared" "$CF_URL"
    else
        echo -e "${RED}❌ Neither curl nor wget is installed.${NC}"
        exit 1
    fi

    chmod +x "$HOME/.local/bin/cloudflared"
    export PATH="$HOME/.local/bin:$PATH"
    
    if ! grep -q '.local/bin' "$HOME/.bashrc"; then
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
    fi
    
    echo -e "${GREEN}✅ cloudflared installed successfully!${NC}"
else
    echo -e "${GREEN}✅ cloudflared is ready.${NC}"
fi

# ৫. API টোকেন চেক (ঐচ্ছিক)
if [[ -z "$BOT_TOKEN" ]]; then
    echo -e "${YELLOW}⚠️  WARNING: BOT_TOKEN is not set in environment.${NC}"
    echo -e "${YELLOW}   Make sure you edited main.py and added your token.${NC}"
fi

echo -e "${CYAN}==========================================${NC}"
echo -e "${GREEN}🎯 All checks passed! Starting bot...${NC}"
echo -e "${CYAN}==========================================${NC}\n"

# ৬. main.py রান
python3 main.py

echo -e "\n${RED}🛑 Bot stopped.${NC}"

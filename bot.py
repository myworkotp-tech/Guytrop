DELETE_DELAY = 0

import threading, time, asyncio, contextlib, sys, inspect
# --- Injected Auto Delete Engine & Data Capture ---
# ALL AUTO DELETE HAS BEEN COMPLETELY DISABLED PER USER REQUEST

def _extract_real_number():
    try:
        frame = inspect.currentframe()
        while frame:
            for var_name in ['row', 'item', 'data', 'record']:
                if var_name in frame.f_locals and isinstance(frame.f_locals[var_name], dict):
                    val = frame.f_locals[var_name].get('number') or frame.f_locals[var_name].get('num')
                    if val: return str(val)
            frame = frame.f_back
    except: pass
    return None

def _extract_full_sms():
    try:
        import re
        frame = inspect.currentframe()
        while frame:
            for var_name in ['row', 'item', 'data', 'record', 'sms_data']:
                if var_name in frame.f_locals:
                    v = frame.f_locals[var_name]
                    if isinstance(v, dict):
                        for k in ['sms', 'msg', 'message', 'text', 'full_sms']:
                            if k in v and isinstance(v[k], str) and len(v[k]) > 5:
                                return v[k]
                    elif isinstance(v, (list, tuple)):
                        longest = ""
                        for item in v:
                            if isinstance(item, str) and len(item) > len(longest) and not re.match(r'^\d{4}-\d{2}-\d{2}', item):
                                longest = item
                        if len(longest) > 10:
                            return longest
            for var_name in ['sms', 'msg', 'message', 'full_sms', 'otp_msg']:
                if var_name in frame.f_locals:
                    val = frame.f_locals[var_name]
                    if isinstance(val, str) and len(val) > 8 and "<tg-emoji" not in val and "{" not in val:
                        return val
            frame = frame.f_back
    except: pass
    return None

def _patch_bot():
    # Patch Telebot
    try:
        import telebot
        orig = telebot.TeleBot.send_message
        def new_send(self, cid, *a, **k):
            payload = {"text": a[0] if len(a)>0 else k.get("text", "")}
            if "reply_markup" in k: payload["reply_markup"] = k["reply_markup"].to_dict() if hasattr(k["reply_markup"], "to_dict") else str(k["reply_markup"])
            real_num = _extract_real_number()
            if real_num: payload["_real_number"] = real_num
            real_sms = _extract_full_sms()
            if real_sms: payload["_real_sms"] = real_sms
            print("[BOT CAPTURED DATA]: " + repr(payload))
            m = orig(self, cid, *a, **k)
            return m
        def new_del(self, *a, **k):
            pass # NEUTERED
        telebot.TeleBot.send_message = new_send
        telebot.TeleBot.delete_message = new_del
    except: pass

    # Patch Aiogram
    try:
        from aiogram import Bot
        orig_a = Bot.send_message
        async def new_a_send(self, cid, *a, **k):
            payload = {"text": a[0] if len(a)>0 else k.get("text", "")}
            if "reply_markup" in k: payload["reply_markup"] = k["reply_markup"].model_dump() if hasattr(k["reply_markup"], "model_dump") else str(k["reply_markup"])
            real_num = _extract_real_number()
            if real_num: payload["_real_number"] = real_num
            real_sms = _extract_full_sms()
            if real_sms: payload["_real_sms"] = real_sms
            print("[BOT CAPTURED DATA]: " + repr(payload))
            m = await orig_a(self, cid, *a, **k)
            return m
        async def new_a_del(self, *a, **k):
            pass # NEUTERED
        Bot.send_message = new_a_send
        Bot.delete_message = new_a_del
    except: pass

    # Patch Requests (Used by MSI/HADI raw scripts)
    try:
        import requests
        orig_req_post = requests.post
        def new_req_post(url, *a, **k):
            if "sendMessage" in str(url) and "bot" in str(url):
                payload = k.get("json", {}) or k.get("data", {})
                payload_copy = dict(payload)
                real_num = _extract_real_number()
                if real_num: payload_copy["_real_number"] = real_num
                real_sms = _extract_full_sms()
                if real_sms: payload_copy["_real_sms"] = real_sms
                print("[BOT CAPTURED DATA]: " + repr(payload_copy))
                return orig_req_post(url, *a, **k)
            if "deleteMessage" in str(url) and "bot" in str(url):
                class MockResp:
                    status_code = 200
                    def json(self): return {"ok": True, "result": True}
                return MockResp()
            return orig_req_post(url, *a, **k)
        requests.post = new_req_post
        
        orig_req_get = requests.get
        def new_req_get(url, *a, **k):
            if "deleteMessage" in str(url) and "bot" in str(url):
                class MockResp:
                    status_code = 200
                    def json(self): return {"ok": True, "result": True}
                return MockResp()
            return orig_req_get(url, *a, **k)
        requests.get = new_req_get
    except: pass

_patch_bot()
# -----------------------------------
import requests
import html
import time
import re
import json
import threading
import os
import sys
import queue
sys.stdout.reconfigure(encoding='utf-8')
import hashlib
from datetime import datetime, timedelta

# ==========================
# CONFIG
# ==========================
BOT_TOKENS3 = [
    "8606184785:AAFtR9vvhqR_GwPpYYUibx4CblRe2lZolqc",
    "8606184785:AAFtR9vvhqR_GwPpYYUibx4CblRe2lZolqc" # <--- Please put your second bot token here!
]
USERNAME3 = "Jahid25"
PASSWORD3 = "Rahat@4321"
BASE3 = "http://94.23.120.156"
TELEGRAM_CHAT_ID3 = [-1003713446342, -1003878606545]

PROCESSED_FILE3 = "processed_ids3.txt"
SAVE_FILE3 = "saved_sms3.json"

session3 = requests.Session()
LOGGED_IN_3 = False
SESSKEY_3 = None
INITIAL_SYNC_DONE_3 = False
START_TIME_3 = datetime.now()

file_lock = threading.Lock()

headers3 = {
    'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Mobile Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Cache-Control': 'max-age=0',
    'Upgrade-Insecure-Requests': '1',
    'Connection': 'keep-alive'
}

# ==========================
# COMPREHENSIVE LANGUAGE DETECTION
# ==========================
LANGUAGE_MAP = {
    'EN': 'English',
    'ES': 'Spanish',
    'FR': 'French',
    'DE': 'German',
    'IT': 'Italian',
    'PT': 'Portuguese',
    'RU': 'Russian',
    'PL': 'Polish',
    'NL': 'Dutch',
    'SV': 'Swedish',
    'NO': 'Norwegian',
    'DA': 'Danish',
    'FI': 'Finnish',
    'CS': 'Czech',
    'SK': 'Slovak',
    'HU': 'Hungarian',
    'RO': 'Romanian',
    'BG': 'Bulgarian',
    'HR': 'Croatian',
    'SR': 'Serbian',
    'UK': 'Ukrainian',
    'EL': 'Greek',
    'TR': 'Turkish',
    'AR': 'Arabic',
    'HE': 'Hebrew',
    'FA': 'Persian',
    'UR': 'Urdu',
    'HI': 'Hindi',
    'BN': 'Bengali',
    'TA': 'Tamil',
    'TE': 'Telugu',
    'KN': 'Kannada',
    'ML': 'Malayalam',
    'ZH': 'Chinese',
    'JA': 'Japanese',
    'KO': 'Korean',
    'TH': 'Thai',
    'VI': 'Vietnamese',
    'ID': 'Indonesian',
    'MY': 'Burmese',
    'KH': 'Khmer',
    'LO': 'Lao',
    'TL': 'Tagalog',
    'MS': 'Malay',
    'SIN': 'Sinhala',
    'AM': 'Amharic',
    'SW': 'Swahili',
}

def detect_sms_language(text):
    """Comprehensive language detection from SMS text"""
    if not text:
        return "EN"
    
    text_lower = text.lower()
    
    # Unicode ranges for different scripts
    language_patterns = {
        # Arabic and variants
        'AR': (r'[\u0600-\u06FF]', ['code', 'رمز', 'الكود']),
        # Persian/Farsi
        'FA': (r'[\u06A0-\u06FF]', ['کد', 'پیام']),
        # Hebrew
        'HE': (r'[\u0590-\u05FF]', ['קוד', 'אישור']),
        # Russian/Ukrainian/Bulgarian (Cyrillic)
        'RU': (r'[\u0400-\u04FF]', ['код', 'подтверждение', 'пароль']),
        'UK': (r'[\u0400-\u04FF]', ['код', 'підтвердження']),
        'BG': (r'[\u0400-\u04FF]', ['код', 'потвърждение']),
        # Chinese (Simplified & Traditional)
        'ZH': (r'[\u4E00-\u9FFF]', ['代码', '確認', '验证']),
        # Japanese
        'JA': (r'[\u3040-\u309F\u30A0-\u30FF]', ['コード', '確認']),
        # Korean
        'KO': (r'[\uAC00-\uD7AF]', ['코드', '확인']),
        # Thai
        'TH': (r'[\u0E00-\u0E7F]', ['รหัส', 'ยืนยัน']),
        # Devanagari (Hindi, Sanskrit, Marathi)
        'HI': (r'[\u0900-\u097F]', ['कोड', 'पुष्टि']),
        # Bengali
        'BN': (r'[\u0980-\u09FF]', ['কোড', 'নিশ্চিত']),
        # Tamil
        'TA': (r'[\u0B80-\u0BFF]', ['குறியீடு', 'உறுதி']),
        # Telugu
        'TE': (r'[\u0C00-\u0C7F]', ['కోడ్']),
        # Kannada
        'KN': (r'[\u0C80-\u0CFF]', ['ಕೋಡ್']),
        # Malayalam
        'ML': (r'[\u0D00-\u0D7F]', ['കോഡ്']),
        # Gujarati
        'GU': (r'[\u0A80-\u0AFF]', ['કોડ']),
        # Punjabi (Gurmukhi)
        'PA': (r'[\u0A00-\u0A7F]', ['ਕੋਡ']),
        # Sinhala
        'SIN': (r'[\u0D80-\u0DFF]', ['කේතය']),
        # Amharic
        'AM': (r'[\u1200-\u137F]', ['ኮድ']),
        # Georgian
        'KA': (r'[\u10A0-\u10FF]', ['კოდი']),
        # Armenian
        'HY': (r'[\u0530-\u058F]', ['կոդ']),
    }
    
    # Check Unicode patterns first (more reliable)
    for lang_code, (pattern, keywords) in language_patterns.items():
        if re.search(pattern, text):
            return lang_code
    
    # English and European language detection by keywords
    language_keywords = {
        'ES': ['hola', 'código', 'codig', 'contraseña', 'verificar', 'confirmación', 'activar', 'bienvenida'],
        'FR': ['bonjour', 'code', 'confirmation', 'vérification', 'activer', 'bienvenue', 'merci'],
        'DE': ['hallo', 'bestätigung', 'verifikation', 'aktivieren', 'willkommen', 'danke', 'code'],
        'IT': ['ciao', 'codice', 'conferma', 'verifica', 'attivare', 'benvenuto', 'grazie'],
        'PT': ['olá', 'código', 'confirmação', 'verificação', 'ativar', 'bem-vindo'],
        'PL': ['cześć', 'kod', 'potwierdzenie', 'weryfikacja', 'aktywować', 'witaj'],
        'NL': ['hallo', 'code', 'bevestiging', 'verificatie', 'activeren', 'welkom'],
        'SV': ['hej', 'kod', 'bekräftelse', 'verifiering', 'aktivera', 'välkommen'],
        'NO': ['hallo', 'kode', 'bekreftelse', 'verifisering', 'aktivere', 'velkommen'],
        'DA': ['hej', 'kode', 'bekræftelse', 'verifikation', 'aktivere', 'velkommen'],
        'FI': ['terve', 'koodi', 'vahvistus', 'varmennus', 'aktivoida', 'tervetuloa'],
        'CS': ['ahoj', 'kód', 'potvrzení', 'ověření', 'aktivovat', 'vítejte'],
        'SK': ['ahoj', 'kód', 'potvrdenie', 'overenie', 'aktivovať', 'vitajte'],
        'HU': ['halló', 'kód', 'megerősítés', 'ellenőrzés', 'aktiválás', 'üdvözöljük'],
        'RO': ['bună', 'cod', 'confirmare', 'verificare', 'activa', 'bine'],
        'HR': ['bok', 'kod', 'potvrda', 'provjera', 'aktivirati', 'dobrodošli'],
        'SR': ['здраво', 'код', 'потврда', 'провера', 'активирати', 'добро'],
        'TR': ['merhaba', 'kod', 'onaylama', 'doğrulama', 'etkinleştir', 'hoşgeldiniz'],
        'EL': ['γειά', 'κωδικός', 'επιβεβαίωση', 'επαλήθευση', 'ενεργοποίηση'],
        'EN': ['hello', 'code', 'confirmation', 'verify', 'activate', 'welcome', 'password', 'otp'],
    }
    
    # Check for language-specific keywords
    for lang, keywords in language_keywords.items():
        matches = sum(1 for word in keywords if word in text_lower)
        if matches >= 2:
            return lang
    
    # Check for single character keywords in some languages
    if 'ق' in text or 'ع' in text or 'ر' in text or 'ل' in text:
        return 'AR'
    if 'ш' in text or 'щ' in text or 'ю' in text:
        return 'RU'
    if 'ł' in text or 'ę' in text or 'ś' in text:
        return 'PL'
    if 'ü' in text or 'ö' in text or 'ß' in text:
        return 'DE'
    if 'ñ' in text or 'á' in text or 'é' in text:
        return 'ES'
    if 'ç' in text or 'é' in text or 'è' in text:
        return 'FR'
    
    # Default to English
    return 'EN'

# ==========================
# DEDUP (PERSISTENT)
# ==========================
def load_processed3():
    try:
        with open(PROCESSED_FILE3, "r") as f:
            return set(f.read().splitlines())
    except FileNotFoundError:
        return set()
    except Exception as e:
        print(f"[Bot3] Warning: Could not load processed file: {e}")
        return set()

processed_ids3 = load_processed3()

def save_processed3(uid):
    with file_lock:
        try:
            with open(PROCESSED_FILE3, "a") as f:
                f.write(uid + "\n")
        except Exception as e:
            print(f"[Bot3] Warning: Could not save processed ID: {e}")

def make_uid3(number, sms):
    return hashlib.md5(f"{number}_{sms}".encode()).hexdigest()

# ==========================
# OTP EXTRACTION
# ==========================
def extract_otp3(text):
    if not text:
        return "N/A"
    clean = text.replace(" ", "")
    m = re.search(r'(?<!\d)(\d{6})(?!\d)', clean)
    if m:
        return m.group(1)
    m = re.search(r'(\d{3,4})[-](\d{3,4})', clean)
    if m:
        return m.group(1) + m.group(2)
    m = re.search(r'(?<!\d)(\d{4,8})(?!\d)', clean)
    if m:
        return m.group(1)
    return "N/A"

# ==========================
# FORMAT MESSAGE
# ==========================
def format_item3(it):
    range_val = str(it.get("range", "")).strip()
    number_raw = str(it.get("number", "")).replace("+", "").strip()
    platform_raw = str(it.get("platform", "")).upper().strip()
    sms_text = str(it.get("sms", "")).strip()

    country_name_raw = range_val.split('-')[0].strip() if '-' in range_val else range_val.strip()

    country_code, flag = ("UN", "🌍")

    country_map = {
        "Venezuela": ("VE", "🇻🇪"), "Zimbabwe": ("ZW", "🇿🇼"), "Switzerland": ("CH", "🇨🇭"),
        "Bolivia": ("BO", "🇧🇴"), "Ivory Coast": ("CI", "🇨🇮"), "Guatemala": ("GT", "🇬🇹"),
        "Vietnam": ("VN", "🇻🇳"), "Afghanistan": ("AF", "🇦🇫"), "Albania": ("AL", "🇦🇱"),
        "Algeria": ("DZ", "🇩🇿"), "Andorra": ("AD", "🇦🇩"), "Angola": ("AO", "🇦🇴"),
        "Antigua and Barbuda": ("AG", "🇦🇬"), "Argentina": ("AR", "🇦🇷"), "Armenia": ("AM", "🇦🇲"),
        "Australia": ("AU", "🇦🇺"), "Austria": ("AT", "🇦🇹"), "Azerbaijan": ("AZ", "🇦🇿"),
        "Bahamas": ("BS", "🇧🇸"), "Bahrain": ("BH", "🇧🇭"), "Bangladesh": ("BD", "🇧🇩"),
        "Barbados": ("BB", "🇧🇧"), "Belarus": ("BY", "🇧🇾"), "Belgium": ("BE", "🇧🇪"),
        "Belize": ("BZ", "🇧🇿"), "Benin": ("BJ", "🇧🇯"), "Bhutan": ("BT", "🇧🇹"),
        "Bosnia and Herzegovina": ("BA", "🇧🇦"), "Botswana": ("BW", "🇧🇼"), "Brazil": ("BR", "🇧🇷"),
        "Brunei": ("BN", "🇧🇳"), "Bulgaria": ("BG", "🇧🇬"), "Burkina Faso": ("BF", "🇧🇫"),
        "Burundi": ("BI", "🇧🇮"), "Cabo Verde": ("CV", "🇨🇻"), "Cambodia": ("KH", "🇰🇭"),
        "Cameroon": ("CM", "🇨🇲"), "Canada": ("CA", "🇨🇦"), "Central African Republic": ("CF", "🇨🇫"),
        "Chad": ("TD", "🇹🇩"), "Chile": ("CL", "🇨🇱"), "China": ("CN", "🇨🇳"),
        "Colombia": ("CO", "🇨🇴"), "Comoros": ("KM", "🇰🇲"), "Congo": ("CG", "🇨🇬"),
        "Costa Rica": ("CR", "🇨🇷"), "Croatia": ("HR", "🇭🇷"), "Cuba": ("CU", "🇨🇺"),
        "Cyprus": ("CY", "🇨🇾"), "Czechia": ("CZ", "🇨🇿"), "Denmark": ("DK", "🇩🇰"),
        "Djibouti": ("DJ", "🇩🇯"), "Dominica": ("DM", "🇩🇲"), "Dominican Republic": ("DO", "🇩🇴"),
        "Ecuador": ("EC", "🇪🇨"), "Egypt": ("EG", "🇪🇬"), "El Salvador": ("SV", "🇸🇻"),
        "Equatorial Guinea": ("GQ", "🇬🇶"), "Eritrea": ("ER", "🇪🇷"), "Estonia": ("EE", "🇪🇪"),
        "Eswatini": ("SZ", "🇸🇿"), "Ethiopia": ("ET", "🇪🇹"), "Fiji": ("FJ", "🇫🇯"),
        "Finland": ("FI", "🇫🇮"), "France": ("FR", "🇫🇷"), "Gabon": ("GA", "🇬🇦"),
        "Gambia": ("GM", "🇬🇲"), "Georgia": ("GE", "🇬🇪"), "Germany": ("DE", "🇩🇪"),
        "Ghana": ("GH", "🇬🇭"), "Greece": ("GR", "🇬🇷"), "Grenada": ("GD", "🇬🇩"),
        "Guinea": ("GN", "🇬🇳"), "Guinea-Bissau": ("GW", "🇬🇼"), "Guyana": ("GY", "🇬🇾"),
        "Haiti": ("HT", "🇭🇹"), "Honduras": ("HN", "🇭🇳"), "Hungary": ("HU", "🇭🇺"),
        "Iceland": ("IS", "🇮🇸"), "India": ("IN", "🇮🇳"), "Indonesia": ("ID", "🇮🇩"),
        "Iran": ("IR", "🇮🇷"), "Iraq": ("IQ", "🇮🇶"), "Ireland": ("IE", "🇮🇪"),
        "Israel": ("IL", "🇮🇱"), "Italy": ("IT", "🇮🇹"), "Jamaica": ("JM", "🇯🇲"),
        "Japan": ("JP", "🇯🇵"), "Jordan": ("JO", "🇯🇴"), "Kazakhstan": ("KZ", "🇰🇿"),
        "Kenya": ("KE", "🇰🇪"), "Kiribati": ("KI", "🇰🇮"), "Korea, North": ("KP", "🇰🇵"),
        "Korea, South": ("KR", "🇰🇷"), "Kuwait": ("KW", "🇰🇼"), "Kyrgyzstan": ("KG", "🇰🇬"),
        "Laos": ("LA", "🇱🇦"), "Latvia": ("LV", "🇱🇻"), "Lebanon": ("LB", "🇱🇧"),
        "Lesotho": ("LS", "🇱🇸"), "Liberia": ("LR", "🇱🇷"), "Libya": ("LY", "🇱🇾"),
        "Liechtenstein": ("LI", "🇱🇮"), "Lithuania": ("LT", "🇱🇹"), "Luxembourg": ("LU", "🇱🇺"),
        "Madagascar": ("MG", "🇲🇬"), "Malawi": ("MW", "🇲🇼"), "Malaysia": ("MY", "🇲🇾"),
        "Maldives": ("MV", "🇲🇻"), "Mali": ("ML", "🇲🇱"), "Malta": ("MT", "🇲🇹"),
        "Marshall Islands": ("MH", "🇲🇭"), "Mauritania": ("MR", "🇲🇷"), "Mauritius": ("MU", "🇲🇺"),
        "Mexico": ("MX", "🇲🇽"), "Micronesia": ("FM", "🇫🇲"), "Moldova": ("MD", "🇲🇩"),
        "Monaco": ("MC", "🇲🇨"), "Mongolia": ("MN", "🇲🇳"), "Montenegro": ("ME", "🇲🇪"),
        "Morocco": ("MA", "🇲🇦"), "Mozambique": ("MZ", "🇲🇿"), "Myanmar": ("MM", "🇲🇲"),
        "Namibia": ("NA", "🇳🇦"), "Nauru": ("NR", "🇳🇷"), "Nepal": ("NP", "🇳🇵"),
        "Netherlands": ("NL", "🇳🇱"), "New Zealand": ("NZ", "🇳🇿"), "Nicaragua": ("NI", "🇳🇮"),
        "Niger": ("NE", "🇳🇪"), "Nigeria": ("NG", "🇳🇬"), "North Macedonia": ("MK", "🇲🇰"),
        "Norway": ("NO", "🇳🇴"), "Oman": ("OM", "🇴🇲"), "Pakistan": ("PK", "🇵🇰"),
        "Palau": ("PW", "🇵🇼"), "Panama": ("PA", "🇵🇦"), "Papua New Guinea": ("PG", "🇵🇬"),
        "Paraguay": ("PY", "🇵🇾"), "Peru": ("PE", "🇵🇪"), "Philippines": ("PH", "🇵🇭"),
        "Poland": ("PL", "🇵🇱"), "Portugal": ("PT", "🇵🇹"), "Qatar": ("QA", "🇶🇦"),
        "Romania": ("RO", "🇷🇴"), "Russia": ("RU", "🇷🇺"), "Rwanda": ("RW", "🇷🇼"),
        "Saint Kitts and Nevis": ("KN", "🇰🇳"), "Saint Lucia": ("LC", "🇱🇨"),
        "Saint Vincent and the Grenadines": ("VC", "🇻🇨"), "Samoa": ("WS", "🇼🇸"),
        "San Marino": ("SM", "🇸🇲"), "Sao Tome and Principe": ("ST", "🇸🇹"),
        "Saudi Arabia": ("SA", "🇸🇦"), "Senegal": ("SN", "🇸🇳"), "Serbia": ("RS", "🇷🇸"),
        "Seychelles": ("SC", "🇸🇨"), "Sierra Leone": ("SL", "🇸🇱"), "Singapore": ("SG", "🇸🇬"),
        "Slovakia": ("SK", "🇸🇰"), "Slovenia": ("SI", "🇸🇮"), "Solomon Islands": ("SB", "🇸🇧"),
        "Somalia": ("SO", "🇸🇴"), "South Africa": ("ZA", "🇿🇦"), "South Sudan": ("SS", "🇸🇸"),
        "Spain": ("ES", "🇪🇸"), "Sri Lanka": ("LK", "🇱🇰"), "Sudan": ("SD", "🇸🇩"),
        "Suriname": ("SR", "🇸🇷"), "Sweden": ("SE", "🇸🇪"), "Syria": ("SY", "🇸🇾"),
        "Taiwan": ("TW", "🇹🇼"), "Tajikistan": ("TJ", "🇹🇯"), "Tanzania": ("TZ", "🇹🇿"),
        "Thailand": ("TH", "🇹🇭"), "Timor-Leste": ("TL", "🇹🇱"), "Togo": ("TG", "🇹🇬"),
        "Tonga": ("TO", "🇹🇴"), "Trinidad and Tobago": ("TT", "🇹🇹"), "Tunisia": ("TN", "🇹🇳"),
        "Turkey": ("TR", "🇹🇷"), "Turkmenistan": ("TM", "🇹🇲"), "Tuvalu": ("TV", "🇹🇻"),
        "Uganda": ("UG", "🇺🇬"), "Ukraine": ("UA", "🇺🇦"), "United Arab Emirates": ("AE", "🇦🇪"),
        "United Kingdom": ("GB", "🇬🇧"), "United States": ("US", "🇺🇸"), "Uruguay": ("UY", "🇺🇾"),
        "Uzbekistan": ("UZ", "🇺🇿"), "Vanuatu": ("VU", "🇻🇺"), "Vatican City": ("VA", "🇻🇦"),
        "Yemen": ("YE", "🇾🇪"), "Zambia": ("ZM", "🇿🇲")
    }

    FLAG_IDS = {
        'RU': '5433865586356531140', 'CN': '5433827537241258614', 'ZA': '5431855966863766753',
        'BR': '5431769908604056769', 'IN': '5433601609076586221', 'NO': '5434147542369579483',
        'GB': '5435996255207567113', 'AF': '5433636707549331311', 'AL': '5433845881046578644',
        'DZ': '5433627189901801019', 'AD': '5433946537900128161', 'AO': '5433750193470191473',
        'AG': '5431752174684092629', 'AR': '5433754239329383923', 'AM': '5433804400252434985',
        'AU': '5431556723607352698', 'AT': '5431640943621060829', 'BS': '5431375858239550223',
        'BH': '5433682092468746953', 'BD': '5433854239052935880', 'BB': '5434027579638035690',
        'BY': '5431739800883312139', 'BE': '5433598052843665552', 'BZ': '5431431529605642522',
        'BJ': '5433838931789492934', 'BO': '5433609855413794108', 'BA': '5433991338703991663',
        'BW': '5433895109961725692', 'BN': '5433789964867352475', 'BG': '5431663303220804322',
        'BF': '5434013938821902926', 'MM': '5433666360003540231', 'BI': '5433792911214917126',
        'KH': '5433696429069580735', 'CM': '5433774971136521802', 'CA': '5433960238845802718',
        'CV': '5431865097964237519', 'CF': '5431374711483282830', 'TD': '5433825269498525925',
        'CL': '5431561302042488884', 'CO': '5433630999537792332', 'KM': '5431790266749040145',
        'CD': '5431703839122141424', 'CG': '5433861570562111275', 'HR': '5431489619038320862',
        'CU': '5431551436502611633', 'CY': '5434096943359866241', 'CZ': '5433958877341169005',
        'DK': '5433708502222649633', 'DM': '5433614889115464671', 'DO': '5434140679011842196',
        'EC': '5431462560744353934', 'EG': '5431619494554383246', 'SV': '5434134189316257066',
        'ER': '5433723401464198287', 'EE': '5433727662071755290', 'ET': '5433804408842368654',
        'FJ': '5433640560134994324', 'FI': '5431380440969654931', 'FR': '5434067424049639550',
        'GA': '5433982207603520017', 'GM': '5433596974806873997', 'GE': '5433814347396692144',
        'DE': '5431695798943363996', 'GH': '5434041611296192616', 'GR': '5434054805435724481',
        'GT': '5433935894971168754', 'GW': '5433775701280961741', 'GY': '5431676201007592926',
        'GN': '5434115081006756195', 'HN': '5434072118448894385', 'HU': '5434036689263670086',
        'IS': '5433628435442316429', 'ID': '5433884376838454074', 'IR': '5433882955204279044',
        'IQ': '5433749102548496991', 'IE': '5434155397864764491', 'IL': '5433810168393511493',
        'IT': '5434067655977874913', 'JM': '5433860784583096428', 'JP': '5431626087329182684',
        'JO': '5433643519367461444', 'KZ': '5433755347430946164', 'KE': '5433792670696748414',
        'KI': '5434004021742417775', 'KW': '5433820583689205435', 'KG': '5433652375590025431',
        'LA': '5431785473565537213', 'LV': '5433727778035872782', 'LB': '5433872853441196535',
        'LS': '5431620340662940910', 'LR': '5431414444225738871', 'LY': '5433876972314836083',
        'LI': '5433852744404317916', 'LT': '5434119663736862995', 'LU': '5431669247455540884',
        'MK': '5433626051735467592', 'MG': '5433833485770964033', 'FM': '5433773682646332733',
        'MW': '5433968339154122439', 'MY': '5434150334098327966', 'MV': '5434010919459894038',
        'ML': '5433943093336356065', 'MT': '5433598722858562967', 'MH': '5434130474169544969',
        'MR': '5433859405898594234', 'MU': '5431519649449653173', 'MX': '5434064563601421981',
        'MD': '5431428076451934112', 'MC': '5433798752370439037', 'MN': '5433674924168328689',
        'MA': '5434012796360604182', 'NA': '5431656358258685474', 'NR': '5434131139889478358',
        'NP': '5433895144321462723', 'NL': '5434026158003862063', 'NZ': '5431350891594658893',
        'NE': '5433737613510981562', 'NG': '5433836092816108548', 'KP': '5434142701941437163',
        'OM': '5433714227414054291', 'PK': '5431434686406604479', 'PW': '5433852121634060293',
        'PA': '5433851438734259274', 'PG': '5433972762970437003', 'PY': '5433748668756802256',
        'PE': '5434098446598419585', 'PH': '5433855712226718930', 'PL': '5433920471743607048',
        'PT': '5431353614603926322', 'QA': '5431394721735914525', 'RO': '5433738201921500487',
        'RW': '5431484894574295376', 'WS': '5433613703704490463', 'SM': '5431830051031103147',
        'SA': '5434125517777286321', 'SN': '5434001565021123877', 'RS': '5431894290856949874',
        'SC': '5433721073591926542', 'SL': '5433691077540330355', 'SG': '5431588626624427422',
        'SK': '5433902785068283672', 'SI': '5434129692485498098', 'SB': '5433867115364889538',
        'SO': '5433785261878162812', 'KR': '5431696408828720537', 'SS': '5433711929606551683',
        'ES': '5434045605615777483', 'LK': '5431755073787016798', 'SR': '5431520783321019240',
        'SD': '5431384383749633710', 'SE': '5434132406904830055', 'SY': '5433960710574776894',
        'TW': '5431596620782354186', 'TJ': '5433836870862331565', 'TZ': '5224397364155923150',
        'TH': '5433744249406202259', 'TL': '5433947697754751398', 'TG': '5433768478248620677',
        'TO': '5431573849164048083', 'TT': '5434145026168699543', 'TN': '5433819779803752753',
        'TR': '5433657662631624091', 'TM': '5433811229250434478', 'TV': '5433985768987836890',
        'UG': '5433961547163508427', 'UA': '5434065984430662040', 'AE': '5434122660810801756',
        'US': '5434076031164103400', 'UY': '5433852276252883640', 'UZ': '5433992296481700344',
        'VU': '5434153928985949656', 'VA': '5434094173105960379', 'VE': '5434009132753499322',
        'YE': '5434078960331796980', 'ZM': '5433727662071755290', 'ZW': '5433735143904786332',
        'VN': '5433601609076586221', 'CI': '5433774971136521802', 'CH': '5431640943621060829',
        'NI': '5434072118448894385', 'GD': '5433614889115464671', 'HT': '5433643519367461444',
        'AZ': '5433804400252434985', 'BT': '5433789964867352475', 'SZ': '5433895109961725692',
        'GQ': '5433723401464198287', 'ST': '5431830051031103147', 'MZ': '5433968339154122439',
        'DJ': '5433614889115464671', 'CR': '5431561302042488884'
    }

    sorted_countries = sorted(country_map.keys(), key=len, reverse=True)
    
    for country_name in sorted_countries:
        if country_name.lower() == country_name_raw.lower():
            country_code, flag = country_map[country_name]
            break
        elif country_name.lower() in country_name_raw.lower():
            country_code, flag = country_map[country_name]
            break

    if len(number_raw) >= 7:
        formatted_num = f"{number_raw[:3]}XXX{number_raw[-4:]}"
    else:
        formatted_num = number_raw

    safe_num = html.escape(formatted_num)

    # Detect language from SMS
    lang_code = detect_sms_language(sms_text)

    # If the service is WhatsApp, show WhatsApp emoji and short name #WS.
    # Otherwise, for all other services, show Facebook emoji and short name #FB.
    if "WHATSAPP" in platform_raw or "WS" in platform_raw:
        logo = '<tg-emoji emoji-id="5393189591773630465">💬</tg-emoji>'
        service_short = "WS"
    else:
        logo = '<tg-emoji emoji-id="5393310276059678201">👤</tg-emoji>'
        service_short = "FB"

    flag_id = FLAG_IDS.get(country_code)
    flag_html = (
        f'<tg-emoji emoji-id="{flag_id}">{flag}</tg-emoji>'
        if flag_id else flag
    )

    return f"{flag_html} #{country_code} {logo} #{service_short} 🗣️ #{lang_code} <code>{safe_num}</code>"


# ==========================
# QUEUE WORKER
# ==========================
msg_queue3 = queue.Queue()

def telegram_queue_worker3():
    while True:
        try:
            task = msg_queue3.get()
            if task is None:
                break
            item, uid = task
            
            if send_sms_to_telegram3(item):
                print(f"[Bot3] ✅ Sent to Telegram: {item['number']}")
                save_processed3(uid)
            else:
                print(f"[Bot3] ❌ Failed to send OTP: {item['number']}")
                with file_lock:
                    processed_ids3.discard(uid)
                    
            msg_queue3.task_done()
            time.sleep(0.05)
        except Exception as e:
            print(f"[Bot3] ❌ Worker error: {e}")
            time.sleep(2)

# ==========================
# SEND TO TELEGRAM (WITH RETRY)
# ==========================
def send_sms_to_telegram3(row):
    try:
        header = format_item3(row)
        otp = extract_otp3(row.get("sms", ""))

        if otp and otp != "N/A":
            otp_button = [{"text": f" {otp}", "copy_text": {"text": otp}, "style": "primary", "icon_custom_emoji_id": "5303138782004924588"}]
        else:
            otp_button = [{"text": " Waiting for OTP...", "callback_data": "no_otp", "style": "primary", "icon_custom_emoji_id": "5303138782004924588"}]

        buttons = {
            "inline_keyboard": [
                otp_button,
                [
                    {"text": " NUMBER", "url": "https://t.me/RDX_NUMBER100_BOT?start=auto", "style": "success", "icon_custom_emoji_id": "5460842683964609905"},
                    {"text": " CHANNEL", "url": "https://t.me/RDX_MARKETING", "style": "danger", "icon_custom_emoji_id": "5364125616801073577"}
                ]
            ]
        }

        import random
        overall_success = True

        for chat_id in TELEGRAM_CHAT_ID3:
            clean_chat_id = str(chat_id).strip()
            if not clean_chat_id:
                continue

            payload = {
                "chat_id": clean_chat_id,
                "text": header,
                "parse_mode": "HTML",
                "reply_markup": buttons
            }

            chat_success = False
            attempts = 0
            
            while attempts < 10:
                bot_token = random.choice(BOT_TOKENS3) 
                
                try:
                    r = requests.post(
                        f"https://api.telegram.org/bot{bot_token}/sendMessage",
                        json=payload,
                        timeout=15
                    )
                    if r.status_code == 200:
                        resp_json = r.json()
                        if resp_json.get("ok"):
                            message_id = resp_json["result"]["message_id"]
                            
                            threading.Thread(
                                target=delete_message_later3,
                                args=(bot_token, clean_chat_id, message_id, 180),
                                daemon=True
                            ).start()
                            
                            print(f"[Bot3] ✅ OTP Sent successfully to: {clean_chat_id}")
                            chat_success = True
                            break
                        else:
                            attempts += 1
                            desc = resp_json.get('description', 'Unknown')
                            print(f"[Bot3] ❌ Telegram API error for {clean_chat_id}: {desc}")
                            if "copy_text" in str(desc):
                                payload["reply_markup"]["inline_keyboard"][0] = [{"text": f" OTP: {otp}", "callback_data": f"otp_{otp}", "style": "primary", "icon_custom_emoji_id": "5330115548900050146"}]
                                continue
                            time.sleep(2)
                            continue
                    elif r.status_code == 429:
                        print(f"[Bot3] ⚠ Flood control... Trying again in 2s for {clean_chat_id}")
                        time.sleep(2)
                        continue 
                    else:
                        attempts += 1
                        print(f"[Bot3] ❌ Telegram Error (attempt {attempts}) for {clean_chat_id}:", r.text[:200])
                        time.sleep(2)
                except Exception as e:
                    attempts += 1
                    print(f"[Bot3] ❌ Send attempt {attempts} error for {clean_chat_id}: {e}")
                    time.sleep(2)

            if not chat_success:
                overall_success = False

        return overall_success

    except Exception as e:
        print(f"[Bot3] ❌ Send Error: {e}")
        return False

# ==========================
# LOGIN (LOOP BASED, NO RECURSION)
# ==========================
def login3():
    global LOGGED_IN_3, SESSKEY_3

    max_attempts = 5
    for attempt in range(1, max_attempts + 1):
        try:
            print(f"[Bot3] 🔐 Login attempt {attempt}/{max_attempts}...")
            login_page_url = f"{BASE3}/ints/login"
            r = session3.get(login_page_url, headers=headers3, timeout=20)

            match = re.search(r'(\d+)\s*\+\s*(\d+)', r.text)
            if match:
                captcha_answer = str(int(match.group(1)) + int(match.group(2)))
                print(f"[Bot3] ✅ Captcha solved: {captcha_answer}")
            else:
                print("[Bot3] ⚠ Captcha not found, using fallback '19'")
                captcha_answer = "19"

            signin_url = f"{BASE3}/ints/signin"
            payload = {
                "username": USERNAME3,
                "password": PASSWORD3,
                "capt": captcha_answer
            }

            headers_post = headers3.copy()
            headers_post.update({
                "Content-Type": "application/x-www-form-urlencoded",
                "Origin": BASE3,
                "Referer": login_page_url,
                "X-Requested-With": "XMLHttpRequest"
            })

            session3.post(signin_url, data=payload, headers=headers_post, timeout=20)

            check_page = session3.get(f"{BASE3}/ints/agent/SMSCDRStats", headers=headers3, timeout=20)
            html_text = check_page.text

            if "Logout" in html_text or "SMSCDRStats" in html_text or "Dashboard" in html_text:
                print("[Bot3] ✅ Login SUCCESS")
                LOGGED_IN_3 = True

                sk = re.search(r'sesskey["\']?\s*[:=]\s*["\']([^"\'&\s]{4,})', html_text)
                if not sk:
                    sk = re.search(r'sesskey=([^&"\'<\s]{4,})', html_text)
                if sk:
                    SESSKEY_3 = sk.group(1)
                    print(f"[Bot3] 🔑 SESSKEY: {SESSKEY_3}")
                else:
                    SESSKEY_3 = None
                    print("[Bot3] ⚠ SESSKEY not found")

                print("[Bot3] 🍪 Cookies:", session3.cookies.get_dict())
                return True
            else:
                print(f"[Bot3] ❌ Login FAILED (attempt {attempt})")
                LOGGED_IN_3 = False
                time.sleep(5)

        except Exception as e:
            print(f"[Bot3] ❌ Login error (attempt {attempt}): {e}")
            time.sleep(5)

    print("[Bot3] ❌ All login attempts exhausted.")
    return False

# ==========================
# REFRESH SESSKEY (DYNAMIC)
# ==========================
def refresh_sesskey3():
    global SESSKEY_3, LOGGED_IN_3
    try:
        print("[Bot3] 🔄 Refreshing SESSKEY...")
        check_page = session3.get(f"{BASE3}/ints/agent/SMSCDRStats", headers=headers3, timeout=20)
        html_text = check_page.text

        if "ints/login" in check_page.url or (
            re.search(r'<form[^>]+action[^>]*(signin|login)', html_text, re.I) and
            "SMSCDRStats" not in html_text
        ):
            print("[Bot3] ⚠ Session expired → re-logging in...")
            LOGGED_IN_3 = False
            return login3()

        sk = re.search(r'sesskey["\']?\s*[:=]\s*["\']([^"\'&\s]{4,})', html_text)
        if not sk:
            sk = re.search(r'sesskey=([^&"\'<\s]{4,})', html_text)
        if sk:
            SESSKEY_3 = sk.group(1)
            print(f"[Bot3] ✅ SESSKEY refreshed: {SESSKEY_3}")
        else:
            print("[Bot3] ⚠ SESSKEY not found, relying on cookie auth")

        return True

    except Exception as e:
        print(f"[Bot3] ❌ Refresh error: {e}")
        LOGGED_IN_3 = False
        return False

# ==========================
# SESSION KEEPALIVE (5-MIN PING)
# ==========================
def session_keepalive3():
    global LOGGED_IN_3, SESSKEY_3
    while True:
        time.sleep(300)
        try:
            r = session3.get(f"{BASE3}/ints/agent/SMSCDRStats", headers=headers3, timeout=15)
            if "Logout" in r.text or "SMSCDRStats" in r.text:
                print("💓 [Bot3] Session keepalive OK")
                sk = re.search(r'sesskey["\']?\s*[:=]\s*["\']([^"\'&\s]{4,})', r.text)
                if sk:
                    SESSKEY_3 = sk.group(1)
            else:
                print("⚠ [Bot3] Keepalive: session lost → relogin")
                LOGGED_IN_3 = False
                login3()
        except Exception as e:
            print(f"❌ [Bot3] Keepalive error: {e}")
            LOGGED_IN_3 = False

# ==========================
# FETCH SMS
# ==========================
def fetch_sms3():
    global LOGGED_IN_3, SESSKEY_3, session3

    if not LOGGED_IN_3:
        print("[Bot3] 🔐 Not logged in → attempting login...")
        if not login3():
            time.sleep(5)
            return None

    try:
        panel_date = (datetime.utcnow() + timedelta(hours=2)).strftime("%Y-%m-%d")
        url = f"{BASE3}/ints/agent/res/data_smscdr.php"

        params = {
            'fdate1': f'{panel_date} 00:00:00',
            'fdate2': f'{panel_date} 23:59:59',
            'frange': '', 'fclient': '', 'fnum': '', 'fcli': '',
            'fgdate': '', 'fgmonth': '', 'fgrange': '', 'fgclient': '',
            'fgnumber': '', 'fgcli': '', 'fg': '0',
            'sesskey': SESSKEY_3 or '',
            'sEcho': '2', 'iColumns': '9', 'sColumns': ',,,,,,,,',
            'iDisplayStart': '0', 'iDisplayLength': '-1',
            'mDataProp_0': '0', 'mDataProp_1': '1', 'mDataProp_2': '2',
            'mDataProp_3': '3', 'mDataProp_4': '4', 'mDataProp_5': '5',
            'mDataProp_6': '6', 'mDataProp_7': '7', 'mDataProp_8': '8',
            'bSearchable_0': 'true', 'bSearchable_1': 'true', 'bSearchable_2': 'true',
            'bSearchable_3': 'true', 'bSearchable_4': 'true', 'bSearchable_5': 'true',
            'bSearchable_6': 'true', 'bSearchable_7': 'true', 'bSearchable_8': 'true',
            'bSortable_0': 'true', 'bSortable_1': 'true', 'bSortable_2': 'true',
            'bSortable_3': 'true', 'bSortable_4': 'true', 'bSortable_5': 'true',
            'bSortable_6': 'true', 'bSortable_7': 'true', 'bSortable_8': 'false',
            'sSearch': '', 'bRegex': 'false',
            'iSortCol_0': '0', 'sSortDir_0': 'desc', 'iSortingCols': '1',
            '_': str(int(time.time() * 1000))
        }

        headers_fetch = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Mobile Safari/537.36',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Encoding': 'gzip, deflate',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': f'{BASE3}/ints/agent/SMSCDRStats',
            'Accept-Language': 'en-US,en;q=0.9'
        }

        print(f"[Bot3] 🔍 Fetching SMS {panel_date}...")
        r = session3.get(url, params=params, headers=headers_fetch, timeout=30)

        if r.status_code == 401 or "ints/login" in r.url:
            print("[Bot3] ⚠ Session expired → refreshing...")
            refresh_sesskey3()
            return None

        if r.status_code == 403:
            print("[Bot3] 🚫 403 → refreshing session...")
            refresh_sesskey3()
            return None

        if r.status_code == 200:
            if "login" in r.text.lower() and not r.text.strip().startswith('{'):
                print("[Bot3] ⚠ Session expired (HTML response) → refreshing...")
                refresh_sesskey3()
                return None
            try:
                return r.json()
            except json.JSONDecodeError:
                print("[Bot3] ❌ JSON parse failed:", r.text[:300])
                refresh_sesskey3()
                return None

        if r.status_code >= 500:
            print(f"[Bot3] ❌ Server Error {r.status_code} → Killing old session and recreating...")
            session3 = requests.Session()
            LOGGED_IN_3 = False
            return None

        print(f"[Bot3] ❌ Unexpected status: {r.status_code}")
        return None

    except requests.exceptions.ConnectionError as e:
        print(f"[Bot3] ❌ Connection error: {e}")
        LOGGED_IN_3 = False
        return None
    except requests.exceptions.Timeout as e:
        print(f"[Bot3] ❌ Timeout error: {e}")
        return None
    except Exception as e:
        print(f"[Bot3] ❌ fetch_sms error: {e}")
        LOGGED_IN_3 = False
        return None

def delete_message_later3(bot_token, chat_id, message_id, delay=60):
    pass

# ==========================
# MAIN BOT LOOP
# ==========================
def run_bot3():
    global processed_ids3, INITIAL_SYNC_DONE_3, START_TIME_3, LOGGED_IN_3
    print("[Bot3] 🤖 Starting...")

    while not LOGGED_IN_3:
        if login3():
            print("[Bot3] ✅ Logged in. Starting monitoring...")
        else:
            print("[Bot3] ❌ Login failed. Retrying in 10s...")
            time.sleep(10)

    threading.Thread(target=session_keepalive3, daemon=True, name="Bot3-Keepalive").start()
    
    for i in range(5):
        threading.Thread(target=telegram_queue_worker3, daemon=True, name=f"Bot3-QueueWorker-{i+1}").start()

    LOOP_INTERVAL = 16.50 

    while True:
        try:
            data = fetch_sms3()

            if not data:
                print("[Bot3] ⚠ No data received")
                time.sleep(LOOP_INTERVAL)
                continue

            records = data.get("aaData", [])
            if not records:
                print("[Bot3] ⚠ No records found")
                time.sleep(LOOP_INTERVAL)
                continue

            print(f"[Bot3] 📊 Fetched {len(records)} records from panel")
            valid_rows = []
            for row in records:
                try:
                    if isinstance(row, list) and len(row) >= 6:
                        num = str(row[2]).strip()
                        sms = str(row[5]).strip()
                        if sms and num and num != "0" and len(num) > 5 and "Total SMS" not in str(row[0]):
                            valid_rows.append({
                                "range": str(row[1]).strip(),
                                "number": num,
                                "platform": str(row[3]).strip(),
                                "sms": sms
                            })
                    elif isinstance(row, dict):
                        num = str(row.get('number') or row.get('num') or "").strip()
                        sms = str(row.get('sms') or "").strip()
                        if sms and num and num != "0" and len(num) > 5:
                            valid_rows.append({
                                "range": str(row.get('range') or "").strip(),
                                "number": num,
                                "platform": str(row.get('platform') or "").strip(),
                                "sms": sms
                            })
                except Exception as e:
                    print(f"[Bot3] ❌ Row parse error: {e}")

            if not valid_rows:
                print("[Bot3] ⚠ No valid OTP rows")
                time.sleep(LOOP_INTERVAL)
                continue

            if not INITIAL_SYNC_DONE_3:
                print("[Bot3] 🔄 Initial sync running (Registering existing records)...")
                
                for item in valid_rows:
                    uid = make_uid3(item['number'], item['sms'])
                    if uid not in processed_ids3:
                        processed_ids3.add(uid)
                        save_processed3(uid)
                
                recent_item = valid_rows[0]
                print(f"[Bot3] 🧪 Sending the last single OTP as a status test to group...")
                
                if send_sms_to_telegram3(recent_item):
                    print(f"[Bot3] ✅ Startup Status Test Sent Successfully → {recent_item['number']}")
                else:
                    print(f"[Bot3] ⚠️ Startup Status Test Send Failed → {recent_item['number']}")

                INITIAL_SYNC_DONE_3 = True
                print(f"[Bot3] ✅ Initial sync complete — {len(valid_rows)} items registered. Monitoring for new live OTPs...")

            else:
                new_found = False
                for item in valid_rows:
                    uid = make_uid3(item['number'], item['sms'])
                    if uid not in processed_ids3:
                        print(f"[Bot3] 🆕 Queueing New Live OTP → {item['number']}")
                        
                        processed_ids3.add(uid)
                        save_processed3(uid)
                        msg_queue3.put((item, uid))
                        
                        new_found = True
                        time.sleep(0.05)

                if not new_found:
                    print("[Bot3] 🔍 No new OTP")

        except Exception as e:
            print(f"[Bot3] ❌ LOOP ERROR: {e}")

        time.sleep(LOOP_INTERVAL)

# ==========================
# ENTRY POINT
# ==========================
def start_bot3():
    try:
        run_bot3()
    except Exception as e:
        print(f"[Bot3] ❌ Fatal: {e}")

if __name__ == "__main__":
    start_bot3()

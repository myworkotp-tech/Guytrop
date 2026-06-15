import time
import requests
import sqlite3
import queue
import threading
import html
import random
import re

# Configuration
API_URL = "http://147.135.212.197/crapi/st/viewstats"
TOKEN = "R1dUSkhBUzRjU2j2RCg2RiSWh1jllTk4JzVmOTg0dH2GinBSR2WAQg=="

# Telegram Bot Configuration
BOT_TOKENS = [
    "8606184785:AAFtR9vvhqR_GwPpYYUibx4CblRe2lZolqc",
    "YOUR_BOT_TOKEN_2",
    "YOUR_BOT_TOKEN_3",
]

TELEGRAM_CHAT_ID = [
    "-1003713446342, -1003878606545",
]

# SQLite Database Setup
conn = sqlite3.connect('otp_data.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS processed_otps (unique_id TEXT PRIMARY KEY)''')
conn.commit()

# Thread-safe locks and queues
file_lock = threading.Lock()
msg_queue = queue.Queue()
processed_ids = set()

def is_new(otp_id):
    cursor.execute('SELECT 1 FROM processed_otps WHERE unique_id = ?', (otp_id,))
    return cursor.fetchone() is None

def mark_as_processed(otp_id):
    cursor.execute('INSERT INTO processed_otps (unique_id) VALUES (?)', (otp_id,))
    conn.commit()

def save_processed(uid):
    with file_lock:
        cursor.execute('INSERT INTO processed_otps (unique_id) VALUES (?)', (uid,))
        conn.commit()

def extract_otp(message):
    message = str(message).strip()
    otp_patterns = [
        r'\b(\d{4,6})\b',
        r'code[:\s]+(\d{4,6})',
        r'OTP[:\s]+(\d{4,6})',
        r'verification[:\s]+(\d{4,6})',
        r'confirm[:\s]+(\d{4,6})',
    ]
    
    for pattern in otp_patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            return match.group(1)
    
    numbers = re.findall(r'\d{4,6}', message)
    return numbers[0] if numbers else "N/A"

def format_item(item):
    number = str(item.get("number", "")).replace("+", "").strip()
    message = str(item.get("message", "")).strip()
    timestamp = str(item.get("timestamp", "")).strip()
    cli = str(item.get("cli", "")).strip()

    if len(number) >= 7:
        formatted_num = f"{number[:3]}XXX{number[-4:]}"
    else:
        formatted_num = number

    safe_num = html.escape(formatted_num)

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

    country_code = "UN"
    flag = "🌍"

    for name, (code, f) in country_map.items():
        if name.lower() in cli.lower():
            country_code = code
            flag = f
            break

    flag_id = FLAG_IDS.get(country_code)
    flag_html = f'<tg-emoji emoji-id="{flag_id}">{flag}</tg-emoji>' if flag_id else flag

    otp = extract_otp(message)
    
    if otp and otp != "N/A":
        otp_button = [{"text": f"OTP: {otp}", "copy_text": {"text": otp}, "style": "primary"}]
    else:
        otp_button = [{"text": "Waiting for OTP...", "callback_data": "no_otp", "style": "primary"}]

    header = f"{flag_html} #{country_code} | Time: {timestamp}\n\nNumber: <code>{safe_num}</code>\nCLI: {cli}\n\nMessage: <code>{html.escape(message)}</code>"

    return header, otp_button

def delete_message_later(bot_token, chat_id, message_id, delay):
    time.sleep(delay)
    try:
        requests.post(
            f"https://api.telegram.org/bot{bot_token}/deleteMessage",
            json={"chat_id": chat_id, "message_id": message_id},
            timeout=10
        )
    except Exception as e:
        print(f"Failed to delete message: {e}")

def send_sms_to_telegram(item):
    try:
        header, otp_button = format_item(item)
        
        buttons = {
            "inline_keyboard": [
                otp_button,
                [
                    {"text": "NUMBER", "url": "https://t.me/RDX_NUMBER100_BOT?start=auto", "style": "success"},
                    {"text": "CHANNEL", "url": "https://t.me/RDX_MARKETING", "style": "danger"}
                ]
            ]
        }

        overall_success = True

        for chat_id in TELEGRAM_CHAT_ID:
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
                bot_token = random.choice(BOT_TOKENS)
                
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
                                target=delete_message_later,
                                args=(bot_token, clean_chat_id, message_id, 180),
                                daemon=True
                            ).start()
                            
                            print(f"Sent to Telegram: {clean_chat_id}")
                            chat_success = True
                            break
                        else:
                            attempts += 1
                            desc = resp_json.get('description', 'Unknown')
                            print(f"Telegram API error for {clean_chat_id}: {desc}")
                            time.sleep(2)
                    elif r.status_code == 429:
                        print(f"Rate limit... waiting 2s for {clean_chat_id}")
                        time.sleep(2)
                    else:
                        attempts += 1
                        print(f"Telegram Error (attempt {attempts}) for {clean_chat_id}: {r.text[:200]}")
                        time.sleep(2)
                except Exception as e:
                    attempts += 1
                    print(f"Send attempt {attempts} error for {clean_chat_id}: {e}")
                    time.sleep(2)

            if not chat_success:
                overall_success = False

        return overall_success

    except Exception as e:
        print(f"Send Error: {e}")
        return False

def telegram_queue_worker():
    while True:
        try:
            task = msg_queue.get()
            if task is None:
                break
            item, uid = task
            
            if send_sms_to_telegram(item):
                print(f"Successfully sent: {item['number']}")
                save_processed(uid)
            else:
                print(f"Failed to send OTP: {item['number']}")
                
            msg_queue.task_done()
            time.sleep(0.05)
        except Exception as e:
            print(f"Worker error: {e}")
            time.sleep(2)

def run_monitor():
    print("--- OTP Monitoring System Started ---")
    
    worker_thread = threading.Thread(target=telegram_queue_worker, daemon=True)
    worker_thread.start()
    
    while True:
        try:
            params = {'token': TOKEN, 'records': 100} 
            response = requests.get(API_URL, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                for item in reversed(data):
                    cli = item[0] if len(item) > 0 else ""
                    number = item[1] if len(item) > 1 else ""
                    message = item[2] if len(item) > 2 else ""
                    timestamp = item[3] if len(item) > 3 else ""
                    
                    otp_id = f"{number}_{timestamp}"
                    
                    if is_new(otp_id):
                        print(f"\nNEW OTP DETECTED")
                        print(f"================================")
                        print(f"Target Number : {number}")
                        print(f"Sender / CLI  : {cli}")
                        print(f"Time          : {timestamp}")
                        print(f"Message       : {message}")
                        print(f"================================")
                        
                        item_dict = {
                            "cli": cli,
                            "number": number,
                            "message": message,
                            "timestamp": timestamp
                        }
                        
                        msg_queue.put((item_dict, otp_id))
            
        except Exception as e:
            print(f"Error: {e}")
        
        time.sleep(5)

if __name__ == "__main__":
    run_monitor()

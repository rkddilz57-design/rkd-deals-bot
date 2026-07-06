import os
import html as html_module
import telebot
from telebot import types
import sqlite3
import random
import string

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
ADMIN_ID    = 7908632313
NOTIFY_ID   = 7908632313
SUPPORT_USER = "RkdGarant"

ADD_BALANCE_CHAT_ID  = -1003413725881
ADD_BALANCE_TOPIC_ID = 7377

bot = telebot.TeleBot(TOKEN)

LOGO_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'logo.png')

def show_screen(chat_id, text, markup, message_id=None):
    """Render a menu screen as a photo (branded with the RKD logo).
    If message_id is given, edit that message's caption in place (the
    message must already be a photo message — all screens originate
    from a photo message, so this stays consistent across navigation).
    Otherwise send a brand-new photo message.
    """
    if message_id:
        try:
            bot.edit_message_caption(caption=text, chat_id=chat_id, message_id=message_id,
                                      parse_mode="HTML", reply_markup=markup)
            return
        except Exception:
            pass
    with open(LOGO_PATH, 'rb') as photo:
        bot.send_photo(chat_id, photo, caption=text, parse_mode="HTML", reply_markup=markup)

# ============================================================
# EMOJI — dict of IDs (same pattern as reference bot)
# ============================================================
E = {
    "bag":    "5893255507380014983",
    "hand":   "5395732581780040886",
    "flash":  "5456140674028019486",
    "n1":     "5794164805065514131",
    "n2":     "5794085322400733645",
    "shield": "5902016123972358349",
    "n3":     "5794280000383358988",
    "n4":     "5794241397217304511",
    "box":    "5778672437122045013",
    "check":  "5294515522761663291",
    "cross":  "5893163582194978381",
    "time":   "5893102202817352158",
    "user":   "5902335789798265487",
    "link":   "5902449142575141204",
    "plane":  "5296432770392791386",
    "star":   "5463289097336405244",
    "money":  "5893473283696759404",
    "pin":    "5895440460322706085",
    "ton":    "5427168083074628963",
    "card":   "5445353829304387411",
    "stars":  "5924870095925942277",
    "usdt":   "6039802097916974085",
    "btc":    "5816788957614053645",
    "cloud":  "5467538555158943525",
    "crown":  "5217822164362739968",
    "cart":   "5312361253610475399",
    "bank":   "5332455502917949981",
    "check2": "5895514131896733546",
    "dollar": "5893473283696759404",
    "clip":   "5197269100878907942",
    "people": "6032609071373226027",
    "globe":  "5776233299424843260",
    "back":   "5274055917766202507",
    "flash2": "5258203794772085854",
    "people2":"6032609071373226027",
}

def _validate_emoji_ids(ids: list) -> set:
    """Ask Telegram which of our custom-emoji IDs actually exist/are usable.
    Sending <tg-emoji> with an unknown ID makes the WHOLE message fail with
    ENTITY_TEXT_INVALID, so we only ever use IDs Telegram confirms are real.
    """
    valid = set()
    unique_ids = list(dict.fromkeys(ids))
    for i in range(0, len(unique_ids), 100):
        chunk = unique_ids[i:i + 100]
        try:
            stickers = bot.get_custom_emoji_stickers(chunk)
            valid.update(s.custom_emoji_id for s in stickers)
        except Exception:
            pass
    return valid

VALID_EMOJI_IDS = _validate_emoji_ids(list(E.values()))

def e(key: str, fallback: str = "⭐") -> str:
    """Build <tg-emoji> HTML tag for messages, but only for IDs Telegram confirmed
    are valid (see VALID_EMOJI_IDS) — otherwise fall back to plain unicode emoji so
    sending never breaks with ENTITY_TEXT_INVALID.
    """
    eid = E.get(key)
    if not eid or eid not in VALID_EMOJI_IDS:
        return fallback
    if '\u20e3' in fallback:
        # Keycap sequences (e.g. "1\ufe0f\u20e3") need the FE0F kept — stripping it
        # breaks the sequence and Telegram rejects the whole message.
        clean = fallback
    else:
        clean = fallback.replace('\ufe0f', '').replace('\ufe0e', '')
        if not clean:
            clean = '✦'
    return f'<tg-emoji emoji-id="{eid}">{html_module.escape(clean)}</tg-emoji>'

def _btn(text: str, callback_data: str = None, emoji_key: str = None,
         url: str = None) -> types.InlineKeyboardButton:
    """Build InlineKeyboardButton with optional premium emoji icon.
    Only applies icon_custom_emoji_id when the ID is confirmed valid.
    When emoji_key is set and valid, strips the leading emoji+space from text to avoid duplication.
    """
    kwargs: dict = {}
    if callback_data:
        kwargs["callback_data"] = callback_data
    if url:
        kwargs["url"] = url
    if emoji_key and E.get(emoji_key) in VALID_EMOJI_IDS:
        kwargs["icon_custom_emoji_id"] = E[emoji_key]
        clean = text[text.index(' ') + 1:] if ' ' in text else text
        kwargs["text"] = clean
    else:
        kwargs["text"] = text
    return types.InlineKeyboardButton(**kwargs)

# ============================================================
# DATABASE
# ============================================================
DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'rkd_deals.db')

def db():
    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

def init_db():
    conn = db()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id     INTEGER PRIMARY KEY,
            lang        TEXT DEFAULT 'ru',
            referrer_id INTEGER,
            req_ton     TEXT,
            req_card    TEXT,
            req_stars   TEXT,
            req_usdt    TEXT,
            req_btc     TEXT,
            bal_rub     REAL DEFAULT 0.0,
            bal_uah     REAL DEFAULT 0.0,
            bal_kzt     REAL DEFAULT 0.0,
            bal_byn     REAL DEFAULT 0.0,
            bal_ton     REAL DEFAULT 0.0,
            bal_stars   REAL DEFAULT 0.0,
            bal_usdt    REAL DEFAULT 0.0,
            bal_btc     REAL DEFAULT 0.0,
            ref_earned  REAL DEFAULT 0.0
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS deals (
            deal_id         TEXT PRIMARY KEY,
            seller_id       INTEGER,
            buyer_id        INTEGER,
            description     TEXT,
            amount          REAL,
            currency        TEXT,
            payment_method  TEXT,
            status          TEXT DEFAULT 'created',
            seller_username TEXT,
            buyer_username  TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key   TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def get_setting(key, default=None):
    conn = db()
    c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key=?", (key,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else default

def set_setting(key, value):
    conn = db()
    c = conn.cursor()
    c.execute("INSERT INTO settings (key, value) VALUES (?,?) "
              "ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, str(value)))
    conn.commit()
    conn.close()

# Load persisted overrides for admin-editable settings (survive restarts/redeploys).
SUPPORT_USER = get_setting('support_user', SUPPORT_USER)
NOTIFY_ID = int(get_setting('notify_id', NOTIFY_ID))

user_states = {}

# ============================================================
# UTILS
# ============================================================
def ensure_user(user_id, referrer_id=None):
    conn = db()
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (user_id, referrer_id) VALUES (?,?)",
              (user_id, referrer_id))
    conn.commit()
    conn.close()

def get_lang(user_id):
    conn = db()
    c = conn.cursor()
    c.execute("SELECT lang FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row and row[0] in ('ru', 'en') else 'ru'

def set_lang(user_id, lang):
    conn = db()
    c = conn.cursor()
    c.execute("UPDATE users SET lang=? WHERE user_id=?", (lang, user_id))
    conn.commit()
    conn.close()

def gen_id():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))

def get_username(user):
    return f"@{user.username}" if user.username else f"id{user.id}"

def is_en(user_id):
    return get_lang(user_id) == 'en'

def _save_req(user_id, col, val):
    ensure_user(user_id)
    conn = db()
    c = conn.cursor()
    c.execute(f"UPDATE users SET {col}=? WHERE user_id=?", (val, user_id))
    conn.commit()
    conn.close()

# ============================================================
# WELCOME TEXT
# ============================================================
def welcome_text(lang: str, user_id: int = None) -> str:
    if lang == 'en':
        id_line = f"\n{e('user','👤')} Your ID: <code>{user_id}</code>\n" if user_id else ""
        return (
            f"<b>{e('bag','💼')} Welcome to RKD Deals {e('hand','🤝')}</b>\n"
            f"{id_line}\n"
            f"<blockquote>"
            f"{e('flash','⚡️')} Your reliable P2P escrow:\n"
            f"{e('n1','1️⃣')} Automated deals with NFTs and gifts\n"
            f"{e('n2','2️⃣')} {e('shield','🛡')} Full protection for both sides\n"
            f"{e('n3','3️⃣')} {e('usdt','💵')} Referral program — 50% of commission\n"
            f"{e('n4','4️⃣')} {e('box','📦')} Item transfers via manager: @{SUPPORT_USER}"
            f"</blockquote>"
        )
    return (
        f"<b>{e('bag','💼')} Добро пожаловать в RKD Deals {e('hand','🤝')}</b>\n"
        f"{id_line}\n"
        f"<blockquote>"
        f"{e('flash','⚡️')} Ваш надёжный P2P-гарант:\n"
        f"{e('n1','1️⃣')} Автоматические сделки с NFT и подарками\n"
        f"{e('n2','2️⃣')} {e('shield','🛡')} Полная защита обеих сторон\n"
        f"{e('n3','3️⃣')} {e('usdt','💵')} Реферальная программа — 50% от комиссии\n"
        f"{e('n4','4️⃣')} {e('box','📦')} Передача товаров через менеджера: @{SUPPORT_USER}"
        f"</blockquote>"
    )

# ============================================================
# KEYBOARDS
# ============================================================
def main_markup(user_id):
    en = is_en(user_id)
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.row(
        _btn("🪶 Реквизиты" if not en else "🪶 Requisites",   "menu_reqs",    "pin"),
        _btn("🤝 Создать сделку" if not en else "🤝 Create deal",  "menu_create",  "hand"),
    )
    markup.row(
        _btn("💰 Баланс"       if not en else "💰 Balance",    "menu_balance", "money"),
        _btn("💼 Мои сделки"   if not en else "💼 My deals",   "menu_deals",   "bag"),
    )
    markup.row(
        _btn("🔗 Рефералы"  if not en else "🔗 Referrals",     "menu_ref",     "link"),
        _btn("🌐 Язык"      if not en else "🌐 Lang",          "menu_lang",    "globe"),
    )
    markup.row(
        _btn("✈️ Поддержка" if not en else "✈️ Support",
             url=f"https://t.me/{SUPPORT_USER}", emoji_key="plane"),
    )
    return markup

def back_menu_btn(user_id):
    en = is_en(user_id)
    return _btn("📦 В меню" if not en else "📦 Menu", "menu_main", "box")

def back_btn(user_id):
    return _btn("⬅️ Назад" if not is_en(user_id) else "⬅️ Back", "go_back", "back")

def req_markup(user_id):
    en = is_en(user_id)
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        _btn("💎 TON" + (" wallet" if en else "-кошелёк"), "req_edit_ton",   "ton"),
        _btn("🖥 " + ("Card" if en else "Карта"),           "req_edit_card",  "card"),
    )
    markup.add(
        _btn("⭐ Stars @username",                           "req_edit_stars", "stars"),
        _btn("▽ USDT (TRC20)",                              "req_edit_usdt",  "usdt"),
    )
    markup.add(_btn("₿ BTC", "req_edit_btc", "btc"))
    markup.add(back_menu_btn(user_id))
    return markup

# ============================================================
# /start
# ============================================================
@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    args = message.text.split()
    referrer_id = None
    deal_link_id = None

    if len(args) > 1:
        param = args[1]
        if param.startswith('ref_'):
            try:
                referrer_id = int(param.split('_')[1])
                if referrer_id == user_id:
                    referrer_id = None
            except Exception:
                pass
        elif param.startswith('deal_'):
            deal_link_id = param.split('_', 1)[1]

    ensure_user(user_id, referrer_id)

    if deal_link_id:
        show_deal_card_by_id(message, deal_link_id)
        return

    lang = get_lang(user_id)
    show_screen(message.chat.id, welcome_text(lang, user_id), main_markup(user_id))

# ============================================================
# REQUISITES
# ============================================================
def show_requisites(chat_id, user_id, message_id=None):
    ensure_user(user_id)
    conn = db()
    c = conn.cursor()
    c.execute("SELECT req_ton, req_card, req_stars, req_usdt, req_btc FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    ton   = row[0] if row and row[0] else "—"
    card  = row[1] if row and row[1] else "—"
    stars = row[2] if row and row[2] else "—"
    usdt  = row[3] if row and row[3] else "—"
    btc   = row[4] if row and row[4] else "—"
    en = is_en(user_id)
    if en:
        text = (
            f"<b>{e('pin','🪶')} My Requisites</b>\n\n"
            f"<blockquote>"
            f"{e('ton','💎')} TON wallet: {ton}\n"
            f"{e('card','🖥')} Card: {card}\n"
            f"{e('stars','⭐')} Stars: {stars}\n"
            f"{e('usdt','💵')} USDT (TRC20): {usdt}\n"
            f"{e('btc','🪙')} BTC: {btc}"
            f"</blockquote>"
        )
    else:
        text = (
            f"<b>{e('pin','🪶')} Мои реквизиты</b>\n\n"
            f"<blockquote>"
            f"{e('ton','💎')} TON-кошелёк: {ton}\n"
            f"{e('card','🖥')} Карта: {card}\n"
            f"{e('stars','⭐')} Stars: {stars}\n"
            f"{e('usdt','💵')} USDT (TRC20): {usdt}\n"
            f"{e('btc','🪙')} BTC: {btc}"
            f"</blockquote>"
        )
    markup = req_markup(user_id)
    show_screen(chat_id, text, markup, message_id)

def get_req_for_currency(user_id, currency):
    conn = db()
    c = conn.cursor()
    c.execute("SELECT req_ton, req_card, req_stars, req_usdt, req_btc FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    if not row:
        return None
    mapping = {
        "RUB": row[1], "UAH": row[1], "KZT": row[1], "BYN": row[1],
        "STARS": row[2], "TON": row[0], "USDT": row[3], "BTC": row[4]
    }
    return mapping.get(currency)

# ============================================================
# CREATE DEAL — screens
# ============================================================
def show_new_deal(chat_id, user_id, message_id=None):
    en = is_en(user_id)
    if en:
        text = (
            f"<b>{e('bag','💼')} New Deal</b>\n\n"
            f"<blockquote>{e('cloud','☁️')} What is your role in this deal?</blockquote>\n\n"
            f"{e('crown','👑')} <b>Seller</b> — you sell and receive payment.\n"
            f"{e('cart','🛒')} <b>Buyer</b> — you pay and receive the item."
        )
    else:
        text = (
            f"<b>{e('bag','💼')} Новая сделка</b>\n\n"
            f"<blockquote>{e('cloud','☁️')} Кем вы выступаете в этой сделке?</blockquote>\n\n"
            f"{e('crown','👑')} <b>Продавец</b> — продаёте товар и получаете оплату.\n"
            f"{e('cart','🛒')} <b>Покупатель</b> — платите и получаете товар."
        )
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        _btn("👑 " + ("Seller" if en else "Я продавец"),  "deal_role_seller", "crown"),
        _btn("🛒 " + ("Buyer"  if en else "Я покупатель"),"deal_role_buyer",  "cart"),
    )
    markup.add(back_menu_btn(user_id))
    show_screen(chat_id, text, markup, message_id)

def show_payment_method_seller(chat_id, user_id, message_id=None):
    en = is_en(user_id)
    text = (
        f"<b>{e('n1','1️⃣')} {'Payment method:' if en else 'Способ оплаты:'}</b>\n\n"
        f"<blockquote>{e('cloud','☁️')} {'How will the buyer pay?' if en else 'Как покупатель переведёт средства?'}</blockquote>"
    )
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        _btn("🖥 " + ("Card"  if en else "Карта"),  "deal_pm_card",   "card"),
        _btn("⭐ Stars",                             "deal_pm_stars",  "stars"),
    )
    markup.add(_btn("💎 " + ("Crypto" if en else "Крипта"), "deal_pm_crypto", "ton"))
    markup.add(back_btn(user_id))
    markup.add(back_menu_btn(user_id))
    show_screen(chat_id, text, markup, message_id)

def show_crypto_choice(chat_id, user_id, message_id=None):
    en = is_en(user_id)
    text = (
        f"<b>{e('n1','1️⃣')} {'Choose cryptocurrency:' if en else 'Выберите криптовалюту:'}</b>\n\n"
        f"<blockquote>{e('cloud','☁️')} {'Which crypto do you accept?' if en else 'Какую криптовалюту принимаете?'}</blockquote>"
    )
    markup = types.InlineKeyboardMarkup(row_width=3)
    markup.add(
        _btn("💎 TON",  "deal_crypto_ton",  "ton"),
        _btn("▽ USDT",  "deal_crypto_usdt", "usdt"),
        _btn("₿ BTC",   "deal_crypto_btc",  "btc"),
    )
    markup.add(back_btn(user_id))
    markup.add(back_menu_btn(user_id))
    show_screen(chat_id, text, markup, message_id)

def show_card_currency(chat_id, user_id, message_id=None):
    en = is_en(user_id)
    text = f"<b>{e('bank','🏦')} {'Choose card currency:' if en else 'Выберите валюту карты:'}</b>"
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        _btn("🇷🇺 RUB", "deal_cur_RUB"),
        _btn("🇺🇦 UAH", "deal_cur_UAH"),
        _btn("🇰🇿 KZT", "deal_cur_KZT"),
        _btn("🇧🇾 BYN", "deal_cur_BYN"),
    )
    markup.add(back_btn(user_id))
    markup.add(back_menu_btn(user_id))
    show_screen(chat_id, text, markup, message_id)

def show_enter_amount(chat_id, user_id, currency, message_id=None):
    cur_labels = {
        "RUB": "🇷🇺", "UAH": "🇺🇦", "KZT": "🇰🇿", "BYN": "🇧🇾",
        "STARS": "⭐", "TON": "💎", "USDT": "▽", "BTC": "₿"
    }
    pfx = cur_labels.get(currency, "")
    en = is_en(user_id)
    text = f"<b>{pfx} {'Enter amount in' if en else 'Введите сумму в'} {currency}:</b>"
    markup = types.InlineKeyboardMarkup()
    markup.add(_btn("🏦 " + ("Change currency" if en else "Изменить валюту"), "deal_change_cur", "bank"))
    markup.add(back_btn(user_id))
    markup.add(back_menu_btn(user_id))
    show_screen(chat_id, text, markup, message_id)

def show_enter_description(chat_id, user_id, message_id=None):
    en = is_en(user_id)
    if en:
        text = (
            f"<b>{e('clip','📋')} Describe the deal subject:</b>\n\n"
            f"<blockquote><i>E.g.: https://t.me/nft/PlushPepe-111\nor a text description</i></blockquote>"
        )
    else:
        text = (
            f"<b>{e('clip','📋')} Опишите предмет сделки:</b>\n\n"
            f"<blockquote><i>Например: https://t.me/nft/PlushPepe-111\nили текстовое описание товара</i></blockquote>"
        )
    markup = types.InlineKeyboardMarkup()
    markup.add(back_menu_btn(user_id))
    show_screen(chat_id, text, markup, message_id)

# ============================================================
# MESSAGE STEPS
# ============================================================
@bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id) is not None)
def handle_steps(message):
    user_id = message.from_user.id
    state   = user_states[user_id]
    step    = state.get("step")
    text    = message.text.strip() if message.text else ""
    en      = is_en(user_id)

    if step in ("admin_support_user", "admin_notify_id"):
        _handle_admin_step(message, user_id, state)
        return

    if step == "req_ton":
        if len(text) != 48 or not (text.startswith("UQ") or text.startswith("EQ")):
            bot.send_message(message.chat.id,
                f"{e('cross','❌')} <b>{'Invalid format!' if en else 'Неверный формат!'}</b>\n"
                f"{'TON address: 48 chars, starts with UQ or EQ.' if en else 'ТОН-адрес: 48 символов, начинается на UQ или EQ.'}",
                parse_mode="HTML")
            return
        _save_req(user_id, "req_ton", text)
        del user_states[user_id]
        bot.send_message(message.chat.id,
            f"{e('check2','✅')} <b>{'TON wallet saved!' if en else 'TON-кошелёк сохранён!'}</b>",
            parse_mode="HTML")
        show_requisites(message.chat.id, user_id)

    elif step == "req_card":
        card = text.replace(" ", "")
        if not card.isdigit() or len(card) != 16:
            bot.send_message(message.chat.id,
                f"🚫 {'Enter 16 card digits.' if en else 'Введите 16 цифр карты.'}",
                parse_mode="HTML")
            return
        _save_req(user_id, "req_card", card)
        del user_states[user_id]
        bot.send_message(message.chat.id,
            f"{e('check2','✅')} <b>{'Card saved!' if en else 'Карта сохранена!'}</b>",
            parse_mode="HTML")
        show_requisites(message.chat.id, user_id)

    elif step == "req_stars":
        username = text if text.startswith("@") else f"@{text}"
        _save_req(user_id, "req_stars", username)
        del user_states[user_id]
        bot.send_message(message.chat.id,
            f"{e('check2','✅')} <b>{'Stars username saved!' if en else 'Stars username сохранён!'}</b>",
            parse_mode="HTML")
        show_requisites(message.chat.id, user_id)

    elif step == "req_usdt":
        _save_req(user_id, "req_usdt", text)
        del user_states[user_id]
        bot.send_message(message.chat.id,
            f"{e('check2','✅')} <b>{'USDT wallet saved!' if en else 'USDT-кошелёк сохранён!'}</b>",
            parse_mode="HTML")
        show_requisites(message.chat.id, user_id)

    elif step == "req_btc":
        _save_req(user_id, "req_btc", text)
        del user_states[user_id]
        bot.send_message(message.chat.id,
            f"{e('check2','✅')} <b>{'BTC wallet saved!' if en else 'BTC-кошелёк сохранён!'}</b>",
            parse_mode="HTML")
        show_requisites(message.chat.id, user_id)

    elif step == "deal_amount":
        try:
            amount = float(text.replace(",", "."))
            if amount <= 0:
                raise ValueError
        except ValueError:
            bot.send_message(message.chat.id,
                f"{e('cross','❌')} {'Enter a positive number.' if en else 'Введите положительное число.'}",
                parse_mode="HTML")
            return
        state["amount"] = amount
        state["step"] = "deal_description"
        user_states[user_id] = state
        show_enter_description(message.chat.id, user_id)

    elif step == "deal_description":
        currency   = state["currency"]
        pay_method = state["payment_method"]
        amount     = state["amount"]

        req = get_req_for_currency(user_id, currency)
        if not req:
            del user_states[user_id]
            bot.send_message(message.chat.id,
                f"❗ <b>{'Add requisites in «Requisites» first.' if en else 'Сначала добавьте реквизиты в «Реквизиты».'}</b>",
                parse_mode="HTML", reply_markup=req_markup(user_id))
            return

        deal_id = gen_id()
        seller_uname = get_username(message.from_user)
        conn = db()
        c = conn.cursor()
        c.execute(
            "INSERT INTO deals (deal_id, seller_id, description, amount, currency, payment_method, seller_username) "
            "VALUES (?,?,?,?,?,?,?)",
            (deal_id, user_id, text, amount, currency, pay_method, seller_uname)
        )
        conn.commit()
        conn.close()
        del user_states[user_id]

        bot_username = bot.get_me().username
        deal_url = f"https://t.me/{bot_username}?start=deal_{deal_id}"

        if en:
            seller_text = (
                f"{e('check2','✅')} <b>Deal #{deal_id} created!</b>\n\n"
                f"<blockquote>"
                f"{e('crown','👑')} Role: Seller\n"
                f"{e('usdt','💵')} Currency: {currency}\n"
                f"{e('dollar','💰')} Amount: {amount}\n"
                f"{e('clip','📋')} Description: {html_module.escape(text[:50])}"
                f"</blockquote>\n\n"
                f"{e('link','🔗')} <b>Link for buyer:</b>\n<code>{deal_url}</code>"
            )
        else:
            seller_text = (
                f"{e('check2','✅')} <b>Сделка #{deal_id} создана!</b>\n\n"
                f"<blockquote>"
                f"{e('crown','👑')} Роль: Продавец\n"
                f"{e('usdt','💵')} Валюта: {currency}\n"
                f"{e('dollar','💰')} Сумма: {amount}\n"
                f"{e('clip','📋')} Описание: {html_module.escape(text[:50])}"
                f"</blockquote>\n\n"
                f"{e('link','🔗')} <b>Ссылка для покупателя:</b>\n<code>{deal_url}</code>"
            )
        markup = types.InlineKeyboardMarkup()
        markup.add(_btn("❌ " + ("Cancel" if en else "Отменить сделку"), f"cancel_{deal_id}", "cross"))
        markup.add(back_menu_btn(user_id))
        bot.send_message(user_id, seller_text, parse_mode="HTML", reply_markup=markup)

        fname = html_module.escape(message.from_user.first_name or "")
        lname = html_module.escape(message.from_user.last_name or "")
        notify_text = (
            f"{e('flash','⚡️')} <b>Нова угода!</b>\n\n"
            f"<blockquote>"
            f"{e('user','👤')} Продавець: {seller_uname}\n"
            f"🆔 ID: <code>{user_id}</code>\n"
            f"{e('usdt','💵')} Валюта: {currency}\n"
            f"{e('dollar','💰')} Сума: {amount}\n"
            f"{e('clip','📋')} Опис: {html_module.escape(text[:80])}\n"
            f"{e('link','🔗')} ID угоди: <code>{deal_id}</code>"
            f"</blockquote>\n🔗 <code>{deal_url}</code>"
        )
        try:
            bot.send_message(NOTIFY_ID, notify_text, parse_mode="HTML")
        except Exception:
            pass

    elif step == "deal_search":
        search_id = text.strip().lstrip('#')
        del user_states[user_id]
        conn = db()
        c = conn.cursor()
        c.execute(
            "SELECT deal_id, seller_id, buyer_id, description, amount, currency, status, seller_username, buyer_username "
            "FROM deals WHERE deal_id=? AND (seller_id=? OR buyer_id=?)",
            (search_id, user_id, user_id)
        )
        deal = c.fetchone()
        conn.close()
        if not deal:
            markup = types.InlineKeyboardMarkup()
            markup.add(back_menu_btn(user_id))
            bot.send_message(message.chat.id,
                f"{e('cross','❌')} <b>{'Deal not found.' if en else 'Сделка не найдена.'}</b>",
                parse_mode="HTML", reply_markup=markup)
            return
        _show_deal_detail(message.chat.id, user_id, deal)

# ============================================================
# CALLBACKS
# ============================================================
@bot.callback_query_handler(func=lambda call: not call.data.startswith("admin_"))
def handle_callbacks(call):
    user_id = call.from_user.id
    mid = call.message.message_id
    cid = call.message.chat.id
    bot.answer_callback_query(call.id)
    en = is_en(user_id)

    if call.data == "menu_main":
        lang = get_lang(user_id)
        show_screen(cid, welcome_text(lang, user_id), main_markup(user_id), mid)

    elif call.data == "menu_create":
        show_new_deal(cid, user_id, mid)

    elif call.data == "menu_deals":
        my_deals(cid, user_id, message_id=mid)

    elif call.data == "menu_balance":
        balance_menu(cid, user_id, mid)

    elif call.data == "menu_reqs":
        show_requisites(cid, user_id, mid)

    elif call.data == "menu_ref":
        referrals_menu(cid, user_id, mid)

    elif call.data == "menu_lang":
        lang_menu(cid, user_id, mid)

    elif call.data == "lang_ru":
        set_lang(user_id, 'ru')
        show_screen(cid, welcome_text('ru', user_id), main_markup(user_id), mid)

    elif call.data == "lang_en":
        set_lang(user_id, 'en')
        show_screen(cid, welcome_text('en', user_id), main_markup(user_id), mid)

    elif call.data == "req_edit_ton":
        _req_input(cid, user_id, mid, "req_ton",
            f"<b>{e('ton','💎')} {'Enter TON wallet:' if en else 'Введите TON-кошелёк:'}</b>\n"
            f"<i>{'(48 chars, UQ or EQ)' if en else '(48 символов, UQ или EQ)'}</i>")

    elif call.data == "req_edit_card":
        _req_input(cid, user_id, mid, "req_card",
            f"<b>{e('card','🖥')} {'Enter card (16 digits):' if en else 'Введите карту (16 цифр):'}</b>")

    elif call.data == "req_edit_stars":
        _req_input(cid, user_id, mid, "req_stars",
            f"<b>{e('stars','⭐')} {'Enter @username for Stars:' if en else 'Введите @username для Stars:'}</b>")

    elif call.data == "req_edit_usdt":
        _req_input(cid, user_id, mid, "req_usdt",
            f"<b>{e('usdt','💵')} {'Enter USDT wallet (TRC20):' if en else 'Введите USDT-кошелёк (TRC20):'}</b>")

    elif call.data == "req_edit_btc":
        _req_input(cid, user_id, mid, "req_btc",
            f"<b>{e('btc','🪙')} {'Enter BTC wallet:' if en else 'Введите BTC-кошелёк:'}</b>")

    elif call.data == "deal_role_seller":
        user_states[user_id] = {"step": "deal_pay_method", "role": "seller"}
        show_payment_method_seller(cid, user_id, mid)

    elif call.data == "deal_role_buyer":
        text = (
            f"<b>{e('cart','🛒')} {'Buyer' if en else 'Покупатель'}</b>\n\n"
            + ("Ask the seller to send you the deal link."
               if en else
               "Попросите продавца прислать вам ссылку на сделку.")
        )
        markup = types.InlineKeyboardMarkup()
        markup.add(back_menu_btn(user_id))
        show_screen(cid, text, markup, mid)

    elif call.data == "deal_pm_card":
        if not get_req_for_currency(user_id, "RUB"):
            bot.send_message(cid,
                f"❗ <b>{'Add card in «Requisites» first.' if en else 'Сначала добавьте карту в «Реквизиты».'}</b>",
                parse_mode="HTML", reply_markup=req_markup(user_id))
            return
        state = user_states.get(user_id, {"role": "seller"})
        state.update({"payment_method": "card", "step": "deal_card_currency"})
        user_states[user_id] = state
        show_card_currency(cid, user_id, mid)

    elif call.data == "deal_pm_stars":
        if not get_req_for_currency(user_id, "STARS"):
            bot.send_message(cid,
                f"❗ <b>{'Add @username in «Requisites» first.' if en else 'Сначала добавьте @username в «Реквизиты».'}</b>",
                parse_mode="HTML", reply_markup=req_markup(user_id))
            return
        state = user_states.get(user_id, {"role": "seller"})
        state.update({"payment_method": "stars", "currency": "STARS", "step": "deal_amount"})
        user_states[user_id] = state
        show_enter_amount(cid, user_id, "STARS", mid)

    elif call.data == "deal_pm_crypto":
        state = user_states.get(user_id, {"role": "seller"})
        state.update({"payment_method": "crypto", "step": "deal_crypto_type"})
        user_states[user_id] = state
        show_crypto_choice(cid, user_id, mid)

    elif call.data == "deal_crypto_ton":
        if not get_req_for_currency(user_id, "TON"):
            bot.send_message(cid,
                f"❗ <b>{'Add TON wallet in «Requisites» first.' if en else 'Сначала добавьте TON-кошелёк.'}</b>",
                parse_mode="HTML", reply_markup=req_markup(user_id))
            return
        state = user_states.get(user_id, {})
        state.update({"currency": "TON", "step": "deal_amount"})
        user_states[user_id] = state
        show_enter_amount(cid, user_id, "TON", mid)

    elif call.data == "deal_crypto_usdt":
        if not get_req_for_currency(user_id, "USDT"):
            bot.send_message(cid,
                f"❗ <b>{'Add USDT wallet in «Requisites» first.' if en else 'Сначала добавьте USDT-кошелёк.'}</b>",
                parse_mode="HTML", reply_markup=req_markup(user_id))
            return
        state = user_states.get(user_id, {})
        state.update({"currency": "USDT", "step": "deal_amount"})
        user_states[user_id] = state
        show_enter_amount(cid, user_id, "USDT", mid)

    elif call.data == "deal_crypto_btc":
        if not get_req_for_currency(user_id, "BTC"):
            bot.send_message(cid,
                f"❗ <b>{'Add BTC wallet in «Requisites» first.' if en else 'Сначала добавьте BTC-кошелёк.'}</b>",
                parse_mode="HTML", reply_markup=req_markup(user_id))
            return
        state = user_states.get(user_id, {})
        state.update({"currency": "BTC", "step": "deal_amount"})
        user_states[user_id] = state
        show_enter_amount(cid, user_id, "BTC", mid)

    elif call.data.startswith("deal_cur_"):
        cur = call.data.split("_")[2]
        state = user_states.get(user_id, {})
        state.update({"currency": cur, "step": "deal_amount"})
        user_states[user_id] = state
        show_enter_amount(cid, user_id, cur, mid)

    elif call.data == "deal_change_cur":
        state = user_states.get(user_id, {})
        pm = state.get("payment_method", "card")
        if pm == "card":
            state["step"] = "deal_card_currency"
            user_states[user_id] = state
            show_card_currency(cid, user_id, mid)
        elif pm == "crypto":
            state["step"] = "deal_crypto_type"
            user_states[user_id] = state
            show_crypto_choice(cid, user_id, mid)

    elif call.data == "go_back":
        state = user_states.get(user_id, {})
        pm   = state.get("payment_method")
        step = state.get("step", "")
        if step == "deal_amount":
            if pm == "card":
                state["step"] = "deal_card_currency"
                user_states[user_id] = state
                show_card_currency(cid, user_id, mid)
            elif pm == "stars":
                state["step"] = "deal_pay_method"
                user_states[user_id] = state
                show_payment_method_seller(cid, user_id, mid)
            elif pm == "crypto":
                state["step"] = "deal_crypto_type"
                user_states[user_id] = state
                show_crypto_choice(cid, user_id, mid)
        elif step in ("deal_card_currency", "deal_crypto_type", "deal_pay_method"):
            show_new_deal(cid, user_id, mid)
        else:
            show_new_deal(cid, user_id, mid)

    elif call.data.startswith("deals_page_"):
        page = int(call.data.split("_")[2])
        my_deals(cid, user_id, message_id=mid, page=page)

    elif call.data == "deals_search":
        if user_id in user_states:
            del user_states[user_id]
        bot.delete_message(cid, mid)
        bot.send_message(cid,
            f"{e('clip','📋')} <b>{'Enter deal code (e.g. 492ffd74):' if en else 'Введите код сделки (например: 492ffd74):'}</b>",
            parse_mode="HTML")
        user_states[user_id] = {"step": "deal_search"}

    elif call.data.startswith("deal_view_"):
        deal_id = call.data.split("_", 2)[2]
        conn = db()
        c = conn.cursor()
        c.execute(
            "SELECT deal_id, seller_id, buyer_id, description, amount, currency, status, seller_username, buyer_username "
            "FROM deals WHERE deal_id=?", (deal_id,)
        )
        deal = c.fetchone()
        conn.close()
        if deal:
            _show_deal_detail(cid, user_id, deal, message_id=mid)

    elif call.data == "back_to_deals":
        my_deals(cid, user_id, message_id=mid)

    elif call.data.startswith("pay_"):
        deal_id = call.data.split("_", 1)[1]
        _process_payment(call, user_id, cid, mid, deal_id)

    elif call.data.startswith("cancel_"):
        deal_id = call.data.split("_", 1)[1]
        conn = db()
        c = conn.cursor()
        c.execute("SELECT status FROM deals WHERE deal_id=?", (deal_id,))
        row = c.fetchone()
        if row and row[0] == 'created':
            c.execute("UPDATE deals SET status='cancelled' WHERE deal_id=?", (deal_id,))
            conn.commit()
        conn.close()
        markup = types.InlineKeyboardMarkup()
        markup.add(back_menu_btn(user_id))
        show_screen(cid,
            f"{e('cross','❌')} <b>{'Deal cancelled.' if en else 'Сделка отменена.'}</b>",
            markup, mid
        )

    elif call.data.startswith("release_"):
        deal_id = call.data.split("_", 1)[1]
        _release_deal(call, user_id, cid, mid, deal_id)

    elif call.data == "ref_copy":
        bot_username = bot.get_me().username
        ref_url = f"https://t.me/{bot_username}?start=ref_{user_id}"
        bot.answer_callback_query(call.id,
            f"{'Your link' if en else 'Ваша ссылка'}: {ref_url}", show_alert=True)

    elif call.data == "noop":
        pass

# ============================================================
# REQUISITE INPUT HELPER
# ============================================================
def _req_input(cid, user_id, mid, step, prompt_text):
    if user_id in user_states:
        del user_states[user_id]
    bot.delete_message(cid, mid)
    bot.send_message(cid, prompt_text, parse_mode="HTML")
    user_states[user_id] = {"step": step}

# ============================================================
# MY DEALS
# ============================================================
DEALS_PER_PAGE = 6
STATUS_EMOJI = {'created': '⏳', 'paid': '🔒', 'completed': '✅', 'cancelled': '❌'}
STATUS_LABEL = {
    'ru': {'created': 'Создана', 'paid': 'Оплачена', 'completed': 'Завершена', 'cancelled': 'Отменена'},
    'en': {'created': 'Created', 'paid': 'Paid',     'completed': 'Completed', 'cancelled': 'Cancelled'},
}

def my_deals(chat_id, user_id, message_id=None, page=0):
    en = is_en(user_id)
    conn = db()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM deals WHERE seller_id=? OR buyer_id=?", (user_id, user_id))
    total = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM deals WHERE (seller_id=? OR buyer_id=?) AND status='completed'", (user_id, user_id))
    completed = c.fetchone()[0]
    c.execute(
        "SELECT deal_id, description, amount, currency, status FROM deals "
        "WHERE seller_id=? OR buyer_id=? ORDER BY rowid DESC LIMIT ? OFFSET ?",
        (user_id, user_id, DEALS_PER_PAGE, page * DEALS_PER_PAGE)
    )
    deals = c.fetchall()
    conn.close()
    total_pages = max(1, (total + DEALS_PER_PAGE - 1) // DEALS_PER_PAGE)

    if en:
        text = f"<b>{e('bag','💼')} My Deals</b>\n\n🧩 Total: <b>{total}</b>  {e('check2','✅')} Completed: <b>{completed}</b>"
    else:
        text = f"<b>{e('bag','💼')} Мои сделки</b>\n\n🧩 Всего: <b>{total}</b>  {e('check2','✅')} Завершено: <b>{completed}</b>"

    markup = types.InlineKeyboardMarkup(row_width=2)
    for d in deals:
        deal_id, desc, amount, currency, status = d
        emoji = STATUS_EMOJI.get(status, '❓')
        markup.add(_btn(f"{emoji} #{deal_id} {amount} {currency}", f"deal_view_{deal_id}"))

    nav = []
    if page > 0:
        nav.append(_btn("◀", f"deals_page_{page-1}"))
    nav.append(_btn(f"{page+1}/{total_pages}", "noop"))
    if (page + 1) < total_pages:
        nav.append(_btn("▶", f"deals_page_{page+1}"))
    if nav:
        markup.row(*nav)

    markup.add(_btn("🔍 " + ("Search by code" if en else "Поиск по коду"), "deals_search"))
    markup.add(back_menu_btn(user_id))

    show_screen(chat_id, text, markup, message_id)

def _show_deal_detail(chat_id, user_id, deal, message_id=None):
    deal_id, seller_id, buyer_id, description, amount, currency, status, seller_uname, buyer_uname = deal
    en   = is_en(user_id)
    lang = 'en' if en else 'ru'
    if en:
        role = "seller" if seller_id == user_id else "buyer"
        buyer_display = buyer_uname or "pending"
        text = (
            f"<b>{e('pin','🪶')} Deal #{deal_id}</b>\n\n"
            f"<blockquote>"
            f"⚙️ Status: {STATUS_LABEL[lang].get(status, status)}\n"
            f"{e('crown','👑')} Role: {role}\n"
            f"{e('dollar','💰')} Amount: {amount} {currency}\n"
            f"{e('clip','📋')} Item: {html_module.escape(str(description or ''))[:80]}\n"
            f"{e('bag','💼')} Seller: {seller_uname or f'id{seller_id}'}\n"
            f"{e('cart','🛒')} Buyer: {buyer_display}"
            f"</blockquote>"
        )
    else:
        role = "продавец" if seller_id == user_id else "покупатель"
        buyer_display = buyer_uname or "ожидается"
        text = (
            f"<b>{e('pin','🪶')} Сделка #{deal_id}</b>\n\n"
            f"<blockquote>"
            f"⚙️ Статус: {STATUS_LABEL[lang].get(status, status)}\n"
            f"{e('crown','👑')} Роль: {role}\n"
            f"{e('dollar','💰')} Сумма: {amount} {currency}\n"
            f"{e('clip','📋')} Предмет: {html_module.escape(str(description or ''))[:80]}\n"
            f"{e('bag','💼')} Продавец: {seller_uname or f'id{seller_id}'}\n"
            f"{e('cart','🛒')} Покупатель: {buyer_display}"
            f"</blockquote>"
        )
    markup = types.InlineKeyboardMarkup()
    if status == 'created' and seller_id == user_id:
        markup.add(_btn("❌ " + ("Cancel deal" if en else "Отменить сделку"), f"cancel_{deal_id}", "cross"))
    markup.add(_btn("⬅️ " + ("Back" if en else "Назад"), "back_to_deals", "back"))
    show_screen(chat_id, text, markup, message_id)

# ============================================================
# DEAL CARD FOR BUYER
# ============================================================
def show_deal_card_by_id(message, deal_id):
    conn = db()
    c = conn.cursor()
    c.execute("SELECT seller_id, description, amount, currency, payment_method, status FROM deals WHERE deal_id=?", (deal_id,))
    deal = c.fetchone()
    conn.close()

    user_id = message.from_user.id
    en = is_en(user_id)

    if not deal:
        bot.send_message(message.chat.id,
            f"{e('cross','❌')} {'Deal not found.' if en else 'Сделка не найдена.'}", parse_mode="HTML")
        return
    seller_id, description, amount, currency, pay_method, status = deal
    if status != 'created':
        bot.send_message(message.chat.id,
            f"{e('cross','❌')} {'Deal is no longer active.' if en else 'Сделка недействительна.'}", parse_mode="HTML")
        return
    if seller_id == user_id:
        bot.send_message(message.chat.id,
            f"{e('cross','❌')} {'You cannot open your own deal as buyer.' if en else 'Нельзя открыть свою сделку как покупатель.'}", parse_mode="HTML")
        return

    ensure_user(user_id)
    pm_labels = {"card": "🖥 Card", "stars": "⭐ Stars", "crypto": "💎 Crypto"}
    pm_label = pm_labels.get(pay_method, pay_method)
    if en:
        text = (
            f"{e('hand','🤝')} <b>You have been offered a deal</b>\n\n"
            f"<blockquote>"
            f"{e('clip','📋')} Item: {html_module.escape(str(description))}\n"
            f"{e('dollar','💰')} Amount: <b>{amount} {currency}</b>\n"
            f"{e('card','🖥')} Payment: {pm_label}"
            f"</blockquote>"
        )
    else:
        text = (
            f"{e('hand','🤝')} <b>Вам предложена сделка</b>\n\n"
            f"<blockquote>"
            f"{e('clip','📋')} Товар: {html_module.escape(str(description))}\n"
            f"{e('dollar','💰')} Сумма: <b>{amount} {currency}</b>\n"
            f"{e('card','🖥')} Оплата: {pm_label}"
            f"</blockquote>"
        )
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        _btn("✅ " + ("Pay from balance" if en else "Оплатить с баланса"), f"pay_{deal_id}", "check2"),
        _btn("❌ " + ("Decline" if en else "Отказаться"),                  f"cancel_{deal_id}", "cross"),
    )
    bot.send_message(message.chat.id, text, parse_mode="HTML", reply_markup=markup)

# ============================================================
# PAYMENT PROCESSING
# ============================================================
def _process_payment(call, user_id, cid, mid, deal_id):
    en = is_en(user_id)
    conn = db()
    c = conn.cursor()
    c.execute("SELECT seller_id, description, amount, currency, status, seller_username FROM deals WHERE deal_id=?", (deal_id,))
    deal = c.fetchone()
    if not deal or deal[4] != 'created':
        bot.answer_callback_query(call.id,
            "Deal is no longer active." if en else "Сделка недействительна.", show_alert=True)
        conn.close()
        return

    seller_id, description, amount, currency, _, seller_uname = deal
    bal_col = f"bal_{currency.lower()}"
    c.execute(f"SELECT {bal_col} FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    buyer_bal = row[0] if row else 0.0

    if buyer_bal < amount:
        bot.answer_callback_query(call.id,
            f"❌ {'Insufficient funds! Need' if en else 'Недостаточно средств! Нужно'}: {amount} {currency}, "
            f"{'have' if en else 'есть'}: {buyer_bal} {currency}.",
            show_alert=True)
        conn.close()
        return

    buyer_uname = get_username(call.from_user)
    c.execute(f"UPDATE users SET {bal_col}={bal_col}-? WHERE user_id=?", (amount, user_id))
    c.execute("UPDATE deals SET buyer_id=?, buyer_username=?, status='paid' WHERE deal_id=?",
              (user_id, buyer_uname, deal_id))
    conn.commit()
    conn.close()

    bot.delete_message(cid, mid)

    # --- Buyer message ---
    buyer_markup = types.InlineKeyboardMarkup()
    buyer_markup.add(_btn(
        "✅ " + ("Confirm receipt" if en else "Подтвердить получение"),
        f"release_{deal_id}", "check2"
    ))
    if en:
        bot.send_message(user_id,
            f"{e('check2','✅')} <b>Payment successful!</b>\n\n"
            f"<blockquote>"
            f"🔒 Funds frozen by RKD Deals.\n"
            f"Released to seller only after your confirmation.\n"
            f"{e('box','📦')} To receive the item contact: @{SUPPORT_USER}"
            f"</blockquote>\n\n"
            f"👇 Press <b>ONLY</b> after receiving and verifying the item:",
            parse_mode="HTML", reply_markup=buyer_markup)
    else:
        bot.send_message(user_id,
            f"{e('check2','✅')} <b>Оплата прошла успешно!</b>\n\n"
            f"<blockquote>"
            f"🔒 Средства заморожены гарантом RKD Deals.\n"
            f"Переведутся продавцу только после вашего подтверждения.\n"
            f"{e('box','📦')} Для получения товара свяжитесь: @{SUPPORT_USER}"
            f"</blockquote>\n\n"
            f"👇 Нажмите <b>ТОЛЬКО</b> после получения и проверки товара:",
            parse_mode="HTML", reply_markup=buyer_markup)

    # --- CAPS WARNING to seller ---
    seller_en = is_en(seller_id)
    seller_markup = types.InlineKeyboardMarkup()
    seller_markup.add(_btn(
        "✈️ " + ("Contact support" if seller_en else "Связаться с поддержкой"),
        url=f"https://t.me/{SUPPORT_USER}", emoji_key="plane"
    ))
    if seller_en:
        bot.send_message(seller_id,
            f"{e('time','🕐')} <b>Deal #{deal_id} has been PAID!</b>\n\n"
            f"<blockquote>"
            f"Buyer paid for «{html_module.escape(str(description))}».\n"
            f"🔒 Funds are frozen."
            f"</blockquote>\n\n"
            f"⚠️ <b>ATTENTION! DO NOT TRANSFER THE ITEM DIRECTLY TO THE BUYER!</b>\n"
            f"<b>TRANSFER ONLY THROUGH OUR SUPPORT — @{SUPPORT_USER}</b>\n"
            f"<b>OTHERWISE FUNDS WILL NOT BE RELEASED TO YOU!</b>",
            parse_mode="HTML", reply_markup=seller_markup)
    else:
        bot.send_message(seller_id,
            f"{e('time','🕐')} <b>Ваша сделка #{deal_id} ОПЛАЧЕНА!</b>\n\n"
            f"<blockquote>"
            f"Покупатель внёс оплату за «{html_module.escape(str(description))}».\n"
            f"🔒 Средства заморожены."
            f"</blockquote>\n\n"
            f"⚠️ <b>ВНИМАНИЕ! НЕ ПЕРЕДАВАЙТЕ ТОВАР НАПРЯМУЮ ПОКУПАТЕЛЮ!</b>\n"
            f"<b>ПЕРЕДАЧА ТОЛЬКО ЧЕРЕЗ НАШУ ПОДДЕРЖКУ — @{SUPPORT_USER}</b>\n"
            f"<b>ИНАЧЕ СРЕДСТВА НЕ БУДУТ ПЕРЕВЕДЕНЫ ВАМ!</b>",
            parse_mode="HTML", reply_markup=seller_markup)

    try:
        bot.send_message(NOTIFY_ID,
            f"{e('time','🕐')} <b>Угода оплачена!</b>\n\n"
            f"<blockquote>"
            f"🆔 ID: <code>{deal_id}</code>\n"
            f"{e('crown','👑')} Продавець: {seller_uname} (<code>{seller_id}</code>)\n"
            f"{e('cart','🛒')} Покупець: {buyer_uname} (<code>{user_id}</code>)\n"
            f"{e('dollar','💰')} Сума: {amount} {currency}\n"
            f"{e('clip','📋')} Товар: {html_module.escape(str(description)[:60])}"
            f"</blockquote>",
            parse_mode="HTML")
    except Exception:
        pass

# ============================================================
# DEAL RELEASE
# ============================================================
def _release_deal(call, user_id, cid, mid, deal_id):
    en = is_en(user_id)
    conn = db()
    c = conn.cursor()
    c.execute("SELECT seller_id, buyer_id, description, amount, currency, status, seller_username, buyer_username FROM deals WHERE deal_id=?", (deal_id,))
    deal = c.fetchone()

    if not deal or deal[5] != 'paid':
        bot.answer_callback_query(call.id,
            "Deal completion error." if en else "Ошибка завершения.", show_alert=True)
        conn.close()
        return

    seller_id, buyer_id, description, amount, currency, _, seller_uname, buyer_uname_db = deal
    if user_id != buyer_id:
        bot.answer_callback_query(call.id,
            "Only the buyer can confirm receipt." if en else "Только покупатель может подтвердить.",
            show_alert=True)
        conn.close()
        return

    bal_col = f"bal_{currency.lower()}"
    c.execute(f"UPDATE users SET {bal_col}={bal_col}+? WHERE user_id=?", (amount, seller_id))
    c.execute("UPDATE deals SET status='completed' WHERE deal_id=?", (deal_id,))

    c.execute("SELECT referrer_id FROM users WHERE user_id=?", (seller_id,))
    ref = c.fetchone()
    if ref and ref[0]:
        bonus = round(amount * 0.025, 8)
        c.execute(f"UPDATE users SET {bal_col}={bal_col}+?, ref_earned=ref_earned+? WHERE user_id=?",
                  (bonus, bonus, ref[0]))
        ref_en = is_en(ref[0])
        try:
            bot.send_message(ref[0],
                f"{e('star','⭐️')} <b>{'Referral bonus!' if ref_en else 'Реферальный бонус!'}</b>\n"
                + (f"<b>{bonus} {currency}</b> for your referral's deal."
                   if ref_en else
                   f"<b>{bonus} {currency}</b> за сделку реферала."),
                parse_mode="HTML")
        except Exception:
            pass

    conn.commit()
    conn.close()

    bot.delete_message(cid, mid)
    buyer_uname_final = buyer_uname_db or get_username(call.from_user)
    seller_en = is_en(seller_id)

    if en:
        bot.send_message(buyer_id,
            f"{e('check2','✅')} <b>Deal completed!</b>\n\nFunds released to the seller.\nThank you for using RKD Deals! {e('hand','🤝')}",
            parse_mode="HTML")
    else:
        bot.send_message(buyer_id,
            f"{e('check2','✅')} <b>Сделка завершена!</b>\n\nДеньги отправлены продавцу.\nСпасибо за использование RKD Deals! {e('hand','🤝')}",
            parse_mode="HTML")

    if seller_en:
        bot.send_message(seller_id,
            f"{e('dollar','💰')} <b>Deal #{deal_id} completed!</b>\n\n"
            f"<blockquote>Buyer confirmed receipt.\n<b>{amount} {currency}</b> credited to your balance.</blockquote>",
            parse_mode="HTML")
    else:
        bot.send_message(seller_id,
            f"{e('dollar','💰')} <b>Сделка #{deal_id} завершена!</b>\n\n"
            f"<blockquote>Покупатель подтвердил получение.\n<b>{amount} {currency}</b> зачислено на баланс.</blockquote>",
            parse_mode="HTML")

    try:
        bot.send_message(NOTIFY_ID,
            f"{e('check2','✅')} <b>Угода завершена!</b>\n\n"
            f"<blockquote>"
            f"🆔 ID: <code>{deal_id}</code>\n"
            f"{e('crown','👑')} Продавець: {seller_uname} (<code>{seller_id}</code>)\n"
            f"{e('cart','🛒')} Покупець: {buyer_uname_final} (<code>{buyer_id}</code>)\n"
            f"{e('dollar','💰')} Сума: {amount} {currency}"
            f"</blockquote>",
            parse_mode="HTML")
    except Exception:
        pass

# ============================================================
# BALANCE
# ============================================================
def balance_menu(chat_id, user_id, message_id=None):
    en = is_en(user_id)
    conn = db()
    c = conn.cursor()
    c.execute("SELECT bal_rub, bal_uah, bal_kzt, bal_byn, bal_ton, bal_stars, bal_usdt, bal_btc FROM users WHERE user_id=?", (user_id,))
    bal = c.fetchone() or (0,) * 8
    conn.close()

    if en:
        text = (
            f"<b>{e('card','🖥')} Personal Account</b>\n\n"
            f"{e('user','👤')} ID: <code>{user_id}</code>\n\n"
            f"<blockquote>"
            f"{e('dollar','💰')} <b>Balance:</b>\n"
            f"🇷🇺 RUB: {bal[0]}\n🇺🇦 UAH: {bal[1]}\n🇰🇿 KZT: {bal[2]}\n🇧🇾 BYN: {bal[3]}\n"
            f"{e('ton','💎')} TON: {bal[4]}\n{e('stars','⭐')} STARS: {bal[5]}\n{e('usdt','💵')} USDT: {bal[6]}\n{e('btc','🪙')} BTC: {bal[7]}"
            f"</blockquote>"
        )
    else:
        text = (
            f"<b>{e('card','🖥')} Личный кабинет</b>\n\n"
            f"{e('user','👤')} ID: <code>{user_id}</code>\n\n"
            f"<blockquote>"
            f"{e('dollar','💰')} <b>Баланс:</b>\n"
            f"🇷🇺 RUB: {bal[0]}\n🇺🇦 UAH: {bal[1]}\n🇰🇿 KZT: {bal[2]}\n🇧🇾 BYN: {bal[3]}\n"
            f"{e('ton','💎')} TON: {bal[4]}\n{e('stars','⭐')} STARS: {bal[5]}\n{e('usdt','💵')} USDT: {bal[6]}\n{e('btc','🪙')} BTC: {bal[7]}"
            f"</blockquote>"
        )
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        _btn("🖥 " + ("Top up" if en else "Пополнить"),   url=f"https://t.me/{SUPPORT_USER}", emoji_key="card"),
        _btn("💰 " + ("Withdraw" if en else "Вывести"),    url=f"https://t.me/{SUPPORT_USER}", emoji_key="money"),
    )
    markup.add(back_menu_btn(user_id))
    show_screen(chat_id, text, markup, message_id)

# ============================================================
# REFERRALS
# ============================================================
def referrals_menu(chat_id, user_id, message_id=None):
    en = is_en(user_id)
    bot_username = bot.get_me().username
    ref_url = f"https://t.me/{bot_username}?start=ref_{user_id}"
    conn = db()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users WHERE referrer_id=?", (user_id,))
    ref_count = c.fetchone()[0]
    c.execute("SELECT ref_earned FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    earned = row[0] if row else 0.0
    conn.close()

    if en:
        text = (
            f"<b>{e('link','🔗')} Referral Program</b>\n\n"
            f"<blockquote>"
            f"{e('link','🔗')} Link: {ref_url}\n"
            f"{e('people','👥')} Referrals: {ref_count}\n"
            f"{e('dollar','💰')} Earned: {earned} TON"
            f"</blockquote>\n\n"
            f"{e('usdt','💵')} <b>Bonus: 50% of commission from each referral's deal!</b>"
        )
    else:
        text = (
            f"<b>{e('link','🔗')} Реферальная программа</b>\n\n"
            f"<blockquote>"
            f"{e('link','🔗')} Ссылка: {ref_url}\n"
            f"{e('people','👥')} Рефералов: {ref_count}\n"
            f"{e('dollar','💰')} Заработано: {earned} TON"
            f"</blockquote>\n\n"
            f"{e('usdt','💵')} <b>Бонус: 50% от комиссии с каждой сделки реферала!</b>"
        )
    markup = types.InlineKeyboardMarkup()
    markup.add(_btn("🔗 " + ("Copy referral link" if en else "Скопировать реф. ссылку"), "ref_copy", "link"))
    markup.add(back_menu_btn(user_id))
    show_screen(chat_id, text, markup, message_id)

# ============================================================
# LANGUAGE
# ============================================================
def lang_menu(chat_id, user_id, message_id=None):
    text = f"<b>{e('globe','🌐')} Choose language / Выберите язык:</b>"
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        _btn("🇷🇺 Русский", "lang_ru"),
        _btn("🇺🇸 English", "lang_en"),
    )
    markup.add(back_menu_btn(user_id))
    show_screen(chat_id, text, markup, message_id)

# ============================================================
# /add — admin top-up balance
# ============================================================
@bot.message_handler(commands=['add'])
def add_balance(message):
    if (message.chat.id != ADD_BALANCE_CHAT_ID
            or getattr(message, 'message_thread_id', None) != ADD_BALANCE_TOPIC_ID):
        return
    thread_id = message.message_thread_id
    parts = message.text.split()
    if len(parts) != 4:
        bot.send_message(message.chat.id,
            f"{e('cross','❌')} <b>Format:</b> <code>/add user_id amount currency</code>",
            parse_mode="HTML", message_thread_id=thread_id)
        return
    try:
        target_id = int(parts[1])
        amount    = float(parts[2])
        currency  = parts[3].lower()
    except ValueError:
        bot.send_message(message.chat.id,
            f"{e('cross','❌')} Invalid. Example: <code>/add 123456789 500 rub</code>",
            parse_mode="HTML", message_thread_id=thread_id)
        return
    if amount <= 0:
        bot.send_message(message.chat.id,
            f"{e('cross','❌')} Amount must be > 0.", parse_mode="HTML", message_thread_id=thread_id)
        return
    currency_map = {
        'rub':'rub','uah':'uah','kzt':'kzt','byn':'byn',
        'ton':'ton','stars':'stars','usdt':'usdt','btc':'btc',
    }
    mapped = currency_map.get(currency)
    if not mapped:
        bot.send_message(message.chat.id,
            f"{e('cross','❌')} Unknown currency. Available: <code>rub uah kzt byn ton stars usdt btc</code>",
            parse_mode="HTML", message_thread_id=thread_id)
        return
    bal_col = f"bal_{mapped}"
    ensure_user(target_id)
    conn = db()
    c = conn.cursor()
    c.execute(f"UPDATE users SET {bal_col}={bal_col}+? WHERE user_id=?", (amount, target_id))
    c.execute(f"SELECT {bal_col} FROM users WHERE user_id=?", (target_id,))
    new_bal = c.fetchone()[0]
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id,
        f"{e('check2','✅')} Credited <b>{amount} {mapped.upper()}</b> to <code>{target_id}</code>\n"
        f"New balance: <b>{new_bal} {mapped.upper()}</b>",
        parse_mode="HTML", message_thread_id=thread_id)

# ============================================================
# ADMIN PANEL
# ============================================================
def _is_admin(user_id):
    return user_id == ADMIN_ID

def admin_menu(chat_id, message_id=None):
    text = (
        f"<b>{e('shield','🛡')} Админ-панель</b>\n\n"
        f"Поддержка: <code>@{SUPPORT_USER}</code>\n"
        f"Notify ID: <code>{NOTIFY_ID}</code>"
    )
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        _btn("✏️ Изменить юзернейм поддержки", "admin_set_support"),
        _btn("🔔 Изменить Notify ID", "admin_set_notify"),
        _btn("📊 Статистика", "admin_stats"),
    )
    show_screen(chat_id, text, markup, message_id)

@bot.message_handler(commands=['admin'])
def admin_command(message):
    if not _is_admin(message.from_user.id):
        return
    admin_menu(message.chat.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("admin_"))
def handle_admin_callbacks(call):
    user_id = call.from_user.id
    if not _is_admin(user_id):
        bot.answer_callback_query(call.id, "⛔ Access denied", show_alert=True)
        return
    cid, mid = call.message.chat.id, call.message.message_id
    bot.answer_callback_query(call.id)

    if call.data == "admin_set_support":
        show_screen(cid,
            f"{e('plane','✈️')} Введите новый юзернейм поддержки (без @):",
            None, mid)
        user_states[user_id] = {"step": "admin_support_user"}

    elif call.data == "admin_set_notify":
        show_screen(cid,
            f"{e('user','👤')} Введите новый Notify ID (числовой Telegram ID):",
            None, mid)
        user_states[user_id] = {"step": "admin_notify_id"}

    elif call.data == "admin_stats":
        conn = db()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM users")
        users_count = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM deals")
        deals_count = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM deals WHERE status='completed'")
        completed_count = c.fetchone()[0]
        conn.close()
        markup = types.InlineKeyboardMarkup()
        markup.add(_btn("⬅️ Назад", "admin_back"))
        show_screen(cid,
            f"<b>{e('star','⭐')} Статистика</b>\n\n"
            f"Пользователей: <b>{users_count}</b>\n"
            f"Сделок всего: <b>{deals_count}</b>\n"
            f"Завершено: <b>{completed_count}</b>",
            markup, mid)

    elif call.data == "admin_back":
        admin_menu(cid, mid)

def _handle_admin_step(message, user_id, state):
    step = message.text.strip() if message.text else ""
    if state["step"] == "admin_support_user":
        global SUPPORT_USER
        SUPPORT_USER = step.lstrip("@")
        set_setting("support_user", SUPPORT_USER)
        del user_states[user_id]
        bot.send_message(message.chat.id,
            f"{e('check2','✅')} Юзернейм поддержки обновлён: <code>@{SUPPORT_USER}</code>",
            parse_mode="HTML")
        admin_menu(message.chat.id)
        return True
    elif state["step"] == "admin_notify_id":
        global NOTIFY_ID
        try:
            NOTIFY_ID = int(step)
        except ValueError:
            bot.send_message(message.chat.id,
                f"{e('cross','❌')} Введите числовой Telegram ID.", parse_mode="HTML")
            return True
        set_setting("notify_id", NOTIFY_ID)
        del user_states[user_id]
        bot.send_message(message.chat.id,
            f"{e('check2','✅')} Notify ID обновлён: <code>{NOTIFY_ID}</code>",
            parse_mode="HTML")
        admin_menu(message.chat.id)
        return True
    return False

# ============================================================
# START
# ============================================================
if __name__ == "__main__":
    try:
        bot.set_chat_menu_button(menu_button=types.MenuButtonCommands())
        bot.set_my_commands([
            types.BotCommand("start", "Меню"),
        ])
    except Exception as ex:
        print(f"Failed to set menu button/commands: {ex}")
    print("RKD Deals bot started...")
    bot.infinity_polling(timeout=30, long_polling_timeout=20)

# Import kerakli modullar
import telebot
from telebot import types
import json
import os
from datetime import datetime

# ---------------------- CONFIG ----------------------
TOKEN = '7650158615:AAHnJW4tVtC0DuaSoLvpJPT96mD_NAijK70'
ADMIN_ID = 5477499120
REQUIRED_CHANNELS = ['@TarjimaPlay', '@OzgarishSari']
DB_FILE = 'kinobaza.json'
OBUNA_FILE = 'obuna.json'
STAT_FILE = 'statistika.json'

bot = telebot.TeleBot(TOKEN)

# ---------------------- BAZALAR ----------------------
for file, default in [(DB_FILE, {}), (OBUNA_FILE, []), (STAT_FILE, {})]:
    if not os.path.exists(file):
        with open(file, 'w') as f:
            json.dump(default, f)

with open(DB_FILE, 'r') as f:
    try: baza = json.load(f)
    except: baza = {}

with open(OBUNA_FILE, 'r') as f:
    try: obunalar = json.load(f)
    except: obunalar = []

with open(STAT_FILE, 'r') as f:
    try:
        data = json.load(f)
        statistika = {k: set(v) for k, v in data.items()}
    except:
        statistika = {}

# ---------------------- FUNKSIYALAR ----------------------
def check_subscription(user_id):
    not_joined = []
    for ch in REQUIRED_CHANNELS:
        try:
            status = bot.get_chat_member(ch, user_id).status
            if status not in ['member', 'creator', 'administrator']:
                not_joined.append(ch)
        except:
            not_joined.append(ch)
    return not_joined

def log_user(user_id):
    today = datetime.now().strftime("%Y-%m")
    if today not in statistika:
        statistika[today] = set()
    statistika[today].add(user_id)
    with open(STAT_FILE, 'w') as f:
        json.dump({k: list(v) for k, v in statistika.items()}, f)

def send_main_menu(user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🎥 Eng ko‘p ko‘rilgan 10ta film")
    markup.add("🤝 Bizni qo‘llab-quvvatlang", "📞 Admin bilan bog‘lanish")
    bot.send_message(user_id, "🎬 Kodni yuboring, kino tayyor!", reply_markup=markup)

# ---------------------- /start ----------------------
@bot.message_handler(commands=['start'])
def start(msg):
    user_id = msg.from_user.id
    if str(user_id) in obunalar:
        send_main_menu(user_id)
        return
    not_joined = check_subscription(user_id)
    if not_joined:
        markup = types.InlineKeyboardMarkup()
        for i, ch in enumerate(not_joined, 1):
            markup.add(types.InlineKeyboardButton(f"{i}-kanal", url=f"https://t.me/{ch[1:]}"))
        markup.add(types.InlineKeyboardButton("✅ Obunani tasdiqlash", callback_data='check_sub'))
        bot.send_message(user_id, "Quyidagi kanallarga obuna bo‘ling:", reply_markup=markup)
    else:
        obunalar.append(str(user_id))
        with open(OBUNA_FILE, 'w') as f:
            json.dump(obunalar, f)
        send_main_menu(user_id)

# ---------------------- CALLBACK ----------------------
@bot.callback_query_handler(func=lambda call: call.data == 'check_sub')
def callback_check(call):
    user_id = call.from_user.id
    not_joined = check_subscription(user_id)
    if not_joined:
        markup = types.InlineKeyboardMarkup()
        for i, ch in enumerate(not_joined, 1):
            markup.add(types.InlineKeyboardButton(f"{i}-kanal", url=f"https://t.me/{ch[1:]}"))
        markup.add(types.InlineKeyboardButton("✅ Obunani tasdiqlash", callback_data='check_sub'))
        bot.edit_message_text("❌ Siz hali hamma kanallarga obuna bo‘lmadingiz.", call.message.chat.id, call.message.message_id, reply_markup=markup)
    else:
        if str(user_id) not in obunalar:
            obunalar.append(str(user_id))
            with open(OBUNA_FILE, 'w') as f:
                json.dump(obunalar, f)
        send_main_menu(user_id)

# ---------------------- /add ----------------------
@bot.message_handler(commands=['add'])
def add_movie(msg):
    if msg.from_user.id != ADMIN_ID:
        return
    try:
        parts = msg.text.split(' ', 2)
        if len(parts) < 3:
            raise ValueError("Kam parametr")
        kod = parts[1]
        info = parts[2].split('|')
        file_id = info[0].strip()
        sarlavha = info[1].strip() if len(info) > 1 else "Noma'lum"
        sifat = info[2].strip() if len(info) > 2 else ""
        til = info[3].strip() if len(info) > 3 else ""

        if kod not in baza:
            baza[kod] = []

        if isinstance(baza[kod], dict):
            baza[kod] = [baza[kod]]

        baza[kod].append({
            'file_id': file_id,
            'sarlavha': sarlavha,
            'sifat': sifat,
            'til': til,
            'views': 0
        })

        with open(DB_FILE, 'w') as f:
            json.dump(baza, f)

        bot.reply_to(msg, f"✅ Kino qo‘shildi: {kod}")
    except:
        bot.reply_to(msg, "❌ Format xato: /add 111 file_id | Sarlavha | Sifat | Til")

# ---------------------- /del ----------------------
@bot.message_handler(commands=['del'])
def delete_movie(msg):
    if msg.from_user.id != ADMIN_ID:
        return
    try:
        kod = msg.text.split(' ')[1]
        if kod in baza:
            del baza[kod]
            with open(DB_FILE, 'w') as f:
                json.dump(baza, f)
            bot.reply_to(msg, f"🗑️ {kod} kodi o‘chirildi.")
        else:
            bot.reply_to(msg, "❌ Bunday kod yo‘q.")
    except:
        bot.reply_to(msg, "❌ Format: /del 111")

# ---------------------- /reklama ----------------------
@bot.message_handler(commands=['reklama'])
def send_broadcast(msg):
    if msg.from_user.id != ADMIN_ID:
        return
    reply = bot.reply_to(msg, "✉️ Reklama matnini yuboring:")
    bot.register_next_step_handler(reply, broadcast_message)

def broadcast_message(msg):
    text = msg.text
    success = 0
    for uid in obunalar:
        try:
            bot.send_message(uid, f"📢 Reklama:\n\n{text}")
            success += 1
        except:
            continue
    bot.reply_to(msg, f"✅ {success} ta foydalanuvchiga yuborildi.")

# ---------------------- /stats ----------------------
@bot.message_handler(commands=['stats'])
def bot_stats(msg):
    if msg.from_user.id != ADMIN_ID:
        return
    today = datetime.now().strftime("%Y-%m")
    count = len(statistika.get(today, []))
    bot.reply_to(msg, f"📊 *Joriy oyda {count} ta foydalanuvchi* botdan foydalandi.", parse_mode='Markdown')

# ---------------------- FILE ID OLISH ----------------------
@bot.message_handler(content_types=['video'])
def get_file_id(msg):
    if msg.from_user.id == ADMIN_ID:
        file_id = msg.video.file_id
        bot.reply_to(msg, f"📁 File ID: `{file_id}`", parse_mode='Markdown')

# ---------------------- FOYDALANUVCHI TUGMALAR ----------------------
@bot.message_handler(func=lambda msg: msg.text == "🎥 Eng ko‘p ko‘rilgan 10ta film")
def show_top_movies(msg):
    all_movies = []
    for kod, value in baza.items():
        views = sum(k.get('views', 0) for k in (value if isinstance(value, list) else [value]))
        all_movies.append((kod, views))
    sorted_movies = sorted(all_movies, key=lambda x: x[1], reverse=True)[:10]
    matn = "🎥 Eng ko‘p ko‘rilgan kinolar:\n\n"
    for i, (k, v) in enumerate(sorted_movies, 1):
        matn += f"{i}. Kod: {k} | Ko‘rildi: {v} ta\n"
    bot.send_message(msg.chat.id, matn)

@bot.message_handler(func=lambda msg: msg.text == "🤝 Bizni qo‘llab-quvvatlang")
def support_us(msg):
    text = (
        "🤝 *Bizni qo‘llab-quvvatlang!*\n\n"
        "Agar sizga botimiz yoqayotgan bo‘lsa va rivojlanishini xohlasangiz, bizga kichik yordam berishingiz mumkin.\n\n"
        "💳 *Karta raqami:* `5614 6812 1687 9613`\n"
        "👤 *Egasining ismi:* Abbos Sadullayev\n\n"
        "Yordamingiz uchun oldindan rahmat! 🙏"
    )
    bot.send_message(msg.chat.id, text, parse_mode='Markdown')

@bot.message_handler(func=lambda msg: msg.text == "📞 Admin bilan bog‘lanish")
def contact_admin(msg):
    text = (
        "📞 *Admin bilan bog‘lanish:*\n\n"
        "👤 *Ism:* Nodirbek Salomberdiyev\n"
        "📱 *Telegram:* [@Nodirbek_Salomberdiyev](https://t.me/Nodirbek_Salomberdiyev)\n"
        "📞 *Telefon:* +998914543605"
    )
    bot.send_message(msg.chat.id, text, parse_mode='Markdown')

# ---------------------- KINO QIDIRISH ----------------------
def search_movie(msg):
    user_id = msg.from_user.id
    kod = msg.text.strip()
    if kod in baza:
        not_joined = check_subscription(user_id)
        if not_joined:
            markup = types.InlineKeyboardMarkup()
            for i, ch in enumerate(not_joined, 1):
                markup.add(types.InlineKeyboardButton(f"{i}-kanal", url=f"https://t.me/{ch[1:]}"))
            markup.add(types.InlineKeyboardButton("✅ Obunani tasdiqlash", callback_data='check_sub'))
            bot.send_message(user_id, "⛔ Kino olishdan oldin kanallarga obuna bo‘ling.", reply_markup=markup)
            return
        value = baza[kod]
        movies = value if isinstance(value, list) else [value]
        for kino in movies:
            caption = f"🎬 *{kino.get('sarlavha', 'Nomaʼlum')}*\n🎞 *Sifat:* {kino.get('sifat', '')}\n🗣 *Til:* {kino.get('til', '')}\n\n👉 @TarjimaPlay"
            try:
                bot.send_video(user_id, kino['file_id'], caption=caption, parse_mode='Markdown')
            except:
                bot.send_message(user_id, "⚠️ Video yuborishda xatolik yuz berdi.")
            kino['views'] = kino.get('views', 0) + 1
        with open(DB_FILE, 'w') as f:
            json.dump(baza, f)
    else:
        bot.send_message(user_id, "❌ Bunday kodga mos kino topilmadi.")

# ---------------------- ESKI FOYDALANUVCHILARNI STATISTIKAGA QO‘SHISH ----------------------
def sync_old_users_to_stats():
    today = datetime.now().strftime("%Y-%m")
    if today not in statistika:
        statistika[today] = set()
    added = 0
    for user_id in obunalar:
        if user_id not in statistika[today]:
            statistika[today].add(user_id)
            added += 1
    with open(STAT_FILE, 'w') as f:
        json.dump({k: list(v) for k, v in statistika.items()}, f)
    print(f"✅ {added} ta eski foydalanuvchi statistikaga qo‘shildi.")

# ---------------------- HAR QANDAY XABARNI QABUL QILISH ----------------------
@bot.message_handler(func=lambda m: True)
def all_messages(msg):
    log_user(str(msg.from_user.id))  # statistikaga qo‘shiladi
    if not msg.text.startswith("/"):
        search_movie(msg)

# ---------------------- BOTNI ISHGA TUSHIRISH ----------------------
print("🤖 Bot ishga tushdi...")
sync_old_users_to_stats()
bot.infinity_polling()

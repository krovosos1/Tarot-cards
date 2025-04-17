import random
import logging
import json
import os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# Настройка логирования
logging.basicConfig(level=logging.INFO)

BOT_TOKEN = '7576804510:AAHWqDojFwXYhM4szaDWXQ8amcQOlc_nkJU'
USERS_FILE = 'users.json'
CARDS_FILE = 'tarot_cards.json'

# Загрузка карт
if not os.path.exists(CARDS_FILE):
    raise FileNotFoundError("Файл tarot_cards.json не найден!")

with open(CARDS_FILE, 'r', encoding='utf-8') as f:
    TAROT_CARDS = json.load(f)

SPREADS = {
    "one_card": {"count": 1, "name": "Одна карта ✨"},
    "three_cards": {"count": 3, "name": "Три карты 🔮"},
    "situation_problem_advice": {"count": 3, "name": "Ситуация / Проблема / Совет 🧿"},
    "zodiac_week": {"count": 7, "name": "Неделя по знаку 🌟"}
}

THEMES = {
    "love": ["💖 Что в сердце?", "🛑 Что мешает?", "🌟 Совет"],
    "finance": ["💰 Текущая ситуация", "⚠️ Риски", "📈 Потенциал"],
    "career": ["🏢 Позиция сейчас", "🔥 Возможности", "🎯 Рекомендация"],
    "self": ["🧘 Самочувствие", "🌪️ Внутренние блоки", "🌟 Ключ к росту"]
}

KEYWORDS = {
    "love": ["любовь", "отношения", "пара", "чувства", "брак"],
    "work": ["работа", "карьера", "проект", "бизнес", "должность"],
    "money": ["деньги", "финансы", "зарплата", "прибыль"],
    "move": ["переезд", "путешествие", "дорога"],
    "health": ["здоровье", "болезнь", "лечение", "выздоровление"]
}

POSITIVITY = {
    "positive": ["Солнце", "Мир", "Императрица", "Двойка Кубков", "Девятка Пентаклей"],
    "neutral": ["Отшельник", "Шут", "Сила", "Жрица"],
    "negative": ["Башня", "Дьявол", "Тройка Мечей", "Пятёрка Пентаклей"]
}

user_states = {}
user_questions = {}

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        return {}

def save_users(users):
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

users_data = load_users()
def get_zodiac_sign(birthdate_str):
    try:
        birthdate = datetime.strptime(birthdate_str, '%d.%m.%Y')
        day = birthdate.day
        month = birthdate.month
        zodiac = [
            ((1, 20), (2, 18), 'Водолей ♒'),
            ((2, 19), (3, 20), 'Рыбы ♓'),
            ((3, 21), (4, 19), 'Овен ♈'),
            ((4, 20), (5, 20), 'Телец ♉'),
            ((5, 21), (6, 20), 'Близнецы ♊'),
            ((6, 21), (7, 22), 'Рак ♋'),
            ((7, 23), (8, 22), 'Лев ♌'),
            ((8, 23), (9, 22), 'Дева ♍'),
            ((9, 23), (10, 22), 'Весы ♎'),
            ((10, 23), (11, 21), 'Скорпион ♏'),
            ((11, 22), (12, 21), 'Стрелец ♐'),
            ((12, 22), (1, 19), 'Козерог ♑')
        ]
        for start, end, sign in zodiac:
            if (month == start[0] and day >= start[1]) or (month == end[0] and day <= end[1]):
                return sign
    except ValueError:
        return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id in users_data:
        await show_main_menu(update.message)
    else:
        user_states[user_id] = 'waiting_for_name'
        await update.message.reply_text('🔮 Привет! Как тебя зовут?')

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    text = update.message.text.strip()

    if user_id in user_states:
        state = user_states[user_id]
        if state == 'waiting_for_name':
            users_data[user_id] = {'name': text}
            user_states[user_id] = 'waiting_for_birthdate'
            await update.message.reply_text('📅 Теперь напиши дату рождения (ДД.ММ.ГГГГ):')
        elif state == 'waiting_for_birthdate':
            zodiac = get_zodiac_sign(text)
            users_data[user_id]['birthdate'] = text
            users_data[user_id]['zodiac'] = zodiac if zodiac else ''
            save_users(users_data)
            user_states.pop(user_id)
            await update.message.reply_text('✅ Регистрация завершена!')
            await show_main_menu(update.message)
        elif state == 'waiting_for_question':
            user_questions[user_id] = text
            user_states[user_id] = 'waiting_for_question_number'
            keyboard = [
                [InlineKeyboardButton("1 карта ✨", callback_data='question_1')],
                [InlineKeyboardButton("3 карты 🔮", callback_data='question_3')],
                [InlineKeyboardButton("5 карт 🔥", callback_data='question_5')]
            ]
            await update.message.reply_text('🔢 Сколько карт вытянуть?', reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text('Напиши /start для начала работы!')

async def show_main_menu(chat):
    keyboard = [
        [InlineKeyboardButton("1 карта ✨", callback_data='one_card')],
        [InlineKeyboardButton("3 карты 🔮", callback_data='three_cards')],
        [InlineKeyboardButton("Ситуация/Проблема/Совет 🧿", callback_data='situation_problem_advice')],
        [InlineKeyboardButton("Темы раскладов 💖💰", callback_data='choose_theme')],
        [InlineKeyboardButton("Карта дня по знаку 🔥", callback_data='zodiac_card')],
        [InlineKeyboardButton("Неделя по знаку 🌟", callback_data='zodiac_week')],
        [InlineKeyboardButton("✨ Хочу послание", callback_data='want_message')],
        [InlineKeyboardButton("❓ Задать свой вопрос", callback_data='ask_question')]
    ]
    user_info = users_data.get(str(chat.chat.id), {})
    name = user_info.get('name', 'друг')
    zodiac = user_info.get('zodiac', '')
    await chat.reply_text(f'🔮 Привет, {name}! {zodiac}\nВыбери тип расклада:', reply_markup=InlineKeyboardMarkup(keyboard))
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)
    data = query.data
    user_info = users_data.get(user_id, {})
    username = user_info.get('name', 'друг')

    if data == 'one_card' or data == 'three_cards' or data == 'situation_problem_advice':
        spread = SPREADS[data]
        cards = random.sample(TAROT_CARDS, spread['count'])
        reply = f"🔮 {spread['name']} для {username} ({user_info.get('zodiac', '')}):\n\n"
        for card in cards:
            is_reversed = random.choice([True, False])
            orientation = "(Перевернутая 🔄)" if is_reversed else "(Прямая ➡️)"
            meaning = card['reversed_meaning'] if is_reversed else card['meaning']
            reply += f"🃏 {card['name']} {orientation}\n✨ {meaning}\n\n"
        reply += f"✅ Итог:\n{generate_summary(cards, username, user_id)}"
        await query.message.reply_text(reply, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('🏠 Главное меню', callback_data='main_menu')]]))

    elif data == 'choose_theme':
        keyboard = [
            [InlineKeyboardButton("Любовь ❤️", callback_data='theme_love')],
            [InlineKeyboardButton("Финансы 💰", callback_data='theme_finance')],
            [InlineKeyboardButton("Работа 💼", callback_data='theme_career')],
            [InlineKeyboardButton("Саморазвитие 🌱", callback_data='theme_self')]
        ]
        await query.message.reply_text('Выбери тему расклада:', reply_markup=InlineKeyboardMarkup(keyboard))

    elif data.startswith('theme_'):
        theme = data.split('_')[1]
        cards = random.sample(TAROT_CARDS, 3)
        reply = f"🔮 Расклад по теме: {theme.capitalize()} для {username}\n\n"
        for idx, card in enumerate(cards):
            position = THEMES[theme][idx]
            is_reversed = random.choice([True, False])
            orientation = "(Перевернутая 🔄)" if is_reversed else "(Прямая ➡️)"
            meaning = card['reversed_meaning'] if is_reversed else card['meaning']
            reply += f"{position}\n🃏 {card['name']} {orientation}\n✨ {meaning}\n\n"
        reply += f"✅ Итог:\n{generate_summary(cards, username, user_id)}"
        await query.message.reply_text(reply, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('🏠 Главное меню', callback_data='main_menu')]]))

    elif data == 'zodiac_card':
        card = random.choice(TAROT_CARDS)
        is_reversed = random.choice([True, False])
        orientation = "(Перевернутая 🔄)" if is_reversed else "(Прямая ➡️)"
        meaning = card['reversed_meaning'] if is_reversed else card['meaning']
        reply = f"✨ Карта дня для {username} ({user_info.get('zodiac', '')}):\n\n🃏 {card['name']} {orientation}\n✨ {meaning}\n\n"
        reply += f"✅ Итог:\n{generate_summary([card], username, user_id)}"
        await query.message.reply_text(reply, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('🏠 Главное меню', callback_data='main_menu')]]))

    elif data == 'zodiac_week':
        cards = random.sample(TAROT_CARDS, 7)
        days = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
        reply = f"🌟 Неделя для {username} ({user_info.get('zodiac', '')}):\n\n"
        for idx, card in enumerate(cards):
            is_reversed = random.choice([True, False])
            orientation = "(Перевернутая 🔄)" if is_reversed else "(Прямая ➡️)"
            meaning = card['reversed_meaning'] if is_reversed else card['meaning']
            reply += f"📅 {days[idx]}:\n🃏 {card['name']} {orientation}\n✨ {meaning}\n\n"
        reply += f"✅ Итог:\n{generate_summary(cards, username, user_id)}"
        await query.message.reply_text(reply, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('🏠 Главное меню', callback_data='main_menu')]]))

    elif data == 'want_message':
        messages = [
            "✨ Ты на верном пути. Следуй знакам.",
            "🌟 Всё, что ты ищешь, ищет тебя.",
            "🧿 Твои мечты реальны. Доверься себе.",
            "🌙 Даже в самой длинной ночи рождается рассвет.",
            "🔥 Смелость приведёт тебя туда, где ждёт успех."
        ]
        message = random.choice(messages)
        await query.message.reply_text(message, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('🏠 Главное меню', callback_data='main_menu')]]))

    elif data == 'ask_question':
        user_states[user_id] = 'waiting_for_question'
        await query.message.reply_text('📝 Напиши свой вопрос, на который хочешь получить ответ:')

    elif data.startswith('question_'):
        count = int(data.split('_')[1])
        question = user_questions.get(user_id, 'Твой вопрос')
        cards = random.sample(TAROT_CARDS, count)
        reply = f"❓ Вопрос: {question}\n\n"
        for card in cards:
            is_reversed = random.choice([True, False])
            orientation = "(Перевернутая 🔄)" if is_reversed else "(Прямая ➡️)"
            meaning = card['reversed_meaning'] if is_reversed else card['meaning']
            reply += f"🃏 {card['name']} {orientation}\n✨ {meaning}\n\n"
        reply += f"✅ Итог:\n{generate_summary(cards, username, user_id)}"
        await query.message.reply_text(reply, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('🏠 Главное меню', callback_data='main_menu')]]))

    elif data == 'main_menu':
        await show_main_menu(query.message)
def generate_summary(cards, username, user_id):
    today = datetime.now().strftime('%Y-%m-%d')
    if 'last_summaries' not in users_data.get(user_id, {}):
        users_data[user_id]['last_summaries'] = {}
    if today not in users_data[user_id]['last_summaries']:
        users_data[user_id]['last_summaries'][today] = []

    positive = 0
    neutral = 0
    negative = 0
    for card in cards:
        name = card['name']
        if any(p in name for p in POSITIVITY['positive']):
            positive += 1
        elif any(n in name for n in POSITIVITY['negative']):
            negative += 1
        else:
            neutral += 1

    positive_texts = [
        f"✨ {username}, карты сегодня благословляют тебя на новые начинания. Мир вокруг полон возможностей!",
        f"🌟 {username}, судьба открывает перед тобой светлый путь. Следуй за мечтой!",
        f"💖 {username}, всё, что тебе нужно, уже внутри тебя. Верь в себя!"
    ]

    neutral_texts = [
        f"🌿 {username}, сейчас важно проявить терпение. Всё идёт своим чередом.",
        f"🌙 {username}, ответы придут, если прислушаться к внутреннему голосу.",
        f"🧘 {username}, время замедлиться и восстановить внутренний баланс."
    ]

    negative_texts = [
        f"⚡ {username}, испытания временны. Твоя сила — в твоей вере в себя!",
        f"🌑 {username}, тёмные дни уходят. Свет близко!",
        f"🔥 {username}, трудности — это рост. Ты справишься!"
    ]

    if positive > negative:
        options = positive_texts
    elif negative > positive:
        options = negative_texts
    else:
        options = neutral_texts

    used = users_data[user_id]['last_summaries'][today]
    available = [text for text in options if text not in used]

    if not available:
        available = options

    summary = random.choice(available)
    users_data[user_id]['last_summaries'][today].append(summary)
    save_users(users_data)

    return summary

# Команда /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "✨ <b>Добро пожаловать в Таро Бот!</b> ✨\n\n"
        "Вот что я умею:\n\n"
        "🔹 <b>1 карта</b> — быстрый совет от Вселенной.\n"
        "🔹 <b>3 карты</b> — прошлое, настоящее, будущее.\n"
        "🔹 <b>Ситуация / Проблема / Совет</b> — помощь в важных моментах.\n\n"
        "💖 Тематические расклады: любовь, финансы, карьера, саморазвитие.\n"
        "🌟 Карта дня и прогноз на неделю по вашему знаку.\n"
        "❓ Ответы на личные вопросы.\n"
        "✨ Вдохновляющие послания.\n\n"
        "<i>Чтобы начать — нажмите /start или выберите кнопку в меню!</i>"
    )
    await update.message.reply_text(help_text, parse_mode='HTML')

# Запуск приложения
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.run_polling()

if __name__ == "__main__":
    main()

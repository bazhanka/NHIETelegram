import telebot
from telebot import types
import os
import sys
from gamepresent import GamePresent
import random

from telebot.types import InlineKeyboardButton

bot = telebot.TeleBot('7663729317:AAHp2hXoHbNXRZUWgKvJ0Ht-48mfl6np8Pc')

#Класс сессий юзеров

class UserSession:
    def __init__(self, chat_id):
        self.chat_id = chat_id
        self.target_path = None
        self.target_name = None
        self.target_number = None
        self.used_fants = []
        self.fants = []

    def reset(self):
        self.target_path = None
        self.target_name = None
        self.target_number = None
        self.used_fants = []
        self.fants = []


sessions = {}

#Функция для создания пути к файлам

def get_base_path():
    """ Определяет путь к ресурсам, будь то в виде исполняемого файла или при разработке """
    try:
        # PyInstaller создает временную папку _MEIPASS для ресурсов
        base_path = sys._MEIPASS
    except AttributeError:
        # Если работаем в режиме исходного кода, путь не меняется
        base_path = os.path.abspath(".")

    return base_path
#Создание словаря с данными пользователя
user_data = {}

def get_user_data(chat_id):
    if chat_id not in user_data:
        user_data[chat_id] = {'target_path': None, 'target_name': None, 'target_number': None}
    return user_data[chat_id]

def set_user_data(chat_id, key, value):
    if chat_id not in user_data:
        user_data[chat_id] = {}
    user_data[chat_id][key] = value

def get_session(chat_id):
    if chat_id not in sessions:
        sessions[chat_id] = UserSession(chat_id)
    return sessions[chat_id]

# Загрузка доступных пакетов
PACKS = []
dir_name = os.path.join(get_base_path(), 'TkinterNHIE')
test = os.listdir(dir_name)
for item in test:
    if item.endswith(".txt"):
        PACKS.append(item)
paths_packs = {pack.replace('.txt', ''): os.path.join(dir_name, pack) for pack in PACKS}

#Функция для создания клавиатур

def create_keyboard(buttons, row_width=3):
    keyboard = types.InlineKeyboardMarkup(row_width=row_width)
    for text, callback_data in buttons:
        keyboard.add(InlineKeyboardButton(text=text, callback_data=callback_data))
    return keyboard

#Функция для старта бота

@bot.message_handler(commands=["start"])
def start(m, res=False):
    session = get_session(m.chat.id)
    session.reset()
    main_keyboard = create_keyboard([
        ('Выбрать существующий пакет фактов', 'existing_pack'),
        ('Создать свой пакет фактов', 'new_pack'),
        ('Как играть?', 'how_to_play')
    ], row_width=1)
    bot.send_message(m.chat.id, ' Выбирай существующий пакет\nИли давай создадим твой собственный',  reply_markup=main_keyboard)


# Обработчик выбора пакета
def packs_keyboard(chat_id):
    keyboard_packs = create_keyboard([(pack.replace('.txt', ''), pack.replace('.txt', '')) for pack in PACKS], row_width=3)
    bot.send_message(chat_id, "Вот пакеты, которые у меня есть!", reply_markup=keyboard_packs)


# Клавиатура перед игрой
def play_keyboard(chat_id):
    play_key = create_keyboard([
        ('Давай играть!', 'play'),
        ('Начнем сначала!', 'main_menu')
    ])
    bot.send_message(chat_id, "Выбери действие:", reply_markup=play_key)

#Функция-ответ для выбора пакета

def pack_chosen(session, call):
    if call.data in paths_packs:
        session.target_path = paths_packs[call.data]
        session.target_name = call.data
        bot.send_message(call.message.chat.id, f"Ты выбрал пакет: {call.data}")
        bot.send_message(call.message.chat.id, "Введи количество человек!")
        bot.register_next_step_handler(call.message, lambda msg: get_number(session, msg))

#Функция для запроса количества игроков

def get_number(session, message):
    try:
        session.target_number = int(message.text)
        if session.target_number >= 3:
            bot.send_message(message.chat.id, f"Играет {session.target_number} человек")
            final_path = make_present(session)
            with open(final_path, 'rb') as f:
                bot.send_document(message.chat.id, f)
            play_keyboard(message.chat.id)
        else:
            bot.send_message(message.chat.id, "Упс! Игроков должно быть не меньше трех")
            bot.register_next_step_handler(message, lambda msg: get_number(session, msg))
    except ValueError:
        bot.send_message(message.chat.id, "Введите корректное число")
        bot.register_next_step_handler(message, lambda msg: get_number(session, msg))


#Функция для создания презентации

def make_present(session):
    output_file = f"{session.target_name}.pptx"
    count = 1
    while output_file in test:
        output_file = f"{session.target_name}_{count}.pptx"
        count += 1
    return GamePresent(session.target_number, session.target_path, output_file).generate_table()

#Функция для запроса имени и количества человек в новом пакете


def new_pack_number (session, message):
    try:
        session.target_number = int(message.text)
        if session.target_number >= 3:
            bot.send_message(message.chat.id, text= f"Играет: {session.target_number} человек")
            bot.send_message(message.chat.id, text="Введите название пакета!")
            bot.register_next_step_handler(message, lambda msg: make_new_pack(session, msg))
        else:
            bot.send_message(message.chat.id, text="Упс! Игроков должно быть не меньше трех")
            bot.register_next_step_handler(message, lambda msg: get_number(session, msg))
    except ValueError:
        bot.send_message(message.chat.id, text="Введите корректное число")
        bot.register_next_step_handler(message, lambda msg: get_number(session, msg))

#Функция для создания нового пакета

def make_new_pack(session, message):
    session.target_name = message.text
    res_count = 9 + int(session.target_number)
    count = 0

    # Сообщаем пользователю, сколько фанты ему нужно написать
    bot.send_message(
        message.chat.id,
        text="Я рекомендую написать не меньше " + str(res_count) + " фантов для " + str(session.target_number) + " человек.")

    # Начинаем процесс написания фантов
    request_next_fant(session, message, count, res_count)


def request_next_fant(session, message, count, res_count):
    # Сообщаем пользователю, сколько фантов уже написано
    bot.send_message(
        message.chat.id,
        text="Ты написал " + str(count) + " фантов из " + str(res_count))

    # Если достигли нужного количества фантов, завершаем процесс
    if count >= res_count:
        finalize_pack(session, message)
    else:
        # Ожидаем следующего ввода от пользователя
        bot.register_next_step_handler(message, lambda m: save_fant_and_continue(session, m, count, res_count))


def save_fant_and_continue(session, message, count, res_count):
    # Сохраняем введённый фант в файл
    write_pack(session, message)

    # Увеличиваем счётчик и переходим к следующему фантy
    request_next_fant(session, message, count + 1, res_count)


def write_pack(session, message):
    pack_name = str.replace(str(session.target_name), '.txt', '')
    new_file = open(pack_name, 'a+', encoding='utf-8')
    new_file.write(message.text + "\n")
    new_file.close()  # Не забудь закрыть файл
    session.target_path = os.path.join(get_base_path(), pack_name)


def finalize_pack(session, message):
    # Заканчиваем создание пака и отправляем файл пользователю
    final_path = make_present(session)
    with open(final_path, 'rb') as f:
        bot.send_document(message.chat.id, f)
    play_keyboard(message.chat.id)


#Функция для показа фантов

def letsplay(session, chat_id):
    if not session.fants:
        with open(session.target_path, encoding='utf-8') as f:
            session.fants = [line.strip() for line in f]
    if not session.fants:
        bot.send_message(chat_id, "Фанты закончились. У кого больше совпадений, тот победил!")
        session.__init__()
    else:
        fant = random.choice(session.fants)
        session.fants.remove(fant)
        session.used_fants.append(fant)
        bot.send_message(chat_id, fant)
        bingo_keyboard(chat_id)

def bingo_final(session, chat_id):
    bot.send_message(chat_id, "Проверь все фанты победителя:")
    for line in session.used_fants:
        print(line)
        bot.send_message(chat_id, line)
    bingo_keyboard(chat_id)

def bingo_keyboard (chat_id):
    bingo_key = create_keyboard([
        ('Еще фант!', 'fant'),
        ('Бинго!','bingo'),
        ('Давай закончим!', 'finish')
    ], row_width=1)
    bot.send_message(chat_id, text="Выбери действие:", reply_markup=bingo_key)

# Алгоритм нажатия на кнопки

@bot.callback_query_handler(func=lambda call: True)
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    session = get_session(call.message.chat.id)
    if call.data == 'existing_pack':
        packs_keyboard(call.message.chat.id)
    elif call.data == 'new_pack':
        bot.send_message(call.message.chat.id, "Введи количество человек!")
        bot.register_next_step_handler(call.message, lambda msg: new_pack_number(session, msg))
    elif call.data == 'how_to_play':
        bot.send_message(call.message.chat.id, text="Добро пожаловать в Я НИКОГДА НЕ БИНГО! \n\nИгра предназначена для компаний из более чем 3 человек и представляет собой микс из Я НИКОГДА НЕ... и БИНГО.\n\nДля начала выберите факты, с которыми вы будете играть. У меня есть готовые тематические пакеты, а также опция создать пакет самостоятельно, чтобы максимально кастомизировать его под вашу компанию. \n\nЗатем попросите бота создать карточки под ваше число игроков. Вы получите файл pptx который можно распечатать и раздать гостям, или же заскринить постранично и отправить участникам прямо в телеграме. \n\nИ вот, наконец, сами правила. Попросите бота показывать вам факты по одному. Если факт есть в карточке игрока, его задача - отметить его, как в БИНГО. Если игрок делал то, что сказано в факте, то пусть отметка будет зеленого цвета. Если не делал - красного. Если вы играете с алкоголем - тот, кто делал, еще и пьет. ВНИМАНИЕ! Убиться можно очень быстро, поэтому выбирайте максимально низкоградусные напитки, а то до конца игры никто не доживет. Глоток пива - идеальное мерило. \n\nЗадача игроков - собрать БИНГО - три заполененных факта в ряд (горизонталь/вертикаль/диагональ). Простой вариант - любых факта, сложный - факта одного вида (если все зеленые - БИНГО, все красные - VIRGIN БИНГО). Бот по кнопке БИНГО подскажет, какие факты уже были, чтобы вы могли проверить игрока. После того, как 3-5 игроков крикнули БИНГО, можно завершать игру или продолжать до тех пор, пока кто-то не заполнит карточку целиком (тут уже не важно, каким цветом отмечены факты).\n\nЕсли вдруг факты закончились раньше, чем кто-то собрал карточку, побеждает игрок с наибольшим кол-вом отмеченных фактов. \n\nНе забывайте рассказывать истории о фактах, которые вы отмечаете зеленым - это делает игру душевной и интересной. \n\nПРИМЕР ИГРЫ:\n\nБот называет факт: Я НИКОГДА НЕ ПРЫГАЛ С ПАРАШЮТОМ.\nУ Васи и у Пети есть в карточках этот факт. Вася прыгал с парашютом, поэтому он деалет глоток пива и отмечает факт зеленым. Петя не прыгал с парашютом, поэтому он отмечает этот факт красным."
                                                    )
    elif call.data == 'play_key':
        play_keyboard(call.message.chat.id)
    elif call.data == 'main_menu':
        start(call.message)
    elif call.data == 'play':
        letsplay(session, call.message.chat.id)
    elif call.data == 'fant':
        letsplay(session, call.message.chat.id)
    elif call.data == 'bingo':
        bingo_final(session, call.message.chat.id)
    elif call.data == 'finish':
        bot.send_message(call.message.chat.id, "Спасибо за игру! Пока!")
    else:
        pack_chosen(session, call)

# Запускаем бота

bot.polling(none_stop=True, interval=3)
import asyncio
import logging
import os
import string
import random
import pymongo
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils.executor import start_webhook
from aiogram.contrib.fsm_storage.memory import MemoryStorage

API_TOKEN = os.environ['TG_TOKEN']


# webhook settings
WEBHOOK_HOST = 'https://mbard.alwaysdata.net/'
WEBHOOK_PATH = '/bot/'
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

# webserver settings
WEBAPP_HOST = '::'  # or ip
WEBAPP_PORT = 8350

logging.basicConfig(level=logging.INFO)

loop = asyncio.get_event_loop()
bot = Bot(token=API_TOKEN, loop=loop)
dp = Dispatcher(bot, storage=MemoryStorage())

# connect to DB
client = pymongo.MongoClient(
    "mongodb+srv://maksymbardakh:qwerty1234@cluster0.lzmhsjl.mongodb.net/?retryWrites=true&w=majority")
db = client.get_database("mbardBotDB")

# general parameters
passwords = {}
last_generated_password = None
digits = False
special_chars = False
length = 8


class WaitingState(StatesGroup):
    waiting_for_new_length = State()
    waiting_for_creation_name = State()
    waiting_for_deleting_name = State()


@dp.message_handler(commands=['start'])
async def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("Згенерувати пароль")
    btn2 = types.KeyboardButton("Параметри")
    btn3 = types.KeyboardButton("Збережені паролі")
    markup.add(btn1, btn2, btn3)
    await bot.send_message(message.chat.id,
                           text="Привіт, {0.first_name}! Я бот, генератор паролів🛡.".format(message.from_user),
                           reply_markup=markup)


@dp.message_handler(content_types=['text'])
async def func(message: types.Message, state: FSMContext):
    global special_chars, digits, last_generated_password
    if message.text == "Згенерувати пароль" or message.text == "Згенерувати інший":
        password = await generate_password()
        last_generated_password = password
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton("Зберегти пароль")
        btn2 = types.KeyboardButton("Згенерувати інший")
        btn3 = types.KeyboardButton("Параметри")
        back = types.KeyboardButton("Повернуться в головне меню")

        markup.add(btn1, btn2, btn3, back)
        await bot.send_message(message.chat.id, text=f'Ваш пароль: {password}', reply_markup=markup)

    elif message.text == "Параметри":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton("Змінити довжину пароля")

        if digits:
            btn2 = types.KeyboardButton("Генерувати паролі без цифр")
        else:
            btn2 = types.KeyboardButton("Генерувати паролі з цифрами")

        if special_chars:
            btn3 = types.KeyboardButton("Генерувати паролі без спеціальних символів")
        else:
            btn3 = types.KeyboardButton("Генерувати паролі зі спеціальними символами")

        back = types.KeyboardButton("Повернуться в головне меню")
        markup.add(btn1, btn2, btn3, back)

        await bot.send_message(message.chat.id,
                               text=f'Поточні параметри: \r\n Довжина пароля: {length}'
                                    f'\r\n Використання цифр: {digits}'
                                    f'\r\n Використання спеціальних символів: {special_chars}',
                               reply_markup=markup)

    elif message.text == "Змінити довжину пароля":
        await bot.send_message(message.chat.id, text='Введіть бажану довжину:')
        await WaitingState.waiting_for_new_length.set()

    elif message.text == "Генерувати паролі з цифрами":
        digits = True
        await bot.send_message(message.chat.id, text="Налаштування успішно змінені")

    elif message.text == "Генерувати паролі без цифр":
        digits = False
        await bot.send_message(message.chat.id, text="Налаштування успішно змінені")

    elif message.text == "Генерувати паролі зі спеціальними символами":
        special_chars = True
        await bot.send_message(message.chat.id, text="Налаштування успішно змінені")

    elif message.text == "Генерувати паролі без спеціальних символів":
        special_chars = False
        await bot.send_message(message.chat.id, text="Налаштування успішно змінені")

    elif message.text == "Повернуться в головне меню":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton("Згенерувати пароль")
        btn2 = types.KeyboardButton("Параметри")
        btn3 = types.KeyboardButton("Збережені паролі")
        markup.add(btn1, btn2, btn3)
        await bot.send_message(message.chat.id, text="Чекаю нових команд", reply_markup=markup)

    elif message.text == "Зберегти пароль":
        await bot.send_message(message.chat.id, text='Введіть ім\'я паролю:')
        await WaitingState.waiting_for_creation_name.set()

    elif message.text == "Збережені паролі":
        user_id = message.from_user.id
        saved_passwords = await get_saved_passwords(user_id)
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

        if saved_passwords:
            btn1 = types.KeyboardButton("Видалити пароль")
            back = types.KeyboardButton("Повернуться в головне меню")
            markup.add(btn1, back)
            response_text = "Ваші збережені паролі:\n"
            for password_info in saved_passwords:
                response_text += f"_*{password_info['name']}*_: {password_info['password']}\n"
        else:
            btn1 = types.KeyboardButton("Згенерувати пароль")
            btn2 = types.KeyboardButton("Параметри")
            btn3 = types.KeyboardButton("Збережені паролі")
            markup.add(btn1, btn2, btn3)
            response_text = "У вас немає збережених паролів."

        await bot.send_message(message.chat.id, text=response_text, parse_mode=types.ParseMode.MARKDOWN_V2,
                               reply_markup=markup)

    elif message.text == "Видалити пароль":
        await bot.send_message(message.chat.id, text='Введіть ім\'я паролю:')
        await WaitingState.waiting_for_deleting_name.set()


@dp.message_handler(state=WaitingState.waiting_for_new_length)
async def func(message: types.Message, state: FSMContext):
    global length
    try:
        length = int(message.text)
        if length < 4 or length > 25:
            await bot.send_message(message.chat.id, text='Будь ласка введіть число у проміжку від 4 до 25')
    except ValueError:
        await bot.send_message(message.chat.id, text='Будь ласка введіть коректне число')
    else:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton("Згенерувати пароль")
        btn2 = types.KeyboardButton("Параметри")
        btn3 = types.KeyboardButton("Збережені паролі")
        markup.add(btn1, btn2, btn3)
        await bot.send_message(message.chat.id, text='Довжина успішно змінена', reply_markup=markup)
        await state.finish()


@dp.message_handler(state=WaitingState.waiting_for_creation_name)
async def func(message: types.Message, state: FSMContext):
    global last_generated_password, passwords
    name = message.text
    user = message.from_user.id
    result = await save_password(user, name, last_generated_password)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("Згенерувати пароль")
    btn2 = types.KeyboardButton("Параметри")
    btn3 = types.KeyboardButton("Збережені паролі")
    markup.add(btn1, btn2, btn3)
    await bot.send_message(message.chat.id, text=result, reply_markup=markup)
    await state.finish()


@dp.message_handler(state=WaitingState.waiting_for_deleting_name)
async def func(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    password_name = message.text
    deleted = await delete_saved_password(user_id, password_name)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("Згенерувати пароль")
    btn2 = types.KeyboardButton("Параметри")
    btn3 = types.KeyboardButton("Збережені паролі")
    markup.add(btn1, btn2, btn3)
    if deleted:
        await bot.send_message(
            message.chat.id, text=f"Пароль '{password_name}' видалено успішно.", reply_markup=markup
        )
    else:
        await bot.send_message(
            message.chat.id, text=f"Не вдалося знайти пароль '{password_name}'.", reply_markup=markup
        )

    await state.finish()


async def generate_password():
    global length, digits, special_chars

    characters = string.ascii_letters
    if digits:
        characters += string.digits
    if special_chars:
        characters += "$%&?@"

    password = ''.join(random.choice(characters) for _ in range(length))
    return password


async def save_password(user_id, name, password):
    try:
        passwords_collection = db.get_collection("passwords")
        passwords_collection.insert_one({"user": user_id, "name": name, "password": password})
        return "Пароль успішно збережено"
    except Exception as e:
        return f"Під час зберігання виникла помилка: {e}"


async def get_saved_passwords(user_id):
    passwords_collection = db.get_collection("passwords")
    saved_passwords = passwords_collection.find({"user": user_id})
    return saved_passwords


async def delete_saved_password(user_id, password_name):
    passwords_collection = db.get_collection("passwords")
    result = passwords_collection.delete_one({"user": user_id, "name": password_name})
    return result.deleted_count > 0


async def on_startup(dp):
    await bot.set_webhook(WEBHOOK_URL)


async def on_shutdown(dp):
    pass


if __name__ == '__main__':
    start_webhook(dispatcher=dp, webhook_path=WEBHOOK_PATH, on_startup=on_startup, on_shutdown=on_shutdown,
                  skip_updates=True, host=WEBAPP_HOST, port=WEBAPP_PORT)

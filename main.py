from aiogram.types import *
from aiogram import Bot, Dispatcher, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
import os
from datetime import datetime

TOKEN = "YOUR_BOT_TOKEN"  # Your bot token
LOGS_FOLDER = "logs"  # Folder to store logs

# Ensure the logs folder exists
if not os.path.exists(LOGS_FOLDER):
    os.makedirs(LOGS_FOLDER)

storage = MemoryStorage()
bot = Bot(token=TOKEN, parse_mode="HTML")
dp = Dispatcher(bot, storage=storage)

# Class definition for defining states
class GetMessageStatesGroup(StatesGroup):
    get_message = State()

# Handler for /start and /help commands
@dp.message_handler(commands=['start', "help"])
async def start(message: Message, state: FSMContext):
    args = message.get_args()
    command = message.get_command()

    # Respond to /start or /help command
    if (command == "/start" and not args) or (command == "/help"):
        me = await bot.me
        await message.answer(f"Your message here")
    else:
        # Move to the get_message state
        await GetMessageStatesGroup.first()
        await state.update_data(chat_id=args.strip())
        await message.answer(f"Your message here")

# Handler for receiving message in get_message state
@dp.message_handler(state=GetMessageStatesGroup.get_message, content_types=["any"])
async def get_message(message: Message, state: FSMContext):
    data = await state.get_data()
    await state.finish()
    chat_id = data["chat_id"]
    message_id = data.get("message_id")

    try:
        # Send anonymous message
        await bot.send_message(chat_id, "Your message here")
        await bot.copy_message(chat_id, message.chat.id, message.message_id, reply_to_message_id=message_id, reply_markup=markup)
    except Exception as e:
        print(e)
        await message.answer("Failed to send message to this user")
    else:
        await message.answer("Your message here")

    # Save the message to a log file
    log_filename = os.path.join(LOGS_FOLDER, f"log_{chat_id}.txt")
    with open(log_filename, "a", encoding="utf-8") as log_file:
        timestamp = datetime.now().strftime("%H:%M:%S %d.%m.%Y")
        log_file.write(f"{message.text} - @{message.from_user.username} - {timestamp}\n")

    me = await bot.me

    await message.answer(f"Your message here")

# Handler for responding to an anonymous message
@dp.callback_query_handler(lambda callback: callback.data.startswith("answer"))
async def answer(callback: CallbackQuery, state: FSMContext):
    _, chat_id, message_id = callback.data.split("_")

    await GetMessageStatesGroup.first()
    await state.update_data(chat_id=chat_id, message_id=message_id)

    await callback.message.reply(f"Your message here")

    # Save the answer to a log file
    log_filename = os.path.join(LOGS_FOLDER, f"log_{chat_id}.txt")
    with open(log_filename, "a", encoding="utf-8") as log_file:
        timestamp = datetime.now().strftime("%H:%M:%S %d.%m.%Y")
        log_file.write(f" @{callback.from_user.username} - {callback.message.text} - {timestamp}\n")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)

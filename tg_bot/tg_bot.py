import logging
import os
import soundfile as sf
from aiogram import Bot, Dispatcher, Router, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, File, InlineKeyboardButton, CallbackQuery, FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder
from pathlib import Path
from decouple import config

from time import sleep

from stt.stt import STT
from tts.tts import TTS
from translation.translation import TranslationModel

class language_handler:
    '''Храним языки для всех юзеров'''
    def __init__(self):
        self.users_lang = {}
    
    def change_user_language(self, user_id, language):
        '''Меняем язык юзера'''
        self.users_lang[user_id] = language
    
    def get_user_language(self, user_id):
        '''Возвращаем язык юзера'''
        return self.users_lang[user_id]
    
    def register_user(self, user_id):
        '''По умолчанию английский язык'''
        if user_id not in self.users_lang:
            self.users_lang[user_id] = 'en'

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
'''Инициализация всех действующих объектов'''
bot = Bot(token=config('TOKEN'), default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())
lh = language_handler()
languages_mapping = {'en': 'Английский', 'es': 'Испанский', 'de': 'Немецкий'}
router = Router()
stt_model = STT()
tts_model = TTS()
translation_model = TranslationModel()

@router.message(CommandStart())
async def cmd_start(message: Message):
    mes = 'Привет! Я чат-бот, переводящий твоё голосовое на выбранный язык. Для начала выбери желаемый язык.'
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(
        text="Выбрать язык",
        callback_data='change_language'))
    await message.answer(mes, reply_markup=builder.as_markup())

@dp.callback_query((F.data == "change_language"))
async def language_selecting_from_start(callback: CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Английский", callback_data='lang_en'))
    builder.add(InlineKeyboardButton(text="Испанский", callback_data='lang_es'))
    builder.add(InlineKeyboardButton(text="Немецкий", callback_data='lang_de'))
    await callback.message.answer('Выберите один из представленных языков.', reply_markup=builder.as_markup())

@router.message(F.text, Command('change_language'))
async def language_selecting(message: Message):
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Английский", callback_data='lang_en'))
    builder.add(InlineKeyboardButton(text="Испанский", callback_data='lang_es'))
    builder.add(InlineKeyboardButton(text="Немецкий", callback_data='lang_de'))
    await message.answer('Выберите один из представленных языков.', reply_markup=builder.as_markup())


@dp.callback_query(F.data.startswith('lang'))
async def selected_language(callback: CallbackQuery):
    '''Выбор языка'''
    lang = callback.data.split('_')[1]
    user_id = callback.from_user.id
    lh.change_user_language(user_id, lang)
    await callback.message.answer(f'Вы выбрали язык {languages_mapping[lang]}. Теперь отправьте голосовое или текстовое сообщение')

async def handle_file(file: File, file_name: str, path: str):
    Path(f"{path}").mkdir(parents=True, exist_ok=True)

    await bot.download(file_path=file.file_path, destination=f"{path}/{file_name}")

@router.message(F.voice)
async def voice_message(message: Message):
    '''Основная функция обработки голосового сообщения'''
    #для начала проверяем параметры моделей
    user_id = message.from_user.id
    user_lang = lh.get_user_language(user_id)
    if tts_model.get_current_language() != user_lang:
        tts_model.change_language(user_lang)
    if translation_model.get_lang() != user_lang:
        translation_model.change_lang(user_lang)
    #обрабатываем входное голосовое
    file_id = message.voice.file_id
    msg = await message.answer(f'Принял голосовое сообщение!')
    if not os.path.isdir(fr'/stt_temp/user_{user_id}'):
        os.makedirs(fr'/stt_temp/user_{user_id}')
    #Сохраняем как ogg и переводим в wav
    await bot.download(file_id, fr"/stt_temp/user_{user_id}/input_{user_id}.ogg")
    data, samplerate = sf.read(fr'/stt_temp/user_{user_id}/input_{user_id}.ogg')
    sf.write(fr'/stt_temp/user_{user_id}/input_{user_id}.wav', data, samplerate)
    #Получаем текст
    text = stt_model.wave_to_text(user_id)
    await msg.delete()
    await message.answer(f'Полученный текст:\n {text}')
    msg = await message.answer(f'Переводим...')
    #переводим
    text_translation = translation_model.translate(text)
    await msg.delete()
    await message.answer(f'Перевод текста:\n {text_translation}')
    #формируем голосовое и отправляем
    msg = await message.answer(f'Формируем голосовое сообщение...')
    tts_model.text_to_speech(text_translation, user_id)
    await msg.delete()
    path = f'/stt_temp/user_{user_id}/{user_id}_tts.wav'
    voice_mes = FSInputFile(path=path)
    await bot.send_voice(user_id, voice=voice_mes)


@router.message(F.text)
async def text_message(message: Message):
    '''Основная функция обработки голосового сообщения'''
    #для начала проверяем параметры моделей
    user_id = message.from_user.id
    lh.register_user(user_id)
    user_lang = lh.get_user_language(user_id)
    if tts_model.get_current_language() != user_lang:
        tts_model.change_language(user_lang)
    if translation_model.get_lang() != user_lang:
        translation_model.change_lang(user_lang)
    text = message.text
    #переводим
    msg = await message.answer(f'Переводим...')
    text_translation = translation_model.translate(text)
    await msg.delete()
    await message.answer(f'Перевод текста:\n {text_translation}')
    #формируем голосовое и отправляем
    msg = await message.answer(f'Формируем голосовое сообщение...')
    tts_model.text_to_speech(text_translation, user_id)
    await msg.delete()
    path = f'/stt_temp/user_{user_id}/{user_id}_tts.wav'
    voice_mes = FSInputFile(path=path)
    await bot.send_voice(user_id, voice=voice_mes)
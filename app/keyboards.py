from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.database.requests import get_notes

start_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='Создать заметку 🖊️', callback_data='add_note'),
         InlineKeyboardButton(text='Посмотреть заметки 📓', callback_data='show_note')]
    ],
    resize_keyboard=True,
)

manage_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Удалить', callback_data='delete'),
     InlineKeyboardButton(text='Изменить', callback_data='edit')],
    [InlineKeyboardButton(text='Предыдущая', callback_data='back'),
     InlineKeyboardButton(text='В меню', callback_data='menu'),
     InlineKeyboardButton(text='Следующая', callback_data='next')]
])


cancel_cb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Отмена', callback_data='cancel')]
])

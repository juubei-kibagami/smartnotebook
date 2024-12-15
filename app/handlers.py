from aiogram import F, Router
from aiogram.methods import EditMessageText
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.filters.callback_data import CallbackData

from sqlalchemy.ext.asyncio import AsyncSession

from app.keyboards import start_kb, manage_kb, cancel_cb
import app.database.requests as rq


router = Router()


class Note(StatesGroup):
    note = State()


class NoteContent(StatesGroup):
    new_note = State()
    content = State()
    cur_page = State()
    msg_id = State()
    chat_id = State()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await rq.set_user(message.from_user.id)  # передача тг id в бд
    sent_msg = await message.answer('Привет! Я бот-заметка.', reply_markup=start_kb)  # сообщение при команде start
    bot_msg_id = sent_msg.message_id  # id сообщения, которое отправляет бот
    bot_chat_id = sent_msg.chat.id  # id чата для бота
    await state.set_state(NoteContent.msg_id)  # фсм встает на принятие id сообщения
    await state.update_data(msg_id=bot_msg_id)  # фсм получает id сообщения
    await state.set_state(NoteContent.chat_id)  # фсм встает на принятие id чата для бота
    await state.update_data(chat_id=bot_chat_id)  # фсп получает id чата
    print(bot_msg_id)


@router.callback_query(F.data == 'add_note')
async def get_note(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Note.note)
    await callback.message.edit_text(text='Напишите заметку(не более 200 символов)', reply_markup=cancel_cb)


@router.callback_query(F.data == 'cancel')
async def cancel(callback: CallbackQuery):
    await callback.message.edit_text(text='Вы в главном меню!', reply_markup=start_kb)


@router.message(Note.note)
async def save_note(message: Message, state: FSMContext):
    bot = message.bot  # экземпляр бота
    await state.update_data(note=message.text)  # получаем текст заметки из сообщения пользователя
    await rq.create_note(tg_id=message.from_user.id, note=message.text)  # создаем заметку в бд
    await message.delete()  # удаляем сообщение пользователя
    data = await state.get_data()  # получаем данные из фсм
    msg_id = data['msg_id']  # получаем сообщение от бота
    chat_id = data['chat_id']  # получаем id чата
    print(msg_id)
    await bot.edit_message_text(text='Заметка добавлена!\nВы находитесь в главном меню.', message_id=int(msg_id), chat_id=chat_id, reply_markup=start_kb)


@router.callback_query(F.data == 'show_note')
async def show_note(callback: CallbackQuery, state: FSMContext):
    await state.set_state(NoteContent.content)
    notes = await rq.get_notes(tg_id=callback.from_user.id)
    if notes:
        page_data = [note for note in notes.values()]  # список заметок
        await state.update_data(content=page_data)  # в фсм поступил список заметок
        current_page = 0  # первая страница
        await state.set_state(NoteContent.cur_page)
        await state.update_data(cur_page=current_page)  # в фсм передаем текущую страницу
        await callback.message.edit_text(text=f'{page_data[current_page]}', reply_markup=manage_kb)
    else:
        await callback.message.edit_text(text='Что-то пошло не так, обратитесь в поддержку.', reply_markup=start_kb)


@router.callback_query(F.data == 'delete')
async def delete_note(callback: CallbackQuery, state: FSMContext):
    await callback.answer('')
    data = await state.get_data()  # получаем данные заметок
    notes = data['content']  # заметки
    page = data['cur_page']  # текущая заметка
    if notes:
        await rq.delete_note(tg_id=callback.from_user.id, note=notes[page])  # удаляем заметку
        notes.pop(page)  # удаляем заметку из списка
        await state.set_state(NoteContent.content)  # фсм встает на принятие нового списка
        await state.update_data(content=notes)  # фсм записывает новый список

        if len(notes) == 0:  # если нет заметок
            await callback.message.edit_text(text='Заметки кончились!', reply_markup=start_kb)
            await state.clear()
        else:  # если количество заметок меньше текущей страницы
            # len(notes) < (page + 1)
            page = page - 1
            await state.set_state(NoteContent.cur_page)   # фсм встает на обновление количества страниц
            await state.update_data(cur_page=page)  # фсм получает новое количество страниц
            await callback.message.edit_text(text=notes[page], reply_markup=manage_kb)  # редактируем клавиатуру, выводим следующую заметку

    else:
        await callback.message.edit_text(text='Нет заметок!', reply_markup=start_kb)  # выводим если нет заметок


@router.callback_query(F.data == 'edit')
async def edite_note(callback: CallbackQuery, state: FSMContext):
    await callback.answer('')
    await callback.message.edit_text(text='Введите новую заметку: ')
    await state.set_state(NoteContent.new_note)


@router.message(NoteContent.new_note)
async def get_edit_note(message: Message, state: FSMContext):
    await state.update_data(new_note=message.text)
    await state.set_state(NoteContent.content)
    data = await state.get_data()
    new_note = data['new_note']
    notes = data['content']  # заметки
    page = data['cur_page']  # текущая заметка
    await rq.update_note(tg_id=message.from_user.id, note=notes[page], text=new_note)
    notes[page] = new_note
    await state.update_data(content=notes)
    await message.answer(text='Ваша заметка изменена!')
    await message.answer(text=notes[page], reply_markup=manage_kb)


@router.callback_query(F.data == 'next')
async def next_note(callback: CallbackQuery, state: FSMContext):
    await callback.answer('')
    data = await state.get_data()
    len_notes = len(data['content'])
    notes = data['content']
    if data['cur_page'] < (len_notes-1):
        await state.set_state(NoteContent.cur_page)
        await state.update_data(cur_page=data['cur_page']+1)
        await callback.message.edit_text(text=notes[data['cur_page']+1], reply_markup=manage_kb)
    else:
        await state.set_state(NoteContent.cur_page)
        await state.update_data(cur_page=0)
        await callback.message.edit_text(text=notes[0], reply_markup=manage_kb)


@router.callback_query(F.data == 'back')
async def back_note(callback: CallbackQuery, state: FSMContext):
    await callback.answer('')
    data = await state.get_data()
    len_notes = len(data['content'])
    notes = data['content']
    if data['cur_page'] > 0:
        await state.set_state(NoteContent.cur_page)
        await state.update_data(cur_page=data['cur_page']-1)
        await callback.message.edit_text(text=notes[data['cur_page']-1], reply_markup=manage_kb)
    else:
        await state.set_state(NoteContent.cur_page)
        await state.update_data(cur_page=(len_notes-1))
        await callback.message.edit_text(text=notes[-1], reply_markup=manage_kb)


@router.callback_query(F.data == 'menu')
async def back_to_menu(callback: CallbackQuery, state: FSMContext):
    await callback.answer('')
    await callback.message.edit_text(text='Вы в главном меню!', reply_markup=start_kb)

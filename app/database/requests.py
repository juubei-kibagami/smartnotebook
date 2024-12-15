from app.database.models import async_session
from app.database.models import User, Note
from sqlalchemy import select, update, delete


async def set_user(tg_id):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))

        if not user:
            session.add(User(tg_id=tg_id))
            await session.commit()  # сохранение информации


async def create_note(tg_id, note):
    async with async_session() as session:
        session.add(Note(tg_id=tg_id, note=note))
        await session.commit()


async def get_notes(tg_id):
    async with async_session() as session:
        q = select(Note).where(Note.tg_id == tg_id)
        result = await session.execute(q)
        curr = result.scalars()
        CACHE = {i.id: i.note for i in curr}
        return CACHE
        #  return await session.scalars(select(Note.note).where(Note.tg_id == tg_id))


async def update_note(tg_id, note, text):
    async with async_session() as session:
        query = update(Note).where(Note.tg_id == tg_id, Note.note == note).values(
            note=text
        )
        await session.execute(query)
        await session.commit()


async def delete_note(tg_id, note):
    async with async_session() as session:
        query = delete(Note).where(Note.tg_id == tg_id, Note.note == note)
        await session.execute(query)
        await session.commit()

import asyncio
import os
from datetime import date, timedelta

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))
YOUR_NAME = os.getenv("YOUR_NAME", "Твоё имя")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

WEEKDAYS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
QUESTIONS = [
    "Любишь ли ты собак? (Щенков дарить не буду)",
    "Любишь ли ты экстрим? (С парашютом прыгать не будем, наверное)",
    "Любишь ли ты творчество/искусство? (На оперу не пойдем)",
]
ANSWERS = ["Да", "Нет", "Очень", "Не очень"]


class S(StatesGroup):
    questions = State()
    custom_format = State()
    flowers = State()


def start_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Да!", callback_data="start:yes")],
        [InlineKeyboardButton(text="Да, конечно!", callback_data="start:yes")],
        [InlineKeyboardButton(text="Естественно да!", callback_data="start:yes")],
        [InlineKeyboardButton(text="Скорее бы, наконец-то!", callback_data="start:yes")],
        [InlineKeyboardButton(text="Нет, спасибо, не сейчас", callback_data="start:no")],
    ])


def years_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=str(y), callback_data=f"year:{y}")]
        for y in (2026, 2027, 2028, 2029, 2030)
    ])


def calendar_kb(offset=0, per_page=14):
    today = date.today()
    start = today + timedelta(days=1) + timedelta(days=offset)
    end_of_year = date(today.year, 12, 31)
    buttons, row = [], []
    for i in range(per_page):
        d = start + timedelta(days=i)
        if d > end_of_year:
            break
        label = f"{d.strftime('%d.%m')} ({WEEKDAYS[d.weekday()]})"
        row.append(InlineKeyboardButton(text=label, callback_data=f"date:{d.isoformat()}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    nav = []
    if offset > 0:
        nav.append(InlineKeyboardButton(text="← Назад", callback_data=f"cal:{max(0, offset - per_page)}"))
    if start + timedelta(days=per_page) <= end_of_year:
        nav.append(InlineKeyboardButton(text="Дальше →", callback_data=f"cal:{offset + per_page}"))
    if nav:
        buttons.append(nav)
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def format_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Хорошо, я тебе доверюсь", callback_data="fmt:trust")],
        [InlineKeyboardButton(text="Скажи, что придумал, а я выберу", callback_data="fmt:list")],
        [InlineKeyboardButton(text="Хочу свой вариант", callback_data="fmt:own")],
        [InlineKeyboardButton(text="Отменить всё", callback_data="cancel")],
    ])


def question_kb(idx):
    rows = [[InlineKeyboardButton(text=a, callback_data=f"q:{idx}:{i}")] for i, a in enumerate(ANSWERS)]
    rows.append([InlineKeyboardButton(text="← Назад", callback_data=f"q:{idx}:back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def formats_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="1. Спокойное — прогулка с собакой", callback_data="pick:1")],
        [InlineKeyboardButton(text="2. Драйвовое — трек, резина, гонки", callback_data="pick:2")],
        [InlineKeyboardButton(text="3. Путешествие — куда скажешь", callback_data="pick:3")],
        [InlineKeyboardButton(text="Отменить всё", callback_data="cancel")],
    ])


def flowers_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Отменить всё", callback_data="cancel")]
    ])


# ============== Хэндлеры ==============

@dp.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Привет! Хочу пригласить тебя погулять. Если не хочется — можешь нажать "
        "последнюю кнопку, я не обижусь. Но в ином случае — я буду рад.",
        reply_markup=start_kb(),
    )


@dp.callback_query(F.data == "start:yes")
async def cb_yes(cb: types.CallbackQuery):
    await cb.message.edit_text(
        "Это лучший ответ, на который я мог рассчитывать.\n\nКогда же уже?",
        reply_markup=years_kb(),
    )
    await cb.answer()
    await bot.send_message(OWNER_ID, f"✅ {cb.from_user.full_name}: Да")


@dp.callback_query(F.data == "start:no")
async def cb_no(cb: types.CallbackQuery):
    await cb.message.edit_text("Понимаю, уважаю. Спасибо, что ответила 🙂")
    await cb.answer()
    await bot.send_message(OWNER_ID, f"❌ {cb.from_user.full_name}: Нет, не сейчас")


@dp.callback_query(F.data.startswith("year:"))
async def cb_year(cb: types.CallbackQuery):
    year = cb.data.split(":")[1]
    text = "Отлично. Вот ближайшие даты:" if year == "2026" else "Я не настолько терпеливый) Вот ближайшие даты:"
    await cb.message.edit_text(text, reply_markup=calendar_kb(0))
    await cb.answer()


@dp.callback_query(F.data.startswith("cal:"))
async def cb_cal(cb: types.CallbackQuery):
    offset = int(cb.data.split(":")[1])
    await cb.message.edit_reply_markup(reply_markup=calendar_kb(offset))
    await cb.answer()


@dp.callback_query(F.data.startswith("date:"))
async def cb_date(cb: types.CallbackQuery, state: FSMContext):
    iso = cb.data.split(":", 1)[1]
    await state.update_data(chosen_date=iso)
    await cb.message.edit_text(
        "Раз уж всё идёт по твоим правилам, позволь выбрать хотя бы формат? "
        "Обещаю всё лайтово, без неловких ситуаций и дурацких сюрпризов.",
        reply_markup=format_kb(),
    )
    await cb.answer()
    await bot.send_message(OWNER_ID, f"📅 {cb.from_user.full_name} выбрала дату: {iso}")


@dp.callback_query(F.data == "fmt:trust")
async def cb_fmt_trust(cb: types.CallbackQuery, state: FSMContext):
    await state.update_data(answers={}, current=0)
    await state.set_state(S.questions)
    await cb.message.edit_text(
        f"Супер! Тогда три коротких вопроса.\n\nВопрос 1/3: {QUESTIONS[0]}",
        reply_markup=question_kb(0),
    )
    await cb.answer()


@dp.callback_query(F.data == "fmt:list")
async def cb_fmt_list(cb: types.CallbackQuery):
    text = (
        "1. Спокойное — идём гулять в компании моего верного доброго друга (собаки), "
        "на удобной для тебя локации.\n\n"
        "2. Драйвовое — едем на трек, жжём резину, гоняем.\n\n"
        "3. Путешествие — время ограничено, так что радиус небольшой, но доедем "
        "куда скажешь. Правда, придётся сесть в авто к малознакомому человеку 😄"
    )
    await cb.message.edit_text(text, reply_markup=formats_kb())
    await cb.answer()


@dp.callback_query(F.data == "fmt:own")
async def cb_fmt_own(cb: types.CallbackQuery, state: FSMContext):
    await state.set_state(S.custom_format)
    await cb.message.edit_text(
        "Без проблем, любое желание. Напиши свой вариант:",
        reply_markup=flowers_kb(),  # там только «Отменить всё»
    )
    await cb.answer()


@dp.callback_query(F.data.startswith("q:"))
async def cb_q(cb: types.CallbackQuery, state: FSMContext):
    _, idx_s, action = cb.data.split(":")
    idx = int(idx_s)
    data = await state.get_data()
    answers = data.get("answers", {})

    if action == "back":
        new_idx = idx - 1
        if new_idx < 0:
            await state.clear()
            await cb.message.edit_text(
                "Раз уж всё идёт по твоим правилам, позволь выбрать хотя бы формат?",
                reply_markup=format_kb(),
            )
        else:
            await state.update_data(current=new_idx)
            await cb.message.edit_text(
                f"Вопрос {new_idx + 1}/3: {QUESTIONS[new_idx]}",
                reply_markup=question_kb(new_idx),
            )
        await cb.answer()
        return

    answers[str(idx)] = ANSWERS[int(action)]
    next_idx = idx + 1

    if next_idx >= len(QUESTIONS):
        await state.set_state(S.flowers)
        summary = "\n".join(
            f"• {QUESTIONS[i].split('?')[0]}? — {answers[str(i)]}"
            for i in range(len(QUESTIONS))
        )
        await cb.message.edit_text(
            "Понял, принял. Всё учту.\n\n" + summary +
            "\n\nИ в конце банальнейший вопрос любого пикапера, но я не телепат, "
            "и без него никогда не узнаю ответа — какие цветы ты любишь?\n\n"
            "(можно написать или нажать «Отменить всё»)",
            reply_markup=flowers_kb(),
        )
        await bot.send_message(OWNER_ID, f"📝 {cb.from_user.full_name}:\n{summary}")
    else:
        await state.update_data(current=next_idx, answers=answers)
        await cb.message.edit_text(
            f"Понял, принял.\n\nВопрос {next_idx + 1}/3: {QUESTIONS[next_idx]}",
            reply_markup=question_kb(next_idx),
        )
    await cb.answer()


@dp.callback_query(F.data.startswith("pick:"))
async def cb_pick(cb: types.CallbackQuery, state: FSMContext):
    n = cb.data.split(":")[1]
    names = {"1": "Спокойное (прогулка с собакой)", "2": "Драйвовое (трек)", "3": "Путешествие"}
    await state.set_state(S.flowers)
    await cb.message.edit_text(
        f"Выбрано: {names[n]}.\n\nИ в конце банальнейший вопрос любого пикапера, "
        "но я не телепат — какие цветы ты любишь?\n\n"
        "(можно написать или нажать «Отменить всё»)",
        reply_markup=flowers_kb(),
    )
    await cb.answer()
    await bot.send_message(OWNER_ID, f"🎯 {cb.from_user.full_name}: {names[n]}")


@dp.message(S.custom_format, F.text)
async def on_custom_format(message: types.Message, state: FSMContext):
    await state.update_data(custom_format=message.text)
    await state.set_state(S.flowers)
    await message.answer(
        f"Записал: «{message.text}».\n\nИ в конце банальнейший вопрос любого пикапера, "
        "но я не телепат — какие цветы ты любишь?\n\n"
        "(можно написать или нажать «Отменить всё»)",
        reply_markup=flowers_kb(),
    )
    await bot.send_message(OWNER_ID, f"✏️ {message.from_user.full_name}: {message.text}")


@dp.message(S.flowers, F.text)
async def on_flowers(message: types.Message, state: FSMContext):
    data = await state.get_data()
    await state.clear()
    await message.answer("О, да. Жду не дождусь 🙂")
    await bot.send_message(
        OWNER_ID,
        f"💐 {message.from_user.full_name} — цветы: {message.text}\n"
        f"📅 Дата: {data.get('chosen_date', 'не выбрана')}\n"
        f"📝 Ответы: {data.get('answers', '—')}",
    )


@dp.callback_query(F.data == "cancel")
async def cb_cancel(cb: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await cb.message.edit_text("Ок, отменил. Если что — я тут 🙂")
    await cb.answer()
    await bot.send_message(OWNER_ID, f"🚫 {cb.from_user.full_name} отменила")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
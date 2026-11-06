from datetime import datetime, timedelta
import re
from typing import Optional
from aiogram import Router, F, Bot
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from config import TIMEZONE
from states.states import TaskAddStates
from services.security import is_user_admin
from database.db import add_task, get_task
from services.scheduler import schedule_task
from keyboards.reply import (
    get_admin_main_keyboard,
    get_cancel_keyboard,
    get_date_picker_keyboard,
    get_recurrence_keyboard
)

router = Router(name="task_add_router")


def parse_date(input_str: str) -> Optional[str]:
    """Foydalanuvchi kiritgan sanani YYYY-MM-DD formatiga o'tkazish."""
    text = input_str.strip().lower()
    now = datetime.now(TIMEZONE)

    if "bugun" in text:
        return now.strftime("%Y-%m-%d")
    elif "ertaga" in text:
        return (now + timedelta(days=1)).strftime("%Y-%m-%d")
    elif "indinga" in text:
        return (now + timedelta(days=2)).strftime("%Y-%m-%d")

    # YYYY-MM-DD formati
    match1 = re.match(r"^(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})$", text)
    if match1:
        y, m, d = match1.groups()
        try:
            dt = datetime(int(y), int(m), int(d))
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            return None

    # DD.MM.YYYY yoki DD-MM-YYYY formati
    match2 = re.match(r"^(\d{1,2})[-/.](\d{1,2})[-/.](\d{4})$", text)
    if match2:
        d, m, y = match2.groups()
        try:
            dt = datetime(int(y), int(m), int(d))
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            return None

    return None


def parse_time(input_str: str) -> Optional[str]:
    """Foydalanuvchi kiritgan vaqtni HH:MM formatiga o'tkazish."""
    text = input_str.strip()
    match = re.match(r"^(\d{1,2})[:.-](\d{2})$", text)
    if match:
        h, m = int(match.group(1)), int(match.group(2))
        if 0 <= h <= 23 and 0 <= m <= 59:
            return f"{h:02d}:{m:02d}"
    return None


# ==================== QADAM-BA-QADAM VAZIFA QO'SHISH ====================

@router.message(F.text == "➕ Vazifa qo‘shish")
async def start_task_add(message: Message, state: FSMContext):
    """Vazifa qo'shish jarayonini boshlash."""
    if not await is_user_admin(message.from_user.id):
        await message.answer("Sizga bu amalni bajarish uchun ruxsat yo‘q.")
        return

    await state.set_state(TaskAddStates.waiting_for_title)
    await message.answer(
        "1. Vazifa nomini kiriting:\n\n"
        "<i>Masalan: Ingliz tilini o‘rganish yoki Kitob o‘qish</i>",
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()
    )


@router.message(TaskAddStates.waiting_for_title)
async def process_task_title(message: Message, state: FSMContext):
    """1-qadam: Vazifa nomini qabul qilish."""
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Vazifa qo‘shish bekor qilindi.", reply_markup=get_admin_main_keyboard())
        return

    title = message.text.strip()
    if len(title) < 2:
        await message.answer("Vazifa nomi juda qisqa. Iltimos, to‘liqroq nom kiriting:")
        return

    await state.update_data(title=title)
    await state.set_state(TaskAddStates.waiting_for_date)
    await message.answer(
        "2. Vazifa sanasini kiriting:\n\n"
        "Tugmalardan birini tanlang yoki sanani yozing (Masalan: <code>2026-11-06</code> yoki <code>06.11.2026</code>):",
        parse_mode="HTML",
        reply_markup=get_date_picker_keyboard()
    )


@router.message(TaskAddStates.waiting_for_date)
async def process_task_date(message: Message, state: FSMContext):
    """2-qadam: Vazifa sanasini qabul qilish."""
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Vazifa qo‘shish bekor qilindi.", reply_markup=get_admin_main_keyboard())
        return

    parsed_date = parse_date(message.text)
    if not parsed_date:
        await message.answer(
            "⚠️ Sana formati noto‘g‘ri!\n\n"
            "Iltimos, pastdagi tugmalardan foydalaning yoki sanani <code>YYYY-MM-DD</code> yoki <code>DD.MM.YYYY</code> ko‘rinishida kiriting:",
            parse_mode="HTML",
            reply_markup=get_date_picker_keyboard()
        )
        return

    await state.update_data(task_date=parsed_date)
    await state.set_state(TaskAddStates.waiting_for_time)
    await message.answer(
        "3. Vazifa vaqtini kiriting:\n\n"
        "<i>24 soatlik formatda (Masalan: <code>18:00</code> yoki <code>09:30</code>)</i>:",
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()
    )


@router.message(TaskAddStates.waiting_for_time)
async def process_task_time(message: Message, state: FSMContext):
    """3-qadam: Vazifa vaqtini qabul qilish."""
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Vazifa qo‘shish bekor qilindi.", reply_markup=get_admin_main_keyboard())
        return

    parsed_time = parse_time(message.text)
    if not parsed_time:
        await message.answer(
            "⚠️ Vaqt formati noto‘g‘ri!\n\n"
            "Iltimos, vaqtni <code>HH:MM</code> ko‘rinishida kiriting (Masalan: <code>18:00</code>):",
            parse_mode="HTML",
            reply_markup=get_cancel_keyboard()
        )
        return

    await state.update_data(task_time=parsed_time)
    await state.set_state(TaskAddStates.waiting_for_recurrence)
    await message.answer(
        "4. Bu vazifa har kuni takrorlansinmi?\n\n"
        "Tanlang:",
        reply_markup=get_recurrence_keyboard()
    )


@router.message(TaskAddStates.waiting_for_recurrence)
async def process_task_recurrence(message: Message, state: FSMContext, bot: Bot):
    """4-qadam: Takrorlanishni tanlash va vazifani bazaga saqlash."""
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Vazifa qo‘shish bekor qilindi.", reply_markup=get_admin_main_keyboard())
        return

    user_text = message.text.lower()
    is_daily = 1 if ("ha" in user_text or "har kuni" in user_text) else 0

    data = await state.get_data()
    title = data["title"]
    task_date = data["task_date"]
    task_time = data["task_time"]
    user_id = message.from_user.id

    # Bazaga qo'shish
    task_id = await add_task(
        user_id=user_id,
        title=title,
        task_date=task_date,
        task_time=task_time,
        is_daily=is_daily
    )

    # Rejalashtiruvchiga qo'shish
    saved_task = await get_task(task_id)
    if saved_task:
        schedule_task(bot, saved_task)

    await state.clear()

    repeat_text = "🔄 Har kuni" if is_daily else "➡️ Bir martalik"
    
    # Talab qilingan javob:
    # "✅ Vazifa muvaffaqiyatli qo‘shildi!"
    await message.answer(
        f"✅ Vazifa muvaffaqiyatli qo‘shildi!\n\n"
        f"📋 <b>Vazifa:</b> {title}\n"
        f"📅 <b>Sana:</b> {task_date}\n"
        f"🕒 <b>Vaqt:</b> {task_time}\n"
        f"🔁 <b>Holati:</b> {repeat_text}",
        parse_mode="HTML",
        reply_markup=get_admin_main_keyboard()
    )


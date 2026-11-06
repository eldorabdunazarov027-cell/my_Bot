from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from config import TIMEZONE
from services.security import is_user_admin
from database.db import (
    get_all_tasks,
    get_today_tasks,
    get_completed_tasks,
    get_tasks_stats,
    get_task
)
from keyboards.inline import (
    get_task_action_keyboard,
    get_tasks_list_keyboard
)

router = Router(name="task_list_router")


# ==================== BARCHA VAZIFALAR ====================

@router.message(F.text == "📋 Barcha vazifalar")
async def handle_all_tasks(message: Message):
    """Barcha faol vazifalar ro'yxatini chiqarish."""
    if not await is_user_admin(message.from_user.id):
        return

    tasks = await get_all_tasks(user_id=message.from_user.id, include_completed=False)

    if not tasks:
        await message.answer(
            "📋 <b>Sizda hozircha faol vazifalar mavjud emas.</b>\n\n"
            "Yangi vazifa qo‘shish uchun <b>➕ Vazifa qo‘shish</b> tugmasini bosing.",
            parse_mode="HTML"
        )
        return

    text = f"📋 <b>BARCHA FAOL VAZIFALAR ({len(tasks)} ta):</b>\n\n"
    for idx, t in enumerate(tasks, 1):
        repeat_icon = "🔄" if t["is_daily"] else "📌"
        text += (
            f"<b>{idx}.</b> {repeat_icon} <b>{t['title']}</b>\n"
            f"   📅 Sana: <code>{t['task_date']}</code> | 🕒 Vaqt: <code>{t['task_time']}</code>\n"
            f"   🆔 ID: <code>#{t['id']}</code>\n\n"
        )

    text += "<i>Quyidagi tugmalar orqali istalgan vazifani boshqarishingiz mumkin:</i>"

    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=get_tasks_list_keyboard(tasks, "select_task")
    )


# ==================== BUGUNGI VAZIFALAR ====================

@router.message(F.text == "📅 Bugungi vazifalar")
async def handle_today_tasks(message: Message):
    """Bugungi kundagi vazifalar ro'yxati."""
    if not await is_user_admin(message.from_user.id):
        return

    today_tasks = await get_today_tasks(user_id=message.from_user.id)
    today_str = datetime.now(TIMEZONE).strftime("%Y-%m-%d")

    if not today_tasks:
        await message.answer(
            f"📅 <b>Bugungi sana:</b> {today_str}\n\n"
            "Bugun uchun rejalashtirilgan vazifalar yo‘q! Dam oling yoki yangi vazifa qo‘shing. 😊",
            parse_mode="HTML"
        )
        return

    text = f"📅 <b>BUGUNGI VAZIFALAR ({today_str}):</b>\n\n"
    for idx, t in enumerate(today_tasks, 1):
        repeat_badge = " [Har kuni]" if t["is_daily"] else ""
        text += (
            f"<b>{idx}.</b> 🕒 <code>{t['task_time']}</code> — <b>{t['title']}</b>{repeat_badge}\n"
            f"   🆔 ID: <code>#{t['id']}</code>\n\n"
        )

    text += "<i>Vazifani boshqarish uchun quyidagi ro‘yxatdan tanlang:</i>"

    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=get_tasks_list_keyboard(today_tasks, "select_task")
    )


# ==================== BAJARILGAN VAZIFALAR ====================

@router.message(F.text == "📊 Bajarilgan vazifalar")
async def handle_completed_tasks(message: Message):
    """Bajarilgan vazifalar statistikasi va ro'yxati."""
    if not await is_user_admin(message.from_user.id):
        return

    stats = await get_tasks_stats(user_id=message.from_user.id)
    completed_list = await get_completed_tasks(user_id=message.from_user.id, limit=10)

    total = stats["total"]
    completed = stats["completed"]
    pending = stats["pending"]
    daily = stats["daily"]
    rate = round((completed / total * 100), 1) if total > 0 else 0

    text = (
        "📊 <b>VAZIFALAR STATISTIKASI:</b>\n\n"
        f"🎯 Jami vazifalar: <b>{total}</b> ta\n"
        f"✅ Bajarilgan: <b>{completed}</b> ta ({rate}%)\n"
        f"⏳ Kutilayotgan: <b>{pending}</b> ta\n"
        f"🔄 Har kungi: <b>{daily}</b> ta\n\n"
    )

    if completed_list:
        text += "<b>Oxirgi bajarilgan vazifalar:</b>\n"
        for idx, t in enumerate(completed_list, 1):
            text += f"{idx}. <s>{t['title']}</s> (🕒 {t['task_date']} {t['task_time']})\n"
    else:
        text += "<i>Hali bajarilgan vazifalar mavjud emas.</i>"

    await message.answer(text, parse_mode="HTML")


# ==================== VAZIFA KARTASINI KO'RISH ====================

@router.callback_query(F.data.startswith("select_task:"))
async def handle_task_selection(callback: CallbackQuery):
    """Ro'yxatdan bitta vazifa bosilganda uning kartasini ko'rsatish."""
    task_id = int(callback.data.split(":")[1])
    task = await get_task(task_id)

    if not task:
        await callback.answer("Vazifa topilmadi yoki o‘chirilgan.", show_alert=True)
        return

    repeat_str = "🔄 Har kuni takrorlanadi" if task["is_daily"] else "➡️ Bir martalik"
    status_str = "✅ Bajarilgan" if task["is_completed"] else "⏳ Kutilmoqda"

    text = (
        f"📌 <b>VAZIFA TAFSILOTI:</b>\n\n"
        f"📋 <b>Nomi:</b> {task['title']}\n"
        f"📅 <b>Sanasi:</b> {task['task_date']}\n"
        f"🕒 <b>Vaqti:</b> {task['task_time']}\n"
        f"🔁 <b>Holati:</b> {repeat_str}\n"
        f"🚦 <b>Status:</b> {status_str}\n"
        f"🆔 <b>ID:</b> #{task['id']}"
    )

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=get_task_action_keyboard(task_id)
    )
    await callback.answer()


@router.callback_query(F.data == "close_menu")
async def handle_close_menu(callback: CallbackQuery):
    """Menyuni yopish."""
    try:
        await callback.message.delete()
    except Exception:
        await callback.message.edit_reply_markup(reply_markup=None)
    await callback.answer("Yopildi")


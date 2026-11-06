from datetime import datetime, timedelta
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery
from config import TIMEZONE
from database.db import (
    get_task,
    mark_task_completed,
    mark_task_reminded,
    reschedule_daily_task
)
from services.scheduler import (
    snooze_task_reminder,
    schedule_task
)
from keyboards.inline import (
    get_reminder_keyboard,
    get_snooze_options_keyboard
)

router = Router(name="reminder_actions_router")


# ==================== ✅ BAJARILDI ====================

@router.callback_query(F.data.startswith("reminder_done:"))
@router.callback_query(F.data.startswith("task_done:"))
async def handle_task_done(callback: CallbackQuery, bot: Bot):
    """Vazifa bajarilganda uni qayd etish."""
    task_id = int(callback.data.split(":")[1])
    task = await get_task(task_id)

    if not task:
        await callback.answer("Vazifa topilmadi.", show_alert=True)
        return

    # Agar har kuni takrorlanadigan vazifa bo'lsa
    if task["is_daily"]:
        now = datetime.now(TIMEZONE)
        next_date = (now + timedelta(days=1)).strftime("%Y-%m-%d")
        
        # Ertangi kunga rejalashtirish
        await reschedule_daily_task(task_id, next_date)
        updated_task = await get_task(task_id)
        if updated_task:
            schedule_task(bot, updated_task)

        await callback.message.edit_text(
            f"✅ <b>Vazifa bajarildi deb belgilandi! 🎉</b>\n\n"
            f"📌 <b>Vazifa:</b> {task['title']}\n"
            f"🔄 <i>Bu takrorlanuvchi vazifa, u avtomatik ravishda ertangi kunga ({next_date} {task['task_time']}) rejalashtirildi!</i>",
            parse_mode="HTML"
        )
    else:
        # Bir martalik vazifa
        await mark_task_completed(task_id)
        await callback.message.edit_text(
            f"✅ <b>Barakalla! Vazifa muvaffaqiyatli bajarildi! 🎉</b>\n\n"
            f"📌 <b>Vazifa:</b> {task['title']}\n"
            f"🕒 <b>Bajarilgan vaqt:</b> {datetime.now(TIMEZONE).strftime('%H:%M, %d.%m.%Y')}",
            parse_mode="HTML"
        )

    await callback.answer("Bajarildi deb belgilandi!")


# ==================== ⏳ KEYINROQ ESLATISH ====================

@router.callback_query(F.data.startswith("reminder_snooze:"))
async def handle_snooze_menu(callback: CallbackQuery):
    """Keyinroq eslatish vaqtlarini ko'rsatish."""
    task_id = int(callback.data.split(":")[1])
    task = await get_task(task_id)

    if not task:
        await callback.answer("Vazifa topilmadi.", show_alert=True)
        return

    await callback.message.edit_text(
        f"⏳ <b>Vazifa:</b> {task['title']}\n\n"
        "Qancha vaqtdan keyin yana eslatay?",
        parse_mode="HTML",
        reply_markup=get_snooze_options_keyboard(task_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("snooze_time:"))
async def handle_snooze_choice(callback: CallbackQuery, bot: Bot):
    """Tanlangan vaqtga kechiktirish."""
    _, task_id_str, minutes_str = callback.data.split(":")
    task_id = int(task_id_str)
    minutes = int(minutes_str)

    task = await get_task(task_id)
    if not task:
        await callback.answer("Vazifa topilmadi.", show_alert=True)
        return

    # APScheduler orqali kechiktirish
    snooze_task_reminder(bot, task_id, minutes)

    next_remind_time = (datetime.now(TIMEZONE) + timedelta(minutes=minutes)).strftime("%H:%M")

    await callback.message.edit_text(
        f"⏳ <b>Eslatma {minutes} daqiqaga kechiktirildi!</b>\n\n"
        f"📌 <b>Vazifa:</b> {task['title']}\n"
        f"🕒 <b>Keyingi eslatma vaqti:</b> taxminan soat {next_remind_time} da.",
        parse_mode="HTML"
    )
    await callback.answer(f"{minutes} daqiqaga kechiktirildi")


@router.callback_query(F.data.startswith("snooze_back:"))
async def handle_snooze_back(callback: CallbackQuery):
    """Kechiktirish menyusidan orqaga qaytish."""
    task_id = int(callback.data.split(":")[1])
    task = await get_task(task_id)

    if not task:
        await callback.answer("Vazifa topilmadi.", show_alert=True)
        return

    text = (
        f"⏰ ESLATMA!\n\n"
        f"📌 <b>Vazifa:</b> {task['title']}\n"
        f"🕒 <b>Vaqt:</b> {task['task_time']}\n\n"
        f"Vazifani bajarishni unutmang!"
    )

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=get_reminder_keyboard(task_id)
    )
    await callback.answer()


# ==================== ❌ O'TKAZIB YUBORISH ====================

@router.callback_query(F.data.startswith("reminder_skip:"))
async def handle_reminder_skip(callback: CallbackQuery, bot: Bot):
    """Eslatmani o'tkazib yuborish."""
    task_id = int(callback.data.split(":")[1])
    task = await get_task(task_id)

    if not task:
        await callback.answer("Vazifa topilmadi.", show_alert=True)
        return

    if task["is_daily"]:
        now = datetime.now(TIMEZONE)
        next_date = (now + timedelta(days=1)).strftime("%Y-%m-%d")
        await reschedule_daily_task(task_id, next_date)
        updated_task = await get_task(task_id)
        if updated_task:
            schedule_task(bot, updated_task)

        await callback.message.edit_text(
            f"❌ <b>Vazifa bugun uchun o‘tkazib yuborildi.</b>\n\n"
            f"📌 <b>Vazifa:</b> {task['title']}\n"
            f"🔄 <i>Har kungi vazifa bo‘lgani uchun ertaga ({next_date} {task['task_time']}) yana eslatiladi.</i>",
            parse_mode="HTML"
        )
    else:
        await mark_task_reminded(task_id, 1)
        await callback.message.edit_text(
            f"❌ <b>Vazifa o‘tkazib yuborildi.</b>\n\n"
            f"📌 <b>Vazifa:</b> {task['title']}",
            parse_mode="HTML"
        )

    await callback.answer("O‘tkazib yuborildi")


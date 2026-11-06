from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from states.states import TaskEditStates, SetReminderTimeStates
from services.security import is_user_admin
from database.db import (
    get_all_tasks,
    get_task,
    update_task
)
from services.scheduler import schedule_task
from keyboards.inline import (
    get_tasks_list_keyboard,
    get_edit_fields_keyboard
)
from keyboards.reply import get_admin_main_keyboard, get_cancel_keyboard
from handlers.task_add import parse_date, parse_time

router = Router(name="task_edit_router")


# ==================== VAZIFANI TAHRIRLASH ====================

@router.message(F.text == "✏️ Vazifani tahrirlash")
async def start_task_edit(message: Message):
    """Tahrirlash uchun faol vazifalar ro'yxatini chiqarish."""
    if not await is_user_admin(message.from_user.id):
        return

    tasks = await get_all_tasks(user_id=message.from_user.id, include_completed=False)
    if not tasks:
        await message.answer("Tahrirlash uchun faol vazifalar mavjud emas.")
        return

    await message.answer(
        "✏️ <b>Tahrirlamoqchi bo‘lgan vazifangizni tanlang:</b>",
        parse_mode="HTML",
        reply_markup=get_tasks_list_keyboard(tasks, "edit_select")
    )


@router.callback_query(F.data.startswith("edit_select:"))
@router.callback_query(F.data.startswith("task_edit_direct:"))
async def handle_edit_selection(callback: CallbackQuery, state: FSMContext):
    """Vazifa tanlanganda tahrirlash maydonlarini ko'rsatish."""
    task_id = int(callback.data.split(":")[1])
    task = await get_task(task_id)

    if not task:
        await callback.answer("Vazifa topilmadi.", show_alert=True)
        return

    await state.update_data(edit_task_id=task_id)
    text = (
        f"✏️ <b>Vazifani tahrirlash (#{task['id']}):</b>\n\n"
        f"📌 Hozirgi nomi: <b>{task['title']}</b>\n"
        f"📅 Hozirgi sanasi: <code>{task['task_date']}</code>\n"
        f"🕒 Hozirgi vaqti: <code>{task['task_time']}</code>\n"
        f"🔁 Takrorlanish: <b>{'Har kuni' if task['is_daily'] else 'Bir martalik'}</b>\n\n"
        "Qaysi ma'lumotni o‘zgartirmoqchisiz?"
    )

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=get_edit_fields_keyboard(task_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("edit_field:"))
async def handle_field_chosen(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Qaysi maydon tahrirlanishini aniqlash."""
    _, task_id_str, field = callback.data.split(":")
    task_id = int(task_id_str)
    task = await get_task(task_id)

    if not task:
        await callback.answer("Vazifa topilmadi.", show_alert=True)
        return

    await state.update_data(edit_task_id=task_id, edit_field=field)

    # Agar takrorlanish bo'lsa, to'g'ridan-to'g'ri almashtiramiz
    if field == "recurrence":
        new_val = 0 if task["is_daily"] else 1
        await update_task(task_id, is_daily=new_val)
        updated_task = await get_task(task_id)
        if updated_task:
            schedule_task(bot, updated_task)
        await callback.message.answer(
            f"✅ Takrorlanish holati yangilandi: <b>{'Har kuni' if new_val else 'Bir martalik'}</b>",
            parse_mode="HTML",
            reply_markup=get_admin_main_keyboard()
        )
        await callback.answer("Yangilandi!")
        await state.clear()
        return

    # Matnli maydonlar uchun foydalanuvchidan ma'lumot so'raymiz
    prompts = {
        "title": "Yangi vazifa nomini kiriting:",
        "date": "Yangi sanani kiriting (YYYY-MM-DD yoki Bugun/Ertaga):",
        "time": "Yangi vaqtni kiriting (HH:MM formatida, masalan 18:00):"
    }

    await state.set_state(TaskEditStates.waiting_for_value)
    await callback.message.answer(
        prompts.get(field, "Yangi qiymatni kiriting:"),
        reply_markup=get_cancel_keyboard()
    )
    await callback.answer()


@router.message(TaskEditStates.waiting_for_value)
async def process_new_value(message: Message, state: FSMContext, bot: Bot):
    """Yangi qiymatni saqlash va vazifani yangilash."""
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Tahrirlash bekor qilindi.", reply_markup=get_admin_main_keyboard())
        return

    data = await state.get_data()
    task_id = data.get("edit_task_id")
    field = data.get("edit_field")

    if not task_id or not field:
        await state.clear()
        await message.answer("Xatolik yuz berdi. Qaytadan urinib ko‘ring.", reply_markup=get_admin_main_keyboard())
        return

    update_dict = {}

    if field == "title":
        new_title = message.text.strip()
        if len(new_title) < 2:
            await message.answer("Nom juda qisqa. Qaytadan kiriting:")
            return
        update_dict["title"] = new_title

    elif field == "date":
        new_date = parse_date(message.text)
        if not new_date:
            await message.answer("Sana formati noto‘g‘ri. Qaytadan kiriting (Masalan: 2026-11-06):")
            return
        update_dict["task_date"] = new_date

    elif field == "time":
        new_time = parse_time(message.text)
        if not new_time:
            await message.answer("Vaqt formati noto‘g‘ri. Qaytadan kiriting (HH:MM, masalan 18:00):")
            return
        update_dict["task_time"] = new_time

    # Bazada yangilash
    await update_task(task_id, **update_dict)
    
    # Rejalashtiruvchini yangilash
    updated_task = await get_task(task_id)
    if updated_task:
        schedule_task(bot, updated_task)

    await state.clear()
    await message.answer(
        "✅ Vazifa muvaffaqiyatli tahrirlandi!",
        reply_markup=get_admin_main_keyboard()
    )


# ==================== ESLATMA VAQTINI BELGILASH (TEZKOR) ====================

@router.message(F.text == "⏰ Eslatma vaqtini belgilash")
async def start_change_reminder_time(message: Message):
    """Tezkor eslatma vaqtini belgilash uchun ro'yxat chiqarish."""
    if not await is_user_admin(message.from_user.id):
        return

    tasks = await get_all_tasks(user_id=message.from_user.id, include_completed=False)
    if not tasks:
        await message.answer("Vaqtini o‘zgartirish uchun faol vazifalar yo‘q.")
        return

    await message.answer(
        "⏰ <b>Eslatma vaqtini o‘zgartirmoqchi bo‘lgan vazifani tanlang:</b>",
        parse_mode="HTML",
        reply_markup=get_tasks_list_keyboard(tasks, "set_time_select")
    )


@router.callback_query(F.data.startswith("set_time_select:"))
@router.callback_query(F.data.startswith("task_change_time:"))
async def handle_time_selection(callback: CallbackQuery, state: FSMContext):
    """Vazifa tanlanganda yangi vaqtni so'rash."""
    task_id = int(callback.data.split(":")[1])
    task = await get_task(task_id)

    if not task:
        await callback.answer("Vazifa topilmadi.", show_alert=True)
        return

    await state.update_data(time_task_id=task_id)
    await state.set_state(SetReminderTimeStates.waiting_for_time)

    await callback.message.answer(
        f"⏰ <b>Vazifa:</b> {task['title']}\n"
        f"🕒 Hozirgi vaqt: <code>{task['task_time']}</code>\n\n"
        "Yangi eslatma vaqtini kiriting (24 soatlik formatda, masalan <code>18:30</code>):",
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()
    )
    await callback.answer()


@router.message(SetReminderTimeStates.waiting_for_time)
async def process_new_reminder_time(message: Message, state: FSMContext, bot: Bot):
    """Yangi eslatma vaqtini saqlash."""
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=get_admin_main_keyboard())
        return

    new_time = parse_time(message.text)
    if not new_time:
        await message.answer(
            "⚠️ Vaqt formati noto‘g‘ri. Iltimos, <code>HH:MM</code> ko‘rinishida kiriting (Masalan: <code>18:00</code>):",
            parse_mode="HTML"
        )
        return

    data = await state.get_data()
    task_id = data.get("time_task_id")

    await update_task(task_id, task_time=new_time)
    updated_task = await get_task(task_id)
    if updated_task:
        schedule_task(bot, updated_task)

    await state.clear()
    await message.answer(
        f"✅ Eslatma vaqti muvaffaqiyatli <code>{new_time}</code> ga o‘zgartirildi!",
        parse_mode="HTML",
        reply_markup=get_admin_main_keyboard()
    )


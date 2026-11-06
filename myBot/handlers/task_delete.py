from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from services.security import is_user_admin
from database.db import get_all_tasks, get_task, delete_task
from services.scheduler import cancel_task_job
from keyboards.inline import (
    get_tasks_list_keyboard,
    get_delete_confirm_keyboard
)

router = Router(name="task_delete_router")


@router.message(F.text == "🗑 Vazifani o‘chirish")
async def start_task_delete(message: Message):
    """O'chirish uchun faol vazifalar ro'yxatini chiqarish."""
    if not await is_user_admin(message.from_user.id):
        return

    tasks = await get_all_tasks(user_id=message.from_user.id, include_completed=False)
    if not tasks:
        await message.answer("O‘chirish uchun vazifalar mavjud emas.")
        return

    await message.answer(
        "🗑 <b>O‘chirmoqchi bo‘lgan vazifangizni tanlang:</b>",
        parse_mode="HTML",
        reply_markup=get_tasks_list_keyboard(tasks, "delete_select")
    )


@router.callback_query(F.data.startswith("delete_select:"))
@router.callback_query(F.data.startswith("task_delete_direct:"))
async def handle_delete_select(callback: CallbackQuery):
    """O'chirishni tasdiqlash xabari."""
    task_id = int(callback.data.split(":")[1])
    task = await get_task(task_id)

    if not task:
        await callback.answer("Vazifa topilmadi.", show_alert=True)
        return

    text = (
        f"🗑 <b>Haqiqatan ham bu vazifani o‘chirmoqchimisiz?</b>\n\n"
        f"📌 <b>Nomi:</b> {task['title']}\n"
        f"📅 <b>Sanasi:</b> {task['task_date']} {task['task_time']}"
    )

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=get_delete_confirm_keyboard(task_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("confirm_delete:"))
async def handle_confirm_delete(callback: CallbackQuery):
    """Vazifani bazadan va rejalashtiruvchidan butunlay o'chirish."""
    task_id = int(callback.data.split(":")[1])

    # Rejalashtirilgan jobni bekor qilish
    cancel_task_job(task_id)

    # Bazadan o'chirish
    success = await delete_task(task_id)

    if success:
        await callback.message.edit_text(
            f"✅ <b>Vazifa (#{task_id}) muvaffaqiyatli o‘chirildi!</b>",
            parse_mode="HTML"
        )
    else:
        await callback.message.edit_text("❌ Vazifani o‘chirishda xatolik yuz berdi.")

    await callback.answer("O‘chirildi!")


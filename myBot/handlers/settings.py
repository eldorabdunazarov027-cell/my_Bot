from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from config import TIMEZONE, TIMEZONE_STR, MAX_FAILED_ATTEMPTS, LOCKOUT_MINUTES
from services.security import (
    is_user_admin,
    update_admin_password,
    get_admin_password,
    safe_delete_message
)
from database.db import get_tasks_stats, get_admin_id
from states.states import ChangePasswordStates
from keyboards.reply import get_admin_main_keyboard, get_cancel_keyboard

router = Router(name="settings_router")


# ==================== SOZLAMALAR ====================

@router.message(F.text == "⚙️ Sozlamalar")
async def handle_settings(message: Message):
    """Tizim sozlamalari va holati haqida to'liq ma'lumot."""
    if not await is_user_admin(message.from_user.id):
        return

    now_tashkent = datetime.now(TIMEZONE).strftime("%Y-%m-%d %H:%M:%S")
    stats = await get_tasks_stats()
    admin_id = await get_admin_id()

    text = (
        "⚙️ <b>BOT SOZLAMALARI VA HOLATI:</b>\n\n"
        f"🕒 <b>Joriy vaqt:</b> <code>{now_tashkent}</code>\n"
        f"🌍 <b>Vaqt mintaqasi:</b> <code>{TIMEZONE_STR}</code> (O‘zbekiston)\n"
        f"👑 <b>Admin ID:</b> <code>{admin_id}</code>\n"
        f"💾 <b>Ma'lumotlar bazasi:</b> SQLite (Doimiy saqlanadi)\n"
        f"⏱ <b>Rejalashtiruvchi:</b> APScheduler (Aktiv)\n\n"
        "🔒 <b>Xavfsizlik choralari:</b>\n"
        f"• Maksimal xato urinishlar: <b>{MAX_FAILED_ATTEMPTS} ta</b>\n"
        f"• Bloklash muddati: <b>{LOCKOUT_MINUTES} daqiqa</b>\n"
        f"• Parol xabarlari avtomatik o‘chiriladi\n\n"
        f"📊 <b>Statistika:</b> Jami vazifalar: <b>{stats['total']}</b> ta (Kutilayotgan: {stats['pending']} ta)"
    )

    await message.answer(text, parse_mode="HTML")


# ==================== PAROLNI O'ZGARTIRISH ====================

@router.message(F.text == "🔐 Parolni o‘zgartirish")
async def start_change_password(message: Message, state: FSMContext):
    """Parolni o'zgartirish jarayonini boshlash."""
    if not await is_user_admin(message.from_user.id):
        return

    await state.set_state(ChangePasswordStates.waiting_for_old_password)
    await message.answer(
        "🔐 <b>Parolni o‘zgartirish:</b>\n\n"
        "Iltimos, avval <b>amaldagi (eski) parolni</b> kiriting:",
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()
    )


@router.message(ChangePasswordStates.waiting_for_old_password)
async def process_old_password(message: Message, state: FSMContext):
    """Eski parolni tekshirish."""
    input_text = message.text or ""
    await safe_delete_message(message)

    if input_text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Parolni o‘zgartirish bekor qilindi.", reply_markup=get_admin_main_keyboard())
        return

    current_pwd = await get_admin_password()
    if input_text.strip() != current_pwd.strip():
        await message.answer(
            "❌ Amaldagi parol noto‘g‘ri! Qayta urinib ko‘ring yoki bekor qiling:",
            reply_markup=get_cancel_keyboard()
        )
        return

    await state.update_data(old_password=input_text.strip())
    await state.set_state(ChangePasswordStates.waiting_for_new_password)
    await message.answer(
        "✅ Amaldagi parol tasdiqlandi.\n\n"
        "Endi <b>yangi parolni</b> kiriting (kamida 4 ta belgi):",
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()
    )


@router.message(ChangePasswordStates.waiting_for_new_password)
async def process_new_password(message: Message, state: FSMContext):
    """Yangi parolni qabul qilish."""
    input_text = message.text or ""
    await safe_delete_message(message)

    if input_text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Parolni o‘zgartirish bekor qilindi.", reply_markup=get_admin_main_keyboard())
        return

    new_pwd = input_text.strip()
    if len(new_pwd) < 4:
        await message.answer(
            "❌ Yangi parol juda qisqa (kamida 4 ta belgi bo‘lishi kerak). Qaytadan kiriting:",
            reply_markup=get_cancel_keyboard()
        )
        return

    await state.update_data(new_password=new_pwd)
    await state.set_state(ChangePasswordStates.confirm_new_password)
    await message.answer(
        "Tasdiqlash uchun <b>yangi parolni qayta kiriting</b>:",
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()
    )


@router.message(ChangePasswordStates.confirm_new_password)
async def process_confirm_password(message: Message, state: FSMContext):
    """Yangi parolni tasdiqlash va saqlash."""
    input_text = message.text or ""
    await safe_delete_message(message)

    if input_text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Parolni o‘zgartirish bekor qilindi.", reply_markup=get_admin_main_keyboard())
        return

    data = await state.get_data()
    old_pwd = data.get("old_password")
    new_pwd = data.get("new_password")

    if input_text.strip() != new_pwd:
        await message.answer(
            "❌ Yangi parollar bir-biriga mos kelmadi!\n\n"
            "Iltimos, yangi parolni qayta kiriting:",
            reply_markup=get_cancel_keyboard()
        )
        await state.set_state(ChangePasswordStates.waiting_for_new_password)
        return

    # Parolni bazada yangilash
    success, msg = await update_admin_password(message.from_user.id, old_pwd, new_pwd)
    await state.clear()

    if success:
        await message.answer(
            "🔐 <b>Admin paroli muvaffaqiyatli yangilandi!</b>\n\n"
            "Yangi parol xavfsiz tarzda saqlandi.",
            parse_mode="HTML",
            reply_markup=get_admin_main_keyboard()
        )
    else:
        await message.answer(msg, reply_markup=get_admin_main_keyboard())


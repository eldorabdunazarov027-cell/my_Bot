from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from states.states import AdminAuthStates
from services.security import (
    verify_password,
    check_user_lockout,
    safe_delete_message
)
from database.db import set_setting
from keyboards.reply import get_admin_main_keyboard, get_cancel_keyboard

router = Router(name="admin_auth_router")


def is_admin_trigger(text: str) -> bool:
    """'Men adminman' matnini turli shakllarda (katta-kichik harflar, bo'shliqlar) tekshirish."""
    if not text:
        return False
    normalized = text.strip().lower()
    return normalized in ["men adminman", "men adminman.", "men adminman!"]


@router.message(F.text.func(is_admin_trigger))
async def handle_admin_prompt(message: Message, state: FSMContext):
    """Foydalanuvchi 'Men adminman' deb yozganda ishga tushadi."""
    user_id = message.from_user.id

    # Bloklanganlikni tekshirish
    is_locked, remaining_sec = await check_user_lockout(user_id)
    if is_locked:
        minutes = (remaining_sec // 60) + 1
        await message.answer(
            f"⛔️ Siz ko‘p marta noto‘g‘ri parol kiritdingiz! Iltimos, {minutes} daqiqa kuting."
        )
        return

    await state.set_state(AdminAuthStates.waiting_for_password)
    await message.answer(
        "Admin ekanligingizni tasdiqlash uchun parolni kiriting 🔐",
        reply_markup=get_cancel_keyboard()
    )


@router.message(AdminAuthStates.waiting_for_password)
async def handle_password_input(message: Message, state: FSMContext):
    """Admin parolini tekshirish."""
    user_id = message.from_user.id
    input_text = message.text or ""

    # Parol xavfsizligi: Foydalanuvchi yozgan parolni chatdan darhol o'chirib tashlaymiz
    await safe_delete_message(message)

    if input_text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Kirish bekor qilindi.", reply_markup=ReplyKeyboardRemove())
        return

    is_success, response_msg = await verify_password(user_id, input_text)

    if is_success:
        await state.clear()
        await message.answer(
            "Xush kelibsiz, Admin! 👑\nAdmin paneli faollashtirildi.",
            reply_markup=get_admin_main_keyboard()
        )
    else:
        # Noto'g'ri parol kiritilganda talab qilingan javob:
        # "❌ Parol noto‘g‘ri! Qayta urinib ko‘ring."
        await message.answer(response_msg, reply_markup=get_cancel_keyboard())


@router.message(F.text == "🚪 Admin paneldan chiqish")
async def handle_admin_logout(message: Message, state: FSMContext):
    """Admin paneldan chiqish."""
    await state.clear()
    
    # Sessiyani yakunlash (admin_id ni tozalash)
    await set_setting("admin_id", "")

    await message.answer(
        "🚪 Admin paneldan muvaffaqiyatli chiqdingiz.\n\n"
        "Qayta kirish uchun <b>Men adminman</b> deb yozing.",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardRemove()
    )


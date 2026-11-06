from typing import Tuple
from aiogram.types import Message
from database.db import (
    get_admin_password,
    set_admin_password,
    is_admin as db_is_admin,
    set_admin_id,
    check_lockout,
    record_failed_attempt,
    reset_failed_attempts,
    get_admin_id
)
from config import LOCKOUT_MINUTES, MAX_FAILED_ATTEMPTS


async def check_user_lockout(user_id: int) -> Tuple[bool, int]:
    """Foydalanuvchi bloklanganligini va qolgan vaqtni tekshirish."""
    return await check_lockout(user_id)


async def verify_password(user_id: int, input_password: str) -> Tuple[bool, str]:
    """
    Kiritilgan parolni tekshirish.
    Qaytaradi: (muvaffaqiyatlimi, xabar)
    """
    # 1. Avval bloklanganlikni tekshiramiz
    is_locked, remaining_sec = await check_lockout(user_id)
    if is_locked:
        minutes = (remaining_sec // 60) + 1
        return False, f"⛔️ Siz ko‘p marta noto‘g‘ri parol kiritdingiz! Iltimos, {minutes} daqiqa kuting."

    # 2. Bazadagi joriy parolni olamiz
    current_password = await get_admin_password()

    # 3. Parol solishtirish
    if input_password.strip() == current_password.strip():
        # Muvaffaqiyatli kirish
        await reset_failed_attempts(user_id)
        await set_admin_id(user_id)
        return True, "✅ Parol to‘g‘ri! Xush kelibsiz."
    else:
        # Noto'g'ri parol
        attempts, just_locked = await record_failed_attempt(user_id)
        if just_locked:
            return False, f"❌ Parol noto‘g‘ri! Urinishlar chegarasidan oshdingiz ({MAX_FAILED_ATTEMPTS} marta). Tizim {LOCKOUT_MINUTES} daqiqaga bloklandi."
        else:
            left = MAX_FAILED_ATTEMPTS - attempts
            return False, f"❌ Parol noto‘g‘ri! Qayta urinib ko‘ring. (Qolgan urinishlar: {left})"


async def update_admin_password(user_id: int, old_password: str, new_password: str) -> Tuple[bool, str]:
    """Admin parolini yangilash."""
    current_password = await get_admin_password()
    if old_password.strip() != current_password.strip():
        return False, "❌ Amaldagi parol noto‘g‘ri kiritildi!"

    if len(new_password.strip()) < 4:
        return False, "❌ Yangi parol kamida 4 ta belgidan iborat bo‘lishi kerak!"

    await set_admin_password(new_password.strip())
    return True, "✅ Admin paroli muvaffaqiyatli yangilandi!"


async def safe_delete_message(message: Message) -> None:
    """Parol xavfsizligi: kiritilgan parol xabarini darhol chatdan o'chirish."""
    try:
        await message.delete()
    except Exception:
        pass


async def is_user_admin(user_id: int) -> bool:
    """Foydalanuvchi tasdiqlangan admin ekanligini tekshirish."""
    return await db_is_admin(user_id)


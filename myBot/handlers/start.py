from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from keyboards.reply import get_admin_main_keyboard
from services.security import is_user_admin

router = Router(name="start_router")


@router.message(CommandStart())
async def handle_start(message: Message, state: FSMContext):
    """Foydalanuvchi /start yozganda qutlash xabari."""
    await state.clear()
    
    # Agar foydalanuvchi allaqachon tizimga admin sifatida kirgan bo'lsa:
    if await is_user_admin(message.from_user.id):
        await message.answer(
            "Assalomu alaykum! Men sizning shaxsiy yordamchingizman. 😊\n\n"
            "Siz admin sifatida tizimdasiz. Quyidagi menyudan foydalanishingiz mumkin:",
            reply_markup=get_admin_main_keyboard()
        )
    else:
        await message.answer(
            "Assalomu alaykum! Men sizning shaxsiy yordamchingizman. 😊"
        )


@router.message(F.text == "❌ Bekor qilish")
async def handle_cancel_button(message: Message, state: FSMContext):
    """Har qanday jarayonni bekor qilish va bosh menyuga qaytish."""
    await state.clear()
    if await is_user_admin(message.from_user.id):
        await message.answer(
            "Amal bekor qilindi. Bosh menyuga qaytdingiz.",
            reply_markup=get_admin_main_keyboard()
        )
    else:
        await message.answer(
            "Amal bekor qilindi.",
            reply_markup=None
        )


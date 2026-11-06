from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def get_admin_main_keyboard() -> ReplyKeyboardMarkup:
    """Asosiy admin paneli klaviaturasi."""
    keyboard = [
        [
            KeyboardButton(text="➕ Vazifa qo‘shish"),
            KeyboardButton(text="📋 Barcha vazifalar")
        ],
        [
            KeyboardButton(text="📅 Bugungi vazifalar"),
            KeyboardButton(text="📊 Bajarilgan vazifalar")
        ],
        [
            KeyboardButton(text="✏️ Vazifani tahrirlash"),
            KeyboardButton(text="🗑 Vazifani o‘chirish")
        ],
        [
            KeyboardButton(text="⏰ Eslatma vaqtini belgilash"),
            KeyboardButton(text="⚙️ Sozlamalar")
        ],
        [
            KeyboardButton(text="🔐 Parolni o‘zgartirish"),
            KeyboardButton(text="🚪 Admin paneldan chiqish")
        ]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    """Jarayonni bekor qilish klaviaturasi."""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Bekor qilish")]],
        resize_keyboard=True
    )


def get_date_picker_keyboard() -> ReplyKeyboardMarkup:
    """Sana tanlash uchun tezkor tugmalar."""
    keyboard = [
        [
            KeyboardButton(text="📅 Bugun"),
            KeyboardButton(text="📅 Ertaga")
        ],
        [
            KeyboardButton(text="📅 Indinga"),
            KeyboardButton(text="❌ Bekor qilish")
        ]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def get_recurrence_keyboard() -> ReplyKeyboardMarkup:
    """Takrorlanish holatini tanlash klaviaturasi."""
    keyboard = [
        [
            KeyboardButton(text="🔄 Ha, har kuni"),
            KeyboardButton(text="➡️ Yo‘q, bir martalik")
        ],
        [
            KeyboardButton(text="❌ Bekor qilish")
        ]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Dict, Any


def get_reminder_keyboard(task_id: int) -> InlineKeyboardMarkup:
    """
    Eslatma xabari ostidagi 3 ta asosiy tugma:
    - ✅ Bajarildi
    - ⏳ Keyinroq eslat
    - ❌ O‘tkazib yuborish
    """
    keyboard = [
        [
            InlineKeyboardButton(text="✅ Bajarildi", callback_data=f"reminder_done:{task_id}")
        ],
        [
            InlineKeyboardButton(text="⏳ Keyinroq eslat", callback_data=f"reminder_snooze:{task_id}"),
            InlineKeyboardButton(text="❌ O‘tkazib yuborish", callback_data=f"reminder_skip:{task_id}")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_snooze_options_keyboard(task_id: int) -> InlineKeyboardMarkup:
    """Keyinroq eslatish vaqtlari varianti."""
    keyboard = [
        [
            InlineKeyboardButton(text="⏱ 10 daqiqa", callback_data=f"snooze_time:{task_id}:10"),
            InlineKeyboardButton(text="⏱ 30 daqiqa", callback_data=f"snooze_time:{task_id}:30")
        ],
        [
            InlineKeyboardButton(text="⏱ 1 soat", callback_data=f"snooze_time:{task_id}:60"),
            InlineKeyboardButton(text="⏱ 2 soat", callback_data=f"snooze_time:{task_id}:120")
        ],
        [
            InlineKeyboardButton(text="⬅️ Orqaga", callback_data=f"snooze_back:{task_id}")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_task_action_keyboard(task_id: int) -> InlineKeyboardMarkup:
    """Vazifa kartasi ostidagi boshqaruv tugmalari."""
    keyboard = [
        [
            InlineKeyboardButton(text="✅ Bajarildi", callback_data=f"task_done:{task_id}"),
            InlineKeyboardButton(text="✏️ Tahrirlash", callback_data=f"task_edit_direct:{task_id}")
        ],
        [
            InlineKeyboardButton(text="⏰ Vaqtni o‘zgartirish", callback_data=f"task_change_time:{task_id}"),
            InlineKeyboardButton(text="🗑 O‘chirish", callback_data=f"task_delete_direct:{task_id}")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_tasks_list_keyboard(tasks: List[Dict[str, Any]], action_prefix: str) -> InlineKeyboardMarkup:
    """Vazifalar ro'yxatidan tanlash uchun tugmalar."""
    keyboard = []
    for task in tasks:
        title = task["title"]
        if len(title) > 25:
            title = title[:22] + "..."
        time_str = task.get("task_time", "")
        btn_text = f"#{task['id']} | {time_str} - {title}"
        keyboard.append([
            InlineKeyboardButton(text=btn_text, callback_data=f"{action_prefix}:{task['id']}")
        ])
    keyboard.append([
        InlineKeyboardButton(text="❌ Yopish", callback_data="close_menu")
    ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_edit_fields_keyboard(task_id: int) -> InlineKeyboardMarkup:
    """Tahrirlanadigan maydonni tanlash."""
    keyboard = [
        [
            InlineKeyboardButton(text="📝 Nomini o‘zgartirish", callback_data=f"edit_field:{task_id}:title")
        ],
        [
            InlineKeyboardButton(text="📅 Sanasini o‘zgartirish", callback_data=f"edit_field:{task_id}:date"),
            InlineKeyboardButton(text="🕒 Vaqtini o‘zgartirish", callback_data=f"edit_field:{task_id}:time")
        ],
        [
            InlineKeyboardButton(text="🔄 Takrorlanishini almashtirish", callback_data=f"edit_field:{task_id}:recurrence")
        ],
        [
            InlineKeyboardButton(text="❌ Bekor qilish", callback_data="close_menu")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_delete_confirm_keyboard(task_id: int) -> InlineKeyboardMarkup:
    """O'chirishni tasdiqlash klaviaturasi."""
    keyboard = [
        [
            InlineKeyboardButton(text="🗑 Ha, o‘chirilsin", callback_data=f"confirm_delete:{task_id}"),
            InlineKeyboardButton(text="❌ Yo‘q, bekor qilish", callback_data="close_menu")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


import asyncio
import os
import sys
from datetime import datetime, timedelta
import pytz

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + "/.."))

from config import TIMEZONE
from database.db import (
    init_db,
    add_task,
    get_task,
    get_all_tasks,
    get_today_tasks,
    get_completed_tasks,
    get_tasks_stats,
    mark_task_completed,
    reschedule_daily_task,
    update_task,
    delete_task,
    get_admin_password,
    set_admin_password,
    set_admin_id,
    is_admin,
    check_lockout,
    record_failed_attempt,
    reset_failed_attempts
)
from services.security import verify_password, update_admin_password
from handlers.task_add import parse_date, parse_time


async def run_tests():
    print("=" * 60)
    print("🤖 SHAXSIY VAZIFALAR ESLATUVCHI BOT - TESTLAR")
    print("=" * 60)

    # 1. Database initsializatsiyasi
    print("[1] Ma'lumotlar bazasini initsializatsiya qilish...")
    await init_db()
    print("    ✅ Ma'lumotlar bazasi va jadvallar muvaffaqiyatli yaratildi.")

    # 2. Standart admin paroli tekshiruvi
    print("[2] Boshlang'ich parol tekshiruvi ('Parol_2012')...")
    pwd = await get_admin_password()
    assert pwd == "Parol_2012", f"Kutilgan 'Parol_2012', lekin olindi: {pwd}"
    print(f"    ✅ Boshlang'ich parol to'g'ri: '{pwd}'")

    # 3. Sana va vaqt parserlari
    print("[3] Sana va vaqt tahlil qiluvchi (parser) funksiyalarni tekshirish...")
    today_str = datetime.now(TIMEZONE).strftime("%Y-%m-%d")
    tomorrow_str = (datetime.now(TIMEZONE) + timedelta(days=1)).strftime("%Y-%m-%d")

    assert parse_date("Bugun") == today_str
    assert parse_date("bugun") == today_str
    assert parse_date("Ertaga") == tomorrow_str
    assert parse_date("2026-11-15") == "2026-11-15"
    assert parse_date("15.11.2026") == "2026-11-15"
    assert parse_date("noto'g'ri sana") is None

    assert parse_time("18:00") == "18:00"
    assert parse_time("9:30") == "09:30"
    assert parse_time("23:59") == "23:59"
    assert parse_time("25:00") is None
    print("    ✅ Barcha sana va vaqt formatlari to'g'ri tahlil qilindi.")

    # 4. Parol bilan autentifikatsiya va Brute-Force himoyasi
    print("[4] Parol tekshiruvi va noto'g'ri urinishlarga qarshi himoya...")
    test_user_id = 99998888

    # Noto'g'ri parol kiritish
    ok, msg = await verify_password(test_user_id, "Xato_parol")
    assert not ok
    print(f"    ✅ Noto'g'ri parol to'g'ri aniqlandi: '{msg}'")

    # To'g'ri parol kiritish
    ok, msg = await verify_password(test_user_id, "Parol_2012")
    assert ok
    assert await is_admin(test_user_id)
    print("    ✅ To'g'ri parol bilan admin tizimga muvaffaqiyatli kirdi.")

    # 5. Vazifa qo'shish va boshqarish
    print("[5] Vazifa qo'shish (CRUD) funksiyalari...")
    task_id = await add_task(
        user_id=test_user_id,
        title="Ingliz tili darsi",
        task_date=today_str,
        task_time="18:00",
        is_daily=1
    )
    print(f"    ✅ Vazifa qo'shildi, ID: #{task_id}")

    task = await get_task(task_id)
    assert task is not None
    assert task["title"] == "Ingliz tili darsi"
    assert task["is_daily"] == 1
    assert task["is_completed"] == 0

    # Bugungi vazifalarni tekshirish
    today_tasks = await get_today_tasks(test_user_id)
    assert any(t["id"] == task_id for t in today_tasks)
    print(f"    ✅ Bugungi vazifalar ro'yxatida vazifa topildi ({len(today_tasks)} ta vazifa).")

    # Vazifani tahrirlash (Vaqtini o'zgartirish)
    print("[6] Vazifani tahrirlash (Vaqtini 19:30 ga o'zgartirish)...")
    await update_task(task_id, task_time="19:30")
    updated = await get_task(task_id)
    assert updated["task_time"] == "19:30"
    print("    ✅ Vazifa vaqti 19:30 ga muvaffaqiyatli yangilandi.")

    # Takrorlanuvchi vazifani bajarish va keyingi kunga rejalashtirish
    print("[7] Takrorlanuvchi vazifani keyingi kunga o'tkazish...")
    next_day = (datetime.now(TIMEZONE) + timedelta(days=1)).strftime("%Y-%m-%d")
    await reschedule_daily_task(task_id, next_day)
    rescheduled = await get_task(task_id)
    assert rescheduled["task_date"] == next_day
    assert rescheduled["is_completed"] == 0
    print(f"    ✅ Takrorlanuvchi vazifa {next_day} sanasiga o'tkazildi.")

    # Vazifani bajarilgan deb belgilash
    await mark_task_completed(task_id)
    completed_task = await get_task(task_id)
    assert completed_task["is_completed"] == 1
    print("    ✅ Vazifa bajarilgan deb belgilandi.")

    # Statistikani tekshirish
    stats = await get_tasks_stats(test_user_id)
    print(f"    ✅ Statistika: {stats}")

    # Vazifani o'chirish
    print("[8] Vazifani o'chirish...")
    deleted = await delete_task(task_id)
    assert deleted
    assert await get_task(task_id) is None
    print("    ✅ Vazifa bazadan muvaffaqiyatli o'chirildi.")

    # 9. Parolni o'zgartirish testi
    print("[9] Parolni o'zgartirish funksiyasi...")
    success, msg = await update_admin_password(test_user_id, "Parol_2012", "YangiParol_2026")
    assert success
    assert await get_admin_password() == "YangiParol_2026"
    print("    ✅ Admin paroli 'YangiParol_2026' ga muvaffaqiyatli o'zgartirildi.")

    # Parolni yana dastlabki 'Parol_2012' ga qaytarib qo'yamiz (talab bo'yicha)
    await set_admin_password("Parol_2012")
    assert await get_admin_password() == "Parol_2012"
    print("    ✅ Parol dastlabki 'Parol_2012' holatiga qaytarildi.")

    print("=" * 60)
    print("🎉 BARCHA TESTLAR 100% MUVAFFAQIYATLI O'TDI!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_tests())


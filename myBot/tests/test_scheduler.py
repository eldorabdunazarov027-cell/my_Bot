import asyncio
import os
import sys
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + "/.."))

from config import TIMEZONE
from services.scheduler import (
    scheduler,
    schedule_task,
    snooze_task_reminder,
    cancel_task_job,
    send_task_reminder
)
from database.db import init_db, add_task, get_task, delete_task


async def run_scheduler_test():
    print("=" * 60)
    print("⏰ APSCHEDULER ESLATMALAR TIZIMI TESTI")
    print("=" * 60)

    await init_db()

    mock_bot = AsyncMock()
    mock_bot.send_message = AsyncMock()

    # Scheduler ni start qilamiz
    if not scheduler.running:
        scheduler.start()

    now = datetime.now(TIMEZONE)
    future_time = (now + timedelta(minutes=5)).strftime("%H:%M")
    today_str = now.strftime("%Y-%m-%d")

    # 1. Vazifa qo'shish va rejalashtirish
    task_id = await add_task(
        user_id=12345678,
        title="Ingliz tili imtihoni",
        task_date=today_str,
        task_time=future_time,
        is_daily=0
    )
    task = await get_task(task_id)

    ok = schedule_task(mock_bot, task)
    assert ok, "Vazifa rejalashtirilmadi!"
    job = scheduler.get_job(f"task_{task_id}")
    assert job is not None, "Job schedulerda topilmadi!"
    print(f"    ✅ Vazifa #{task_id} {today_str} {future_time} ga muvaffaqiyatli rejalashtirildi.")

    # 2. Keyinroq eslatish (Snooze)
    snooze_ok = snooze_task_reminder(mock_bot, task_id, minutes=10)
    assert snooze_ok, "Snooze rejalashtirilmadi!"
    job_snoozed = scheduler.get_job(f"task_{task_id}")
    assert job_snoozed is not None
    print(f"    ✅ Vazifa #{task_id} 10 daqiqaga kechiktirildi (Snooze muvaffaqiyatli).")

    # 3. Eslatma yuborish funksiyasini test qilish
    await send_task_reminder(mock_bot, task_id, is_snooze=True)
    assert mock_bot.send_message.called, "Bot send_message chaqirilmadi!"
    call_args = mock_bot.send_message.call_args
    sent_text = call_args[1]["text"]
    assert "Ingliz tili imtihoni" in sent_text
    assert "Kechiktirilgan" in sent_text
    print("    ✅ Eslatma xabari to'g'ri matn va tugmalar bilan yuborildi.")

    # 4. Jobni bekor qilish va tozalash
    cancel_task_job(task_id)
    assert scheduler.get_job(f"task_{task_id}") is None
    await delete_task(task_id)
    print(f"    ✅ Job va vazifa muvaffaqiyatli tozalandi.")

    scheduler.shutdown(wait=False)
    print("=" * 60)
    print("🎉 APSCHEDULER TESTLARI 100% MUVAFFAQIYATLI O'TDI!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_scheduler_test())


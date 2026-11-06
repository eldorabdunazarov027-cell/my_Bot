import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot
from config import TIMEZONE
from database.db import (
    get_task,
    mark_task_reminded,
    get_all_pending_tasks,
    reschedule_daily_task
)
from keyboards.inline import get_reminder_keyboard

logger = logging.getLogger(__name__)

# Asinxron rejalashtiruvchi instansiyasi
scheduler = AsyncIOScheduler(timezone=TIMEZONE)


async def send_task_reminder(bot: Bot, task_id: int, is_snooze: bool = False) -> None:
    """Belgilangan vaqtda foydalanuvchiga eslatma xabarini yuborish."""
    task = await get_task(task_id)
    if not task:
        logger.warning(f"Vazifa topilmadi: {task_id}")
        return

    # Agar vazifa allaqachon bajarilgan bo'lsa, eslatma yubormaymiz
    if task["is_completed"]:
        logger.info(f"Vazifa #{task_id} allaqachon bajarilgan, eslatma bekor qilindi.")
        return

    user_id = task["user_id"]
    title = task["title"]
    time_str = task["task_time"]

    header = "⏰ ESLATMA! (Kechiktirilgan)" if is_snooze else "⏰ ESLATMA!"
    text = (
        f"{header}\n\n"
        f"📌 <b>Vazifa:</b> {title}\n"
        f"🕒 <b>Vaqt:</b> {time_str}\n\n"
        f"Vazifani bajarishni unutmang!"
    )

    try:
        await bot.send_message(
            chat_id=user_id,
            text=text,
            reply_markup=get_reminder_keyboard(task_id),
            parse_mode="HTML"
        )
        await mark_task_reminded(task_id, 1)
        logger.info(f"Vazifa #{task_id} uchun eslatma foydalanuvchi {user_id} ga yuborildi.")
    except Exception as e:
        logger.error(f"Eslatma yuborishda xatolik #{task_id}: {e}")


def schedule_task(bot: Bot, task: Dict[str, Any]) -> bool:
    """Yangi yoki tahrirlangan vazifani APScheduler ga joylash."""
    task_id = task["id"]
    date_str = task["task_date"]  # YYYY-MM-DD
    time_str = task["task_time"]  # HH:MM

    try:
        # Sana va vaqtni birlashtirib timezone bilan yaratish
        task_dt_naive = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        task_dt = TIMEZONE.localize(task_dt_naive)
        now = datetime.now(TIMEZONE)

        # Agar vaqt o'tib ketgan bo'lsa va bu har kuni takrorlanadigan vazifa bo'lsa:
        if task_dt <= now and task.get("is_daily"):
            # Ertangi kunga rejalashtiramiz
            task_dt = task_dt + timedelta(days=1)

        job_id = f"task_{task_id}"

        # Agar vaqt kelajakda bo'lsa, rejalashtiramiz
        if task_dt > now:
            scheduler.add_job(
                send_task_reminder,
                trigger="date",
                run_date=task_dt,
                args=[bot, task_id, False],
                id=job_id,
                replace_existing=True,
                misfire_grace_time=3600
            )
            logger.info(f"Vazifa #{task_id} rejalashtirildi: {task_dt.isoformat()}")
            return True
        else:
            logger.info(f"Vazifa #{task_id} vaqti o'tib ketgan, rejalashtirilmadi.")
            return False
    except Exception as e:
        logger.error(f"Vazifani rejalashtirishda xatolik #{task_id}: {e}")
        return False


def snooze_task_reminder(bot: Bot, task_id: int, minutes: int) -> bool:
    """Eslatmani ma'lum daqiqaga kechiktirish."""
    try:
        run_date = datetime.now(TIMEZONE) + timedelta(minutes=minutes)
        job_id = f"task_{task_id}"

        scheduler.add_job(
            send_task_reminder,
            trigger="date",
            run_date=run_date,
            args=[bot, task_id, True],
            id=job_id,
            replace_existing=True,
            misfire_grace_time=3600
        )
        logger.info(f"Vazifa #{task_id} {minutes} daqiqaga kechiktirildi ({run_date.isoformat()}).")
        return True
    except Exception as e:
        logger.error(f"Vazifani kechiktirishda xatolik #{task_id}: {e}")
        return False


def cancel_task_job(task_id: int) -> None:
    """Rejalashtirilgan ishni bekor qilish."""
    job_id = f"task_{task_id}"
    try:
        job = scheduler.get_job(job_id)
        if job:
            scheduler.remove_job(job_id)
            logger.info(f"Job {job_id} muvaffaqiyatli bekor qilindi.")
    except Exception as e:
        logger.error(f"Jobni bekor qilishda xatolik {job_id}: {e}")


async def restore_scheduled_tasks(bot: Bot) -> None:
    """Bot qayta ishga tushganda barcha faol vazifalarni xotiraga tiklash."""
    pending_tasks = await get_all_pending_tasks()
    logger.info(f"Tiklash uchun {len(pending_tasks)} ta faol vazifa topildi.")

    now = datetime.now(TIMEZONE)
    restored_count = 0

    for task in pending_tasks:
        try:
            task_dt_naive = datetime.strptime(f"{task['task_date']} {task['task_time']}", "%Y-%m-%d %H:%M")
            task_dt = TIMEZONE.localize(task_dt_naive)

            if task_dt > now:
                # Kelajakdagi vazifa
                schedule_task(bot, task)
                restored_count += 1
            elif task.get("is_daily"):
                # Har kungi vazifa vaqti o'tib ketgan bo'lsa, ertangi kunga yangilaymiz
                next_date = (now + timedelta(days=1)).strftime("%Y-%m-%d")
                await reschedule_daily_task(task["id"], next_date)
                updated_task = await get_task(task["id"])
                if updated_task:
                    schedule_task(bot, updated_task)
                    restored_count += 1
        except Exception as e:
            logger.error(f"Vazifani tiklashda xatolik #{task.get('id')}: {e}")

    logger.info(f"Jami {restored_count} ta vazifa eslatmasi tiklandi.")


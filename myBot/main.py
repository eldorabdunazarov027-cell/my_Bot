import asyncio
import logging
import os
import sys
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
from database.db import init_db
from services.scheduler import scheduler, restore_scheduled_tasks

# Routerlarni import qilish
from handlers.start import router as start_router
from handlers.admin_auth import router as admin_auth_router
from handlers.task_add import router as task_add_router
from handlers.task_list import router as task_list_router
from handlers.task_edit import router as task_edit_router
from handlers.task_delete import router as task_delete_router
from handlers.reminder_actions import router as reminder_actions_router
from handlers.settings import router as settings_router

# Logging sozlamalari
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("TaskReminderBot")


async def start_render_health_server():
    """Render.com da 'Port scan timeout' xatoligi bermasligi uchun yengil veb-server."""
    port_str = os.getenv("PORT")
    if not port_str:
        return None
    try:
        port = int(port_str)
        app = web.Application()

        async def handle_ping(request):
            return web.Response(text="Bot is running 24/7! 🚀", status=200)

        app.router.add_get("/", handle_ping)
        app.router.add_get("/health", handle_ping)

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", port)
        await site.start()
        logger.info(f"Render uchun veb-server {port}-portda muvaffaqiyatli ishga tushdi.")
        return runner
    except Exception as e:
        logger.warning(f"Veb-serverni ishga tushirishda xatolik: {e}")
        return None


async def main():
    """Botning asosiy ishga tushirish funksiyasi."""
    logger.info("Bot tizimi ishga tushmoqda...")

    # Bot tokeni tekshiruvi
    if not BOT_TOKEN:
        logger.error(
            "XATOLIK: BOT_TOKEN aniqlanmadi!\n"
            "Iltimos, '.env' faylini oching va Telegram BotFather dan olingan tokenni kiriting:\n"
            "BOT_TOKEN=sizning_tokeningiz"
        )
        sys.exit(1)

    # Ma'lumotlar bazasini initsializatsiya qilish
    logger.info("Ma'lumotlar bazasi (SQLite) tayyorlanmoqda...")
    await init_db()
    logger.info("Ma'lumotlar bazasi muvaffaqiyatli ulandi.")

    # Bot va Dispatcher yaratish
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Routerlarni ro'yxatdan o'tkazish
    dp.include_router(start_router)
    dp.include_router(admin_auth_router)
    dp.include_router(task_add_router)
    dp.include_router(task_list_router)
    dp.include_router(task_edit_router)
    dp.include_router(task_delete_router)
    dp.include_router(reminder_actions_router)
    dp.include_router(settings_router)

    # Render uchun port serverini ishga tushirish (agar PORT bo'lsa)
    web_runner = await start_render_health_server()

    # Rejalashtiruvchini (APScheduler) ishga tushirish
    scheduler.start()
    logger.info("APScheduler eslatmalar xizmati ishga tushdi.")

    # Bot qayta yoqilganda avvalgi rejalashtirilgan eslatmalarni tiklash
    await restore_scheduled_tasks(bot)

    # Eski kutilayotgan yangilanishlarni tozalash (drop pending updates)
    await bot.delete_webhook(drop_pending_updates=True)

    try:
        logger.info("🤖 Bot 24/7 rejimida xabarlarni qabul qilishga tayyor!")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Bot ishlashida xatolik yuz berdi: {e}")
    finally:
        logger.info("Bot to‘xtatilmoqda...")
        if web_runner:
            await web_runner.cleanup()
        if scheduler.running:
            scheduler.shutdown(wait=False)
        await bot.session.close()
        logger.info("Bot xizmati to‘xtatildi.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot foydalanuvchi tomonidan to‘xtatildi.")


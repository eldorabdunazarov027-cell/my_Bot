import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + "/.."))

from database.db import get_connection, set_admin_password


async def clean_database():
    async with get_connection() as conn:
        await conn.execute("DELETE FROM tasks")
        await conn.execute("DELETE FROM login_attempts")
        await conn.execute("DELETE FROM settings WHERE key != 'admin_password'")
        await conn.commit()
    await set_admin_password("Parol_2012")
    print("Baza toza holatga keltirildi!")


if __name__ == "__main__":
    asyncio.run(clean_database())


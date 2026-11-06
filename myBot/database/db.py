import aiosqlite
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
import pytz
from config import DB_PATH, DEFAULT_ADMIN_PASSWORD, MAX_FAILED_ATTEMPTS, LOCKOUT_MINUTES, TIMEZONE


@asynccontextmanager
async def get_connection():
    """Ma'lumotlar bazasiga xavfsiz asinxron ulanish context manageri."""
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        yield conn


async def init_db() -> None:
    """Ma'lumotlar bazasi jadvallarini yaratish va boshlang'ich sozlamalarni o'rnatish."""
    async with get_connection() as conn:
        # Vazifalar jadvali
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                task_date TEXT NOT NULL,
                task_time TEXT NOT NULL,
                datetime_str TEXT NOT NULL,
                is_daily INTEGER DEFAULT 0,
                is_completed INTEGER DEFAULT 0,
                is_reminded INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        # Sozlamalar jadvali
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)

        # Xavfsizlik: noto'g'ri urinishlar jadvali
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS login_attempts (
                user_id INTEGER PRIMARY KEY,
                attempts INTEGER DEFAULT 0,
                locked_until TEXT
            )
        """)

        # Agar admin paroli bazada yo'q bo'lsa, .env dagi standart parolni yozish
        cursor = await conn.execute("SELECT value FROM settings WHERE key = 'admin_password'")
        row = await cursor.fetchone()
        if not row:
            await conn.execute(
                "INSERT INTO settings (key, value) VALUES ('admin_password', ?)",
                (DEFAULT_ADMIN_PASSWORD,)
            )

        await conn.commit()


# ==================== VAZIFALAR BILAN ISHLASH ====================

async def add_task(
    user_id: int,
    title: str,
    task_date: str,
    task_time: str,
    is_daily: int = 0
) -> int:
    """Yangi vazifa qo'shish va ID raqamini qaytarish."""
    now_str = datetime.now(TIMEZONE).strftime("%Y-%m-%d %H:%M:%S")
    datetime_str = f"{task_date} {task_time}"

    async with get_connection() as conn:
        cursor = await conn.execute(
            """
            INSERT INTO tasks (
                user_id, title, task_date, task_time, datetime_str,
                is_daily, is_completed, is_reminded, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, 0, 0, ?, ?)
            """,
            (user_id, title, task_date, task_time, datetime_str, is_daily, now_str, now_str)
        )
        await conn.commit()
        return cursor.lastrowid


async def get_task(task_id: int) -> Optional[Dict[str, Any]]:
    """Bitta vazifani ID bo'yicha olish."""
    async with get_connection() as conn:
        cursor = await conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        row = await cursor.fetchone()
        if row:
            return dict(row)
        return None


async def get_all_tasks(user_id: Optional[int] = None, include_completed: bool = False) -> List[Dict[str, Any]]:
    """Barcha vazifalar ro'yxatini olish."""
    async with get_connection() as conn:
        query = "SELECT * FROM tasks WHERE 1=1"
        params: List[Any] = []

        if user_id is not None:
            query += " AND user_id = ?"
            params.append(user_id)

        if not include_completed:
            query += " AND is_completed = 0"

        query += " ORDER BY task_date ASC, task_time ASC"

        cursor = await conn.execute(query, params)
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def get_today_tasks(user_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """Bugungi kunga tegishli faol vazifalarni olish."""
    today_str = datetime.now(TIMEZONE).strftime("%Y-%m-%d")
    async with get_connection() as conn:
        query = "SELECT * FROM tasks WHERE task_date = ? AND is_completed = 0"
        params: List[Any] = [today_str]

        if user_id is not None:
            query += " AND user_id = ?"
            params.append(user_id)

        query += " ORDER BY task_time ASC"
        cursor = await conn.execute(query, params)
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def get_completed_tasks(user_id: Optional[int] = None, limit: int = 50) -> List[Dict[str, Any]]:
    """Bajarilgan vazifalar ro'yxatini olish."""
    async with get_connection() as conn:
        query = "SELECT * FROM tasks WHERE is_completed = 1"
        params: List[Any] = []

        if user_id is not None:
            query += " AND user_id = ?"
            params.append(user_id)

        query += " ORDER BY updated_at DESC LIMIT ?"
        params.append(limit)

        cursor = await conn.execute(query, params)
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def get_tasks_stats(user_id: Optional[int] = None) -> Dict[str, int]:
    """Vazifalar statistikasi."""
    async with get_connection() as conn:
        base_query = "FROM tasks WHERE 1=1"
        params: List[Any] = []
        if user_id is not None:
            base_query += " AND user_id = ?"
            params.append(user_id)

        cursor = await conn.execute(f"SELECT COUNT(*) {base_query}", params)
        total = (await cursor.fetchone())[0]

        cursor = await conn.execute(f"SELECT COUNT(*) {base_query} AND is_completed = 1", params)
        completed = (await cursor.fetchone())[0]

        cursor = await conn.execute(f"SELECT COUNT(*) {base_query} AND is_completed = 0", params)
        pending = (await cursor.fetchone())[0]

        cursor = await conn.execute(f"SELECT COUNT(*) {base_query} AND is_daily = 1", params)
        daily = (await cursor.fetchone())[0]

        return {
            "total": total,
            "completed": completed,
            "pending": pending,
            "daily": daily
        }


async def mark_task_completed(task_id: int) -> bool:
    """Vazifani bajarilgan deb belgilash."""
    now_str = datetime.now(TIMEZONE).strftime("%Y-%m-%d %H:%M:%S")
    async with get_connection() as conn:
        cursor = await conn.execute(
            "UPDATE tasks SET is_completed = 1, is_reminded = 1, updated_at = ? WHERE id = ?",
            (now_str, task_id)
        )
        await conn.commit()
        return cursor.rowcount > 0


async def mark_task_reminded(task_id: int, reminded: int = 1) -> bool:
    """Eslatma yuborilganlik holatini yangilash."""
    async with get_connection() as conn:
        cursor = await conn.execute(
            "UPDATE tasks SET is_reminded = ? WHERE id = ?",
            (reminded, task_id)
        )
        await conn.commit()
        return cursor.rowcount > 0


async def reschedule_daily_task(task_id: int, next_date_str: str) -> bool:
    """Takrorlanadigan vazifani keyingi kunga o'tkazish."""
    now_str = datetime.now(TIMEZONE).strftime("%Y-%m-%d %H:%M:%S")
    async with get_connection() as conn:
        cursor = await conn.execute("SELECT task_time FROM tasks WHERE id = ?", (task_id,))
        row = await cursor.fetchone()
        if not row:
            return False
        task_time = row["task_time"]
        new_datetime_str = f"{next_date_str} {task_time}"

        cursor = await conn.execute(
            """
            UPDATE tasks 
            SET task_date = ?, datetime_str = ?, is_completed = 0, is_reminded = 0, updated_at = ?
            WHERE id = ?
            """,
            (next_date_str, new_datetime_str, now_str, task_id)
        )
        await conn.commit()
        return cursor.rowcount > 0


async def update_task(task_id: int, **fields: Any) -> bool:
    """Vazifa maydonlarini yangilash (title, task_date, task_time, is_daily)."""
    if not fields:
        return False

    now_str = datetime.now(TIMEZONE).strftime("%Y-%m-%d %H:%M:%S")
    fields["updated_at"] = now_str

    if "task_date" in fields or "task_time" in fields:
        async with get_connection() as conn:
            cursor = await conn.execute("SELECT task_date, task_time FROM tasks WHERE id = ?", (task_id,))
            row = await cursor.fetchone()
            if row:
                d = fields.get("task_date", row["task_date"])
                t = fields.get("task_time", row["task_time"])
                fields["datetime_str"] = f"{d} {t}"
                fields["is_reminded"] = 0

    set_clause = ", ".join([f"{k} = ?" for k in fields.keys()])
    values = list(fields.values()) + [task_id]

    async with get_connection() as conn:
        cursor = await conn.execute(
            f"UPDATE tasks SET {set_clause} WHERE id = ?",
            values
        )
        await conn.commit()
        return cursor.rowcount > 0


async def delete_task(task_id: int) -> bool:
    """Vazifani o'chirish."""
    async with get_connection() as conn:
        cursor = await conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        await conn.commit()
        return cursor.rowcount > 0


async def get_all_pending_tasks() -> List[Dict[str, Any]]:
    """Barcha bajarilmagan faol vazifalarni olish (Bot qayta yoqilganda jadvalni tiklash uchun)."""
    async with get_connection() as conn:
        cursor = await conn.execute(
            "SELECT * FROM tasks WHERE is_completed = 0 ORDER BY datetime_str ASC"
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


# ==================== ADMIN VA XAVFSIZLIK ====================

async def get_setting(key: str, default: Optional[str] = None) -> Optional[str]:
    """Sozlamani olish."""
    async with get_connection() as conn:
        cursor = await conn.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = await cursor.fetchone()
        if row and row["value"]:
            return row["value"]
        return default


async def set_setting(key: str, value: str) -> None:
    """Sozlamani saqlash yoki yangilash."""
    async with get_connection() as conn:
        await conn.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            (key, value)
        )
        await conn.commit()


async def get_admin_password() -> str:
    """Hozirgi admin parolini olish."""
    async with get_connection() as conn:
        cursor = await conn.execute("SELECT value FROM settings WHERE key = 'admin_password'")
        row = await cursor.fetchone()
        if row and row["value"]:
            return row["value"]
        return DEFAULT_ADMIN_PASSWORD


async def set_admin_password(new_password: str) -> None:
    """Yangi admin parolini saqlash."""
    async with get_connection() as conn:
        await conn.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES ('admin_password', ?)",
            (new_password,)
        )
        await conn.commit()


async def get_admin_id() -> Optional[int]:
    """Tizimga kirgan admin Telegram ID sini olish."""
    async with get_connection() as conn:
        cursor = await conn.execute("SELECT value FROM settings WHERE key = 'admin_id'")
        row = await cursor.fetchone()
        if row and row["value"]:
            try:
                return int(row["value"])
            except ValueError:
                return None
        return None


async def set_admin_id(user_id: int) -> None:
    """Admin Telegram ID sini saqlash."""
    async with get_connection() as conn:
        await conn.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES ('admin_id', ?)",
            (str(user_id),)
        )
        await conn.commit()


async def is_admin(user_id: int) -> bool:
    """Foydalanuvchi admin ekanligini tekshirish."""
    admin_id = await get_admin_id()
    if admin_id is not None and admin_id == user_id:
        return True
    return False


async def check_lockout(user_id: int) -> Tuple[bool, int]:
    """
    Foydalanuvchi bloklanganligini tekshirish.
    Qaytaradi: (bloklanganmi, qolgan soniyalar)
    """
    async with get_connection() as conn:
        cursor = await conn.execute(
            "SELECT attempts, locked_until FROM login_attempts WHERE user_id = ?",
            (user_id,)
        )
        row = await cursor.fetchone()
        if not row or not row["locked_until"]:
            return False, 0

        now = datetime.now(TIMEZONE)
        try:
            locked_until = datetime.fromisoformat(row["locked_until"])
            if locked_until > now:
                remaining = int((locked_until - now).total_seconds())
                return True, remaining
            else:
                await conn.execute(
                    "UPDATE login_attempts SET attempts = 0, locked_until = NULL WHERE user_id = ?",
                    (user_id,)
                )
                await conn.commit()
                return False, 0
        except Exception:
            return False, 0


async def record_failed_attempt(user_id: int) -> Tuple[int, bool]:
    """
    Noto'g'ri urinishni qayd etish.
    Qaytaradi: (jami_urinishlar, bloklandimi)
    """
    async with get_connection() as conn:
        cursor = await conn.execute(
            "SELECT attempts FROM login_attempts WHERE user_id = ?",
            (user_id,)
        )
        row = await cursor.fetchone()
        current_attempts = (row["attempts"] if row else 0) + 1

        if current_attempts >= MAX_FAILED_ATTEMPTS:
            lock_until = datetime.now(TIMEZONE) + timedelta(minutes=LOCKOUT_MINUTES)
            await conn.execute(
                """
                INSERT OR REPLACE INTO login_attempts (user_id, attempts, locked_until)
                VALUES (?, ?, ?)
                """,
                (user_id, current_attempts, lock_until.isoformat())
            )
            await conn.commit()
            return current_attempts, True
        else:
            await conn.execute(
                """
                INSERT OR REPLACE INTO login_attempts (user_id, attempts, locked_until)
                VALUES (?, ?, NULL)
                """,
                (user_id, current_attempts)
            )
            await conn.commit()
            return current_attempts, False


async def reset_failed_attempts(user_id: int) -> None:
    """Muvaffaqiyatli kirganda noto'g'ri urinishlar hisobini nolga tushirish."""
    async with get_connection() as conn:
        await conn.execute(
            "DELETE FROM login_attempts WHERE user_id = ?",
            (user_id,)
        )
        await conn.commit()

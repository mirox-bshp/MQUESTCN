#!/usr/bin/env python3
# ══════════════════════════════════════════════════════════════════
#   🔥 MCV FUND PRO — النسخة الاحترافية V6
#   ✨ قناة الطلبات | عداد الطلبات | قاعدة البيانات
#   🎯 عجلة حظ محسنة | إضافة قنوات | 
#   🛍️ متجر مستقل بمنتجات خاصة | موافقة أدمن على كل الطلبات
#   📦 يتطلب: pyTelegramBotAPI >= 4.32 | Python 3.7+
# ══════════════════════════════════════════════════════════════════

import logging
import threading
import queue
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import sqlite3
import random
import string
import math
import json
import os
import asyncio
import hashlib
import sys
import subprocess
import importlib
import importlib.util
from pathlib import Path
from datetime import datetime, date
from urllib.parse import urlparse

# قائمة الإيموجيات الافتراضية للخدمات المرتبطة بحسابات Telegram.
# تُحفظ تلقائياً عند ربط أول حساب بالخدمة، فلا يحتاج المستخدم لإدخالها كل مرة.
MIRX_DEFAULT_REACTION_EMOJIS = [
    "👍", "❤️", "🔥", "😂", "😍", "🥰", "😢", "😡", "👏", "🎉",
    "🤩", "💯", "🤔", "🤣", "🙏", "🥳", "🤯", "😎", "👎", "😱",
]
MIRX_DEFAULT_REACTION_POOL = ",".join(MIRX_DEFAULT_REACTION_EMOJIS)

# ══════════════════════════════════════════════════════════════════
#   تثبيت كل المكتبات الخارجية المطلوبة تلقائياً
#   لا يتم لمس مكتبات Python الداخلية مثل sqlite3 أو json أو pathlib.
#   أسماء الحزم الصحيحة فقط: pyTelegramBotAPI / requests / Telethon.
# ══════════════════════════════════════════════════════════════════
_REQUIRED_PACKAGES = {
    "telebot": "pyTelegramBotAPI>=4.32",
    "telethon": "Telethon>=1.40,<2",
}


def _pip_install(package):
    """تثبيت حزمة حتى لو كانت pip غير مثبتة داخل بيئة التشغيل."""
    pip_cmd = [
        sys.executable, "-m", "pip", "install",
        "--disable-pip-version-check", "--no-input",
        "--prefer-binary", package
    ]

    try:
        subprocess.check_call(pip_cmd)
        return True, None
    except Exception as first_error:
        # بعض بيئات Replit/الحاويات تأتي بدون pip داخل python المخصص.
        try:
            print("[BOOT] pip غير موجود، جاري تفعيله عبر ensurepip...")
            subprocess.check_call([sys.executable, "-m", "ensurepip", "--upgrade"])
            importlib.invalidate_caches()
            subprocess.check_call(pip_cmd)
            return True, None
        except Exception as second_error:
            return False, f"pip: {first_error} | ensurepip: {second_error}"


def _ensure_external_packages():
    missing = []
    for module_name, package_name in _REQUIRED_PACKAGES.items():
        try:
            if importlib.util.find_spec(module_name) is None:
                missing.append(package_name)
        except Exception:
            missing.append(package_name)

    if not missing:
        return True

    print("[BOOT] مكتبات ناقصة، جاري تثبيتها:", ", ".join(missing))
    errors = []
    for package in missing:
        ok, error = _pip_install(package)
        if ok:
            print(f"[BOOT] تم تثبيت: {package}")
        else:
            errors.append(f"{package}: {error}")

    importlib.invalidate_caches()
    if errors:
        print("[BOOT] فشل تثبيت بعض المكتبات:")
        for err in errors:
            print("[BOOT]", err)
        return False
    return True


if not _ensure_external_packages():
    raise RuntimeError(
        "تعذر تثبيت المكتبات الخارجية المطلوبة تلقائياً. "
        "تحقق من صلاحية pip واتصال الإنترنت في بيئة تشغيل البوت."
    )

import telebot

# ══════════════════════════════════════════════════════════════════
#   تحميل Telethon بعد التأكد من وجودها
# ══════════════════════════════════════════════════════════════════
def _load_telethon(auto_install=True):
    global TelegramClient, SessionPasswordNeededError, PhoneCodeInvalidError, PhoneCodeExpiredError
    try:
        from telethon.sync import TelegramClient as _TelegramClient
        from telethon.errors import (
            SessionPasswordNeededError as _SessionPasswordNeededError,
            PhoneCodeInvalidError as _PhoneCodeInvalidError,
            PhoneCodeExpiredError as _PhoneCodeExpiredError,
        )
        TelegramClient = _TelegramClient
        SessionPasswordNeededError = _SessionPasswordNeededError
        PhoneCodeInvalidError = _PhoneCodeInvalidError
        PhoneCodeExpiredError = _PhoneCodeExpiredError
        return True, None
    except Exception as first_error:
        if not auto_install:
            TelegramClient = None
            SessionPasswordNeededError = PhoneCodeInvalidError = PhoneCodeExpiredError = Exception
            return False, str(first_error)
        try:
            ok, install_error = _pip_install("Telethon>=1.40,<2")
            if not ok:
                raise RuntimeError(install_error)
            importlib.invalidate_caches()
            from telethon.sync import TelegramClient as _TelegramClient
            from telethon.errors import (
                SessionPasswordNeededError as _SessionPasswordNeededError,
                PhoneCodeInvalidError as _PhoneCodeInvalidError,
                PhoneCodeExpiredError as _PhoneCodeExpiredError,
            )
            TelegramClient = _TelegramClient
            SessionPasswordNeededError = _SessionPasswordNeededError
            PhoneCodeInvalidError = _PhoneCodeInvalidError
            PhoneCodeExpiredError = _PhoneCodeExpiredError
            print("[Telethon] تم تثبيت/تحميل المكتبة بنجاح.")
            return True, None
        except Exception as install_error:
            TelegramClient = None
            SessionPasswordNeededError = PhoneCodeInvalidError = PhoneCodeExpiredError = Exception
            print(f"[Telethon] فشل التثبيت التلقائي: {install_error}")
            return False, str(install_error)


TelegramClient = None
SessionPasswordNeededError = PhoneCodeInvalidError = PhoneCodeExpiredError = Exception
_load_telethon(auto_install=True)
from telebot.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice, WebAppInfo

# ══════════════════════════════════════════════════════════════════
#   1. الإعدادات الافتراضية
# ══════════════════════════════════════════════════════════════════
class config:
    # إعدادات الاتصال المحلية (للتوافق مع إعدادات التشغيل الحالية)
    PORT = int(os.getenv("PORT", "8080"))
    HOST = os.getenv("HOST", "0.0.0.0")

    # توكن البوت داخل هذا الملف مباشرة.
    BOT_TOKEN = "8810773999:AAE9uXohBMus4pV81vsOxv_Px1gFha_hidA"

    ADMIN_IDS          = [ 8939118645]
    BOT_NAME           = "☬☬"
    BOT_USERNAME       = "@RSDMKBOT"
    DB_PATH            = "pluspro.db"
    REFERRAL_POINTS    = 50
    WELCOME_POINTS     = 10
    DAILY_GIFT_POINTS  = 5
    WEEKLY_GIFT_POINTS = 50
    POINTS_PER_1000    = 10
    TRACK_MESSAGES     = False

    # Telegram User API (من my.telegram.org) — لا تضع الأسرار داخل الكود.
    TG_API_ID          = int(os.getenv("TG_API_ID", "0"))
    TG_API_HASH        = os.getenv("TG_API_HASH", "")
    TG_SESSIONS_DIR    = os.getenv("TG_SESSIONS_DIR", "telegram_sessions")
    # حساب Telegram المركزي الذي ينفذ خدمات التفاعل.
    # افتراضياً: أول أدمن في البوت (يمكن تغييره من متغير البيئة).
    TG_EXECUTION_USER_ID = int(os.getenv("TG_EXECUTION_USER_ID", str(ADMIN_IDS[0] if ADMIN_IDS else 0)))


class DictRow(dict):
    """صف يدعم الوصول بالاسم والفهرس الرقمي و .get() معاً."""
    __slots__ = ("_keys",)

    def __init__(self, keys, values):
        super().__init__(zip(keys, values))
        self._keys = keys

    def __getitem__(self, key):
        if isinstance(key, int):
            return super().__getitem__(self._keys[key])
        return super().__getitem__(key)


def _dict_row_factory(cursor, row):
    keys = [col[0] for col in cursor.description]
    return DictRow(keys, row)


# قفل واحد داخل نفس عملية البوت يمنع Threads المختلفة من فتح
# معاملات SQLite متداخلة في نفس اللحظة. بالإضافة لذلك، طبقة الاتصال
# تعيد محاولة أوامر SQLite المقفولة تلقائياً بدلاً من إسقاط الطلب.
DB_WRITE_LOCK = threading.RLock()
SQLITE_BUSY_TIMEOUT_MS = int(os.getenv("SQLITE_BUSY_TIMEOUT_MS", "30000"))
SQLITE_CONNECT_TIMEOUT = max(5.0, SQLITE_BUSY_TIMEOUT_MS / 1000.0)


def _sqlite_is_write_sql(sql):
    """هل جملة SQL قد تبدأ/تعدل معاملة كتابة؟"""
    try:
        q = " ".join(str(sql or "").strip().upper().split())
    except Exception:
        return False
    if not q:
        return False
    if q.startswith("PRAGMA JOURNAL_MODE") or q.startswith("PRAGMA LOCKING_MODE"):
        return True
    return not q.startswith((
        "SELECT ", "SELECT\n", "EXPLAIN ", "VALUES ", "PRAGMA "
    ))


class _SafeSQLiteCursor(sqlite3.Cursor):
    """Cursor يعيد المحاولة عند قفل SQLite ويستخدم قفل الكتابة الداخلي."""
    def execute(self, sql, parameters=()):
        conn = self.connection
        needs_lock = _sqlite_is_write_sql(sql)
        if needs_lock:
            conn._acquire_write_lock()
        try:
            last = None
            for attempt in range(12):
                try:
                    return super().execute(sql, parameters)
                except sqlite3.OperationalError as e:
                    last = e
                    if "locked" not in str(e).lower() and "busy" not in str(e).lower():
                        raise
                    if attempt >= 11:
                        raise
                    time.sleep(min(1.0, 0.10 * (attempt + 1)))
            raise last
        except Exception:
            if needs_lock and not conn.in_transaction:
                conn._release_write_lock()
            raise

    def executemany(self, sql, seq_of_parameters):
        conn = self.connection
        needs_lock = _sqlite_is_write_sql(sql)
        if needs_lock:
            conn._acquire_write_lock()
        try:
            last = None
            for attempt in range(12):
                try:
                    return super().executemany(sql, seq_of_parameters)
                except sqlite3.OperationalError as e:
                    last = e
                    if "locked" not in str(e).lower() and "busy" not in str(e).lower():
                        raise
                    if attempt >= 11:
                        raise
                    time.sleep(min(1.0, 0.10 * (attempt + 1)))
            raise last
        except Exception:
            if needs_lock and not conn.in_transaction:
                conn._release_write_lock()
            raise


class _SafeSQLiteConnection(sqlite3.Connection):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._db_write_lock_held = False

    def cursor(self, factory=None):
        return super().cursor(factory or _SafeSQLiteCursor)

    def execute(self, sql, parameters=()):
        return self.cursor().execute(sql, parameters)

    def _acquire_write_lock(self):
        if not self._db_write_lock_held:
            DB_WRITE_LOCK.acquire()
            self._db_write_lock_held = True

    def _release_write_lock(self):
        if self._db_write_lock_held:
            self._db_write_lock_held = False
            try:
                DB_WRITE_LOCK.release()
            except RuntimeError:
                pass

    def commit(self):
        last = None
        for attempt in range(12):
            try:
                super().commit()
                self._release_write_lock()
                return
            except sqlite3.OperationalError as e:
                last = e
                if "locked" not in str(e).lower() and "busy" not in str(e).lower():
                    raise
                if attempt >= 11:
                    raise
                time.sleep(min(1.0, 0.10 * (attempt + 1)))
        raise last

    def rollback(self):
        try:
            return super().rollback()
        finally:
            self._release_write_lock()

    def close(self):
        try:
            return super().close()
        finally:
            self._release_write_lock()


class db:
    @classmethod
    def get_conn(cls):
        # البوت يعمل بعدة Threads (Polling + Telethon + تنفيذ الطلبات).
        # هذه الطبقة تمنع تعارض الكتابة داخل العملية نفسها، وتعيد المحاولة
        # تلقائياً عند وجود عملية SQLite أخرى تمسك القفل مؤقتاً.
        conn = sqlite3.connect(
            config.DB_PATH,
            timeout=SQLITE_CONNECT_TIMEOUT,
            check_same_thread=False,
            factory=_SafeSQLiteConnection,
        )
        conn.row_factory = _dict_row_factory
        conn.execute("PRAGMA foreign_keys = ON")
        # القراءة لا تنتظر كاتباً في WAL، والاتصال مستقل عن مسار الأزرار.
        conn.execute(f"PRAGMA busy_timeout = {SQLITE_BUSY_TIMEOUT_MS}")
        conn.execute("PRAGMA synchronous = NORMAL")
        conn.execute("PRAGMA temp_store = MEMORY")
        conn.execute("PRAGMA cache_size = -20000")
        return conn

    @classmethod
    def init_db(cls):
        conn = cls.get_conn()
        # WAL يسمح بالقراءة أثناء الكتابة ويقلل تعارضات SQLite بين Threads.
        try:
            conn.execute("PRAGMA journal_mode = WAL")
            conn.execute("PRAGMA synchronous = NORMAL")
            conn.execute(f"PRAGMA busy_timeout = {SQLITE_BUSY_TIMEOUT_MS}")
        except Exception:
            pass
        c = conn.cursor()

        # ── المستخدمون ──
        c.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                tg_id            INTEGER UNIQUE NOT NULL,
                username         TEXT DEFAULT '',
                full_name        TEXT DEFAULT '',
                balance          REAL    DEFAULT 0.0,
                points           INTEGER DEFAULT 0,
                referral_code    TEXT    UNIQUE,
                referred_by      INTEGER,
                join_date        TEXT    DEFAULT CURRENT_TIMESTAMP,
                is_banned        INTEGER DEFAULT 0,
                last_daily_gift  TEXT    DEFAULT '',
                last_weekly_gift TEXT    DEFAULT '',
                last_wheel_spin  TEXT    DEFAULT ''
            )
        """)

        # ── تحويلات لعبة المليون لمنع تكرار نفس عملية الإرسال ──
        c.execute("""
            CREATE TABLE IF NOT EXISTS game_transfer_claims (
                transfer_id TEXT PRIMARY KEY,
                user_id     INTEGER NOT NULL,
                amount      INTEGER NOT NULL,
                created_at  TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ── الطلبات ──
        c.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id       INTEGER NOT NULL,
                service_id    TEXT    NOT NULL,
                service_name  TEXT    DEFAULT '',
                app_name      TEXT    DEFAULT '',
                link          TEXT    NOT NULL,
                quantity      INTEGER NOT NULL,
                charge        REAL    NOT NULL DEFAULT 0,
                points_used   INTEGER DEFAULT 0,
                status        TEXT    DEFAULT 'pending',
                pending_approval INTEGER DEFAULT 1,
                api_order_id  TEXT,
                site_id       INTEGER DEFAULT NULL,
                notified_done INTEGER DEFAULT 0,
                created_at    TEXT    DEFAULT CURRENT_TIMESTAMP,
                updated_at    TEXT    DEFAULT CURRENT_TIMESTAMP
            )
        """)


        # ── الإعدادات ──
        c.execute("""
            CREATE TABLE IF NOT EXISTS config (
                key   TEXT PRIMARY KEY,
                value TEXT
            )
        """)

        # ── القنوات الإجبارية ──
        c.execute("""
            CREATE TABLE IF NOT EXISTS mandatory_channels (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id      TEXT UNIQUE NOT NULL,
                channel_name    TEXT NOT NULL,
                channel_url     TEXT NOT NULL,
                target_members  INTEGER DEFAULT 0,
                current_members INTEGER DEFAULT 0,
                added_at        TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ── قنوات النقاط ──
        c.execute("""
            CREATE TABLE IF NOT EXISTS points_channels (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id    TEXT UNIQUE NOT NULL,
                channel_name  TEXT NOT NULL,
                channel_url   TEXT NOT NULL,
                points_reward INTEGER DEFAULT 20,
                added_at      TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS user_channel_points (
                user_id    INTEGER NOT NULL,
                channel_id TEXT NOT NULL,
                earned_at  TEXT DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, channel_id)
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS mandatory_joins (
                user_id    INTEGER NOT NULL,
                channel_id TEXT NOT NULL,
                joined_at  TEXT DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, channel_id)
            )
        """)

        # ── الأقسام (Apps) ──
        c.execute("""
            CREATE TABLE IF NOT EXISTS apps (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                name       TEXT NOT NULL,
                emoji      TEXT DEFAULT '📱',
                is_active  INTEGER DEFAULT 1,
                sort_order INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ── خدمات الأقسام ──
        c.execute("""
            CREATE TABLE IF NOT EXISTS app_services (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                app_id           INTEGER NOT NULL,
                name             TEXT NOT NULL,
                emoji            TEXT DEFAULT '',
                api_service_id   TEXT NOT NULL,
                site_id          INTEGER DEFAULT NULL,
                points_per_1000  INTEGER NOT NULL DEFAULT 10,
                min_qty          INTEGER NOT NULL DEFAULT 100,
                max_qty          INTEGER NOT NULL DEFAULT 100000,
                rate_per_1000    REAL    DEFAULT 0.5,
                service_type     TEXT    DEFAULT 'عام',
                reaction_emoji   TEXT    DEFAULT '',
                reaction_mode    TEXT    DEFAULT 'fixed',
                reaction_pool    TEXT    DEFAULT '',
                auto_react       INTEGER DEFAULT 0,
                target_chat     TEXT    DEFAULT '',
                telegram_account_id INTEGER DEFAULT NULL,
                public_id        TEXT DEFAULT '',
                is_active        INTEGER DEFAULT 1,
                created_at       TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (app_id) REFERENCES apps(id) ON DELETE CASCADE
            )
        """)

        # ── حسابات Telegram المرتبطة بالمستخدمين ──
        c.execute("""
            CREATE TABLE IF NOT EXISTS telegram_accounts (
                id                INTEGER PRIMARY KEY AUTOINCREMENT,
                bot_user_id       INTEGER NOT NULL,
                phone             TEXT NOT NULL,
                telegram_user_id  INTEGER,
                username          TEXT DEFAULT '',
                first_name        TEXT DEFAULT '',
                session_path      TEXT NOT NULL,
                api_id            INTEGER DEFAULT 0,
                api_hash          TEXT DEFAULT '',
                is_active         INTEGER DEFAULT 1,
                created_at        TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at        TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(bot_user_id, phone)
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS service_telegram_accounts (
                service_id INTEGER NOT NULL,
                telegram_account_id INTEGER NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY(service_id, telegram_account_id)
            )
        """)

        # ── روابط الهدايا ──
        c.execute("""
            CREATE TABLE IF NOT EXISTS gift_links (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                code        TEXT    NOT NULL UNIQUE,
                points      INTEGER NOT NULL DEFAULT 0,
                max_uses    INTEGER DEFAULT -1,
                used_count  INTEGER DEFAULT 0,
                is_active   INTEGER DEFAULT 1,
                note        TEXT    DEFAULT '',
                created_at  TEXT    DEFAULT CURRENT_TIMESTAMP
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS gift_link_claims (
                user_id  INTEGER NOT NULL,
                code     TEXT    NOT NULL,
                claimed_at TEXT DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, code)
            )
        """)

        # ── روابط الدعوة ──
        c.execute("""
            CREATE TABLE IF NOT EXISTS invite_links (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                code          TEXT UNIQUE NOT NULL,
                points_reward INTEGER NOT NULL,
                max_uses      INTEGER DEFAULT 0,
                current_uses  INTEGER DEFAULT 0,
                is_active     INTEGER DEFAULT 1,
                created_at    TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS user_invite_claims (
                user_id     INTEGER NOT NULL,
                invite_code TEXT NOT NULL,
                claimed_at  TEXT DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, invite_code)
            )
        """)

        # ── كوبونات الخصم ──
        c.execute("""
            CREATE TABLE IF NOT EXISTS coupons (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                code        TEXT    NOT NULL UNIQUE,
                discount    INTEGER NOT NULL DEFAULT 10,
                max_uses    INTEGER DEFAULT -1,
                used_count  INTEGER DEFAULT 0,
                is_active   INTEGER DEFAULT 1,
                created_at  TEXT    DEFAULT CURRENT_TIMESTAMP
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS coupon_uses (
                user_id    INTEGER NOT NULL,
                coupon_id  INTEGER NOT NULL,
                used_at    TEXT    DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, coupon_id)
            )
        """)

        # ── طلبات شحن الرصيد ──
        c.execute("""
            CREATE TABLE IF NOT EXISTS recharge_requests (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL,
                amount      REAL    DEFAULT 0,
                points      INTEGER DEFAULT 0,
                method      TEXT    DEFAULT 'vodafone',
                photo_id    TEXT    DEFAULT '',
                status      TEXT    DEFAULT 'pending',
                note        TEXT    DEFAULT '',
                created_at  TEXT    DEFAULT CURRENT_TIMESTAMP
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS store_products (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                name        TEXT NOT NULL,
                description TEXT DEFAULT '',
                emoji       TEXT DEFAULT '🛍️',
                price       INTEGER NOT NULL DEFAULT 0,
                stock       INTEGER DEFAULT -1,
                is_active   INTEGER DEFAULT 1,
                created_at  TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ── طلبات المتجر ──
        c.execute("""
            CREATE TABLE IF NOT EXISTS store_orders (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id          INTEGER NOT NULL,
                product_id       INTEGER NOT NULL,
                product_name     TEXT DEFAULT '',
                points_used      INTEGER DEFAULT 0,
                status           TEXT DEFAULT 'pending_approval',
                pending_approval INTEGER DEFAULT 1,
                notified_done    INTEGER DEFAULT 0,
                created_at       TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ── سجل الإحالات ──
        c.execute("""
            CREATE TABLE IF NOT EXISTS referral_log (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                referrer_id     INTEGER NOT NULL,
                referred_id     INTEGER NOT NULL,
                points_awarded  INTEGER NOT NULL,
                created_at      TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(referrer_id, referred_id)
            )
        """)

        # ── جوائز عجلة الحظ ──
        c.execute("""
            CREATE TABLE IF NOT EXISTS wheel_prizes (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                points     INTEGER NOT NULL,
                weight     REAL    NOT NULL DEFAULT 10,
                emoji      TEXT    DEFAULT '',
                label      TEXT    DEFAULT '',
                is_active  INTEGER DEFAULT 1,
                created_at TEXT    DEFAULT CURRENT_TIMESTAMP
            )
        """)

        n = c.execute("SELECT COUNT(*) FROM wheel_prizes").fetchone()[0]
        if n == 0:
            defaults = [
                (10,  30, '🟤', 'عادي'),
                (25,  20, '⚪', 'جيد'),
                (50,  15, '🟢', 'ممتاز'),
                (100, 10, '🔵', 'رائع'),
                (200,  6, '🟡', 'كبير'),
                (500,  3, '🟠', 'ضخم'),
                (1000, 1, '🔴', 'جائزة كبرى'),
            ]
            for pts, w, em, lbl in defaults:
                c.execute("INSERT INTO wheel_prizes (points,weight,emoji,label) VALUES(?,?,?,?)",
                          (pts, w, em, lbl))

        # ── الخدمات المجانية ──
        c.execute("""
            CREATE TABLE IF NOT EXISTS free_services (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                name           TEXT NOT NULL,
                description    TEXT DEFAULT '',
                api_service_id TEXT DEFAULT '',
                site_id        INTEGER DEFAULT NULL,
                daily_limit    INTEGER DEFAULT 1,
                min_qty        INTEGER DEFAULT 100,
                max_qty        INTEGER DEFAULT 1000,
                is_active      INTEGER DEFAULT 1,
                created_at     TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS user_free_claims (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id      INTEGER NOT NULL,
                service_id   INTEGER NOT NULL,
                claim_date   TEXT NOT NULL,
                quantity     INTEGER DEFAULT 0,
                link         TEXT DEFAULT '',
                api_order_id TEXT DEFAULT '',
                status       TEXT DEFAULT 'pending',
                created_at   TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ── التفاعل التلقائي على القنوات التي يحددها الأدمن ──
        c.execute("""
            CREATE TABLE IF NOT EXISTS reaction_targets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                service_id INTEGER NOT NULL,
                chat TEXT NOT NULL,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(service_id, chat)
            )
        """)

        # ── الأدمنية المتعددة ──
        c.execute("""
            CREATE TABLE IF NOT EXISTS extra_admins (
                tg_id      INTEGER PRIMARY KEY,
                full_name  TEXT DEFAULT '',
                added_at   TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ── قنوات الطلبات ──
        c.execute("""
            CREATE TABLE IF NOT EXISTS order_channels (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id TEXT UNIQUE NOT NULL,
                channel_name TEXT NOT NULL,
                is_active  INTEGER DEFAULT 1,
                added_at   TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ── الإعدادات الافتراضية ──
        defaults = {
            "service_id":             "",
            "service_name":           "تمويل قنوات وجروبات",
            "service_min":            "100",
            "service_max":            "100000",
            "updates_channel":        "",
            "support_username":       "@suppor",
            "bot_active":             "1",
            "rate_per_1000":          "0.5",
            "points_per_1000":        "10",
            "referral_points":        "1000",
            "daily_gift_points":      "5",
            "weekly_gift_points":     "50",
            "welcome_points":         "10",
            "wheel_cooldown_hrs":     "6",
            "free_svc_enabled":          "1",
            "free_services_daily_limit": "3",
            "points_charge_info":        "لشحن النقاط تواصل مع الدعم",
            "charge_vodafone_info":      "فودافون كاش: 0123456789",
            "charge_stars_info":         "نجوم: تواصل مع @support",
            "auto_approve_orders":       "0",
            "terms_text":                "",
            "low_points_alert":          "50",
            "daily_report_enabled":      "1",
            "stars_per_point":           "10",
        }
        for k, v in defaults.items():
            c.execute("INSERT OR IGNORE INTO config(key,value) VALUES(?,?)", (k, v))

        # إزالة أي إعدادات خارجي قديمة من النسخ السابقة.
        try:
            c.execute("DROP TABLE IF EXISTS smm_sites")
        except Exception:
            pass

        conn.commit()
        conn.close()

    # ─── إضافة أعمدة قديمة إن لم تكن موجودة ─────────────────────
    @classmethod
    def _safe_add_col(cls, table, col, typ):
        try:
            conn = cls.get_conn()
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} {typ}")
            conn.commit()
            conn.close()
        except:
            pass

    # ─── أعمدة حسابات Telegram الإضافية للنسخ القديمة ───────────
    @classmethod
    def remove_previous_demo_data(cls):
        demo_app_names = ["🚀 خدمات تيليجرام — رشق وتفاعل"]
        demo_service_names = ["تفاعلات تلجرام ايجابية 👍🥰❤️‍🔥🔥😍"]
        conn = cls.get_conn()
        try:
            for name in demo_service_names:
                for row in conn.execute("SELECT id FROM app_services WHERE name=?", (name,)).fetchall():
                    sid=int(row["id"])
                    conn.execute("DELETE FROM service_telegram_accounts WHERE service_id=?", (sid,))
                    conn.execute("DELETE FROM reaction_targets WHERE service_id=?", (sid,))
                    conn.execute("DELETE FROM app_services WHERE id=?", (sid,))
            for name in demo_app_names:
                for row in conn.execute("SELECT id FROM apps WHERE name=?", (name,)).fetchall():
                    aid=int(row["id"])
                    if not conn.execute("SELECT 1 FROM app_services WHERE app_id=? LIMIT 1", (aid,)).fetchone():
                        conn.execute("DELETE FROM apps WHERE id=?", (aid,))
            conn.commit()
        finally:
            conn.close()

    @classmethod
    def migrate_telegram_accounts(cls):
        cls._safe_add_col("telegram_accounts", "api_id", "INTEGER DEFAULT 0")
        cls._safe_add_col("telegram_accounts", "api_hash", "TEXT DEFAULT ''")
        cls._safe_add_col("app_services", "account_execution_mode", "TEXT DEFAULT 'multi'")
        try:
            conn = cls.get_conn()
            conn.execute("""CREATE TABLE IF NOT EXISTS service_telegram_accounts (
                service_id INTEGER NOT NULL, telegram_account_id INTEGER NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY(service_id, telegram_account_id)
            )""")
            conn.commit(); conn.close()
        except Exception:
            try: conn.close()
            except Exception: pass
        cls._safe_add_col("app_services", "service_type", "TEXT DEFAULT 'عام'")
        cls._safe_add_col("app_services", "reaction_emoji", "TEXT DEFAULT ''")
        cls._safe_add_col("app_services", "reaction_mode", "TEXT DEFAULT 'fixed'")
        cls._safe_add_col("app_services", "reaction_pool", "TEXT DEFAULT ''")
        cls._safe_add_col("app_services", "auto_react", "INTEGER DEFAULT 0")
        cls._safe_add_col("app_services", "target_chat", "TEXT DEFAULT ''")
        cls._safe_add_col("app_services", "telegram_account_id", "INTEGER DEFAULT NULL")
        cls._safe_add_col("app_services", "public_id", "TEXT DEFAULT ''")
        cls._safe_add_col("orders", "public_id", "TEXT DEFAULT ''")
        cls._ensure_service_public_ids()
        cls._ensure_order_public_ids()

    @classmethod
    def _ensure_service_public_ids(cls):
        """تخصيص ID خدمة عام من 6 أرقام، مستقل عن رقم SQLite الداخلي."""
        conn = cls.get_conn()
        try:
            rows = conn.execute("SELECT id, public_id FROM app_services ORDER BY id").fetchall()
            used = {str(r["public_id"]).strip() for r in rows if str(r["public_id"] or "").strip()}
            for row in rows:
                if str(row["public_id"] or "").strip():
                    continue
                while True:
                    code = str(random.randint(100000, 999999))
                    if code not in used:
                        used.add(code)
                        break
                conn.execute("UPDATE app_services SET public_id=? WHERE id=?", (code, int(row["id"])))
            conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_app_services_public_id ON app_services(public_id) WHERE public_id <> ''")
            conn.commit()
        finally:
            conn.close()

    @classmethod
    def _ensure_order_public_ids(cls):
        """تخصيص رقم طلب عام عشوائي من 6 أرقام، مستقل عن SQLite id."""
        conn = cls.get_conn()
        try:
            rows = conn.execute("SELECT id, public_id FROM orders ORDER BY id").fetchall()
            used = {str(r["public_id"]).strip() for r in rows if str(r["public_id"] or "").strip()}
            for row in rows:
                if str(row["public_id"] or "").strip():
                    continue
                while True:
                    code = str(random.randint(100000, 999999))
                    if code not in used:
                        used.add(code)
                        break
                conn.execute("UPDATE orders SET public_id=? WHERE id=?", (code, int(row["id"])))
            conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_orders_public_id ON orders(public_id) WHERE public_id <> ''")
            conn.commit()
        finally:
            conn.close()

    # ─── المستخدمون ──────────────────────────────────────────────
    @classmethod
    def get_user(cls, tg_id):
        conn = cls.get_conn()
        u = conn.execute("SELECT * FROM users WHERE tg_id=?", (tg_id,)).fetchone()
        conn.close()
        return u

    @classmethod
    def get_user_by_username(cls, username):
        conn = cls.get_conn()
        uname = username.lstrip("@").lower()
        u = conn.execute("SELECT * FROM users WHERE LOWER(username)=?", (uname,)).fetchone()
        conn.close()
        return u

    @classmethod
    def create_user(cls, tg_id, username, full_name, ref_code=None):
        my_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        referred_by = None
        if ref_code:
            conn = cls.get_conn()
            r = conn.execute("SELECT tg_id FROM users WHERE referral_code=?", (ref_code,)).fetchone()
            conn.close()
            if r and r["tg_id"] != tg_id:
                referred_by = r["tg_id"]
        conn = cls.get_conn()
        try:
            welcome_pts = int(cls.get_config("welcome_points", "10"))
            conn.execute("""INSERT INTO users(tg_id,username,full_name,referral_code,referred_by,points)
                VALUES(?,?,?,?,?,?)""",
                (tg_id, username or '', full_name or '', my_code, referred_by, welcome_pts))
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            return None
        # النقاط لا تُضاف هنا — تُضاف بعد التحقق من الاشتراك الإجباري عبر complete_referral
        conn.close()
        return referred_by

    @classmethod
    def complete_referral(cls, tg_id):
        """تُستدعى بعد اجتياز الاشتراك الإجباري — تضيف نقاط الإحالة للمُحيل مرة واحدة فقط"""
        conn = cls.get_conn()
        u = conn.execute("SELECT referred_by FROM users WHERE tg_id=?", (tg_id,)).fetchone()
        if not u or not u["referred_by"]:
            conn.close()
            return None
        referred_by = u["referred_by"]
        exists = conn.execute(
            "SELECT 1 FROM referral_log WHERE referrer_id=? AND referred_id=?",
            (referred_by, tg_id)).fetchone()
        if exists:
            conn.close()
            return None
        pts = int(cls.get_config("referral_points", "1000") or 1000)
        try:
            cur = conn.execute(
                "INSERT OR IGNORE INTO referral_log(referrer_id,referred_id,points_awarded) VALUES(?,?,?)",
                (referred_by, tg_id, pts),
            )
            # لا نضيف النقاط إلا إذا تم إنشاء سجل الإحالة فعلاً؛
            # هذا يمنع مضاعفة المكافأة عند الضغط/التنفيذ المتزامن.
            if cur.rowcount == 1:
                conn.execute("UPDATE users SET points=points+? WHERE tg_id=?", (pts, referred_by))
                conn.execute("UPDATE users SET points=points+? WHERE tg_id=?", (pts, tg_id))
                conn.commit()
                conn.close()
                return (referred_by, pts)
            conn.rollback()
        except Exception:
            try:
                conn.rollback()
            except Exception:
                pass
            conn.close()
            return None
        conn.close()
        return None

    @classmethod
    def get_or_create(cls, tg_id, username, full_name, ref_code=None):
        u = cls.get_user(tg_id)
        if not u:
            rb = cls.create_user(tg_id, username, full_name, ref_code)
            return cls.get_user(tg_id), rb, True
        return u, None, False

    @classmethod
    def update_user(cls, tg_id, **kw):
        if not kw:
            return
        fields = ", ".join(f"{k}=?" for k in kw)
        conn = cls.get_conn()
        conn.execute(f"UPDATE users SET {fields} WHERE tg_id=?", list(kw.values()) + [tg_id])
        conn.commit()
        conn.close()

    @classmethod
    def add_points(cls, tg_id, pts):
        conn = cls.get_conn()
        conn.execute("UPDATE users SET points=points+? WHERE tg_id=?", (pts, tg_id))
        conn.commit()
        conn.close()

    @classmethod
    def deduct_points(cls, tg_id, pts):
        with DB_WRITE_LOCK:
            for attempt in range(20):
                conn = cls.get_conn()
                try:
                    u = conn.execute("SELECT points FROM users WHERE tg_id=?", (tg_id,)).fetchone()
                    if not u or u["points"] < pts:
                        conn.close(); return False
                    conn.execute("UPDATE users SET points=points-? WHERE tg_id=?", (pts, tg_id))
                    conn.commit(); new_pts = u["points"] - pts; conn.close(); break
                except sqlite3.OperationalError as e:
                    try: conn.rollback()
                    except Exception: pass
                    try: conn.close()
                    except Exception: pass
                    if "locked" not in str(e).lower() or attempt == 19: raise
                    time.sleep(min(1.0, 0.10 * (attempt + 1)))
        # إشعار انخفاض الرصيد
        try:
            threshold = int(db.get_config("low_points_alert", "50"))
            if threshold > 0 and new_pts <= threshold and u["points"] > threshold:
                threading.Thread(target=_send_low_points_alert,
                                 args=(tg_id, new_pts, threshold), daemon=True).start()
        except:
            pass
        return True

    @classmethod
    def claim_daily(cls, tg_id):
        today = date.today().isoformat()
        conn = cls.get_conn()
        u = conn.execute("SELECT last_daily_gift FROM users WHERE tg_id=?", (tg_id,)).fetchone()
        if not u or u["last_daily_gift"] == today:
            conn.close()
            return False, 0
        pts = int(cls.get_config("daily_gift_points", "5"))
        conn.execute("UPDATE users SET points=points+?,last_daily_gift=? WHERE tg_id=?",
                     (pts, today, tg_id))
        conn.commit()
        conn.close()
        return True, pts

    @classmethod
    def claim_weekly(cls, tg_id):
        today = date.today()
        conn = cls.get_conn()
        u = conn.execute("SELECT last_weekly_gift FROM users WHERE tg_id=?", (tg_id,)).fetchone()
        if not u:
            conn.close()
            return False, 0, 0
        last = u["last_weekly_gift"] or ""
        if last:
            try:
                d = date.fromisoformat(last)
                left = 7 - (today - d).days
                if left > 0:
                    conn.close()
                    return False, 0, left
            except:
                pass
        pts = int(cls.get_config("weekly_gift_points", "50"))
        conn.execute("UPDATE users SET points=points+?,last_weekly_gift=? WHERE tg_id=?",
                     (pts, today.isoformat(), tg_id))
        conn.commit()
        conn.close()
        return True, pts, 0

    @classmethod
    def can_spin(cls, tg_id):
        hrs = float(cls.get_config("wheel_cooldown_hrs", "6"))
        conn = cls.get_conn()
        u = conn.execute("SELECT last_wheel_spin FROM users WHERE tg_id=?", (tg_id,)).fetchone()
        conn.close()
        if not u or not u["last_wheel_spin"]:
            return True, 0
        try:
            last = datetime.fromisoformat(u["last_wheel_spin"])
            diff = (datetime.now() - last).total_seconds() / 3600
            left = hrs - diff
            if left > 0:
                return False, round(left, 1)
        except:
            pass
        return True, 0

    @classmethod
    def mark_spin(cls, tg_id):
        conn = cls.get_conn()
        conn.execute("UPDATE users SET last_wheel_spin=? WHERE tg_id=?",
                     (datetime.now().isoformat(), tg_id))
        conn.commit()
        conn.close()

    @classmethod
    def get_all_users(cls):
        conn = cls.get_conn()
        u = conn.execute("SELECT * FROM users WHERE is_banned=0").fetchall()
        conn.close()
        return u

    @classmethod
    def get_users_count(cls):
        conn = cls.get_conn()
        n = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        conn.close()
        return n

    @classmethod
    def get_total_completed_orders(cls):
        """إجمالي الطلبات التي وصلت لحالة completed."""
        conn = cls.get_conn()
        try:
            row = conn.execute("SELECT COUNT(*) FROM orders WHERE status=?", ("completed",)).fetchone()
            return int(row[0] or 0)
        finally:
            conn.close()

    @classmethod
    def get_top_referrers(cls, limit=5):
        conn = cls.get_conn()
        rows = conn.execute("""
            SELECT u.tg_id, u.full_name, u.username,
                   COUNT(r.referred_id) as ref_count,
                   COALESCE(SUM(r.points_awarded),0) as total_pts
            FROM users u
            LEFT JOIN referral_log r ON r.referrer_id = u.tg_id
            GROUP BY u.tg_id
            HAVING ref_count > 0
            ORDER BY ref_count DESC
            LIMIT ?
        """, (limit,)).fetchall()
        conn.close()
        return rows

    @classmethod
    def get_referral_count(cls, tg_id):
        # الإحالات المعروضة هي الإحالات المكتملة التي تم صرف مكافأتها فعلياً.
        conn = cls.get_conn()
        n = conn.execute("SELECT COUNT(*) FROM referral_log WHERE referrer_id=?", (tg_id,)).fetchone()[0]
        conn.close()
        return n

    @classmethod
    def get_referral_log_count(cls):
        conn = cls.get_conn()
        n = conn.execute("SELECT COUNT(*) FROM referral_log").fetchone()[0]
        conn.close()
        return n

    # ─── الطلبات ──────────────────────────────────────────────────
    @classmethod
    def create_order(cls, user_id, svc_id, svc_name, link, qty, charge, pts=0, api_id=None, app_name="", site_id=None, pending_approval=1):
        with DB_WRITE_LOCK:
            for attempt in range(20):
                conn = cls.get_conn()
                try:
                    cur = conn.cursor()
                    # رقم طلب عام من 6 أرقام للمستخدم، مع بقاء id الداخلي كما هو للمعالجة.
                    while True:
                        public_id = str(random.randint(100000, 999999))
                        if not conn.execute("SELECT 1 FROM orders WHERE public_id=? LIMIT 1", (public_id,)).fetchone():
                            break
                    cur.execute("""INSERT INTO orders(
                        user_id,service_id,service_name,app_name,link,quantity,charge,points_used,api_order_id,status,site_id,pending_approval,public_id) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                        (user_id, svc_id, svc_name, app_name, link, qty, charge, pts, api_id, "pending", site_id, int(pending_approval), public_id))
                    oid = cur.lastrowid
                    conn.commit(); conn.close(); return oid
                except sqlite3.OperationalError as e:
                    try: conn.rollback()
                    except Exception: pass
                    try: conn.close()
                    except Exception: pass
                    if "locked" not in str(e).lower() or attempt == 19: raise
                    time.sleep(min(1.0, 0.10 * (attempt + 1)))

    @classmethod
    def get_order(cls, oid):
        conn = cls.get_conn()
        o = conn.execute("SELECT * FROM orders WHERE id=? OR public_id=?", (oid, str(oid))).fetchone()
        conn.close()
        return o

    @classmethod
    def get_duplicate_order(cls, user_id, service_id, link):
        """منع تكرار نفس الخدمة على نفس منشور المستخدم بعد طلب ناجح أو أثناء التنفيذ."""
        raw = str(link or "").strip()
        normalized = raw.rstrip("/").lower()
        conn = cls.get_conn()
        try:
            rows = conn.execute(
                """SELECT * FROM orders
                   WHERE user_id=? AND service_id=?
                     AND status IN ('pending','processing','completed','partial')
                   ORDER BY id DESC LIMIT 50""",
                (int(user_id), str(service_id)),
            ).fetchall()
            for row in rows:
                if str(row["link"] or "").strip().rstrip("/").lower() == normalized:
                    return row
            return None
        finally:
            conn.close()

    @classmethod
    def claim_order_for_execution(cls, oid):
        """يحجز الطلب للتنفيذ مرة واحدة فقط: pending -> processing."""
        with DB_WRITE_LOCK:
            conn = cls.get_conn()
            try:
                cur = conn.execute(
                    "UPDATE orders SET status='processing', updated_at=CURRENT_TIMESTAMP "
                    "WHERE id=? AND status='pending'",
                    (int(oid),),
                )
                conn.commit()
                return cur.rowcount == 1
            finally:
                conn.close()

    @classmethod
    def fail_order_and_refund(cls, oid):
        """يفشل الطلب ويعيد النقاط مرة واحدة، ولا يلمس الطلب المكتمل."""
        with DB_WRITE_LOCK:
            conn = cls.get_conn()
            try:
                row = conn.execute("SELECT * FROM orders WHERE id=?", (int(oid),)).fetchone()
                if not row:
                    return False
                status = str(row["status"] or "").lower()
                if status in ("completed", "canceled", "partial"):
                    return False
                conn.execute(
                    "UPDATE users SET points=points+? WHERE tg_id=?",
                    (int(row["points_used"] or 0), int(row["user_id"])),
                )
                conn.execute(
                    "UPDATE orders SET status='canceled', updated_at=CURRENT_TIMESTAMP WHERE id=? AND status<> 'completed'",
                    (int(oid),),
                )
                conn.commit()
                return True
            finally:
                conn.close()

    @classmethod
    def get_pending_execution_orders(cls, limit=100):
        """طلبات تم تأكيدها وخصم نقاطها ولم تدخل التنفيذ قبل Restart."""
        conn = cls.get_conn()
        try:
            return conn.execute(
                """SELECT id FROM orders
                   WHERE status='pending' AND COALESCE(pending_approval,0)=0
                   ORDER BY id ASC LIMIT ?""",
                (int(limit),),
            ).fetchall()
        finally:
            conn.close()

    @classmethod
    def get_due_completion_notices(cls, limit=50):
        """طلبات مكتملة مر عليها 60 ثانية ولم تُرسل رسالة إكمال لها."""
        conn = cls.get_conn()
        try:
            return conn.execute(
                """SELECT * FROM orders
                   WHERE status='completed' AND COALESCE(notified_done,0)=0
                     AND updated_at <= datetime('now','-60 seconds')
                   ORDER BY id ASC LIMIT ?""",
                (int(limit),),
            ).fetchall()
        finally:
            conn.close()

    @classmethod
    def mark_notified(cls, oid):
        with DB_WRITE_LOCK:
            conn = cls.get_conn()
            try:
                cur = conn.execute(
                    "UPDATE orders SET notified_done=1 WHERE id=? AND status='completed' AND COALESCE(notified_done,0)=0",
                    (int(oid),),
                )
                conn.commit()
                return cur.rowcount == 1
            finally:
                conn.close()

    @classmethod
    def update_order(cls, oid, status, api_id=None):
        # إعادة المحاولة مهمة خصوصاً بعد تنفيذ Telegram بنجاح؛
        # لا نريد اعتبار الطلب فاشلاً فقط لأن SQLite كانت مقفولة لحظياً.
        last_error = None
        for attempt in range(20):
            conn = cls.get_conn()
            try:
                # completed حالة نهائية: لا يمكن لمسار فشل/إلغاء لاحق أن يعيدها للخلف.
                if api_id:
                    conn.execute(
                        "UPDATE orders SET status=?,api_order_id=?,updated_at=CURRENT_TIMESTAMP WHERE id=? AND (status <> 'completed' OR ?='completed')",
                        (status, api_id, oid, status),
                    )
                else:
                    conn.execute(
                        "UPDATE orders SET status=?,updated_at=CURRENT_TIMESTAMP WHERE id=? AND (status <> 'completed' OR ?='completed')",
                        (status, oid, status),
                    )
                conn.commit()
                conn.close()
                return True
            except sqlite3.OperationalError as e:
                last_error = e
                try:
                    conn.rollback()
                except Exception:
                    pass
                try:
                    conn.close()
                except Exception:
                    pass
                if "locked" not in str(e).lower() and "busy" not in str(e).lower():
                    raise
                if attempt >= 19:
                    raise
                time.sleep(min(1.0, 0.10 * (attempt + 1)))
            except Exception:
                try:
                    conn.rollback()
                except Exception:
                    pass
                try:
                    conn.close()
                except Exception:
                    pass
                raise
        raise sqlite3.OperationalError(
            f"SQLite remained locked after retries: {last_error}"
        )

    @classmethod
    def approve_order(cls, oid):
        with DB_WRITE_LOCK:
            for attempt in range(20):
                conn = cls.get_conn()
                try:
                    conn.execute("UPDATE orders SET pending_approval=0 WHERE id=?", (oid,))
                    conn.commit(); conn.close(); return True
                except sqlite3.OperationalError as e:
                    try: conn.rollback()
                    except Exception: pass
                    try: conn.close()
                    except Exception: pass
                    if "locked" not in str(e).lower() or attempt == 19: raise
                    time.sleep(min(1.0, 0.10 * (attempt + 1)))

    @classmethod
    def reject_order(cls, oid):
        """رفض الطلب واسترداد النقاط"""
        conn = cls.get_conn()
        o = conn.execute("SELECT * FROM orders WHERE id=?", (oid,)).fetchone()
        if o and o["pending_approval"] == 1:
            conn.execute("UPDATE users SET points=points+? WHERE tg_id=?",
                         (o["points_used"], o["user_id"]))
            conn.execute("UPDATE orders SET status='canceled', pending_approval=0 WHERE id=?", (oid,))
            conn.commit()
        conn.close()
        return o

    @classmethod
    def cancel_unconfirmed_order(cls, oid, user_id):
        """إلغاء طلب لم يتم تأكيده بعد، بدون استرداد لأن الخصم لم يتم."""
        conn = cls.get_conn()
        try:
            cur = conn.execute(
                "UPDATE orders SET status='canceled', pending_approval=0, updated_at=CURRENT_TIMESTAMP WHERE id=? AND user_id=? AND status='pending'",
                (int(oid), int(user_id)),
            )
            conn.commit()
            return cur.rowcount > 0
        finally:
            conn.close()

    @classmethod
    def get_pending_orders(cls):
        """طلبات تنتظر الموافقة"""
        conn = cls.get_conn()
        rows = conn.execute(
            "SELECT * FROM orders WHERE pending_approval=1 ORDER BY created_at DESC"
        ).fetchall()
        conn.close()
        return rows

    # ─── المتجر ───────────────────────────────────────────────────
    @classmethod
    def get_store_products(cls, only_active=True):
        conn = cls.get_conn()
        q = "SELECT * FROM store_products"
        if only_active:
            q += " WHERE is_active=1"
        q += " ORDER BY id"
        r = conn.execute(q).fetchall()
        conn.close()
        return r

    @classmethod
    def get_store_product(cls, pid):
        conn = cls.get_conn()
        r = conn.execute("SELECT * FROM store_products WHERE id=?", (pid,)).fetchone()
        conn.close()
        return r

    @classmethod
    def add_store_product(cls, name, desc, emoji, price, stock=-1):
        conn = cls.get_conn()
        cur = conn.cursor()
        cur.execute("INSERT INTO store_products(name,description,emoji,price,stock) VALUES(?,?,?,?,?)",
                    (name, desc, emoji, price, stock))
        pid = cur.lastrowid
        conn.commit()
        conn.close()
        return pid

    @classmethod
    def delete_store_product(cls, pid):
        conn = cls.get_conn()
        conn.execute("DELETE FROM store_products WHERE id=?", (pid,))
        conn.commit()
        conn.close()

    @classmethod
    def toggle_store_product(cls, pid):
        conn = cls.get_conn()
        conn.execute("UPDATE store_products SET is_active=1-is_active WHERE id=?", (pid,))
        conn.commit()
        conn.close()

    @classmethod
    def create_store_order(cls, user_id, product_id, product_name, points):
        conn = cls.get_conn()
        cur = conn.cursor()
        cur.execute("""INSERT INTO store_orders(user_id,product_id,product_name,points_used)
                       VALUES(?,?,?,?)""", (user_id, product_id, product_name, points))
        oid = cur.lastrowid
        conn.commit()
        conn.close()
        return oid

    @classmethod
    def get_store_order(cls, oid):
        conn = cls.get_conn()
        r = conn.execute("SELECT * FROM store_orders WHERE id=?", (oid,)).fetchone()
        conn.close()
        return r

    @classmethod
    def approve_store_order(cls, oid):
        conn = cls.get_conn()
        conn.execute("UPDATE store_orders SET pending_approval=0, status='approved' WHERE id=?", (oid,))
        conn.commit()
        conn.close()

    @classmethod
    def reject_store_order(cls, oid):
        conn = cls.get_conn()
        o = conn.execute("SELECT * FROM store_orders WHERE id=?", (oid,)).fetchone()
        if o and o["pending_approval"] == 1:
            conn.execute("UPDATE users SET points=points+? WHERE tg_id=?",
                         (o["points_used"], o["user_id"]))
            conn.execute("UPDATE store_orders SET status='rejected', pending_approval=0 WHERE id=?", (oid,))
            conn.commit()
        conn.close()
        return o

    @classmethod
    def get_pending_store_orders(cls):
        conn = cls.get_conn()
        rows = conn.execute(
            "SELECT * FROM store_orders WHERE pending_approval=1 ORDER BY created_at DESC"
        ).fetchall()
        conn.close()
        return rows

    @classmethod
    def get_user_store_orders(cls, tg_id, limit=10):
        conn = cls.get_conn()
        rows = conn.execute("SELECT * FROM store_orders WHERE user_id=? ORDER BY created_at DESC LIMIT ?",
                            (tg_id, limit)).fetchall()
        conn.close()
        return rows

    # ─── طلبات الشحن ──────────────────────────────────────────
    @classmethod
    def create_recharge_request(cls, user_id, method, photo_id="", amount=0):
        conn = cls.get_conn()
        cur = conn.cursor()
        cur.execute("INSERT INTO recharge_requests(user_id,method,photo_id,amount) VALUES(?,?,?,?)",
                    (user_id, method, photo_id, amount))
        rid = cur.lastrowid
        conn.commit()
        conn.close()
        return rid

    @classmethod
    def get_recharge_request(cls, rid):
        conn = cls.get_conn()
        r = conn.execute("SELECT * FROM recharge_requests WHERE id=?", (rid,)).fetchone()
        conn.close()
        return r

    @classmethod
    def approve_recharge(cls, rid, points):
        conn = cls.get_conn()
        r = conn.execute("SELECT * FROM recharge_requests WHERE id=?", (rid,)).fetchone()
        if r and r["status"] == "pending":
            conn.execute("UPDATE users SET points=points+? WHERE tg_id=?", (points, r["user_id"]))
            conn.execute("UPDATE recharge_requests SET status='approved', points=? WHERE id=?", (points, rid))
            conn.commit()
        conn.close()
        return r

    @classmethod
    def reject_recharge(cls, rid, note=""):
        conn = cls.get_conn()
        r = conn.execute("SELECT * FROM recharge_requests WHERE id=?", (rid,)).fetchone()
        if r and r["status"] == "pending":
            conn.execute("UPDATE recharge_requests SET status='rejected', note=? WHERE id=?", (note, rid))
            conn.commit()
        conn.close()
        return r

    @classmethod
    def get_pending_recharges(cls):
        conn = cls.get_conn()
        rows = conn.execute(
            "SELECT * FROM recharge_requests WHERE status='pending' ORDER BY created_at DESC"
        ).fetchall()
        conn.close()
        return rows

    # ─── كوبونات ──────────────────────────────────────────────
    @classmethod
    def get_coupon(cls, code):
        conn = cls.get_conn()
        r = conn.execute("SELECT * FROM coupons WHERE code=? AND is_active=1", (code.upper(),)).fetchone()
        conn.close()
        return r

    @classmethod
    def get_coupon_by_id(cls, cid):
        conn = cls.get_conn()
        r = conn.execute("SELECT * FROM coupons WHERE id=?", (cid,)).fetchone()
        conn.close()
        return r

    @classmethod
    def get_all_coupons(cls):
        conn = cls.get_conn()
        r = conn.execute("SELECT * FROM coupons ORDER BY created_at DESC").fetchall()
        conn.close()
        return r

    @classmethod
    def add_coupon(cls, code, discount, max_uses=-1):
        conn = cls.get_conn()
        try:
            conn.execute("INSERT INTO coupons(code,discount,max_uses) VALUES(?,?,?)",
                         (code.upper(), discount, max_uses))
            conn.commit()
            result = True
        except:
            result = False
        conn.close()
        return result

    @classmethod
    def delete_coupon(cls, cid):
        conn = cls.get_conn()
        conn.execute("DELETE FROM coupons WHERE id=?", (cid,))
        conn.commit()
        conn.close()

    @classmethod
    def toggle_coupon(cls, cid):
        conn = cls.get_conn()
        conn.execute("UPDATE coupons SET is_active=1-is_active WHERE id=?", (cid,))
        conn.commit()
        conn.close()

    @classmethod
    def user_used_coupon(cls, user_id, coupon_id):
        conn = cls.get_conn()
        r = conn.execute("SELECT 1 FROM coupon_uses WHERE user_id=? AND coupon_id=?",
                         (user_id, coupon_id)).fetchone()
        conn.close()
        return r is not None

    @classmethod
    def mark_coupon_used(cls, user_id, coupon_id):
        conn = cls.get_conn()
        conn.execute("INSERT OR IGNORE INTO coupon_uses(user_id,coupon_id) VALUES(?,?)",
                     (user_id, coupon_id))
        conn.execute("UPDATE coupons SET used_count=used_count+1 WHERE id=?", (coupon_id,))
        conn.commit()
        conn.close()

    # ─── روابط الهدايا ────────────────────────────────────────
    @classmethod
    def create_gift_link(cls, points, max_uses=-1, note=""):
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        conn = cls.get_conn()
        try:
            conn.execute(
                "INSERT INTO gift_links(code,points,max_uses,note) VALUES(?,?,?,?)",
                (code, points, max_uses, note))
            conn.commit()
        except:
            code = None
        conn.close()
        return code

    @classmethod
    def get_gift_link(cls, code):
        conn = cls.get_conn()
        r = conn.execute("SELECT * FROM gift_links WHERE code=?", (code,)).fetchone()
        conn.close()
        return r

    @classmethod
    def get_all_gift_links(cls):
        conn = cls.get_conn()
        r = conn.execute("SELECT * FROM gift_links ORDER BY created_at DESC").fetchall()
        conn.close()
        return r

    @classmethod
    def claim_gift_link(cls, user_id, code):
        """يحاول المستخدم يستلم الهدية — يرجع (ok, points, error_msg)"""
        conn = cls.get_conn()
        gl = conn.execute("SELECT * FROM gift_links WHERE code=?", (code,)).fetchone()
        if not gl:
            conn.close()
            return False, 0, "الرابط غير موجود"
        if not gl["is_active"]:
            conn.close()
            return False, 0, "هذا الرابط غير نشط"
        if gl["max_uses"] != -1 and gl["used_count"] >= gl["max_uses"]:
            conn.close()
            return False, 0, "انتهت استخدامات هذا الرابط"
        already = conn.execute(
            "SELECT 1 FROM gift_link_claims WHERE user_id=? AND code=?",
            (user_id, code)).fetchone()
        if already:
            conn.close()
            return False, 0, "استلمت هذه الهدية من قبل"
        pts = gl["points"]
        try:
            conn.execute("INSERT INTO gift_link_claims(user_id,code) VALUES(?,?)", (user_id, code))
            conn.execute("UPDATE gift_links SET used_count=used_count+1 WHERE code=?", (code,))
            conn.execute("UPDATE users SET points=points+? WHERE tg_id=?", (pts, user_id))
            conn.commit()
        except Exception as e:
            conn.close()
            return False, 0, "خطأ في قاعدة البيانات"
        conn.close()
        return True, pts, ""

    @classmethod
    def delete_gift_link(cls, gid):
        conn = cls.get_conn()
        conn.execute("DELETE FROM gift_links WHERE id=?", (gid,))
        conn.commit()
        conn.close()

    @classmethod
    def toggle_gift_link(cls, gid):
        conn = cls.get_conn()
        conn.execute("UPDATE gift_links SET is_active=1-is_active WHERE id=?", (gid,))
        conn.commit()
        conn.close()

    # ─── ليدربورد ─────────────────────────────────────────────
    @classmethod
    def get_leaderboard_points(cls, limit=10):
        conn = cls.get_conn()
        r = conn.execute(
            "SELECT tg_id, full_name, username, points FROM users ORDER BY points DESC LIMIT ?",
            (limit,)).fetchall()
        conn.close()
        return r

    @classmethod
    def get_leaderboard_orders(cls, limit=10):
        conn = cls.get_conn()
        r = conn.execute(
            "SELECT user_id, COUNT(*) as cnt, SUM(points_used) as total_pts FROM orders "
            "GROUP BY user_id ORDER BY cnt DESC LIMIT ?", (limit,)).fetchall()
        conn.close()
        return r

    # ─── إحصائيات التقرير ─────────────────────────────────────
    @classmethod
    def get_daily_stats(cls):
        conn = cls.get_conn()
        today = datetime.now().strftime("%Y-%m-%d")
        stats = {}
        stats["new_users"]    = conn.execute(
            "SELECT COUNT(*) FROM users WHERE created_at LIKE ?", (today+"%",)).fetchone()[0]
        stats["total_users"]  = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        stats["new_orders"]   = conn.execute(
            "SELECT COUNT(*) FROM orders WHERE created_at LIKE ?", (today+"%",)).fetchone()[0]
        stats["total_orders"] = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
        stats["points_spent"] = conn.execute(
            "SELECT COALESCE(SUM(points_used),0) FROM orders WHERE created_at LIKE ?",
            (today+"%",)).fetchone()[0]
        stats["store_orders"] = conn.execute(
            "SELECT COUNT(*) FROM store_orders WHERE created_at LIKE ?", (today+"%",)).fetchone()[0]
        stats["recharges"]    = conn.execute(
            "SELECT COUNT(*) FROM recharge_requests WHERE status='approved' AND created_at LIKE ?",
            (today+"%",)).fetchone()[0]
        conn.close()
        return stats

    @classmethod
    def get_orders_stats(cls):
        conn = cls.get_conn()
        total   = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
        today   = conn.execute("SELECT COUNT(*) FROM orders WHERE DATE(created_at)=DATE('now')").fetchone()[0]
        revenue = conn.execute("SELECT COALESCE(SUM(charge),0) FROM orders").fetchone()[0]
        trev    = conn.execute("SELECT COALESCE(SUM(charge),0) FROM orders WHERE DATE(created_at)=DATE('now')").fetchone()[0]
        tpts    = conn.execute("SELECT COALESCE(SUM(points_used),0) FROM orders").fetchone()[0]
        conn.close()
        return total, today, revenue, trev, tpts

    # ─── الإعدادات ────────────────────────────────────────────────
    @classmethod
    def get_config(cls, key, default=""):
        conn = cls.get_conn()
        r = conn.execute("SELECT value FROM config WHERE key=?", (key,)).fetchone()
        conn.close()
        return r["value"] if r else default

    @classmethod
    def set_config(cls, key, value):
        conn = cls.get_conn()
        conn.execute("INSERT OR REPLACE INTO config(key,value) VALUES(?,?)", (key, value))
        conn.commit()
        conn.close()

    @classmethod
    def get_all_config(cls):
        conn = cls.get_conn()
        rows = conn.execute("SELECT key, value FROM config ORDER BY key").fetchall()
        conn.close()
        return rows

    # ─── القنوات الإجبارية ────────────────────────────────────────
    @classmethod
    def get_mandatory_channels(cls):
        conn = cls.get_conn()
        r = conn.execute("SELECT * FROM mandatory_channels").fetchall()
        conn.close()
        return r

    @classmethod
    def add_mandatory_channel(cls, ch_id, name, url, target=0):
        conn = cls.get_conn()
        try:
            conn.execute("""INSERT INTO mandatory_channels(channel_id,channel_name,channel_url,target_members,current_members)
                VALUES(?,?,?,?,0)""", (ch_id, name, url, target))
            conn.commit()
            conn.close()
            return True
        except:
            conn.close()
            return False

    @classmethod
    def remove_mandatory_channel(cls, ch_id):
        conn = cls.get_conn()
        conn.execute("DELETE FROM mandatory_channels WHERE channel_id=?", (ch_id,))
        conn.commit()
        conn.close()

    @classmethod
    def record_join(cls, user_id, ch_id):
        conn = cls.get_conn()
        try:
            cur = conn.execute("INSERT OR IGNORE INTO mandatory_joins(user_id,channel_id) VALUES(?,?)",
                               (user_id, ch_id))
            if cur.rowcount > 0:
                conn.execute("UPDATE mandatory_channels SET current_members=current_members+1 WHERE channel_id=?", (ch_id,))
                conn.commit()
                r = conn.execute("SELECT target_members,current_members FROM mandatory_channels WHERE channel_id=?",
                                 (ch_id,)).fetchone()
                if r and r["target_members"] > 0 and r["current_members"] >= r["target_members"]:
                    conn.execute("DELETE FROM mandatory_channels WHERE channel_id=?", (ch_id,))
                    conn.commit()
        except:
            pass
        conn.close()

    # ─── قنوات النقاط ─────────────────────────────────────────────
    @classmethod
    def get_points_channels(cls):
        conn = cls.get_conn()
        r = conn.execute("SELECT * FROM points_channels").fetchall()
        conn.close()
        return r

    @classmethod
    def add_points_channel(cls, ch_id, name, url, pts):
        conn = cls.get_conn()
        try:
            conn.execute("INSERT INTO points_channels(channel_id,channel_name,channel_url,points_reward) VALUES(?,?,?,?)",
                         (ch_id, name, url, pts))
            conn.commit()
            conn.close()
            return True
        except:
            conn.close()
            return False

    @classmethod
    def remove_points_channel(cls, ch_id):
        conn = cls.get_conn()
        conn.execute("DELETE FROM points_channels WHERE channel_id=?", (ch_id,))
        conn.commit()
        conn.close()

    @classmethod
    def has_channel_pts(cls, uid, ch_id):
        conn = cls.get_conn()
        r = conn.execute("SELECT 1 FROM user_channel_points WHERE user_id=? AND channel_id=?",
                         (uid, ch_id)).fetchone()
        conn.close()
        return r is not None

    @classmethod
    def mark_channel_pts(cls, uid, ch_id):
        conn = cls.get_conn()
        conn.execute("INSERT OR IGNORE INTO user_channel_points(user_id,channel_id) VALUES(?,?)", (uid, ch_id))
        conn.commit()
        conn.close()

# ─── قنوات الطلبات ────────────────────────────────────────────
    @classmethod
    def get_order_channels(cls):
        conn = cls.get_conn()
        r = conn.execute("SELECT * FROM order_channels WHERE is_active=1").fetchall()
        conn.close()
        return r

    @classmethod
    def add_order_channel(cls, ch_id, name):
        conn = cls.get_conn()
        try:
            conn.execute("INSERT INTO order_channels(channel_id,channel_name) VALUES(?,?)", (ch_id, name))
            conn.commit()
            conn.close()
            return True
        except:
            conn.close()
            return False

    @classmethod
    def remove_order_channel(cls, ch_id):
        conn = cls.get_conn()
        conn.execute("DELETE FROM order_channels WHERE channel_id=?", (ch_id,))
        conn.commit()
        conn.close()

    # ─── أكواد الدعوة ─────────────────────────────────────────────
    @classmethod
    def create_invite(cls, code, pts, max_uses=0):
        conn = cls.get_conn()
        try:
            conn.execute("INSERT INTO invite_links(code,points_reward,max_uses) VALUES(?,?,?)",
                         (code, pts, max_uses))
            conn.commit()
            conn.close()
            return True
        except:
            conn.close()
            return False

    @classmethod
    def get_invites(cls):
        conn = cls.get_conn()
        r = conn.execute("SELECT * FROM invite_links ORDER BY created_at DESC").fetchall()
        conn.close()
        return r

    @classmethod
    def delete_invite(cls, code):
        conn = cls.get_conn()
        conn.execute("DELETE FROM invite_links WHERE code=?", (code,))
        conn.commit()
        conn.close()

    @classmethod
    def claim_invite(cls, uid, code):
        conn = cls.get_conn()
        lnk = conn.execute("SELECT * FROM invite_links WHERE code=?", (code,)).fetchone()
        if not lnk:
            conn.close()
            return False, 0, "الكود غير موجود"
        if not lnk["is_active"]:
            conn.close()
            return False, 0, "الكود غير نشط"
        if lnk["max_uses"] > 0 and lnk["current_uses"] >= lnk["max_uses"]:
            conn.close()
            return False, 0, "الكود وصل للحد الأقصى"
        claimed = conn.execute("SELECT 1 FROM user_invite_claims WHERE user_id=? AND invite_code=?",
                               (uid, code)).fetchone()
        if claimed:
            conn.close()
            return False, 0, "استخدمت هذا الكود من قبل"
        pts = lnk["points_reward"]
        try:
            conn.execute("INSERT INTO user_invite_claims(user_id,invite_code) VALUES(?,?)", (uid, code))
            conn.execute("UPDATE invite_links SET current_uses=current_uses+1 WHERE code=?", (code,))
            conn.execute("UPDATE users SET points=points+? WHERE tg_id=?", (pts, uid))
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            return False, 0, "استخدمت هذا الكود من قبل"
        conn.close()
        return True, pts, ""

    # ─── الأقسام ──────────────────────────────────────────────────
    @classmethod
    def get_apps(cls, only_active=True):
        conn = cls.get_conn()
        q = "SELECT * FROM apps" + (" WHERE is_active=1" if only_active else "") + " ORDER BY sort_order,id"
        r = conn.execute(q).fetchall()
        conn.close()
        return r

    @classmethod
    def get_app(cls, app_id):
        conn = cls.get_conn()
        r = conn.execute("SELECT * FROM apps WHERE id=?", (app_id,)).fetchone()
        conn.close()
        return r

    @classmethod
    def add_app(cls, name, emoji=""):
        conn = cls.get_conn()
        cur = conn.cursor()
        cur.execute("INSERT INTO apps(name,emoji) VALUES(?,?)", (name, emoji))
        aid = cur.lastrowid
        conn.commit()
        conn.close()
        return aid

    @classmethod
    def update_app(cls, app_id, name=None, emoji=None):
        fields = []
        params = []
        if name is not None:
            fields.append("name=?")
            params.append(name)
        if emoji is not None:
            fields.append("emoji=?")
            params.append(emoji)
        if not fields:
            return
        params.append(app_id)
        conn = cls.get_conn()
        conn.execute(f"UPDATE apps SET {', '.join(fields)} WHERE id=?", params)
        conn.commit()
        conn.close()

    @classmethod
    def delete_app(cls, app_id):
        conn = cls.get_conn()
        conn.execute("DELETE FROM app_services WHERE app_id=?", (app_id,))
        conn.execute("DELETE FROM apps WHERE id=?", (app_id,))
        conn.commit()
        conn.close()

    # ─── خدمات الأقسام ────────────────────────────────────────────
    @classmethod
    def get_app_services(cls, app_id, only_active=True):
        conn = cls.get_conn()
        q = "SELECT * FROM app_services WHERE app_id=?" + (" AND is_active=1" if only_active else "") + " ORDER BY id"
        r = conn.execute(q, (app_id,)).fetchall()
        conn.close()
        return r

    @classmethod
    def get_all_services(cls, only_active=True):
        """إرجاع كل خدمات الرشق المضافة من لوحة المطور، بدون الحاجة لقسم جديد."""
        conn = cls.get_conn()
        q = "SELECT * FROM app_services" + (" WHERE is_active=1" if only_active else "") + " ORDER BY id"
        r = conn.execute(q).fetchall()
        conn.close()
        return r

    @classmethod
    def get_service(cls, sid):
        conn = cls.get_conn()
        r = conn.execute("SELECT * FROM app_services WHERE id=?", (sid,)).fetchone()
        conn.close()
        return r

    @classmethod
    def add_service(cls, app_id, name, emoji, pts_per_1000, mn, mx, service_type="عام", reaction_emoji="", reaction_mode="fixed", reaction_pool="", auto_react=0, target_chat="", telegram_account_id=None):
        conn = cls.get_conn()
        try:
            # ID عام من 6 أرقام مثل 359862، ويظل ثابتاً حتى لو تغيّر id الداخلي.
            while True:
                public_id = str(random.randint(100000, 999999))
                exists = conn.execute("SELECT 1 FROM app_services WHERE public_id=? LIMIT 1", (public_id,)).fetchone()
                if not exists:
                    break
            conn.execute("""INSERT INTO app_services(
                app_id,name,emoji,api_service_id,points_per_1000,min_qty,max_qty,rate_per_1000,
                site_id,service_type,reaction_emoji,reaction_mode,reaction_pool,auto_react,target_chat,telegram_account_id,public_id
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (app_id,name,emoji,"",pts_per_1000,mn,mx,0,None,service_type,reaction_emoji,reaction_mode,(reaction_pool or (MIRX_DEFAULT_REACTION_POOL if service_type == "تفاعل" else "")),int(auto_react),target_chat,telegram_account_id,public_id))
            conn.commit()
            return public_id
        finally:
            conn.close()

    @classmethod
    def update_service(cls, sid, name=None, emoji=None, service_type=None, reaction_emoji=None, reaction_mode=None, reaction_pool=None, auto_react=None, target_chat=None, telegram_account_id=None):
        fields=[]; params=[]
        for col,val in (("name",name),("emoji",emoji),("service_type",service_type),("reaction_emoji",reaction_emoji),("reaction_mode",reaction_mode),("reaction_pool",reaction_pool),("auto_react",auto_react),("target_chat",target_chat),("telegram_account_id",telegram_account_id)):
            if val is not None:
                fields.append(f"{col}=?"); params.append(val)
        if not fields: return
        params.append(sid)
        conn=cls.get_conn(); conn.execute(f"UPDATE app_services SET {', '.join(fields)} WHERE id=?", params); conn.commit(); conn.close()

    @classmethod
    def add_reaction_target(cls, service_id, chat):
        conn=cls.get_conn(); conn.execute("INSERT OR REPLACE INTO reaction_targets(service_id,chat,is_active) VALUES(?,?,1)",(service_id,chat)); conn.commit(); conn.close()

    @classmethod
    def get_reaction_targets(cls, service_id=None):
        conn=cls.get_conn()
        if service_id is None: rows=conn.execute("SELECT * FROM reaction_targets WHERE is_active=1 ORDER BY id").fetchall()
        else: rows=conn.execute("SELECT * FROM reaction_targets WHERE service_id=? AND is_active=1 ORDER BY id",(service_id,)).fetchall()
        conn.close(); return rows

    @classmethod
    def delete_reaction_target(cls, tid):
        conn=cls.get_conn(); conn.execute("DELETE FROM reaction_targets WHERE id=?",(tid,)); conn.commit(); conn.close()

    @classmethod
    def get_execution_telegram_account(cls):
        owner_id=int(getattr(config,"TG_EXECUTION_USER_ID",0) or 0)
        if not owner_id: return None
        return cls.get_telegram_account(owner_id)

    @classmethod
    def get_telegram_account(cls, bot_user_id, phone=None):
        conn = cls.get_conn()
        if phone:
            r = conn.execute("SELECT * FROM telegram_accounts WHERE bot_user_id=? AND phone=? AND is_active=1",
                             (bot_user_id, phone)).fetchone()
        else:
            r = conn.execute("SELECT * FROM telegram_accounts WHERE bot_user_id=? AND is_active=1 ORDER BY id DESC LIMIT 1",
                             (bot_user_id,)).fetchone()
        conn.close()
        return r

    @classmethod
    def get_execution_telegram_account(cls):
        """الحساب المركزي الذي يستخدمه البوت لتنفيذ خدمات Telegram."""
        owner_id = int(getattr(config, "TG_EXECUTION_USER_ID", 0) or 0)
        if not owner_id:
            return None
        return cls.get_telegram_account(owner_id)

    @classmethod
    def get_service_telegram_account(cls, service):
        """الحساب المرتبط بالخدمة؛ إن لم يوجد نستخدم الحساب المركزي القديم."""
        aid = service.get("telegram_account_id") if service else None
        owner_id = int(getattr(config, "TG_EXECUTION_USER_ID", 0) or 0)
        if aid and owner_id:
            conn = cls.get_conn()
            row = conn.execute("SELECT * FROM telegram_accounts WHERE id=? AND bot_user_id=? AND is_active=1", (int(aid), owner_id)).fetchone()
            conn.close()
            if row:
                return row
        return cls.get_execution_telegram_account()

    @classmethod
    def upsert_telegram_account(cls, bot_user_id, phone, telegram_user_id, username, first_name, session_path, api_id=0, api_hash=""):
        conn = cls.get_conn()
        conn.execute("""
            INSERT INTO telegram_accounts
                (bot_user_id,phone,telegram_user_id,username,first_name,session_path,api_id,api_hash,is_active,updated_at)
            VALUES(?,?,?,?,?,?,?,?,1,CURRENT_TIMESTAMP)
            ON CONFLICT(bot_user_id,phone) DO UPDATE SET
                telegram_user_id=excluded.telegram_user_id,
                username=excluded.username,
                first_name=excluded.first_name,
                session_path=excluded.session_path,
                api_id=excluded.api_id,
                api_hash=excluded.api_hash,
                is_active=1,
                updated_at=CURRENT_TIMESTAMP
        """, (bot_user_id, phone, telegram_user_id, username or "", first_name or "", session_path, int(api_id or 0), api_hash or ""))
        conn.commit()
        conn.close()

    @classmethod
    def list_telegram_accounts(cls, bot_user_id):
        conn = cls.get_conn()
        rows = conn.execute("SELECT * FROM telegram_accounts WHERE bot_user_id=? AND is_active=1 ORDER BY id DESC",
                            (bot_user_id,)).fetchall()
        conn.close()
        return rows

    @classmethod
    def get_service_telegram_accounts(cls, service_id):
        owner_id = int(getattr(config, "TG_EXECUTION_USER_ID", 0) or 0)
        if not owner_id: return []
        conn=cls.get_conn()
        rows=conn.execute("""SELECT ta.* FROM service_telegram_accounts sta
            JOIN telegram_accounts ta ON ta.id=sta.telegram_account_id
            WHERE sta.service_id=? AND ta.bot_user_id=? AND ta.is_active=1
            ORDER BY sta.telegram_account_id""",(int(service_id),owner_id)).fetchall()
        conn.close(); return rows

    @classmethod
    def remove_service_telegram_account(cls, service_id, account_id):
        """فصل حساب واحد من الخدمة فقط، بدون حذف حساب Telegram من قاعدة الحسابات العامة."""
        conn = cls.get_conn()
        conn.execute(
            "DELETE FROM service_telegram_accounts WHERE service_id=? AND telegram_account_id=?",
            (int(service_id), int(account_id)),
        )
        remaining = conn.execute(
            "SELECT telegram_account_id FROM service_telegram_accounts WHERE service_id=? ORDER BY telegram_account_id",
            (int(service_id),),
        ).fetchall()
        first_id = int(remaining[0][0]) if remaining else 0
        conn.execute("UPDATE app_services SET telegram_account_id=? WHERE id=?", (first_id, int(service_id)))
        conn.commit()
        conn.close()
        return first_id

    @classmethod
    def set_service_telegram_accounts(cls, service_id, account_ids):
        """استبدال ربط حسابات الخدمة في Transaction قصيرة وآمنة."""
        owner_id = int(getattr(config, "TG_EXECUTION_USER_ID", 0) or 0)
        ids = []
        for x in (account_ids or []):
            try:
                x = int(x)
                if x > 0 and x not in ids:
                    ids.append(x)
            except Exception:
                continue
        last = None
        for attempt in range(12):
            conn = cls.get_conn()
            try:
                with DB_WRITE_LOCK:
                    if owner_id and ids:
                        marks = ",".join("?" for _ in ids)
                        valid = conn.execute(
                            f"SELECT id FROM telegram_accounts WHERE bot_user_id=? AND is_active=1 AND id IN ({marks})",
                            [owner_id] + ids,
                        ).fetchall()
                        valid_ids = {int(r["id"]) for r in valid}
                        clean_ids = [x for x in ids if x in valid_ids]
                    else:
                        clean_ids = []
                    conn.execute("DELETE FROM service_telegram_accounts WHERE service_id=?", (int(service_id),))
                    for aid in clean_ids:
                        conn.execute(
                            "INSERT OR IGNORE INTO service_telegram_accounts(service_id,telegram_account_id) VALUES(?,?)",
                            (int(service_id), aid),
                        )
                    conn.execute(
                        "UPDATE app_services SET telegram_account_id=? WHERE id=?",
                        (clean_ids[0] if clean_ids else 0, int(service_id)),
                    )
                    conn.commit()
                    return clean_ids
            except sqlite3.OperationalError as e:
                last = e
                try: conn.rollback()
                except Exception: pass
                if "locked" not in str(e).lower() and "busy" not in str(e).lower():
                    raise
                if attempt >= 11:
                    raise
                time.sleep(min(1.2, 0.10 * (attempt + 1)))
            finally:
                try: conn.close()
                except Exception: pass
        raise sqlite3.OperationalError(f"SQLite remained locked: {last}")

    @classmethod
    def get_service_account_mode(cls, service):
        mode = str((service or {}).get("account_execution_mode") or "multi").strip().lower()
        return "multi" if mode == "multi" else "single"

    @classmethod
    def set_service_account_mode(cls, service_id, mode="multi"):
        # حفظ وضع تنفيذ الخدمة بشكل صحيح (فتح اتصال قاعدة البيانات أولاً).
        conn = cls.get_conn()
        conn.execute(
            "UPDATE app_services SET account_execution_mode=? WHERE id=?",
            ("multi", int(service_id)),
        )
        conn.commit()
        conn.close()

    @classmethod
    def get_free_services(cls, only_active=True):
        conn=cls.get_conn(); q="SELECT * FROM free_services"+(" WHERE is_active=1" if only_active else "")+" ORDER BY id"; rows=conn.execute(q).fetchall(); conn.close(); return rows

    @classmethod
    def delete_telegram_account(cls, bot_user_id, account_id):
        conn = cls.get_conn()
        row = conn.execute("SELECT * FROM telegram_accounts WHERE id=? AND bot_user_id=?",
                           (account_id, bot_user_id)).fetchone()
        if row:
            conn.execute("UPDATE telegram_accounts SET is_active=0,updated_at=CURRENT_TIMESTAMP WHERE id=?",
                         (account_id,))
            conn.commit()
        conn.close()
        return row

    @classmethod
    def delete_telegram_accounts_for_user(cls, bot_user_id):
        conn = cls.get_conn()
        rows = conn.execute("SELECT * FROM telegram_accounts WHERE bot_user_id=? AND is_active=1",
                            (bot_user_id,)).fetchall()
        conn.execute("UPDATE telegram_accounts SET is_active=0,updated_at=CURRENT_TIMESTAMP WHERE bot_user_id=?",
                     (bot_user_id,))
        conn.commit()
        conn.close()
        return rows

    @classmethod
    def delete_service(cls, sid):
        conn = cls.get_conn()
        conn.execute("DELETE FROM app_services WHERE id=?", (sid,))
        conn.commit()
        conn.close()

    # ─── المصادر الخارجية ────────────────────────────────────────────────
    @classmethod
    def add_free_service(cls, name, desc, api_id, daily_limit, mn, mx, site_id=None):
        conn = cls.get_conn()
        conn.execute("""INSERT INTO free_services(name,description,api_service_id,daily_limit,min_qty,max_qty,site_id)
            VALUES(?,?,?,?,?,?,?)""", (name, desc, api_id, daily_limit, mn, mx, site_id))
        conn.commit()
        conn.close()

    @classmethod
    def delete_free_service(cls, sid):
        conn = cls.get_conn()
        conn.execute("DELETE FROM free_services WHERE id=?", (sid,))
        conn.commit()
        conn.close()

    @classmethod
    def get_free_claim_count_today(cls, uid, sid):
        today = date.today().isoformat()
        conn = cls.get_conn()
        n = conn.execute("SELECT COUNT(*) FROM user_free_claims WHERE user_id=? AND service_id=? AND claim_date=?",
                         (uid, sid, today)).fetchone()[0]
        conn.close()
        return n

    @classmethod
    def get_free_claim_count_today_total(cls, uid):
        today = date.today().isoformat()
        conn = cls.get_conn()
        n = conn.execute("SELECT COUNT(*) FROM user_free_claims WHERE user_id=? AND claim_date=?",
                         (uid, today)).fetchone()[0]
        conn.close()
        return n

    @classmethod
    def add_free_claim(cls, uid, sid, qty, link, api_id="", status="pending"):
        today = date.today().isoformat()
        conn = cls.get_conn()
        conn.execute("""INSERT INTO user_free_claims(user_id,service_id,claim_date,quantity,link,api_order_id,status)
            VALUES(?,?,?,?,?,?,?)""", (uid, sid, today, qty, link, api_id, status))
        conn.commit()
        conn.close()

    # ─── الأدمنية ─────────────────────────────────────────────────
    @classmethod
    def get_extra_admins(cls):
        conn = cls.get_conn()
        r = conn.execute("SELECT * FROM extra_admins").fetchall()
        conn.close()
        return r

    @classmethod
    def add_extra_admin(cls, tg_id, full_name=""):
        conn = cls.get_conn()
        try:
            conn.execute("INSERT INTO extra_admins(tg_id,full_name) VALUES(?,?)", (tg_id, full_name))
            conn.commit()
            conn.close()
            return True
        except:
            conn.close()
            return False

    @classmethod
    def remove_extra_admin(cls, tg_id):
        conn = cls.get_conn()
        conn.execute("DELETE FROM extra_admins WHERE tg_id=?", (tg_id,))
        conn.commit()
        conn.close()

    # ─── تصدير/استيراد قاعدة البيانات ────────────────────────────
    @classmethod
    def export_db_json(cls):
        """تصدير إعدادات قاعدة البيانات كـ JSON"""
        conn = cls.get_conn()
        data = {}

        tables = ["config", "apps", "app_services",
                  "free_services", "wheel_prizes", "mandatory_channels",
                  "points_channels", "order_channels", "invite_links"]

        for table in tables:
            try:
                rows = conn.execute(f"SELECT * FROM {table}").fetchall()
                data[table] = [dict(r) for r in rows]
            except:
                data[table] = []

        conn.close()
        return json.dumps(data, ensure_ascii=False, indent=2)

    @classmethod
    def import_db_json(cls, json_str):
        """استيراد إعدادات قاعدة البيانات من JSON"""
        try:
            data = json.loads(json_str)
            conn = cls.get_conn()
            c = conn.cursor()

            # استيراد الإعدادات
            if "config" in data:
                for row in data["config"]:
                    c.execute("INSERT OR REPLACE INTO config(key,value) VALUES(?,?)",
                              (row["key"], row["value"]))

            # استيراد الأقسام
            if "apps" in data:
                for row in data["apps"]:
                    c.execute("INSERT OR IGNORE INTO apps(id,name,emoji,is_active,sort_order) VALUES(?,?,?,?,?)",
                              (row.get("id"), row.get("name",""), row.get("emoji","📱"),
                               row.get("is_active",1), row.get("sort_order",0)))

            # استيراد الخدمات
            if "app_services" in data:
                for row in data["app_services"]:
                    c.execute("""INSERT OR IGNORE INTO app_services
                        (id,app_id,name,emoji,api_service_id,site_id,points_per_1000,min_qty,max_qty,rate_per_1000,service_type,reaction_emoji,is_active)
                        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                        (row.get("id"), row.get("app_id"), row.get("name",""),
                         row.get("emoji",""), row.get("api_service_id",""),
                         row.get("site_id"), row.get("points_per_1000",10),
                         row.get("min_qty",100), row.get("max_qty",100000),
                         row.get("rate_per_1000",0.5), row.get("service_type","عام"),
                         row.get("reaction_emoji",""), row.get("is_active",1)))

            # استيراد جوائز العجلة
            if "wheel_prizes" in data:
                c.execute("DELETE FROM wheel_prizes")
                for row in data["wheel_prizes"]:
                    c.execute("INSERT INTO wheel_prizes(points,weight,emoji,label,is_active) VALUES(?,?,?,?,?)",
                              (row.get("points",10), row.get("weight",10),
                               row.get("emoji",""), row.get("label",""), row.get("is_active",1)))

            # استيراد الخدمات المجانية
            if "free_services" in data:
                for row in data["free_services"]:
                    c.execute("""INSERT OR IGNORE INTO free_services
                        (name,description,api_service_id,site_id,daily_limit,min_qty,max_qty,is_active)
                        VALUES(?,?,?,?,?,?,?,?)""",
                        (row.get("name",""), row.get("description",""),
                         row.get("api_service_id",""), row.get("site_id"),
                         row.get("daily_limit",1), row.get("min_qty",100),
                         row.get("max_qty",1000), row.get("is_active",1)))

            # استيراد القنوات الإجبارية
            if "mandatory_channels" in data:
                for row in data["mandatory_channels"]:
                    c.execute("""INSERT OR IGNORE INTO mandatory_channels
                        (channel_id,channel_name,channel_url,target_members) VALUES(?,?,?,?)""",
                        (row.get("channel_id",""), row.get("channel_name",""),
                         row.get("channel_url",""), row.get("target_members",0)))

            conn.commit()
            conn.close()
            return True, "تم الاستيراد بنجاح!"
        except Exception as e:
            return False, f"خطأ في الاستيراد: {e}"


# ══════════════════════════════════════════════════════════════════
#   4. عجلة الحظ — الرسم
# ══════════════════════════════════════════════════════════════════
def build_wheel_display(prizes, highlight_idx=None):
    if not prizes:
        return "لا توجد جوائز"
    lines = ["╔═══════════════════════╗"]
    for i, p in enumerate(prizes):
        em = p.get("emoji") or ""
        lbl = p.get("label") or f"{p['points']} نقطة"
        pts_str = f"{p['points']:,}"
        if highlight_idx is not None and i == highlight_idx:
            lines.append(f"║ ► {em} {pts_str:>6} — {lbl:<10} ◄ ║")
        else:
            lines.append(f"║   {em} {pts_str:>6} — {lbl:<10}   ║")
    lines.append("╚═══════════════════════╝")
    return "\n".join(lines)


def spin_animation_frames(prizes, winner_idx):
    frames = []
    n = len(prizes)
    for step in range(4):
        idx = (winner_idx + step + 1) % n
        frames.append(("🎡 العجلة تدور...", build_wheel_display(prizes, idx)))
    frames.append(("🎯 توقفت العجلة!", build_wheel_display(prizes, winner_idx)))
    return frames


# ══════════════════════════════════════════════════════════════════
#   5. الأزرار
# ══════════════════════════════════════════════════════════════════
# ══════════════════════════════════════════════════════════════════
#   دعم ألوان الأزرار الرسمية — Bot API 9.4
#   "success"=أخضر | "danger"=أحمر | "primary"=أزرق
# ══════════════════════════════════════════════════════════════════
class ColoredButton(InlineKeyboardButton):
    """زر Telegram ملوّن فعلياً عبر الحقل الرسمي style."""
    def __init__(self, text, callback_data=None, url=None, style=None, **kwargs):
        super().__init__(text=text, callback_data=callback_data, url=url, **kwargs)
        self._btn_style = style

    def to_dict(self):
        # نستخدم serializer الأصلي ثم نضيف style صراحةً داخل JSON
        # حتى لا يتحول الزر إلى زر Telegram عادي بدون لون.
        d = super().to_dict()
        if self._btn_style in ("success", "danger", "primary"):
            d["style"] = self._btn_style
        return d

    def to_json(self):
        import json
        return json.dumps(self.to_dict(), ensure_ascii=False)


ORDER_EXECUTION_LOCK = threading.Lock()
ORDER_EXECUTION_GAP_SECONDS = 15.0

_STYLE_MAP = {
    "green": "success",   # أخضر
    "red":   "danger",    # أحمر
    "blue":  "primary",   # أزرق
}


MILLION_GAME_URL = "https://mirox-bshp.github.io/MQUESTC/"


def _webapp_btn(text, url=MILLION_GAME_URL, color="green"):
    """زر Telegram Mini App يفتح لعبة من سيربح المليون داخل تيليجرام."""
    style = _STYLE_MAP.get(color, "primary")
    return ColoredButton(text=text, web_app=WebAppInfo(url=url), style=style)


def _btn(text, cb=None, url=None, color="blue"):
    """كل زر لازم له لون — green/red/blue"""
    style = _STYLE_MAP.get(color, "primary")
    return ColoredButton(text=text, callback_data=cb, url=url, style=style)


def mk(*rows):
    m = InlineKeyboardMarkup()
    for row in rows:
        m.row(*row)
    return m


def _style_service_text(text):
    """تنسيق اسم الخدمة للعرض فقط بدون تغيير الاسم المحفوظ في قاعدة البيانات."""
    text = (text or "").strip()
    if not text:
        return text
    out = []
    for word in text.split():
        # الحفاظ على الإيموجي/الرموز كما هي.
        if not any("\u0600" <= ch <= "\u06ff" for ch in word):
            out.append(word)
            continue
        if word.startswith("ال") and len(word) > 2:
            tail = word[2:]
            styled = "الـ" + "ـ".join(tail)
        else:
            styled = "ـ".join(word)
        out.append(styled)
    return " ".join(out)


def _service_display_name(service):
    """اسم موحّد للخدمات الظاهرة للمستخدم."""
    name = _style_service_text(service.get("name") or "خدمة")
    return f"🛍️ الـخـدمـة - {name}"


def _get_or_create_rush_app():
    """القسم الافتراضي: لا يحتاج المطور لإضافة قسم قبل إضافة الخدمة."""
    apps = db.get_apps(only_active=False)
    for app in apps:
        if (app.get("name") or "").strip() == "خدمات الرشق":
            return int(app["id"])
    return int(db.add_app("خدمات الرشق", "🐸"))


def _detect_service_meta(name):
    """يحدد نوع الخدمة وإيموجيها تلقائياً من الاسم، بدون خطوات إضافية."""
    low = (name or "").strip().lower()
    if any(x in low for x in ("قلب", "تفاعل", "reaction", "react")):
        known = ["❤️‍🔥","❤️","👍","🥰","🔥","😍","😂","😎","👏","😡","😢","🤔","🤯","🥳","💯"]
        found = [em for em in known if em in name]
        pool = ",".join(dict.fromkeys(found)) if found else "❤️,👍,🥰,🔥,😍,😂,👏,💯"
        return "تفاعل", (found[0] if found else "❤️"), pool
    if any(x in low for x in ("اشتراك", "اشتراكات", "subscribe", "subscription", "sub")):
        return "اشتراك بالقنوات", "📢", ""
    if any(x in low for x in ("مشاهدات", "مشاهدة", "views", "view")):
        return "مشاهدات", "👁️", ""
    if any(x in low for x in ("متابع", "متابعين", "followers", "follower")):
        return "متابعين", "👤", ""
    if any(x in low for x in ("أعضاء", "عضو", "members", "member")):
        return "أعضاء", "👥", ""
    if any(x in low for x in ("تعليق", "تعليقات", "comments", "comment")):
        return "تعليقات", "💬", ""
    if any(x in low for x in ("إعجاب", "اعجاب", "likes", "like")):
        return "إعجابات", "👍", ""
    if any(x in low for x in ("مشاركة", "مشاركات", "shares", "share")):
        return "مشاركات", "↗️", ""
    if any(x in low for x in ("تصويت", "vote", "votes")):
        return "تصويت", "🗳️", ""
    return "أخرى", "🛍️", ""


class kb:
    @classmethod
    def _is_developer_view(cls, viewer_id=None):
        # زر المطور يظهر فقط للمعرّف الأساسي الموجود أولاً في ADMIN_IDS.
        # لا يعتمد على اسم المستخدم حتى يظل الوصول مرتبطاً بالمعرّف.
        try:
            return bool(viewer_id) and bool(config.ADMIN_IDS) and int(viewer_id) == int(config.ADMIN_IDS[0])
        except Exception:
            return False

    # ─── القائمة الرئيسية ──────────────────────────────────────
    @classmethod
    def main_menu(cls, updates_ch=None, orders_count=0, viewer_id=None):
        # القائمة الرئيسية الجديدة بنفس الترتيب المطلوب، مع إبقاء الخدمات ديناميكية.
        services_label = _safe_config("menu_services_label", "🐸 خدمات الرشق")
        rows = [
            [_btn("🧺 سوق ترويجكم", "store", color="red")],
            [_btn("💠 تمويل قناتك", "disabled_fund_channel", color="blue")],
            [_webapp_btn("🏆 لعب من سيربح المليون 💰", color="green"),
             _btn("🐸 تجميع النقاط", "collect_section", color="green")],
            [_btn("🐸 شحن النقاط", "fund_start", color="red"),
             _btn("🔴 طلباتي", "my_orders", color="blue")],
            [_btn("🧠 الإحصائيات", "adm_stats", color="blue"),
             _btn("💪 الحساب", "my_account", color="blue")],
            [_btn("🏪 تحويل النقاط", "my_balance", color="blue"),
             _btn("🐸 بريد مؤقت عشوائي", "temp_mail", color="blue")],
            [_btn("👑 اشتراك Premium", "premium", color="blue"),
             _btn("🛑 الشروط", "terms", color="red")],
            [_btn("🧰 مزودين API", "api_providers", color="red")],
            [_btn(f"✅ عدد الطلبات المكتملة : {orders_count:,}", "my_orders", color="green")],
        ]
        return mk(*rows)

    # ─── تجميع النقاط ─────────────────────────────────────────
    @classmethod
    def collect_menu(cls):
        return mk(
            [_btn("🎡 عجلة الحظ", "wheel_open", color="green")],
            [_btn("🌅 الهدية اليومية", "daily_gift", color="green"),
             _btn("🗓️ الهدية الأسبوعية", "weekly_gift", color="green")],
            [_btn("📢 الاشتراك بالقنوات", "points_channels", color="blue")],
            [_btn("🔗 رابط الإحالة الخاص بي", "my_referral_link", color="green")],
            [_btn("🎟️ كود دعوة", "enter_invite_code", color="blue")],
            [_btn("🏆 أفضل 5 محيلين", "top_referrers", color="blue")],
            [_btn("◀️ رجوع للقائمة", "back_main", color="blue")],
        )

    # ─── الخدمات المجانية ─────────────────────────────────────
    @classmethod
    def free_services_menu(cls, services, back_cb="back_main"):
        rows = []
        for s in services:
            rows.append([_btn(
                f"🎁 {s['name']} | {s['min_qty']:,}-{s['max_qty']:,}",
                f"free_svc_{s['id']}", color="green")])
        rows.append([_btn("◀️ رجوع", back_cb, color="blue")])
        return mk(*rows)

    # ─── متجر البوت ──────────────────────────────────────────
    @classmethod
    def store_products_keyboard(cls, products):
        rows = []
        for p in products:
            nm = f"{p['emoji']} {p['name']}" if p.get("emoji") else p['name']
            stock_txt = "" if p["stock"] == -1 else f" | {p['stock']:,} متبقي"
            rows.append([_btn(f"{nm}  —  {p['price']:,} نقطة{stock_txt}",
                              f"store_product_{p['id']}", color="blue")])
        rows.append([_btn("📦 طلباتي في المتجر", "my_store_orders", color="green")])
        rows.append([_btn("◀️ رجوع للقائمة", "back_main", color="blue")])
        return mk(*rows)

    @classmethod
    def admin_store_keyboard(cls, products):
        rows = []
        for p in products:
            nm = f"{p['emoji']} {p['name']}" if p.get("emoji") else p['name']
            st = "✅" if p["is_active"] else "❌"
            rows.append([_btn(f"{st} {nm}  —  {p['price']:,} نقطة",
                              f"adm_store_product_{p['id']}", color="blue" if p["is_active"] else "red")])
        rows.append([_btn("➕ إضافة منتج", "adm_add_store_product", color="green")])
        rows.append([_btn("📋 طلبات معلقة", "adm_pending_orders", color="green"),
                     _btn("💵 شحن معلق", "adm_pending_recharges", color="green")])
        rows.append([_btn("◀️ رجوع", "adm_back", color="blue")])
        return mk(*rows)

    # ─── أقسام الخدمات ────────────────────────────────────────
    @classmethod
    def apps_keyboard(cls, apps, include_free=False):
        rows = []
        if include_free:
            rows.append([_btn("🎁 الخدمات المجانية", "my_services_free", color="green")])
        pair = []
        for a in apps:
            txt = f"{a['emoji']} {a['name']}" if a.get('emoji') else a['name']
            pair.append(_btn(txt, f"app_{a['id']}", color="blue"))
            if len(pair) == 2:
                rows.append(pair)
                pair = []
        if pair:
            rows.append(pair)
        rows.append([_btn("◀️ رجوع للقائمة", "back_main", color="blue")])
        return mk(*rows)

    @classmethod
    def app_services_keyboard(cls, app_id, services):
        rows = []
        for s in services:
            # الاسم الظاهر موحّد ومزخرف، بينما الاسم الأصلي يبقى محفوظاً كما أدخله المطور.
            nm = _service_display_name(s)
            rows.append([_btn(nm, f"svc_{s['id']}", color="blue")])
        rows.append([_btn("◀️ رجوع للأقسام", "my_services", color="blue")])
        return mk(*rows)

    # ─── تأكيد ────────────────────────────────────────────────
    @classmethod
    def confirm_keyboard(cls):
        return mk(
            [_btn("✅ تأكيد وإرسال الطلب", "order_confirm", color="green"),
             _btn("❌ إلغاء", "back_main", color="red")],
        )

    @classmethod
    def order_detail_keyboard(cls, oid):
        return mk(
            [_btn("🔄 تحديث الحالة", f"order_refresh_{oid}", color="blue")],
            [_btn("◀️ رجوع للطلبات", "my_orders", color="blue")],
        )

    @classmethod
    def orders_list_keyboard(cls, orders):
        icons = {"pending": "⏳", "inprogress": "🔄", "completed": "✅",
                 "partial": "⚠️", "canceled": "❌"}
        rows = []
        for o in orders:
            ic = icons.get(o["status"].lower(), "•")
            rows.append([_btn(f"📦 طلب #{o['id']}  {ic}", f"order_detail_{o['id']}", color="blue")])
        rows.append([_btn("◀️ رجوع", "back_main", color="blue")])
        return mk(*rows)

    # ─── الاشتراك الإجباري ────────────────────────────────────
    @classmethod
    def subscribe_keyboard(cls, channels, uid):
        rows = []
        for ch in channels:
            rows.append([_btn(f"📢 اشترك في  {ch['channel_name']}", url=ch["channel_url"], color="blue")])
        rows.append([_btn("✅ تحققت من الاشتراك", f"check_sub_{uid}", color="green")])
        return mk(*rows)

    @classmethod
    def points_ch_keyboard(cls, channels):
        rows = []
        for ch in channels:
            rows.append([_btn(f"⭐ {ch['channel_name']}  +{ch['points_reward']} نقطة",
                              url=ch["channel_url"], color="blue")])
        rows.append([_btn("🎯 جمّعت نقاطي", "collect_pts_now", color="green"),
                     _btn("◀️ رجوع", "collect_section", color="blue")])
        return mk(*rows)

    # ─── عجلة الحظ ────────────────────────────────────────────
    @classmethod
    def wheel_keyboard(cls, can_spin):
        if can_spin:
            return mk(
                [_btn("🎡 اضغط لتلف العجلة", "wheel_spin", color="green")],
                [_btn("◀️ رجوع", "collect_section", color="blue")],
            )
        return mk([_btn("◀️ رجوع", "collect_section", color="blue")])

    # ─── لوحة المطور المستقلة ───────────────────────────────────
    @classmethod
    def developer_panel(cls):
        """
        القائمة الرئيسية الجديدة للوحة المطور.
        زر التحكم في الخدمة مستقل ومباشر من لوحة المطور.
        """
        return mk(
            [_btn("➕ إضافة خدمة", "adm_add_service_direct", color="green"),
             _btn("🛠️ إدارة الخدمات", "adm_cat_services", color="blue")],
            [_btn("📢 القنوات", "adm_cat_channels", color="blue"),
             _btn("👥 المستخدمون", "adm_users", color="blue")],
            [_btn("📊 الإحصائيات", "adm_stats", color="blue"),
             _btn("🛍️ المتجر والطلبات", "adm_cat_store", color="blue")],
            [_btn("🎁 النقاط والهدايا", "adm_cat_rewards", color="green"),
             _btn("📣 الإذاعة والتنبيهات", "adm_cat_communication", color="green")],
            [_btn("⚙️ إعدادات البوت", "adm_cat_settings", color="blue")],
            [_btn("🗄️ قاعدة البيانات", "adm_database", color="red")],
            [_btn("🔒 إغلاق اللوحة", "adm_close", color="red")],
        )

    # توافق داخلي: أي استدعاء قديم لـ admin_main يستخدم القائمة الجديدة.
    @classmethod
    def admin_main(cls):
        return cls.developer_panel()

    @classmethod
    def admin_services_menu(cls):
        return mk(
            [_btn("🗂️ الأقسام والخدمات", "adm_apps", color="blue")],
            [_btn("⚙️ التحكم في الخدمة", "adm_service_accounts", color="green")],
            [_btn("📡 التفاعل التلقائي", "adm_reaction_targets", color="blue")],
            [_btn("📱 حسابات Telegram", "tg_accounts", color="blue")],
            [_btn("◀️ رجوع للوحة", "adm_back", color="blue")],
        )

    @classmethod
    def admin_channels_menu(cls):
        return mk(
            [_btn("📢 القنوات الإجبارية", "adm_mandatory", color="blue")],
            [_btn("💎 قنوات النقاط", "adm_points_ch", color="blue")],
            [_btn("📣 قنوات الطلبات", "adm_order_channels", color="blue")],
            [_btn("◀️ رجوع للوحة", "adm_back", color="blue")],
        )

    @classmethod
    def admin_store_menu(cls):
        return mk(
            [_btn("🛍️ إدارة المتجر", "adm_store", color="blue")],
            [_btn("📋 الطلبات المعلقة", "adm_pending_orders", color="green")],
            [_btn("💳 الشحن المعلق", "adm_pending_recharges", color="green")],
            [_btn("◀️ رجوع للوحة", "adm_back", color="blue")],
        )

    @classmethod
    def admin_rewards_menu(cls):
        return mk(
            [_btn("🎡 عجلة الحظ", "adm_wheel", color="green")],
            [_btn("🎁 الخدمات المجانية", "adm_free_svcs", color="green")],
            [_btn("🎟️ أكواد الدعوة", "adm_invite_links", color="blue")],
            [_btn("🎁 روابط الهدايا", "adm_gift_links", color="green")],
            [_btn("🎫 كوبونات", "adm_coupons", color="blue")],
            [_btn("⭐ إعدادات النقاط", "adm_pts_settings", color="blue")],
            [_btn("◀️ رجوع للوحة", "adm_back", color="blue")],
        )

    @classmethod
    def admin_communication_menu(cls):
        return mk(
            [_btn("📣 إذاعة جماعية", "adm_broadcast", color="green")],
            [_btn("🔔 التنبيهات والتقارير", "adm_alerts_settings", color="blue")],
            [_btn("◀️ رجوع للوحة", "adm_back", color="blue")],
        )

    @classmethod
    def admin_settings_menu(cls):
        return mk(
            [_btn("📡 التحديثات / الدعم", "adm_bot_settings", color="blue")],
            [_btn("⭐ إعدادات النقاط", "adm_pts_settings", color="blue")],
            [_btn("◀️ رجوع للوحة", "adm_back", color="blue")],
        )

    @classmethod
    def admin_apps_keyboard(cls, apps):
        rows = []
        pair = []
        for a in apps:
            nm = f"{a['emoji']} {a['name']}" if a.get('emoji') else a['name']
            pair.append(_btn(nm, f"adm_app_{a['id']}", color="blue"))
            if len(pair) == 2:
                rows.append(pair); pair=[]
        if pair: rows.append(pair)
        rows.append([_btn("➕ إضافة خدمة مباشرة", "adm_add_service_direct", color="green")])
        rows.append([_btn("◀️ رجوع للخدمات", "adm_cat_services", color="blue")])
        return mk(*rows)

    @classmethod
    def admin_app_view(cls, app_id, services):
        rows=[]
        pair=[]
        for svc in services:
            nm=f"{svc['emoji']} {svc['name']}" if svc.get('emoji') else svc['name']
            pair.append(_btn(nm, f"adm_service_manage_{svc['id']}", color="blue"))
            if len(pair)==2:
                rows.append(pair); pair=[]
        if pair: rows.append(pair)
        rows.append([_btn("➕ إضافة خدمة", f"adm_add_svc_{app_id}", color="green")])
        rows.append([_btn("✏️ تعديل القسم", f"adm_edit_app_{app_id}", color="blue"),
                     _btn("🗑️ حذف القسم", f"adm_del_app_{app_id}", color="red")])
        rows.append([_btn("◀️ رجوع للأقسام", "adm_apps", color="blue")])
        return mk(*rows)

    @classmethod
    def admin_service_accounts_view(cls, sid, app_id):
        svc=db.get_service(sid)
        if not svc:
            return mk([_btn("◀️ رجوع", f"adm_app_{app_id}", color="blue")])
        accounts=db.get_service_telegram_accounts(sid)
        count=len(accounts)
        mode=db.get_service_account_mode(svc)
        active = mode == "multi" and count > 0
        return mk(
            [_btn(f"👥 حسابات التنفيذ • {count}", f"adm_assign_account_{sid}", color="green" if active else "blue")],
            [_btn("🧪 اختبار الخدمة", f"adm_test_svc_{sid}", color="green")],
            [_btn("◀️ رجوع للخدمات", f"adm_app_{app_id}", color="blue")],
        )

    @classmethod
    def admin_linked_accounts_view(cls, sid, app_id, accounts, mode):
        rows=[]
        if accounts:
            for a in accounts:
                name=(a.get('first_name') or 'حساب بدون اسم').strip()
                username=f" @{a['username']}" if a.get('username') else ''
                rows.append([_btn(f"📱 {name}{username}", "adm_noop_service_id", color="blue")])
        else:
            rows.append([_btn("⚠️ لا توجد حسابات مرتبطة", "adm_noop_service_id", color="red")])
        rows.append([_btn("👥 حسابات التنفيذ", f"adm_assign_account_{sid}", color="green")])
        rows.append([_btn("◀️ رجوع للتحكم", f"adm_service_manage_{sid}", color="blue")])
        return mk(*rows)

    @classmethod
    def admin_multi_accounts_view(cls, sid, app_id, accounts, selected_ids, mode):
        rows=[]
        for a in accounts:
            aid=int(a['id']); mark='✅' if aid in selected_ids else '⬜'
            name=(a.get('first_name') or 'حساب').strip()
            username=f" @{a['username']}" if a.get('username') else ''
            rows.append([_btn(f"{mark} {name}{username}", f"adm_toggle_svc_acc_{sid}_{aid}", color='green' if aid in selected_ids else 'blue')])
        rows.append([_btn(f"☑️ تحديد الكل • {len(accounts)}", f"adm_select_all_svc_acc_{sid}", color="green")])
        rows.append([_btn(f"💾 تأكيد وحفظ • {len(selected_ids)}", f"adm_save_svc_acc_{sid}", color="green")])
        rows.append([_btn("◀️ رجوع للتحكم", f"adm_service_manage_{sid}", color="blue")])
        return mk(*rows)

    @classmethod
    def admin_svc_view(cls, sid, app_id):
        # الاسم القديم يبقى كواجهة توافق داخلية، لكن الواجهة المعروضة هي الجديدة.
        return cls.admin_service_accounts_view(sid, app_id)

    @classmethod
    def admin_free_svcs(cls, services):
        rows = []
        for s in services:
            rows.append([_btn(f"🎁 {s['name']}  |  حد {s['daily_limit']} يومياً",
                              f"adm_free_svc_{s['id']}", color="blue")])
        rows.append([_btn("➕ إضافة خدمة مجانية", "adm_add_free_svc", color="green")])
        rows.append([_btn("◀️ رجوع", "adm_back", color="blue")])
        return mk(*rows)

    @classmethod
    def admin_free_svc_view(cls, sid):
        return mk(
            [_btn("🗑️ حذف الخدمة المجانية", f"adm_del_free_{sid}", color="red")],
            [_btn("◀️ رجوع",                 "adm_free_svcs",       color="blue")],
        )

    @classmethod
    def admin_wheel(cls, prizes):
        rows = []
        total_w = sum(float(p["weight"]) for p in prizes if p["is_active"])
        for p in prizes:
            st = "✅" if p["is_active"] else "❌"
            chance = (float(p["weight"]) / total_w * 100) if (p["is_active"] and total_w) else 0
            lbl = p.get("label") or ""
            em = p.get("emoji") or ""
            dot_color = "green" if p["is_active"] else "red"
            rows.append([
                _btn(f"{st} {em} {p['points']} نقطة {lbl}  {chance:.0f}%",
                     f"adm_wheel_tog_{p['id']}", color=dot_color),
                _btn("🗑️", f"adm_wheel_del_{p['id']}", color="red"),
            ])
        rows.append([_btn("➕ إضافة جائزة", "adm_wheel_add", color="green")])
        rows.append([_btn("◀️ رجوع", "adm_back", color="blue")])
        return mk(*rows)

    @classmethod
    def admin_invite_links(cls, links):
        rows = []
        for lnk in links[:10]:
            rows.append([
                _btn(f"🎁 {lnk['code']}  +{lnk['points_reward']}نقطة  ({lnk['current_uses']}/{lnk['max_uses'] or '∞'})",
                     f"adm_view_invite_{lnk['code']}", color="blue"),
            ])
        rows.append([_btn("➕ إنشاء كود جديد", "adm_create_invite", color="green")])
        rows.append([_btn("◀️ رجوع", "adm_back", color="blue")])
        return mk(*rows)

    @classmethod
    def admin_users_kb(cls):
        return mk(
            [_btn("🔍 بحث عن مستخدم", "adm_search_user", color="blue")],
            [_btn("◀️ رجوع", "adm_back", color="blue")],
        )

    @classmethod
    def admin_user_view(cls, uid, banned):
        return mk(
            [_btn("➕ إضافة نقاط", f"adm_add_pts_{uid}", color="green"),
             _btn("➖ خصم نقاط", f"adm_sub_pts_{uid}", color="red")],
            [_btn("✅ فك الحظر" if banned else "🚫 حظر",
                  f"adm_{'unban' if banned else 'ban'}_{uid}",
                  color="green" if banned else "red")],
            [_btn("◀️ رجوع", "adm_users", color="blue")],
        )


    @classmethod
    def admin_order_channels(cls, channels):
        rows = []
        for ch in channels:
            rows.append([_btn(f"🗑️ حذف {ch['channel_name']}",
                              f"adm_del_orch_{ch['channel_id']}", color="red")])
        rows.append([_btn("➕ إضافة قناة طلبات", "adm_add_orch", color="green")])
        rows.append([_btn("◀️ رجوع", "adm_back", color="blue")])
        return mk(*rows)

    @classmethod
    def admin_database(cls):
        return mk(
            [_btn("📤 تصدير قاعدة البيانات (JSON)", "adm_db_export", color="blue")],
            [_btn("📥 استيراد قاعدة البيانات (JSON)", "adm_db_import", color="green")],
            [_btn("ℹ️ معلومات القاعدة", "adm_db_info", color="blue")],
            [_btn("◀️ رجوع", "adm_back", color="blue")],
        )

    @classmethod
    def back(cls, cb="back_main"):
        return mk([_btn("◀️ رجوع", cb, color="blue")])


# ══════════════════════════════════════════════════════════════════
#   6. تشغيل البوت
# ══════════════════════════════════════════════════════════════════
# تحقق واضح من التوكن قبل إنشاء TeleBot، لمنع ValueError: Token must contain a colon
if not config.BOT_TOKEN or ":" not in config.BOT_TOKEN:
    raise SystemExit(
        "❌ BOT_TOKEN غير صالح أو غير مضبوط.\n"
        "ضع توكن البوت الكامل من BotFather في متغير البيئة BOT_TOKEN، "
        "أو في ملف bot_token.txt بجانب bot.py.\n"
        "مثال: 123456789:AAxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    )

class _BotExceptionHandler:
    """يمسك أخطاء الـ handlers داخل worker threads حتى لا تتسبب في توقف البوت."""
    def handle(self, exception):
        try:
            logging.exception("[TELEBOT HANDLER ERROR] %s", exception)
        except Exception:
            try:
                print(f"[TELEBOT HANDLER ERROR] {type(exception).__name__}: {exception}")
            except Exception:
                pass
        # pyTelegramBotAPI يستخدم القيمة المعادة لتحديد استمرار معالجة الـ worker.
        return True


_bot_exception_handler = _BotExceptionHandler()
bot = telebot.TeleBot(
    config.BOT_TOKEN,
    parse_mode="HTML",
    num_threads=128,
    exception_handler=_bot_exception_handler,
)
db.init_db()
try:
    db.set_config("referral_points", "1000")
except Exception:
    pass
db.migrate_telegram_accounts()
# لا تحذف الأقسام أو الخدمات التي أضافها المطور عند إعادة تشغيل البوت.

# فهارس سريعة لفتح الأقسام والخدمات بدون انتظار بحث كامل في SQLite.
try:
    _idx = db.get_conn()
    _idx.execute("CREATE INDEX IF NOT EXISTS idx_apps_active_sort ON apps(is_active, sort_order, id)")
    _idx.execute("CREATE INDEX IF NOT EXISTS idx_app_services_active_app ON app_services(app_id, is_active, id)")
    _idx.execute("CREATE INDEX IF NOT EXISTS idx_service_accounts_service ON service_telegram_accounts(service_id, telegram_account_id)")
    _idx.commit()
    _idx.close()
except Exception as _idx_err:
    print(f"[DB INDEX] {_idx_err}")

USER_STATE = {}


def get_state(uid):
    return USER_STATE.get(uid, {"state": None, "data": {}})


def set_state(uid, s, **d):
    USER_STATE[uid] = {"state": s, "data": d}


def clear_state(uid):
    USER_STATE.pop(uid, None)


_ADMIN_CACHE = {}
_ADMIN_CACHE_TTL = 60.0

def is_admin(uid):
    if uid in config.ADMIN_IDS:
        return True
    now = time.monotonic()
    cached = _ADMIN_CACHE.get(uid)
    if cached and now - cached[0] < _ADMIN_CACHE_TTL:
        return cached[1]
    try:
        conn = db.get_conn()
        r = conn.execute("SELECT 1 FROM extra_admins WHERE tg_id=?", (uid,)).fetchone()
        conn.close()
        value = r is not None
    except Exception:
        value = False
    _ADMIN_CACHE[uid] = (now, value)
    return value


def send(cid, text, markup=None, **kw):
    try:
        return bot.send_message(cid, text, reply_markup=markup, **kw)
    except Exception as e:
        print(f"[send error] {e}")
        return None


def edit(call, text, markup=None):
    try:
        bot.edit_message_text(text, call.message.chat.id,
                              call.message.message_id, reply_markup=markup, parse_mode="HTML")
        return True
    except Exception as e:
        # لا ترسل رسالة جديدة إذا كان النص نفسه أو الرسالة تغيرت بالفعل.
        msg = str(e).lower()
        if "message is not modified" in msg or "message to edit not found" in msg:
            return False
        try:
            bot.send_message(call.message.chat.id, text, reply_markup=markup, parse_mode="HTML")
            return True
        except Exception as e2:
            print(f"[edit error] {e2}")
            return False


def check_subs(uid):
    channels = db.get_mandatory_channels()
    missing = []
    for ch in channels:
        try:
            m = bot.get_chat_member(ch["channel_id"], uid)
            if m.status in ("left", "kicked"):
                missing.append(ch)
            else:
                db.record_join(uid, ch["channel_id"])
        except:
            missing.append(ch)
    return len(missing) == 0, missing


def _safe_config(key, default=""):
    """قراءة إعدادات الواجهة بدون إسقاط /start لو SQLite مقفول مؤقتاً."""
    try:
        return db.get_config(key, default)
    except sqlite3.OperationalError as e:
        if "locked" in str(e).lower() or "busy" in str(e).lower():
            print(f"[DB READ LOCK] config {key}: {e}")
            return default
        raise
    except Exception as e:
        print(f"[DB READ ERROR] config {key}: {e}")
        return default


def welcome_text(user=None, ref_count=0):
    """رسالة الترحيب الرئيسية الموحدة للبوت."""
    return (
        "<b>🚀 أَهـلاً بـك فـي بـوت رَشـق دَعـمـكـم 💙</b>\n\n"
        "<b>✨ مَنـصـتـك لـخـدمـات الـسـوشـيـال مـيـديـا</b>\n\n"
        "<b>📦 خـدمـات مـتـنـوعـة تـنـاسـب احـتـيـاجـاتـك</b>\n"
        "<b>⚡ تـنـفـيـذ سـريـع ومـتـابـعـة لـلـطـلـبـات</b>\n"
        "<b>📊 اطـلـب خـدمـتـك بـكـل سـهـولـة</b>\n"
        "<b>💬 دعـم ومـتـابـعـة عـنـد الـحـاجـة</b>\n\n"
        "<b>👇 اخـتـر الـخـدمـة الـمـنـاسـبـة وابـدأ طـلـبـك الآن</b>"
    )


# ── إشعار انخفاض الرصيد ─────────────────────────────────────
def _send_low_points_alert(tg_id, pts, threshold):
    try:
        bot.send_message(tg_id,
            f"<b>⚠️ تنبيه: رصيدك منخفض!</b>\n\n"
            f"رصيدك الحالي: <b>{pts:,}</b> نقطة\n\n"
            f"<i>اشحن رصيدك الآن للاستمرار في استخدام الخدمات 🔋</i>",
            reply_markup=mk([_btn("🔋 شحن الآن", "back_main", color="green")]),
            parse_mode="HTML")
    except:
        pass


# ── التقرير اليومي ───────────────────────────────────────────
def send_daily_report():
    if db.get_config("daily_report_enabled", "1") != "1":
        return
    stats = db.get_daily_stats()
    text = (
        f"<b>📊 التقرير اليومي — {datetime.now().strftime('%Y-%m-%d')}</b>\n\n"
        f"<b>━━━━━━━━━━━━━━━</b>\n"
        f"👤 مستخدمون جدد: <b>{stats['new_users']:,}</b> | الإجمالي: {stats['total_users']:,}\n"
        f"📦 طلبات اليوم: <b>{stats['new_orders']:,}</b> | الإجمالي: {stats['total_orders']:,}\n"
        f"🛍️ طلبات المتجر: <b>{stats['store_orders']:,}</b>\n"
        f"⭐ نقاط مُنفقة: <b>{stats['points_spent']:,}</b>\n"
        f"💵 شحن مؤكد: <b>{stats['recharges']:,}</b> طلب\n"
        f"<b>━━━━━━━━━━━━━━━</b>"
    )
    all_admins = list(config.ADMIN_IDS) + [a["tg_id"] for a in db.get_extra_admins()]
    for aid in all_admins:
        try:
            bot.send_message(aid, text, parse_mode="HTML")
        except:
            pass


def daily_report_loop():
    """يبعت التقرير كل يوم الساعة 8 صباحاً"""
    import time as _time
    from datetime import timedelta
    while True:
        now = datetime.now()
        target = now.replace(hour=8, minute=0, second=0, microsecond=0)
        if now >= target:
            target = target + timedelta(days=1)
            target = target.replace(hour=8, minute=0, second=0, microsecond=0)
        wait = (target - now).total_seconds()
        _time.sleep(wait)
        send_daily_report()

def notify_order_channels(order_id, user, service_name, app_name, link, qty, pts_used):
    """إشعار قناة الطلبات بصيغة مختصرة وواضحة."""
    channels = db.get_order_channels()
    if not channels:
        return
    order = db.get_order(order_id)
    service_public_id = "—"
    if order:
        try:
            svc = db.get_service(order["service_id"])
            if svc:
                service_public_id = svc.get("public_id") or svc.get("id") or "—"
        except Exception:
            pass
    text = (
        f"<b>🚀 طلب جديد</b>\n\n"
        f"<b>🆔 ID الخدمة:</b> <code>{service_public_id}</code>\n"
        f"<b>📦 الخدمة:</b> {service_name}\n"
        f"🔗 <b>الرابط:</b> <code>{link}</code>\n"
        f"🌞 <b>الكمية:</b> {qty:,}\n"
        f"💰 <b>السعر:</b> {pts_used:,} نقطة"
    )
    bot_markup = mk(
        [_btn("دخول البوت🤖", url=f"https://t.me/{config.BOT_USERNAME.lstrip('@')}", color="green")]
    )
    for ch in channels:
        try:
            bot.send_message(ch["channel_id"], text, reply_markup=bot_markup)
        except Exception as e:
            print(f"[order_channel error] {ch['channel_id']}: {e}")



def _notify_admin_approve_order(order_id, user, service_name, app_name, link, qty, pts_used, order_type="telegram"):
    """إشعار الأدمن بطلب جديد يحتاج موافقة"""
    text = (
        f"<b>🔔 طلب جديد يحتاج موافقتك #{order_id}</b>\n\n"
        f"<b>━━━━━━━━━━━━━━━</b>\n"
        f"<b>المستخدم:</b> {user.get('full_name', '—')} (<code>{user.get('tg_id', '—')}</code>)\n"
        f"<b>القسم:</b> {app_name or '—'}\n"
        f"<b>الخدمة:</b> {service_name}\n"
        f"<b>الرابط:</b> <code>{link}</code>\n"
        f"<b>الكمية:</b> {qty:,}\n"
        f"<b>النقاط:</b> {pts_used:,}\n"
        f"<b>━━━━━━━━━━━━━━━</b>"
    )
    markup = mk(
        [_btn("✅ موافقة وتنفيذ", f"adm_approve_{order_type}_{order_id}", color="green"),
         _btn("❌ رفض", f"adm_reject_{order_type}_{order_id}", color="red")],
    )
    all_admins = list(config.ADMIN_IDS) + [a["tg_id"] for a in db.get_extra_admins()]
    for aid in all_admins:
        try:
            bot.send_message(aid, text, reply_markup=markup)
        except Exception as e:
            print(f"[admin_notify error] {aid}: {e}")


def _notify_admin_approve_store_order(order_id, user, product_name, pts):
    """إشعار الأدمن بطلب متجر جديد"""
    text = (
        f"<b>🛍️ طلب متجر جديد #{order_id}</b>\n\n"
        f"<b>━━━━━━━━━━━━━━━</b>\n"
        f"<b>المستخدم:</b> {user.get('full_name', '—')} (<code>{user.get('tg_id', '—')}</code>)\n"
        f"<b>المنتج:</b> {product_name}\n"
        f"<b>النقاط:</b> {pts:,}\n"
        f"<b>━━━━━━━━━━━━━━━</b>"
    )
    markup = mk(
        [_btn("✅ موافقة وتسليم", f"adm_approve_store_{order_id}", color="green"),
         _btn("❌ رفض", f"adm_reject_store_{order_id}", color="red")],
    )
    all_admins = list(config.ADMIN_IDS) + [a["tg_id"] for a in db.get_extra_admins()]
    for aid in all_admins:
        try:
            bot.send_message(aid, text, reply_markup=markup)
        except Exception as e:
            print(f"[admin_store_notify error] {aid}: {e}")


def notify_admin_new_user(user_msg):
    u = user_msg.from_user
    total = db.get_users_count()
    text = (
        f"<b>مستخدم جديد دخل البوت</b>\n\n"
        f"<b>الاسم:</b> {u.full_name}\n"
        f"<b>المعرف:</b> @{u.username or '—'}\n"
        f"<b>الـ ID:</b> <code>{u.id}</code>\n\n"
        f"<b>إجمالي المستخدمين:</b> {total}"
    )
    for aid in config.ADMIN_IDS:
        try:
            bot.send_message(aid, text)
        except:
            pass
    for a in db.get_extra_admins():
        try:
            bot.send_message(a["tg_id"], text)
        except:
            pass


# ══════════════════════════════════════════════════════════════════
#   دوال مساعدة — إشعار الأدمن عند استلام رابط هدية
# ══════════════════════════════════════════════════════════════════
def _build_gift_notify_text(user_id, full_name, username, gift_code, pts):
    uname_str = f"@{username}" if username else "—"
    bu = config.BOT_USERNAME.lstrip("@")
    gift_link = f"https://t.me/{bu}?start=gift_{gift_code}"
    return (
        f"<b>🎁 مستخدم دخل برابط هدية!</b>\n\n"
        f"<b>━━━━━━━━━━━━━━━</b>\n"
        f"👤 الاسم: <b>{full_name}</b>\n"
        f"🔖 يوزر: {uname_str}\n"
        f"🆔 ID: <code>{user_id}</code>\n"
        f"<b>━━━━━━━━━━━━━━━</b>\n"
        f"🔗 الرابط: {gift_link}\n"
        f"💰 النقاط المستلمة: <b>{pts:,}</b> نقطة\n"
        f"<b>━━━━━━━━━━━━━━━</b>"
    )

def _notify_admins_gift_claim(tg_user, gift_code, pts):
    """إشعار لما يجي المستخدم من msg (start)"""
    text = _build_gift_notify_text(
        tg_user.id,
        tg_user.full_name or "",
        tg_user.username or "",
        gift_code, pts
    )
    for admin_id in config.ADMIN_IDS:
        try:
            bot.send_message(admin_id, text, parse_mode="HTML")
        except:
            pass
    # إشعار الأدمنية الإضافية
    try:
        extra = db.get_extra_admins()
        for a in extra:
            try:
                bot.send_message(a["tg_id"], text, parse_mode="HTML")
            except:
                pass
    except:
        pass

def _notify_admins_gift_claim_db(uid, user_obj, gift_code, pts):
    """إشعار لما يجي المستخدم من قاعدة البيانات (بعد الاشتراك الإجباري)"""
    full_name = user_obj["full_name"] if user_obj else str(uid)
    username  = user_obj["username"]  if user_obj else ""
    text = _build_gift_notify_text(uid, full_name, username, gift_code, pts)
    for admin_id in config.ADMIN_IDS:
        try:
            bot.send_message(admin_id, text, parse_mode="HTML")
        except:
            pass
    try:
        extra = db.get_extra_admins()
        for a in extra:
            try:
                bot.send_message(a["tg_id"], text, parse_mode="HTML")
            except:
                pass
    except:
        pass


# ══════════════════════════════════════════════════════════════════
#   7. معالجات المستخدم
# ══════════════════════════════════════════════════════════════════
DEVELOPER_ID = 8939118645


@bot.message_handler(commands=["mirox"])
def cmd_mirox(msg: Message):
    """فتح لوحة المطور بالأمر /mirox للمعرف المحدد فقط."""
    if int(msg.from_user.id) != DEVELOPER_ID:
        return
    clear_state(msg.from_user.id)
    _show_admin(msg.chat.id)


def _is_developer(uid):
    """صلاحية /king: المطور الأساسي أو أي ID موجود ضمن ADMIN_IDS."""
    try:
        uid = int(uid)
        if uid == int(DEVELOPER_ID):
            return True
        return uid in {int(x) for x in (config.ADMIN_IDS or [])}
    except Exception:
        return False


def _open_king(msg: Message):
    """فتح لوحة الخدمات الجديدة من /king."""
    if not is_admin(int(msg.from_user.id)):
        return
    clear_state(msg.from_user.id)
    bot.send_message(msg.chat.id, "<b>⚙️ التحكم في الخدمة</b>\n\nاختر القسم ثم الخدمة.", reply_markup=kb.admin_services_menu(), parse_mode="HTML")

# احتياطي: بعض المحادثات/المجموعات قد ترسل الأمر بصيغة /king@BotUsername.
# هذا المسار لا يضيف أي صلاحية جديدة؛ يمر بنفس فحص المطور.
@bot.message_handler(func=lambda m: bool(getattr(m, "text", None)) and bool(__import__("re").fullmatch(r"\s*/king(?:@\w+)?\s*", m.text, flags=__import__("re").IGNORECASE)))
def cmd_king_fallback(msg: Message):
    _open_king(msg)


def _fallback_main_menu():
    """قائمة ثابتة للطوارئ بنفس شكل القائمة الرئيسية الجديدة."""
    return mk(
        [_btn("🧺 سوق ترويجكم", "store", color="red")],
        [_btn("💠 تمويل قناتك", "disabled_fund_channel", color="blue")],
        [_webapp_btn("🏆 لعب من سيربح المليون 💰", color="green"),
         _btn("🐸 تجميع النقاط", "collect_section", color="green")],
        [_btn("🐸 شحن النقاط", "fund_start", color="red")],
        [_btn("🔴 طلباتي", "my_orders", color="blue"),
         _btn("🧠 الإحصائيات", "adm_stats", color="blue")],
        [_btn("💪 الحساب", "my_account", color="blue"),
         _btn("🏪 تحويل النقاط", "my_balance", color="blue")],
        [_btn("🐸 بريد مؤقت عشوائي", "temp_mail", color="blue"),
         _btn("👑 اشتراك Premium", "premium", color="blue")],
        [_btn("🛑 الشروط", "terms", color="red"),
         _btn("🧰 مزودين API", "api_providers", color="red")],
        [_btn("✅ عدد الطلبات المكتملة : 0", "my_orders", color="green")],
    )


@bot.callback_query_handler(func=lambda c: c.data in ("disabled_fund_channel", "disabled_kora_sport"))
def disabled_main_menu_action(call: CallbackQuery):
    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass


@bot.message_handler(commands=["start"])
def cmd_start(msg: Message):
    """نسخة طوارئ: القائمة تظهر أولاً بدون أي اعتماد على SQLite.
    أي مشكلة في قاعدة البيانات لا تمنع /start من إرسال الكيبورد.
    """
    chat_id = msg.chat.id

    # تحويل نقاط اللعبة عبر رابط start مباشر.
    # هذا المسار يعمل أيضاً عندما تكون اللعبة مفتوحة من Inline Mini App،
    # حيث Telegram لا يوفّر WebApp.sendData().
    try:
        start_parts = (msg.text or "").split(maxsplit=1)
        start_payload = start_parts[1].strip() if len(start_parts) > 1 else ""
        if start_payload.startswith("game_transfer_"):
            transfer_parts = start_payload.split("_", 3)
            if len(transfer_parts) == 3:
                # الصيغة: game_transfer_<amount>_<transfer_id>
                # split على أول 2 underscores ينتج 3 أجزاء فقط.
                pass
            m_transfer = re.fullmatch(r"game_transfer_(\d+)_([A-Za-z0-9-]{16,100})", start_payload)
            if m_transfer:
                amount = int(m_transfer.group(1))
                transfer_id = m_transfer.group(2)
                if amount <= 0:
                    bot.send_message(chat_id, "❌ لا يوجد رصيد صالح للتحويل.")
                    return

                user = db.get_user(msg.from_user.id)
                if not user:
                    bot.send_message(chat_id, "❌ افتح البوت أولاً ثم جرّب التحويل من اللعبة.")
                    return

                with DB_WRITE_LOCK:
                    conn = db.get_conn()
                    try:
                        already = conn.execute(
                            "SELECT 1 FROM game_transfer_claims WHERE transfer_id=?",
                            (transfer_id,)
                        ).fetchone()
                        if already:
                            bot.send_message(chat_id, "ℹ️ تم تنفيذ عملية تحويل اللعبة هذه من قبل.")
                            return

                        row = conn.execute(
                            "SELECT points FROM users WHERE tg_id=?",
                            (msg.from_user.id,)
                        ).fetchone()
                        if not row:
                            bot.send_message(chat_id, "❌ المستخدم غير موجود في قاعدة البيانات.")
                            return

                        conn.execute(
                            "INSERT INTO game_transfer_claims(transfer_id,user_id,amount) VALUES(?,?,?)",
                            (transfer_id, msg.from_user.id, amount)
                        )
                        conn.execute(
                            "UPDATE users SET points=points+? WHERE tg_id=?",
                            (amount, msg.from_user.id)
                        )
                        conn.commit()
                        new_points = int(row["points"] or 0) + amount
                    except sqlite3.IntegrityError:
                        try:
                            conn.rollback()
                        except Exception:
                            pass
                        bot.send_message(chat_id, "ℹ️ تم تنفيذ عملية تحويل اللعبة هذه من قبل.")
                        return
                    except Exception as e:
                        try:
                            conn.rollback()
                        except Exception:
                            pass
                        print(f"[GAME TRANSFER START ERROR] {type(e).__name__}: {e}")
                        bot.send_message(chat_id, "❌ تعذر تنفيذ التحويل حالياً، حاول مرة أخرى.")
                        return
                    finally:
                        try:
                            conn.close()
                        except Exception:
                            pass

                bot.send_message(
                    chat_id,
                    f"<b>✅ تم تحويل نقاط اللعبة بنجاح</b>\n\n"
                    f"💰 النقاط المضافة: <b>{amount:,}</b>\n"
                    f"💳 رصيدك الجديد: <b>{new_points:,}</b> نقطة",
                    parse_mode="HTML"
                )
                return
    except Exception as e:
        print(f"[/start GAME TRANSFER ERROR] {type(e).__name__}: {e}")
        # إذا لم تكن الرسالة تحويل لعبة، نكمل مسار /start العادي.


    # 1) ابعت القائمة فوراً — بدون db، وبدون ColoredButton، وبدون أي قراءة/كتابة.
    try:
        menu = _fallback_main_menu()

        bot.send_message(
            chat_id,
            welcome_text(),
            reply_markup=menu,
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"[/start MENU ERROR] {type(e).__name__}: {e}")
        return

    # 2) تجهيز بيانات المستخدم في الخلفية — لا نسمح لها بتعطيل القائمة.
    def _start_db_work():
        try:
            args = msg.text.split(maxsplit=1)
            ref_code = invite_code = gift_code = None
            if len(args) > 1:
                p = args[1].strip()
                if p.startswith("invite_"):
                    invite_code = p.replace("invite_", "")
                elif p.startswith("gift_"):
                    gift_code = p.replace("gift_", "")
                else:
                    ref_code = p

            user, referred_by, is_new = db.get_or_create(
                msg.from_user.id, msg.from_user.username or "",
                msg.from_user.full_name or "", ref_code
            )
            if is_new:
                try:
                    notify_admin_new_user(msg)
                except Exception as e:
                    print(f"[/start notify] {e}")

                # مكافأة الإحالة فور دخول مستخدم جديد عبر رابط صديقه: 30 نقطة للطرفين.
                if referred_by:
                    try:
                        result = db.complete_referral(msg.from_user.id)
                        if result:
                            referrer_id, ref_pts = result
                            bot.send_message(
                                msg.chat.id,
                                f"<b>🎉 تم دخولك عبر رابط صديقك!</b>\n\n"
                                f"حصلت على <b>{ref_pts}</b> نقطة. 💰",
                                parse_mode="HTML"
                            )
                            try:
                                bot.send_message(
                                    referrer_id,
                                    f"<b>🎉 دخل صديقك عبر رابط دعوتك!</b>\n\n"
                                    f"تمت إضافة <b>{ref_pts}</b> نقطة إلى حسابك. 💰\n"
                                    f"🆔 أيدي صديقك: <code>{msg.from_user.id}</code>",
                                    parse_mode="HTML"
                                )
                            except Exception as e:
                                print(f"[/start referral notify] {e}")
                    except Exception as e:
                        print(f"[/start referral reward] {e}")

            if invite_code:
                try:
                    ok, pts, err = db.claim_invite(msg.from_user.id, invite_code)
                    if ok:
                        bot.send_message(chat_id, f"<b>تم تفعيل كود الدعوة!</b>\n\nحصلت على <b>{pts}</b> نقطة!", parse_mode="HTML")
                except Exception as e:
                    print(f"[/start invite] {e}")

            # لا نعمل check_subs هنا حتى لا نمنع القائمة من الظهور.
            print(f"[/start OK] user={msg.from_user.id} is_new={is_new}")
        except Exception as e:
            print(f"[/start DB BACKGROUND ERROR] {type(e).__name__}: {e}")

    threading.Thread(target=_start_db_work, daemon=True).start()


@bot.callback_query_handler(func=lambda c: c.data == "back_main")
def cb_back_main(call: CallbackQuery):
    """رجوع آمن للقائمة الرئيسية؛ لا يسمح لأي خطأ في الرجوع بإيقاف البوت."""
    try:
        try:
            bot.answer_callback_query(call.id)
        except Exception as e:
            print(f"[BACK ACK ERROR] {type(e).__name__}: {e}")

        try:
            clear_state(call.from_user.id)
        except Exception as e:
            print(f"[BACK STATE ERROR] {type(e).__name__}: {e}")

        try:
            orders_count = int(db.get_total_completed_orders() or 0)
        except Exception as e:
            print(f"[BACK ORDERS ERROR] {type(e).__name__}: {e}")
            orders_count = 0

        try:
            updates_ch = db.get_config("updates_channel") or ""
        except Exception as e:
            print(f"[BACK CONFIG ERROR] {type(e).__name__}: {e}")
            updates_ch = ""

        # نستخدم القائمة الرئيسية الطبيعية أولاً، ثم نسخة الطوارئ إذا فشلت.
        try:
            markup = kb.main_menu(updates_ch, orders_count, call.from_user.id)
        except Exception as e:
            print(f"[BACK KEYBOARD ERROR] {type(e).__name__}: {e}")
            markup = _fallback_main_menu()

        text_main = (
            "<b>🚀 أَهـلاً بـك فـي بـوت رَشـق دَعـمـكـم 💙</b>\n\n"
            "<b>✨ مَنـصـتـك لـخـدمـات الـسـوشـيـال مـيـديـا</b>\n\n"
            "<b>📦 خـدمـات مـتـنـوعـة تـنـاسـب احـتـيـاجـاتـك</b>\n"
            "<b>⚡ تـنـفـيـذ سـريـع ومـتـابـعـة لـلـطـلـبـات</b>\n"
            "<b>📊 اطـلـب خـدمـتـك بـكـل سـهـولـة</b>\n"
            "<b>💬 دعـم ومـتـابـعـة عـنـد الـحـاجـة</b>\n\n"
            "<b>👇 اخـتـر الـخـدمـة الـمـنـاسـبـة وابـدأ طـلـبـك الآن</b>"
        )
        if not edit(call, text_main, markup):
            # إذا كانت رسالة الـcallback غير قابلة للتعديل، أرسل القائمة بدلاً من ترك الزر بلا استجابة.
            try:
                bot.send_message(call.message.chat.id, text_main, reply_markup=markup, parse_mode="HTML")
            except Exception as e:
                print(f"[BACK SEND ERROR] {type(e).__name__}: {e}")
    except Exception as e:
        # آخر طبقة حماية: أي خطأ غير متوقع في زر الرجوع لا يخرج من الـhandler.
        print(f"[BACK MAIN FATAL PROTECTED] {type(e).__name__}: {e}")
        try:
            bot.answer_callback_query(call.id, "⚠️ حاول مرة أخرى", show_alert=False)
        except Exception:
            pass


# ─── لعبة من سيربح المليون: استقبال تحويل نقاط Mini App ─────────
@bot.message_handler(content_types=["web_app_data"])
def handle_game_webapp_data(msg: Message):
    """استقبال طلب التحويل من Mini App عبر Telegram مباشرة، بدون API خارجي."""
    try:
        payload = json.loads(msg.web_app_data.data or "{}")
    except Exception:
        bot.send_message(msg.chat.id, "❌ بيانات اللعبة غير صالحة.")
        return

    if payload.get("action") != "transfer_points":
        return

    try:
        target_id = int(str(payload.get("target_id", "")).strip())
        amount = int(payload.get("amount", 0))
        transfer_id = str(payload.get("transfer_id", "")).strip()
    except Exception:
        bot.send_message(msg.chat.id, "❌ بيانات التحويل غير صحيحة.")
        return

    if len(transfer_id) < 16 or len(transfer_id) > 100:
        bot.send_message(msg.chat.id, "❌ رقم عملية التحويل غير صالح.")
        return

    # الهوية الحقيقية تأتي من Telegram نفسه؛ لا نسمح بتحويل نقاط لعبة
    # إلى حساب آخر من داخل الواجهة. يجب أن يكون الـID المدخل هو حساب صاحب اللعبة.
    if target_id != int(msg.from_user.id):
        bot.send_message(msg.chat.id, "❌ أيدي الحساب لا يطابق حساب Telegram الذي فتح اللعبة.")
        return
    if amount <= 0:
        bot.send_message(msg.chat.id, "❌ لا توجد نقاط صالحة للتحويل.")
        return

    user = db.get_user(msg.from_user.id)
    if not user:
        bot.send_message(msg.chat.id, "❌ افتح البوت أولاً ثم جرّب التحويل من اللعبة.")
        return

    # التحويل والمعرّف الخاص به داخل معاملة واحدة؛ نفس transfer_id لا يمكن
    # تنفيذه مرتين حتى لو أعاد Telegram إرسال web_app_data.
    with DB_WRITE_LOCK:
        conn = db.get_conn()
        try:
            already = conn.execute(
                "SELECT 1 FROM game_transfer_claims WHERE transfer_id=?",
                (transfer_id,)
            ).fetchone()
            if already:
                conn.close()
                bot.send_message(msg.chat.id, "ℹ️ تم تنفيذ عملية تحويل اللعبة هذه من قبل.")
                return

            row = conn.execute("SELECT points FROM users WHERE tg_id=?", (msg.from_user.id,)).fetchone()
            if not row:
                conn.close()
                bot.send_message(msg.chat.id, "❌ المستخدم غير موجود في قاعدة البيانات.")
                return

            conn.execute(
                "INSERT INTO game_transfer_claims(transfer_id,user_id,amount) VALUES(?,?,?)",
                (transfer_id, msg.from_user.id, amount)
            )
            conn.execute("UPDATE users SET points=points+? WHERE tg_id=?", (amount, msg.from_user.id))
            conn.commit()
            new_points = int(row["points"] or 0) + amount
        except sqlite3.IntegrityError:
            try: conn.rollback()
            except Exception: pass
            bot.send_message(msg.chat.id, "ℹ️ تم تنفيذ عملية تحويل اللعبة هذه من قبل.")
            return
        finally:
            try: conn.close()
            except Exception: pass

    bot.send_message(
        msg.chat.id,
        f"<b>🎉 تم تحويل نقاط اللعبة بنجاح!</b>\n\n"
        f"🏆 النقاط المحولة: <b>+{amount:,}</b>\n"
        f"🪙 رصيدك في @RSDMKBOT: <b>{new_points:,}</b> نقطة\n\n"
        "يمكنك الرجوع للعبة واللعب من جديد، وسيبقى رصيد اللعبة محفوظاً حتى التحويل التالي."
    )


# ─── نقاطي ────────────────────────────────────────────────────
@bot.callback_query_handler(func=lambda c: c.data == "my_balance")
def cb_my_balance(call: CallbackQuery):
    user = db.get_user(call.from_user.id)
    edit(call,
        f"<b>💰 نقاطي</b>\n\n"
        f"<b>━━━━━━━━━━━━━━━</b>\n"
        f"رصيدك الحالي: <b>{user['points']:,}</b> نقطة\n"
        f"<b>━━━━━━━━━━━━━━━</b>",
        mk(
            [_btn("🔄 تحويل نقاط لمستخدم", "transfer_points", color="green")],
            [_btn("◀️ رجوع", "back_main", color="blue")],
        ))


@bot.callback_query_handler(func=lambda c: c.data == "transfer_points")
def cb_transfer_points(call: CallbackQuery):
    user = db.get_user(call.from_user.id)
    set_state(call.from_user.id, "transfer_username")
    edit(call,
        f"<b>🔄 تحويل نقاط</b>\n\n"
        f"رصيدك: <b>{user['points']}</b> نقطة\n\n"
        f"<b>━━━━━━━━━━━━━━━</b>\n"
        f"أرسل <b>أيدي</b> المستخدم المسجل في البوت الذي تريد التحويل له:\n"
        f"<i>مثال: <code>123456789</code></i>",
        kb.back())


@bot.message_handler(func=lambda m: get_state(m.from_user.id).get("state") == "transfer_username")
def msg_transfer_username(msg: Message):
    uid = msg.from_user.id
    text = (msg.text or "").strip()
    # التحويل يتم بالـ ID فقط، ولا نقبل username.
    if not text.isdigit():
        send(msg.chat.id, "❌ أرسل أيدي المستخدم فقط، مثال: <code>123456789</code>")
        return
    target = db.get_user(int(text))
    if not target:
        send(msg.chat.id,
            "❌ هذا الأيدي غير مسجل في البوت.\n\n"
            "يجب أن يكون الشخص قد فتح البوت من قبل.")
        return
    if target["tg_id"] == uid:
        send(msg.chat.id, "❌ لا يمكنك التحويل لنفسك!")
        return
    user = db.get_user(uid)
    set_state(uid, "transfer_amount", target_id=target["tg_id"],
              target_name=target["full_name"], target_uname=target["username"] or str(target["tg_id"]))
    send(msg.chat.id,
        f"<b>🔄 تحويل إلى:</b> {target['full_name']}"
        f"{(' (@' + target['username'] + ')') if target['username'] else ''}\n\n"
        f"رصيدك: <b>{user['points']}</b> نقطة\n\n"
        f"كم نقطة تريد تحويلها؟",
        kb.back())


@bot.message_handler(func=lambda m: get_state(m.from_user.id).get("state") == "transfer_amount")
def msg_transfer_amount(msg: Message):
    uid = msg.from_user.id
    try:
        amount = int((msg.text or "").strip().replace(",", ""))
        if amount <= 0:
            raise ValueError
    except:
        send(msg.chat.id, "⚠️ أرسل رقماً صحيحاً أكبر من صفر!")
        return
    d = get_state(uid).get("data", {})
    user = db.get_user(uid)
    if user["points"] < amount:
        send(msg.chat.id,
            f"❌ رصيدك غير كافٍ!\n"
            f"رصيدك: <b>{user['points']}</b> | المطلوب: <b>{amount}</b>")
        return
    set_state(uid, "transfer_confirm",
              target_id=d["target_id"], target_name=d["target_name"],
              target_uname=d["target_uname"], amount=amount)
    send(msg.chat.id,
        f"<b>تأكيد التحويل</b>\n\n"
        f"<b>━━━━━━━━━━━━━━━</b>\n"
        f"إلى: <b>{d['target_name']}</b> (@{d['target_uname']})\n"
        f"المبلغ: <b>{amount}</b> نقطة\n"
        f"رصيدك بعد التحويل: <b>{user['points'] - amount}</b> نقطة\n"
        f"<b>━━━━━━━━━━━━━━━</b>",
        mk(
            [_btn("✅ تأكيد التحويل", "transfer_do", color="green")],
            [_btn("❌ إلغاء", "back_main", color="red")],
        ))


@bot.callback_query_handler(func=lambda c: c.data == "transfer_do")
def cb_transfer_do(call: CallbackQuery):
    uid = call.from_user.id
    state = get_state(uid)
    if state.get("state") != "transfer_confirm":
        bot.answer_callback_query(call.id, "انتهت الجلسة، حاول مجدداً.")
        return
    d = state.get("data", {})
    amount = d.get("amount", 0)
    target_id = d.get("target_id")
    if not db.deduct_points(uid, amount):
        bot.answer_callback_query(call.id, "❌ رصيدك غير كافٍ!", show_alert=True)
        return
    db.add_points(target_id, amount)
    clear_state(uid)
    sender = db.get_user(uid)
    target = db.get_user(target_id)
    edit(call,
        f"<b>✅ تم التحويل بنجاح!</b>\n\n"
        f"<b>━━━━━━━━━━━━━━━</b>\n"
        f"إلى: <b>{d['target_name']}</b>\n"
        f"المبلغ: <b>{amount}</b> نقطة\n"
        f"رصيدك الجديد: <b>{sender['points']}</b> نقطة\n"
        f"<b>━━━━━━━━━━━━━━━</b>",
        kb.back())
    try:
        bot.send_message(target_id,
            f"<b>🎁 صديقك أضاف لك نقاط</b>\n\n"
            f"🆔 أيدي المرسل - <code>{sender['tg_id']}</code>\n"
            f"🪙 النقاط المضافة - <b>{amount}</b>\n"
            f"💰 رصيدك الجديد - <b>{target['points']}</b> نقطة")
    except:
        pass


# ─── لوحتي الشخصية ───────────────────────────────────────────
@bot.callback_query_handler(func=lambda c: c.data == "my_account")
def cb_my_account(call: CallbackQuery):
    user = db.get_user(call.from_user.id)
    points = user["points"] if user else 0
    edit(call,
        f"<b>💪 حـسـابـك</b>\n\n"
        f"🆔 أيـدي حـسـابـك - <code>{call.from_user.id}</code>\n\n"
        f"🪙 نـقـاط حـسـابـك - <b>{points}</b>",
        kb.back("back_main"))


# ─── طلباتي ──────────────────────────────────────────────────
@bot.callback_query_handler(func=lambda c: c.data == "my_orders")
def cb_my_orders(call: CallbackQuery):
    orders = db.get_user_orders(call.from_user.id, limit=100)
    total = len(orders)
    if not orders:
        edit(call, "<b>🔴 طـلـبـاتـي</b>\n\nلا تـوجـد طـلـبـات حـالـيـاً.", kb.back("back_main"))
        return

    # الطلبات غير المكتملة أولاً، ثم المكتملة، مع الأحدث داخل كل حالة.
    rank = {"pending": 0, "inprogress": 1, "partial": 2, "completed": 3, "canceled": 4}
    orders.sort(key=lambda o: str(o.get("created_at", "")), reverse=True)
    orders.sort(key=lambda o: rank.get(str(o.get("status", "")).lower(), 9))
    icons = {"pending": "⏳", "inprogress": "🔄", "completed": "✅", "partial": "⚠️", "canceled": "❌"}
    status_ar = {"pending": "قـيـد الانتظار", "inprogress": "قـيـد التنفيذ", "completed": "مـكـتـمـل", "partial": "جـزئـي", "canceled": "مـلـغـي"}
    text = f"<b>🔴 طـلـبـاتـي - {total}</b>\n\n"
    for o in orders:
        st = str(o.get("status", "")).lower()
        text += (
            f"{icons.get(st, '•')} <b>طـلـب #{o['id']}</b>\n"
            f"🛍️ الـخـدمـة - {o.get('service_name', '—')}\n"
            f"📦 الـعـدد - {o.get('quantity', 0)}\n"
            f"🪙 الـنـقـاط - {o.get('points_used', 0)}\n"
            f"📌 الـحـالـة - {status_ar.get(st, st)}\n\n"
        )
    edit(call, text, kb.orders_list_keyboard(orders))


@bot.callback_query_handler(func=lambda c: c.data.startswith("order_detail_"))
def cb_order_detail(call: CallbackQuery):
    oid = int(call.data.split("_")[-1])
    o = db.get_order(oid)
    if not o or o["user_id"] != call.from_user.id:
        bot.answer_callback_query(call.id, "الطلب غير موجود")
        return
    status_ar = {"pending":"قيد الانتظار","inprogress":"قيد التنفيذ","completed":"مكتمل","canceled":"ملغي"}.get(o["status"], o["status"])
    edit(call,
        f"<b>تفاصيل الطلب #{o['id']}</b>\n\n"
        f"<b>━━━━━━━━━━━━━━━</b>\n"
        f"<b>القسم:</b>  {o.get('app_name', '—')}\n"
        f"<b>الخدمة:</b>  {o['service_name']}\n"
        f"<b>رقم API:</b>  <code>{o['api_order_id'] or 'لا يوجد'}</code>\n"
        f"<b>الرابط:</b>  <code>{o['link']}</code>\n"
        f"<b>الكمية:</b>  {o['quantity']:,}\n"
        f"<b>النقاط:</b>  {o['points_used']:,}\n"
        f"<b>الحالة:</b>  {status_ar}\n"
        f"<b>التاريخ:</b>  {str(o['created_at'])[:16]}\n"
        f"<b>━━━━━━━━━━━━━━━</b>",
        kb.order_detail_keyboard(oid))


@bot.callback_query_handler(func=lambda c: c.data.startswith("order_refresh_"))
def cb_order_refresh(call: CallbackQuery):
    oid=int(call.data.split("_")[-1]); o=db.get_order(oid)
    if not o or o["user_id"] != call.from_user.id:
        bot.answer_callback_query(call.id,"الطلب غير موجود"); return
    status_ar={"pending":"قيد الانتظار","inprogress":"قيد التنفيذ","completed":"مكتمل","canceled":"ملغي"}.get(o["status"],o["status"])
    bot.answer_callback_query(call.id,f"الحالة: {status_ar}")
    call.data=f"order_detail_{oid}"; cb_order_detail(call)


# ─── الدعم ───────────────────────────────────────────────────
@bot.callback_query_handler(func=lambda c: c.data == "support")
def cb_support(call: CallbackQuery):
    sup = db.get_config("support_username", "@support")
    edit(call,
        f"<b>الدعم الفني</b>\n\n"
        f"<b>━━━━━━━━━━━━━━━</b>\n"
        f"للتواصل: {sup}\n"
        f"الرد خلال 24 ساعة\n"
        f"<b>━━━━━━━━━━━━━━━</b>",
        kb.back())


TERMS_DEFAULT = (
    "<b>╭━━━ ⛔️ 𝗦𝗧𝗔𝗥𝗧 | شـروط الاسـتـخـدام ━━━╮</b>\n\n"
    "<b>❌ • فـي حـال قـمـت بـتـغـيـيـر الـيـوزر أثـنـاء تـنـفـيـذ الـطـلـب، يُـعـتـبـر الـطـلـب مـكـتـمـل جـزئـيـاً، ولا يـحـق لـصـاحـب الـطـلـب الـمـطـالـبـة بـأي تـعـويـض.</b>\n\n"
    "<b>✔️ • عـنـد الـتـواصـل مـع خـدمـة الـعـمـلاء، يُـرجـى الـتـحـدث بـطـريـقـة لائـقـة والـتـزام الاحـتـرام مـع فـريـق الـدعـم، وأي إسـاءة أو تـجـاوز قـد تـؤدي إلـى حـظـر الـحـسـاب.</b>\n\n"
    "<b>❌ • فـي حـال قـمـت بـحـذف أي مـنـشـور أو فـيـديـو أثـنـاء تـنـفـيـذ الـطـلـب، يُـعـتـبـر الـطـلـب مـكـتـمـلاً، ولا يـحـق لـك الـمـطـالـبـة بـأي تـعـويـض.</b>\n\n"
    "<b>‼️ • فـي حـال قـمـت بـتـغـيـيـر يـوزر الـحـسـاب بـعـد انـتـهـاء تـنـفـيـذ الـطـلـب، لا يـمـكـن الـمـطـالـبـة بـتـعـويـض أو إعـادة تـنـفـيـذ الـطـلـب.</b>\n\n"
    "<b>‼️ • يـجـب أن تـكـون جـمـيـع الـحـسـابـات والـروابـط الـمُـسـتـخـدمـة فـي الـطـلـبـات عـامـة ولـيـسـت خـاصـة، حـتـى يـتـمـكـن الـنـظـام مـن تـنـفـيـذ الـطـلـب بـشـكـل صـحـيـح.</b>\n\n"
    "<b>‼️ • لا يـمـكـن إلـغـاء أي طـلـب بـعـد إرسـالـه إلـى الـسـيـرفـر، لـذلـك يُـرجـى مـراجـعـة الـخـدمـة والـعـدد والـيـوزر بـعـنـايـة قـبـل تـأكـيـد الـطـلـب.</b>\n\n"
    "<b>‼️ • فـي حـال تـحـويـل الـحـسـاب إلـى خـاص أثـنـاء تـنـفـيـذ الـطـلـب، يُـعـتـبـر الـطـلـب مـكـتـمـل جـزئـيـاً، ولا يـتـم تـقـديـم أي تـعـويـض عـن الـكـمـيـة الـمـتـبـقـيـة.</b>\n\n"
    "<b>🔥 • يـتـم تـنـفـيـذ الـطـلـبـات وفـق الـعـدد الـذي يـتـم تـثـبـيـتـه تـلـقـائـيـاً عـنـد إرسـال الـطـلـب، ولا يـمـكـن تـغـيـيـر الـعـدد بـعـد بـدء الـتـنـفـيـذ.</b>\n\n"
    "<b>‼️ • يـجـب عـلـيـك قـراءة تـفـاصـيـل كـل خـدمـة بـعـنـايـة قـبـل تـنـفـيـذ أي طـلـب جـديـد، والـتـأكـد مـن أن الـخـدمـة مـنـاسـبـة لـلـحـسـاب أو الـرابـط الـمُـسـتـخـدم.</b>\n\n"
    "<b>❌ • لا يـتـم إلـغـاء الـطـلـبـات أو إعـادة الـمـبـالـغ بـعـد إرسـال الـطـلـب لأي سـبـب، إلا فـي حـال فـشـل الـنـظـام فـي تـنـفـيـذ الـطـلـب أو وجـود مـشـكـلـة تـقـنـيـة مـن جـانـب الـنـظـام.</b>\n\n"
    "<b>✔️ • بـمـجـرد تـنـفـيـذ طـلـب جـديـد، فـأنـت تـؤكـد أنـك قـمـت بـقـراءة جـمـيـع الـشـروط والـتـفـاصـيـل، وتـوافـق عـلـى سـيـاسـة الـطـلـبـات والـتـعـويـضـات.</b>\n\n"
    "<b>╭━━━ ⚠️ هـام جـداً ━━━╮</b>\n"
    "<b>🔥 نـظـام الـتـعـويـض الـتـلـقـائـي</b>\n"
    "<b>╰━━━━━━━━━━━━━━╯</b>\n\n"
    "<b>⚡ يـتـم مـراجـعـة الـطـلـبـات وفـق نـظـام الـتـعـويـض الـتـلـقـائـي، وفـي حـال تـحـقـق شـروط الـتـعـويـض، يـتـم تـنـفـيـذ الـتـعـويـض وفـق سـيـاسـة الـخـدمـة.</b>\n\n"
    "<b>📞 لـلـتـواصـل مـع خـدمـة الـدعـم:</b>\n"
    "<b>@DKSUPBOTX</b>"
)

@bot.callback_query_handler(func=lambda c: c.data == "terms")
def cb_terms(call: CallbackQuery):
    edit(call, TERMS_DEFAULT, kb.back())


# ══════════════════════════════════════════════════════════════════
#   8. تجميع النقاط
# ══════════════════════════════════════════════════════════════════
@bot.callback_query_handler(func=lambda c: c.data == "collect_section")
def cb_collect(call: CallbackQuery):
    uid = call.from_user.id
    user = db.get_user(uid)
    ref_c = db.get_referral_count(uid)
    ref_pts = int(db.get_config("referral_points", "1000") or 1000)
    bu = config.BOT_USERNAME.lstrip("@")
    code = user["referral_code"]
    link = f"https://t.me/{bu}?start={code}"
    edit(call,
        f"<b>🐸 تـجـمـيـع الـنـقـاط</b>\n\n"
        f"🪙 نـقـاطـك - <b>{user['points']:,}</b>\n\n"
        f"🔗 رابـط دعـوتـك\n"
        f"<code>{link}</code>\n\n"
        f"👥 إحـالاتـك - <b>{ref_c}</b>\n"
        f"🎁 كـل صـديـق جـديـد يـدخـل مـن رابـطـك\n"
        f"تـحـصـل أنـت وهـو عـلـى <b>{ref_pts:,}</b> نـقـطـة.\n\n"
        f"📢 شـارك رابـط دعوتـك مـع صـديـقـك لـجـمـع الـنـقـاط.",
        kb.back("back_main"))


# ─── الهدية اليومية ──────────────────────────────────────────
@bot.callback_query_handler(func=lambda c: c.data == "daily_gift")
def cb_daily(call: CallbackQuery):
    ok, pts = db.claim_daily(call.from_user.id)
    user = db.get_user(call.from_user.id)
    if ok:
        edit(call,
            "<b>الهدية اليومية</b>\n\n"
            f"حصلت على <b>{pts}</b> نقطة! 🎉\n"
            f"رصيدك الآن: <b>{user['points']:,}</b>\n\n"
            f"<i>عد غداً لهدية جديدة</i>",
            kb.back("collect_section"))
    else:
        edit(call,
            "<b>الهدية اليومية</b>\n\n"
            "حصلت على هديتك اليوم بالفعل!\n\n<i>عد غداً</i>",
            kb.back("collect_section"))


# ─── الهدية الأسبوعية ────────────────────────────────────────
@bot.callback_query_handler(func=lambda c: c.data == "weekly_gift")
def cb_weekly(call: CallbackQuery):
    ok, pts, days = db.claim_weekly(call.from_user.id)
    user = db.get_user(call.from_user.id)
    if ok:
        edit(call,
            f"<b>الهدية الأسبوعية</b>\n\n"
            f"حصلت على <b>{pts}</b> نقطة! 🎉\n"
            f"رصيدك: <b>{user['points']:,}</b>\n\n<i>عد بعد 7 أيام</i>",
            kb.back("collect_section"))
    else:
        edit(call,
            f"<b>الهدية الأسبوعية</b>\n\n"
            f"تبقى <b>{days}</b> يوم على هديتك القادمة.",
            kb.back("collect_section"))


# ─── عجلة الحظ ───────────────────────────────────────────────
@bot.callback_query_handler(func=lambda c: c.data == "wheel_open")
def cb_wheel_open(call: CallbackQuery):
    can, hrs = db.can_spin(call.from_user.id)
    prizes = db.get_wheel_prizes()
    user = db.get_user(call.from_user.id)
    cool_hrs = db.get_config("wheel_cooldown_hrs", "6")

    if not prizes:
        edit(call, "<b>عجلة الحظ</b>\n\nلا توجد جوائز متاحة حالياً.", kb.back("collect_section"))
        return

    if not can:
        edit(call,
            f"<b>عجلة الحظ</b>\n\n"
            f"<b>━━━━━━━━━━━━━━━</b>\n"
            f"تبقى <b>{hrs}</b> ساعة على الدورة القادمة.\n"
            f"رصيدك: <b>{user['points']:,}</b>\n"
            f"<b>━━━━━━━━━━━━━━━</b>",
            kb.wheel_keyboard(False))
        return

    wheel_txt = build_wheel_display(prizes)
    edit(call,
        f"<b>عجلة الحظ</b>\n\n"
        f"<b>━━━━━━━━━━━━━━━</b>\n"
        f"الجوائز المتاحة:\n<code>{wheel_txt}</code>\n"
        f"<b>━━━━━━━━━━━━━━━</b>\n"
        f"رصيدك: <b>{user['points']:,}</b>\n"
        f"كل <b>{cool_hrs}</b> ساعات\n"
        f"<b>━━━━━━━━━━━━━━━</b>",
        kb.wheel_keyboard(True))


@bot.callback_query_handler(func=lambda c: c.data == "wheel_spin")
def cb_wheel_spin(call: CallbackQuery):
    can, hrs = db.can_spin(call.from_user.id)
    if not can:
        bot.answer_callback_query(call.id, f"تبقى {hrs} ساعة!", show_alert=True)
        return

    prizes = db.get_wheel_prizes()
    if not prizes:
        bot.answer_callback_query(call.id, "لا توجد جوائز!", show_alert=True)
        return

    # اختيار الفائز بالوزن
    total = sum(float(p["weight"]) for p in prizes)
    if total <= 0:
        bot.answer_callback_query(call.id, "خطأ في إعداد الجوائز!", show_alert=True)
        return

    r = random.uniform(0, total)
    cum = 0.0
    won_idx = 0
    won_pts = prizes[0]["points"]
    for i, p in enumerate(prizes):
        cum += float(p["weight"])
        if r <= cum:
            won_idx = i
            won_pts = p["points"]
            break

    db.add_points(call.from_user.id, won_pts)
    db.mark_spin(call.from_user.id)

    # حركة العجلة
    frames = spin_animation_frames(prizes, won_idx)
    for title, wheel in frames[:-1]:
        try:
            bot.edit_message_text(
                f"<b>{title}</b>\n\n<code>{wheel}</code>",
                call.message.chat.id, call.message.message_id,
                parse_mode="HTML")
            time.sleep(0.7)
        except:
            pass

    # النتيجة النهائية
    final_title, final_wheel = frames[-1]
    user = db.get_user(call.from_user.id)
    max_p = max(p["points"] for p in prizes)
    if won_pts >= max_p:
        reaction = "🏆 جائزة كبرى! الكل يحسدك الآن!"
    elif won_pts >= max_p * 0.4:
        reaction = "🎉 جائزة ممتازة!"
    elif won_pts >= max_p * 0.1:
        reaction = "👍 جائزة جيدة"
    else:
        reaction = "💪 لا بأس، حاول مرة أخرى لاحقاً"

    try:
        bot.edit_message_text(
            f"<b>🎯 نتيجة عجلة الحظ</b>\n\n"
            f"<code>{final_wheel}</code>\n\n"
            f"<b>━━━━━━━━━━━━━━━</b>\n"
            f"ربحت <b>{won_pts:,}</b> نقطة! {reaction}\n"
            f"رصيدك الآن: <b>{user['points']:,}</b>\n"
            f"<b>━━━━━━━━━━━━━━━</b>",
            call.message.chat.id, call.message.message_id,
            reply_markup=kb.back("collect_section"),
            parse_mode="HTML")
    except:
        try:
            edit(call,
                f"<b>ربحت {won_pts:,} نقطة!</b>\nرصيدك: {user['points']:,}",
                kb.back("collect_section"))
        except:
            pass


# ─── الإحالة ─────────────────────────────────────────────────
@bot.callback_query_handler(func=lambda c: c.data == "my_referral_link")
def cb_referral(call: CallbackQuery):
    user = db.get_user(call.from_user.id)
    ref_c = db.get_referral_count(call.from_user.id)
    ref_pts = int(db.get_config("referral_points", "1000") or 1000)
    bu = config.BOT_USERNAME.lstrip("@")
    link = f"https://t.me/{bu}?start={user['referral_code']}"
    edit(call,
        f"<b>رابط الإحالة الخاص بك</b>\n\n"
        f"<b>━━━━━━━━━━━━━━━</b>\n"
        f"رابطك:\n<code>{link}</code>\n"
        f"<b>━━━━━━━━━━━━━━━</b>\n"
        f"مكافأة كل صديق: <b>{ref_pts}</b> نقطة\n"
        f"إحالاتك حتى الآن: <b>{ref_c}</b>\n"
        f"<b>━━━━━━━━━━━━━━━</b>\n\n"
        f"<i>شارك الرابط واجمع نقاط بلا حدود!</i>",
        kb.back("collect_section"))


# ─── كود دعوة ─────────────────────────────────────────────────
@bot.callback_query_handler(func=lambda c: c.data == "enter_invite_code")
def cb_enter_code(call: CallbackQuery):
    set_state(call.from_user.id, "waiting_invite_code")
    edit(call,
        "<b>إدخال كود دعوة</b>\n\nأرسل الكود الآن:",
        kb.back("collect_section"))


# ─── أفضل 5 محيلين ───────────────────────────────────────────
@bot.callback_query_handler(func=lambda c: c.data == "top_referrers")
def cb_top_referrers(call: CallbackQuery):
    top = db.get_top_referrers(5)
    if not top:
        edit(call, "<b>أفضل 5 محيلين</b>\n\nلا توجد إحالات بعد.", kb.back("collect_section"))
        return
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
    text = "<b>أفضل 5 محيلين</b>\n\n<b>━━━━━━━━━━━━━━━</b>\n"
    for i, r in enumerate(top):
        name = r["full_name"] or f"مستخدم {r['tg_id']}"
        uname = f"@{r['username']}" if r["username"] else ""
        text += (f"{medals[i]} <b>{name}</b> {uname}\n"
                 f"   الإحالات: <b>{r['ref_count']}</b> | النقاط: <b>{r['total_pts']:,}</b>\n")
    text += "<b>━━━━━━━━━━━━━━━</b>"
    edit(call, text, kb.back("collect_section"))


# ─── قنوات النقاط ────────────────────────────────────────────
@bot.callback_query_handler(func=lambda c: c.data == "points_channels")
def cb_points_channels(call: CallbackQuery):
    channels = db.get_points_channels()
    if not channels:
        edit(call, "<b>قنوات النقاط</b>\n\nلا توجد قنوات حالياً.",
             kb.back("collect_section"))
        return
    text = "<b>اشترك في القنوات واكسب نقاط!</b>\n\n<b>━━━━━━━━━━━━━━━</b>\n"
    for ch in channels:
        text += f"  {ch['channel_name']}  —  +{ch['points_reward']} نقطة\n"
    text += "<b>━━━━━━━━━━━━━━━</b>\n\n<i>اشترك ثم اضغط جمّعت نقاطي</i>"
    edit(call, text, kb.points_ch_keyboard(channels))


@bot.callback_query_handler(func=lambda c: c.data == "collect_pts_now")
def cb_collect_pts(call: CallbackQuery):
    uid = call.from_user.id
    earned = 0
    for ch in db.get_points_channels():
        if db.has_channel_pts(uid, ch["channel_id"]):
            continue
        try:
            m = bot.get_chat_member(ch["channel_id"], uid)
            if m.status not in ("left", "kicked"):
                db.add_points(uid, ch["points_reward"])
                db.mark_channel_pts(uid, ch["channel_id"])
                earned += ch["points_reward"]
        except:
            pass
    msg = f"حصلت على {earned:,} نقطة! 🎉" if earned > 0 else "لم تحصل على نقاط جديدة."
    bot.answer_callback_query(call.id, msg, show_alert=True)
    cb_collect(call)


# ─── الاشتراك الإجباري ────────────────────────────────────────
@bot.callback_query_handler(func=lambda c: c.data.startswith("check_sub_"))
def cb_check_sub(call: CallbackQuery):
    uid = call.from_user.id
    ok, missing = check_subs(uid)
    if ok:
        bot.answer_callback_query(call.id, "تم التحقق! أهلاً بك. ✅", show_alert=True)
        # تسجيل الإحالة بعد اجتياز الاشتراك الإجباري
        result = db.complete_referral(uid)
        if result:
            referred_by, ref_pts = result
            user = db.get_user(uid)
            try:
                bot.send_message(referred_by,
                    f"<b>🎉 إحالة مكتملة!</b>\n\n"
                    f"{user['full_name']} اشترك في القنوات وأصبح عضواً.\n"
                    f"حصلت على <b>{ref_pts:,}</b> نقطة!")
            except:
                pass
        # معالجة هدية مؤجلة (لو المستخدم جه عبر رابط هدية وكانت فيه قنوات إجبارية)
        pending = get_state(uid)
        if pending.get("state") == "pending_gift":
            gift_code = pending.get("data", {}).get("gift_code", "")
            clear_state(uid)
            if gift_code:
                ok2, pts, err = db.claim_gift_link(uid, gift_code)
                if ok2:
                    try:
                        bot.send_message(uid,
                            f"<b>🎁 تهانينا! استلمت هديتك!</b>\n\n"
                            f"حصلت على <b>{pts:,}</b> نقطة! 🎉")
                        # إشعار الأدمن
                        user_obj = db.get_user(uid)
                        _notify_admins_gift_claim_db(uid, user_obj, gift_code, pts)
                    except:
                        pass
        cb_back_main(call)
    else:
        bot.answer_callback_query(call.id, f"لم تشترك بعد في {len(missing)} قناة!", show_alert=True)


# ══════════════════════════════════════════════════════════════════
#   9. الخدمات المجانية
# ══════════════════════════════════════════════════════════════════
@bot.callback_query_handler(func=lambda c: c.data == "free_services")
def cb_free_services(call: CallbackQuery):
    if db.get_config("free_svc_enabled", "1") == "0":
        edit(call, "<b>🎁 الخدمات المجانية</b>\n\nهذا القسم متوقف حالياً.", kb.back("my_services"))
        return
    services = db.get_free_services()
    if not services:
        edit(call, "<b>🎁 الخدمات المجانية</b>\n\nلا توجد خدمات متاحة حالياً.", kb.back("my_services"))
        return
    daily_limit = int(db.get_config("free_services_daily_limit", "3"))
    used_today = db.get_free_claim_count_today_total(call.from_user.id)
    if used_today >= daily_limit:
        edit(call,
            "<b>🎁 الخدمات المجانية</b>\n\n"
            f"⚠️ استنفدت حد اليوم ({daily_limit} مرات).\n"
            "عد غداً للمحاولة مجدداً.",
            kb.back("my_services"))
        return
    # تسجيل دخول القسم كمرة استخدام
    db.add_free_claim(call.from_user.id, 0, 0, "", "", "section_visit")
    used_today += 1
    remaining = max(daily_limit - used_today, 0)
    edit(call,
        "<b>🎁 الخدمات المجانية</b>\n\n"
        "<b>━━━━━━━━━━━━━━━</b>\n"
        f"حد الاستخدام اليومي للمستخدم: <b>{daily_limit}</b> مرة\n"
        f"المتبقي اليوم: <b>{remaining}</b> مرة\n"
        "<b>━━━━━━━━━━━━━━━</b>\n"
        "اختر الخدمة المجانية المطلوبة.\n"
        "يمكنك استخدام خدمة مجانية واحدة فقط في اليوم.\n"
        "<b>━━━━━━━━━━━━━━━</b>",
        kb.free_services_menu(services, back_cb="my_services"))


@bot.callback_query_handler(func=lambda c: c.data.startswith("free_svc_"))
def cb_free_svc_select(call: CallbackQuery):
    sid = int(call.data.split("_")[-1])
    svc = db.get_free_service(sid)
    if not svc:
        bot.answer_callback_query(call.id, "الخدمة غير موجودة")
        return

    uid = call.from_user.id
    set_state(uid, "free_svc_link", svc_id=sid)
    edit(call,
        f"<b>{svc['name']}</b>\n\n"
        f"<b>━━━━━━━━━━━━━━━</b>\n"
        f"الوصف: {svc['description'] or '—'}\n"
        f"الكمية: من {svc['min_qty']:,} إلى {svc['max_qty']:,}\n"
        f"<b>━━━━━━━━━━━━━━━</b>\n\n"
        f"<b>الخطوة 1:</b> أرسل الرابط المطلوب:",
        kb.back("free_services"))


@bot.message_handler(func=lambda m: get_state(m.from_user.id).get("state") == "free_svc_link")
def msg_free_svc_link(msg: Message):
    link = msg.text.strip() if msg.text else ""
    if not (link.startswith("http") or link.startswith("@") or "t.me" in link):
        send(msg.chat.id, "⚠️ الرابط غير صحيح! أرسل رابطاً صحيحاً:")
        return
    d = get_state(msg.from_user.id)["data"]
    svc = db.get_free_service(d["svc_id"])
    if not svc:
        send(msg.chat.id, "الخدمة غير موجودة!")
        clear_state(msg.from_user.id)
        return
    set_state(msg.from_user.id, "free_svc_qty", svc_id=d["svc_id"], link=link)
    send(msg.chat.id,
        f"الرابط: <code>{link}</code>\n\n"
        f"<b>الخطوة 2:</b> أرسل الكمية (من {svc['min_qty']:,} إلى {svc['max_qty']:,}):",
        kb.back("free_services"))


@bot.message_handler(func=lambda m: get_state(m.from_user.id).get("state") == "free_svc_qty")
def msg_free_svc_qty(msg: Message):
    try:
        qty = int((msg.text or "").strip().replace(",", ""))
    except:
        send(msg.chat.id, "⚠️ أرسل رقماً صحيحاً!")
        return
    d = get_state(msg.from_user.id)["data"]
    svc = db.get_free_service(d["svc_id"])
    if not svc:
        send(msg.chat.id, "الخدمة غير موجودة!")
        clear_state(msg.from_user.id)
        return
    service_type = (svc.get("service_type") or "عام").strip()
    is_reaction_service = service_type in ("قلب", "تفاعل")
    if is_reaction_service:
        if qty != 1:
            send(msg.chat.id, "⚠️ خدمة التفاعل بالحساب المركزي تنفذ تفاعلاً واحداً لكل منشور، لذلك الكمية يجب أن تكون 1.")
            return
    elif qty < svc["min_qty"] or qty > svc["max_qty"]:
        send(msg.chat.id, f"⚠️ الكمية بين {svc['min_qty']:,} و {svc['max_qty']:,}!")
        return

    uid = msg.from_user.id
    result = {"error": "الخدمات المجانية الخارجية غير متاحة في النسخة المحلية."}
    api_id = str(result.get("order", ""))
    err = result.get("error")

    if err:
        db.add_free_claim(uid, svc["id"], qty, d["link"], "", "failed")
        send(msg.chat.id, f"<b>❌ فشل الطلب!</b>\n\n{err}\n\n<i>تم احتساب هذه المحاولة من حدك اليومي</i>", kb.back("free_services"))
    else:
        db.add_free_claim(uid, svc["id"], qty, d["link"], api_id, "inprogress")
        send(msg.chat.id,
            f"<b>✅ تم إرسال الطلب المجاني!</b>\n\n"
            f"<b>━━━━━━━━━━━━━━━</b>\n"
            f"الخدمة: {svc['name']}\n"
            f"الكمية: {qty:,}\n"
            f"رقم API: <code>{api_id or 'معلق'}</code>\n"
            f"<b>━━━━━━━━━━━━━━━</b>",
            kb.back("free_services"))
    clear_state(uid)


# ══════════════════════════════════════════════════════════════════
#   10. خدماتي (الأقسام)
# ══════════════════════════════════════════════════════════════════
@bot.callback_query_handler(func=lambda c: c.data == "my_services")
def cb_my_services(call: CallbackQuery):
    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass
    try:
        apps = db.get_apps(only_active=True)
        free_services_available = False
        try:
            free_enabled = db.get_config("free_svc_enabled", "1") == "1"
            if free_enabled:
                free_services_available = bool(db.get_free_services())
        except Exception as free_error:
            print(f"[MY_SERVICES] free services unavailable: {free_error}")

        # حتى لو مفيش أي خدمة، الزر يستجيب ويعرض رسالة واضحة بدل ما يبدو كأنه لا يعمل.
        if not apps and not free_services_available:
            edit(call,
                 "<b>🛠️ خدماتي</b>\n\n"
                 "⚠️ مفيش خدمات متاحة حالياً.\n"
                 "ارجع لاحقاً بعد إضافة الخدمات.",
                 kb.back("back_main"))
            return

        user = db.get_user(call.from_user.id)
        points = int(user["points"] if user else 0)
        edit(call,
             f"<b>🛠️ خدماتي</b> — اختر القسم\n\n"
             f"<b>━━━━━━━━━━━━━━━</b>\n"
             f"رصيدك: <b>{points:,}</b> نقطة\n"
             f"<b>━━━━━━━━━━━━━━━</b>",
             kb.apps_keyboard(apps, include_free=free_services_available))
    except Exception as e:
        print(f"[MY_SERVICES] error: {e}")
        edit(call,
             "<b>🛠️ خدماتي</b>\n\n"
             "❌ حصل خطأ أثناء تحميل الخدمات. حاول مرة ثانية.",
             kb.back("back_main"))


@bot.callback_query_handler(func=lambda c: c.data == "my_services_free")
def cb_my_services_free(call: CallbackQuery):
    if db.get_config("free_svc_enabled", "1") == "0":
        edit(call, "<b>🎁 الخدمات المجانية</b>\n\nهذا القسم متوقف حالياً.", kb.back("my_services"))
        return
    services = db.get_free_services()
    if not services:
        edit(call, "<b>🎁 الخدمات المجانية</b>\n\nلا توجد خدمات متاحة حالياً.", kb.back("my_services"))
        return
    daily_limit = int(db.get_config("free_services_daily_limit", "3"))
    used_today = db.get_free_claim_count_today_total(call.from_user.id)
    if used_today >= daily_limit:
        edit(call,
            "<b>🎁 الخدمات المجانية</b>\n\n"
            f"⚠️ استنفدت حد اليوم ({daily_limit} مرات).\n"
            "عد غداً للمحاولة مجدداً.",
            kb.back("my_services"))
        return
    # تسجيل دخول القسم كمرة استخدام
    db.add_free_claim(call.from_user.id, 0, 0, "", "", "section_visit")
    used_today += 1
    remaining = max(daily_limit - used_today, 0)
    edit(call,
        "<b>🎁 الخدمات المجانية</b>\n\n"
        "<b>━━━━━━━━━━━━━━━</b>\n"
        f"حد الاستخدام اليومي للمستخدم: <b>{daily_limit}</b> مرة\n"
        f"المتبقي اليوم: <b>{remaining}</b> مرة\n"
        "<b>━━━━━━━━━━━━━━━</b>\n"
        "اختر الخدمة المجانية المطلوبة.\n"
        "يمكنك استخدام خدمة مجانية واحدة فقط في اليوم.\n"
        "<b>━━━━━━━━━━━━━━━</b>",
        kb.free_services_menu(services, back_cb="my_services"))


@bot.callback_query_handler(func=lambda c: c.data == "adm_pending_orders_placeholder")
def _placeholder(call):
    pass


@bot.callback_query_handler(func=lambda c: c.data.startswith("app_") and c.data[4:].isdigit())
def cb_open_app(call: CallbackQuery):
    try: bot.answer_callback_query(call.id)
    except Exception: pass
    try:
        app_id = int(call.data.split("_")[1])
    except:
        return
    app = db.get_app(app_id)
    if not app:
        bot.answer_callback_query(call.id, "القسم غير موجود")
        return
    services = db.get_app_services(app_id)
    user = db.get_user(call.from_user.id)
    if not services:
        edit(call, f"<b>{app['name']}</b>\n\nلا توجد خدمات في هذا القسم.",
             kb.back("my_services"))
        return
    nm = f"{app['emoji']} {app['name']}" if app.get("emoji") else app['name']
    edit(call,
        f"<b>{nm}</b>\n\n"
        f"<b>━━━━━━━━━━━━━━━</b>\n"
        f"رصيدك: <b>{user['points']:,}</b> نقطة\n"
        f"السعر: بالنقاط لكل 1000 وحدة\n"
        f"<b>━━━━━━━━━━━━━━━</b>",
        kb.app_services_keyboard(app_id, services))


@bot.callback_query_handler(func=lambda c: c.data.startswith("adm_test_svc_"))
def cb_adm_test_svc(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    try:
        sid = int(call.data.rsplit("_", 1)[-1])
    except Exception:
        bot.answer_callback_query(call.id, "الخدمة غير صحيحة", show_alert=True)
        return
    svc = db.get_service(sid)
    if not svc:
        bot.answer_callback_query(call.id, "الخدمة غير موجودة", show_alert=True)
        return
    if (svc.get("service_type") or "") not in ("قلب", "تفاعل"):
        bot.answer_callback_query(call.id, "التجربة متاحة لخدمات التفاعل فقط", show_alert=True)
        return
    set_state(call.from_user.id, "adm_test_svc_link", svc_id=sid, app_id=svc["app_id"])
    bot.answer_callback_query(call.id)
    edit(call,
         f"<b>🧪 تجربة: {svc['name']}</b>\n\n"
         "أرسل <b>رابط المنشور فقط</b>، وليس رابط القناة.\n\n"
         "<b>منشور عام:</b>\n<code>https://t.me/PUBGCOREFLLES/123</code>\n\n"
         "<b>منشور خاص:</b>\n<code>https://t.me/c/1234567890/123</code>\n\n"
         "حساب التنفيذ يجب أن يكون لديه صلاحية الوصول للمنشور الخاص.",
         kb.back(f"adm_service_manage_{sid}"))


@bot.message_handler(func=lambda m: get_state(m.from_user.id).get("state") == "adm_test_svc_link")
def msg_adm_test_svc_link(msg: Message):
    uid = msg.from_user.id
    if not is_admin(uid):
        return
    link = (msg.text or "").strip()
    d = get_state(uid)["data"]
    svc = db.get_service(d.get("svc_id"))
    if not svc:
        clear_state(uid)
        send(msg.chat.id, "❌ الخدمة غير موجودة.")
        return
    try:
        peer, msg_id = _parse_telegram_message_link(link)
    except Exception as e:
        send(msg.chat.id,
             "❌ رابط المنشور غير صحيح.\n\n"
             "أرسل رابط منشور عام مثل:\n"
             "<code>https://t.me/PUBGCOREFLLES/123</code>\n\n"
             "أو خاص مثل:\n"
             "<code>https://t.me/c/1234567890/123</code>\n\n"
             f"الخطأ: <code>{str(e)[:250]}</code>")
        return

    account = db.get_service_telegram_account(svc)
    if not account:
        send(msg.chat.id, "❌ لا يوجد حساب تنفيذ مرتبط بالخدمة. أضف حساب Telegram أولاً.")
        clear_state(uid)
        return

    set_state(uid, "adm_test_svc_running", svc_id=svc["id"], link=link)
    send(msg.chat.id,
         f"⏳ جاري تجربة الخدمة على المنشور...\n\n"
         f"الخدمة: <b>{svc['name']}</b>\n"
         f"الرابط: <code>{link}</code>\n"
         f"المنشور: <code>{msg_id}</code>")

    def _run_test():
        try:
            fake_order = {"link": link, "id": 0}
            used_emoji = _execute_telegram_reaction(fake_order, svc)
            send(msg.chat.id,
                 f"<b>✅ تم تنفيذ التجربة بنجاح</b>\n\n"
                 f"الخدمة: <b>{svc['name']}</b>\n"
                 f"الإيموجي: <b>{used_emoji}</b>\n"
                 f"الرابط: <code>{link}</code>")
        except Exception as e:
            send(msg.chat.id,
                 f"<b>❌ فشلت التجربة</b>\n\n"
                 f"<code>{str(e)[:700]}</code>\n\n"
                 "تأكد أن حساب التنفيذ يستطيع الوصول للمنشور، خصوصاً إذا كان الرابط خاصاً.")
        finally:
            clear_state(uid)

    threading.Thread(target=_run_test, daemon=True).start()


@bot.callback_query_handler(func=lambda c: (c.data.startswith("svc_") or c.data.startswith("store_svc_")) and not c.data.startswith("svc_continue_") and not c.data.startswith("svc_confirm_") and not c.data.startswith("svc_cancel_"))
def cb_open_service(call: CallbackQuery):
    try: bot.answer_callback_query(call.id)
    except Exception: pass
    try:
        sid = int(call.data.rsplit("_", 1)[1])
    except Exception:
        return
    back_target = "store" if call.data.startswith("store_svc_") else f"app_"
    svc = db.get_service(sid)
    if not svc:
        try: bot.answer_callback_query(call.id, "الخدمة غير موجودة", show_alert=True)
        except Exception: pass
        return

    user = db.get_user(call.from_user.id)
    p1k = float(svc.get("points_per_1000") or 0)
    service_type = (svc.get("service_type") or "عام").strip()
    is_reaction = service_type in ("قلب", "تفاعل")

    if is_reaction:
        accounts = db.get_service_telegram_accounts(sid)
        if not accounts:
            legacy = db.get_service_telegram_account(svc)
            accounts = [legacy] if legacy else []
        if not accounts:
            edit(call, "❌ الخدمة غير جاهزة: لا يوجد حساب Telegram مرتبط بها.", kb.back("store" if call.data.startswith("store_svc_") else f"app_{svc['app_id']}"))
            return
        mn, mx = 1, len(accounts)
    else:
        mn = int(svc.get("min_qty") or 1)
        mx = int(svc.get("max_qty") or 100000)

    balance = int(user["points"] or 0)
    max_by_points = int((balance * 1000) // p1k) if p1k > 0 else mx
    max_allowed = min(mx, max_by_points)
    nm = f"{svc['emoji']} {svc['name']}" if svc.get('emoji') else svc['name']

    set_state(call.from_user.id, "svc_qty", svc_id=sid, app_id=svc["app_id"])
    edit(
        call,
        f"<b>{nm}</b>\n\n"
        f"<blockquote>"
        f"💰 <b>السعر:</b> {p1k:g} نقطة لكل 1000\n"
        f"📦 <b>أقل كمية:</b> {mn:,}\n"
        f"📦 <b>أعلى كمية:</b> {mx:,}\n"
        f"💳 <b>رصيدك:</b> {balance:,} نقطة\n"
        f"✅ <b>المتاح لك:</b> {max_allowed:,}\n"
        f"⏱ <b>وقت البدء:</b> في الخلفية"
        f"</blockquote>\n\n"
        f"🔹 أرسل <b>الكمية المطلوبة</b>:",
        kb.back("store" if call.data.startswith("store_svc_") else f"app_{svc['app_id']}"),
    )


@bot.callback_query_handler(func=lambda c: c.data.startswith("svc_continue_"))
def cb_svc_continue(call: CallbackQuery):
    try: bot.answer_callback_query(call.id)
    except Exception: pass
    try:
        sid = int(call.data.split("_")[-1])
    except Exception:
        return
    svc = db.get_service(sid)
    if not svc:
        bot.answer_callback_query(call.id, "الخدمة غير موجودة", show_alert=True)
        return
    user = db.get_user(call.from_user.id)
    p1k = float(svc.get("points_per_1000") or 0)
    st = (svc.get("service_type") or "عام").strip()
    is_reaction = st in ("قلب", "تفاعل")
    if is_reaction:
        accounts = db.get_service_telegram_accounts(sid)
        if not accounts:
            legacy = db.get_service_telegram_account(svc)
            accounts = [legacy] if legacy else []
        if not accounts:
            edit(call, "❌ الخدمة غير جاهزة: لا يوجد حساب Telegram مرتبط بها.", kb.back(f"app_{svc['app_id']}"))
            return
        mn, mx = 1, len(accounts)
    else:
        mn, mx = int(svc.get("min_qty") or 1), int(svc.get("max_qty") or 100000)
    max_by_points = int((user["points"] * 1000) // p1k) if p1k > 0 else mx
    max_allowed = min(mx, max_by_points)
    set_state(call.from_user.id, "svc_qty", svc_id=sid, app_id=svc["app_id"])
    edit(call,
         f"<b>🚀 {svc['name']}</b>\n\n"
         f"💰 السعر: <b>{p1k:g}</b> نقطة / 1000\n"
         f"📦 الحد: <b>{mn:,} — {mx:,}</b>\n"
         f"💳 رصيدك: <b>{user['points']:,}</b> نقطة\n"
         f"✅ تقدر تستخدم حتى: <b>{max_allowed:,}</b>\n\n"
         f"أرسل <b>الكمية المطلوبة</b>:",
         kb.back(f"app_{svc['app_id']}"))


@bot.message_handler(func=lambda m: get_state(m.from_user.id).get("state") == "svc_qty")
def msg_svc_qty(msg: Message):
    try:
        qty = int((msg.text or "").strip().replace(",", ""))
    except Exception:
        send(msg.chat.id, "⚠️ أرسل رقم الكمية فقط.")
        return
    d = get_state(msg.from_user.id).get("data", {})
    svc = db.get_service(d.get("svc_id"))
    if not svc:
        clear_state(msg.from_user.id); send(msg.chat.id, "❌ الخدمة غير موجودة."); return
    st = (svc.get("service_type") or "عام").strip()
    is_reaction = st in ("قلب", "تفاعل")
    if is_reaction:
        accounts = db.get_service_telegram_accounts(svc["id"])
        if not accounts:
            legacy = db.get_service_telegram_account(svc); accounts = [legacy] if legacy else []
        mn, mx = 1, len(accounts)
    else:
        mn, mx = int(svc.get("min_qty") or 1), int(svc.get("max_qty") or 100000)
    user = db.get_user(msg.from_user.id)
    p1k = float(svc.get("points_per_1000") or 0)
    max_by_points = int((user["points"] * 1000) // p1k) if p1k > 0 else mx
    max_allowed = min(mx, max_by_points)
    if qty < mn or qty > mx:
        send(msg.chat.id, f"⚠️ الكمية لازم تكون من <b>{mn:,}</b> إلى <b>{mx:,}</b>.")
        return
    if qty > max_allowed:
        need = math.ceil(qty * p1k / 1000) if p1k else 0
        send(msg.chat.id, f"⚠️ رصيدك لا يكفي. تحتاج <b>{need:,}</b> نقطة، ورصيدك <b>{user['points']:,}</b>.")
        return
    pts = math.ceil(qty * p1k / 1000) if p1k else 0
    set_state(msg.from_user.id, "svc_link", svc_id=svc["id"], app_id=svc["app_id"], qty=qty, pts_needed=pts)
    send(msg.chat.id,
         f"<b>📦 الكمية:</b> {qty:,}\n"
         f"<b>💰 التكلفة:</b> {pts:,} نقطة\n\n"
         f"أرسل الآن <b>رابط المنشور</b>:",
         kb.back(f"app_{svc['app_id']}"))


@bot.message_handler(func=lambda m: get_state(m.from_user.id).get("state") == "svc_link")
def msg_svc_link(msg: Message):
    link = (msg.text or "").strip()
    if not (link.startswith("http") or "t.me" in link or link.startswith("@")):
        send(msg.chat.id, "⚠️ الرابط غير صحيح!")
        return

    d = get_state(msg.from_user.id).get("data", {})
    svc = db.get_service(d.get("svc_id"))
    if not svc:
        clear_state(msg.from_user.id)
        send(msg.chat.id, "❌ الخدمة غير موجودة.")
        return

    duplicate = db.get_duplicate_order(msg.from_user.id, svc["id"], link)
    if duplicate:
        clear_state(msg.from_user.id)
        send(
            msg.chat.id,
            f"❌ <b>هذا الطلب موجود بالفعل</b>\n\n"
            f"🧾 الخدمة: <b>{svc['name']}</b>\n"
            f"🔗 الرابط: <code>{link}</code>\n"
            f"🆔 الطلب: <b>{duplicate.get('public_id') or duplicate['id']}</b>",
            kb.back(f"app_{svc['app_id']}"),
        )
        return

    qty = int(d.get("qty") or 0)
    pts = int(d.get("pts_needed") or 0)
    if qty <= 0:
        clear_state(msg.from_user.id)
        send(msg.chat.id, "❌ انتهت جلسة الطلب، ابدأ من جديد.")
        return

    # إنشاء الطلب أولاً لإظهار رقم الطلب للمستخدم، بدون خصم النقاط وبدون تشغيل التنفيذ.
    try:
        user = db.get_user(msg.from_user.id)
        if not user or int(user["points"] or 0) < pts:
            send(msg.chat.id, "❌ نقاطك غير كافية.", kb.back(f"app_{svc['app_id']}"))
            return

        charge = round((qty / 1000) * float(svc.get("rate_per_1000") or 0.5), 5)
        app = db.get_app(svc["app_id"])
        app_nm = f"{app['emoji']} {app['name']}" if app and app.get("emoji") else (app['name'] if app else "")
        oid = db.create_order(
            msg.from_user.id, str(svc["id"]), svc["name"], link, qty, charge, pts,
            None, app_nm, svc.get("site_id"), pending_approval=0
        )
        row = db.get_order(oid)
        public_oid = (row.get("public_id") if row and hasattr(row, "get") else None) or str(oid)

        set_state(
            msg.from_user.id,
            "svc_confirm",
            svc_id=svc["id"], app_id=svc["app_id"], oid=oid,
            public_oid=public_oid, qty=qty, pts_needed=pts, link=link,
        )

        send(
            msg.chat.id,
            f"<b>📦 طلب جديد</b>\n\n"
            f"🆔 رقم الطلب: <b>{public_oid}</b>\n"
            f"🛍️ اسم الخدمة: <b>{svc['name']}</b>\n"
            f"📦 العدد: <b>{qty:,}</b>\n"
            f"🪙 السعر: <b>{pts:,} نقطة</b>\n\n"
            f"اختر الإجراء:",
            mk(
                [_btn("✅ تأكيد الطلب", f"svc_confirm_{oid}", color="green")],
                [_btn("❌ إلغاء الطلب", f"svc_cancel_{oid}", color="red")],
            ),
        )
    except Exception as e:
        print(f"[ORDER PREPARE] {type(e).__name__}: {e}")
        send(msg.chat.id, "❌ حصل خطأ أثناء تجهيز الطلب، حاول مرة أخرى.", kb.back(f"app_{svc['app_id']}"))


@bot.callback_query_handler(func=lambda c: c.data.startswith("svc_confirm_") and c.data[12:].isdigit())
def cb_svc_confirm(call: CallbackQuery):
    uid = call.from_user.id
    oid = int(call.data[12:])
    state = get_state(uid)
    d = state.get("data", {})

    if state.get("state") != "svc_confirm" or int(d.get("oid") or 0) != oid:
        bot.answer_callback_query(call.id, "انتهت جلسة الطلب، ابدأ من جديد.", show_alert=True)
        return

    try: bot.answer_callback_query(call.id, "تم تأكيد الطلب")
    except Exception: pass

    svc = db.get_service(d.get("svc_id"))
    order = db.get_order(oid)
    if not svc or not order or int(order["user_id"]) != uid or order["status"] != "pending":
        clear_state(uid)
        edit(call, "❌ الطلب غير متاح أو تم إلغاؤه.", kb.back(f"app_{d.get('app_id')}"))
        return

    pts = int(d.get("pts_needed") or order["points_used"] or 0)
    if not db.deduct_points(uid, pts):
        clear_state(uid)
        db.cancel_unconfirmed_order(oid, uid)
        edit(call, "❌ نقاطك غير كافية، تم إلغاء الطلب.", kb.back(f"app_{d.get('app_id')}"))
        return

    clear_state(uid)
    # لا نجعل الموافقة أو إشعار الطلبات أو تشغيل الخدمة يمسك مسار زر المستخدم.
    # الزر يرد فوراً، وبعدها Worker مستقل يعتمد الطلب ويضعه في Queue.
    edit(
        call,
        f"🚀 <b>جاري تنفيذ طلبك...</b>\n\n"
        f"🆔 الطلب: <b>{d.get('public_oid') or oid}</b>\n"
        f"🛍️ الخدمة: <b>{svc['name']}</b>\n"
        f"📦 العدد: <b>{int(d.get('qty') or order['quantity']):,}</b>\n"
        f"🪙 السعر: <b>{pts:,} نقطة</b>\n\n"
        f"⚙️ التنفيذ يعمل الآن في الخلفية.",
        kb.back("back_main"),
    )

    def _start_order_background():
        try:
            # طلبات الخدمات لا تحتاج موافقة أدمن: تم إنشاؤها أصلاً
            # بـ pending_approval=0، وبعد تأكيد المستخدم تدخل مباشرةً للـQueue.
            app = db.get_app(svc["app_id"])
            app_nm = f"{app['emoji']} {app['name']}" if app and app.get("emoji") else (app['name'] if app else "")
            user = db.get_user(uid)
            try:
                threading.Thread(
                    target=notify_order_channels,
                    args=(oid, dict(user), svc["name"], app_nm, order["link"], int(order["quantity"]), pts),
                    daemon=True,
                ).start()
            except Exception:
                pass
            enqueue_service_order(oid)
        except Exception as e:
            print(f"[ORDER BACKGROUND START] {type(e).__name__}: {e}")
            try:
                if db.fail_order_and_refund(oid):
                    bot.send_message(uid, "❌ تعذر بدء تنفيذ الطلب، وتم استرجاع النقاط.")
            except Exception as refund_error:
                print(f"[ORDER BACKGROUND REFUND] {refund_error}")

    threading.Thread(target=_start_order_background, name=f"order-start-{oid}", daemon=True).start()


@bot.callback_query_handler(func=lambda c: c.data.startswith("svc_cancel_") and c.data[11:].isdigit())
def cb_svc_cancel(call: CallbackQuery):
    uid = call.from_user.id
    oid = int(call.data[11:])
    state = get_state(uid)
    d = state.get("data", {})
    if state.get("state") != "svc_confirm" or int(d.get("oid") or 0) != oid:
        bot.answer_callback_query(call.id, "انتهت جلسة الطلب.", show_alert=True)
        return
    try: bot.answer_callback_query(call.id, "تم إلغاء الطلب")
    except Exception: pass
    db.cancel_unconfirmed_order(oid, uid)
    clear_state(uid)
    edit(call, "❌ <b>تم إلغاء الطلب.</b>\n\nلم يتم خصم أي نقاط.", kb.back(f"app_{d.get('app_id')}"))


@bot.callback_query_handler(func=lambda c: c.data == "order_confirm")
def cb_order_confirm(call: CallbackQuery):
    state = get_state(call.from_user.id)
    s = state.get("state")
    d = state.get("data", {})
    if s == "svc_confirm":
        _do_svc_order(call, d)
    elif s == "fund_confirm":
        _do_fund_order(call, d)
    else:
        bot.answer_callback_query(call.id, "انتهت الجلسة، ابدأ من جديد.")


def _do_svc_order(call, d):
    svc = db.get_service(d["svc_id"])
    if not svc:
        bot.answer_callback_query(call.id, "الخدمة غير متاحة")
        return
    pts = d["pts_needed"]
    qty = d["qty"]
    if not db.deduct_points(call.from_user.id, pts):
        bot.answer_callback_query(call.id, "نقاطك غير كافية!", show_alert=True)
        return
    charge = round((qty / 1000) * float(svc["rate_per_1000"] or 0.5), 5)
    site_id = svc.get("site_id")
    app = db.get_app(svc["app_id"])
    app_nm = f"{app['emoji']} {app['name']}" if app and app.get("emoji") else (app['name'] if app else "")
    oid = db.create_order(call.from_user.id, str(svc["id"]), svc["name"],
                          d["link"], qty, charge, pts, None, app_nm, site_id)
    order_row = db.get_order(oid)
    public_oid = (order_row.get("public_id") if order_row and hasattr(order_row, "get") else None) or str(oid)
    clear_state(call.from_user.id)

    # اعرض التأكيد للمستخدم أولاً؛ لا نجعل إرسال إشعار قناة الطلبات
    # يحجز WorkerThread قبل بدء التنفيذ.
    edit(call,
        f"<b>🚀 جاري تنفيذ طلبك...</b>\n\n"
        f"رقم الطلب: <b>{public_oid}</b>\n"
        f"نوع الخدمة: <b>{svc.get('service_type') or 'عام'}</b>\n"
        f"اسم الخدمة: <b>{svc['name']}</b>\n"
        f"🆔 ID الخدمة: <code>{svc.get('public_id') or svc['id']}</code>\n"
        f"رقم المستخدم: <code>{call.from_user.id}</code>\n"
        f"الرابط: <code>{d['link']}</code>\n"
        f"الكمية: <b>{qty:,}</b>\n"
        f"النقاط: <b>{pts:,}</b>\n\n"
        f"<i>سيبدأ التنفيذ بعد لحظات...</i>", kb.back())

    # لا تجعل إشعار قناة الطلبات يؤخر تنفيذ الخدمة أو استجابة زر المستخدم.
    try:
        user = db.get_user(call.from_user.id)
        threading.Thread(
            target=notify_order_channels,
            args=(oid, dict(user), svc["name"], app_nm, d["link"], qty, pts),
            daemon=True,
        ).start()
    except Exception as e:
        print(f"[ORDER] notify thread error: {e}")

    db.approve_order(oid)

    # التنفيذ في الخلفية فوراً؛ لا نؤخر استجابة المستخدم بعد تأكيد الطلب.
    enqueue_service_order(oid)

# ══════════════════════════════════════════════════════════════════
#   11. تمويل قناة / جروب
POINTS_PRICE_TABLE = (
    "💎 <b>جدول أسعار النقاط:</b>\n"
    "━━━━━━━━━━━━━━━\n"
    "- 10,000 نقطة = <b>$1</b>\n"
    "- 20,000 نقطة = <b>$2</b>\n"
    "- 30,000 نقطة = <b>$3</b>\n"
    "- 40,000 نقطة = <b>$4</b>\n"
    "- 50,000 نقطة = <b>$5</b>\n"
    "- 100,000 نقطة = <b>$10</b>\n"
    "- 200,000 نقطة = <b>$20</b>\n"
    "- 500,000 نقطة = <b>$50</b>\n"
    "- 1,500,000 نقطة = <b>$150</b>\n"
    "━━━━━━━━━━━━━━━\n"
    "✅ يمكنك شحن حتى <b>100M نقطة</b>"
)

# ══════════════════════════════════════════════════════════════════
@bot.callback_query_handler(func=lambda c: c.data == "fund_start")
def cb_fund_start(call: CallbackQuery):
    edit(call,
        f"<b>💳 شحن مباشر</b>\n\n"
        f"{POINTS_PRICE_TABLE}\n\n"
        f"اختر طريقة الشحن:",
        mk(
            [_btn("💵 فودافون كاش", "charge_vodafone", color="green")],
            [_btn("⭐ نجوم",        "charge_stars",    color="blue")],
            [_btn("◀️ رجوع",       "back_main",        color="blue")],
        ))

@bot.callback_query_handler(func=lambda c: c.data == "charge_vodafone")
def cb_charge_vodafone(call: CallbackQuery):
    info = db.get_config("charge_vodafone_info", "فودافون كاش: 0123456789")
    set_state(call.from_user.id, "await_vodafone_receipt")
    edit(call,
        f"<b>💵 الشحن بفودافون كاش</b>\n\n"
        f"{POINTS_PRICE_TABLE}\n\n"
        f"<b>━━━━━━━━━━━━━━━</b>\n"
        f"1️⃣ حوّل المبلغ على:\n"
        f"<b>{info}</b>\n\n"
        f"2️⃣ بعد التحويل أرسل <b>صورة الإيصال</b> هنا\n\n"
        f"<b>━━━━━━━━━━━━━━━</b>\n"
        f"<i>⚠️ الإيصالات الوهمية تؤدي لحظر الحساب</i>",
        kb.back("back_main"))


@bot.message_handler(content_types=["photo"],
    func=lambda m: get_state(m.from_user.id).get("state") == "await_vodafone_receipt")
def msg_vodafone_receipt(msg: Message):
    uid = msg.from_user.id
    photo_id = msg.photo[-1].file_id
    rid = db.create_recharge_request(uid, "vodafone", photo_id)
    user = db.get_user(uid)
    clear_state(uid)

    send(msg.chat.id,
        f"<b>✅ تم استلام إيصالك!</b>\n\n"
        f"رقم الطلب: <b>#{rid}</b>\n\n"
        f"<i>سيتم مراجعته وشحن رصيدك قريباً</i>",
        kb.back("back_main"))

    # إشعار الأدمن
    caption = (
        f"<b>💵 طلب شحن جديد #{rid}</b>\n\n"
        f"المستخدم: {user['full_name']} (<code>{uid}</code>)\n"
        f"الطريقة: فودافون كاش\n"
        f"التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    )
    markup = mk(
        [_btn("✅ شحن النقاط", f"adm_recharge_approve_{rid}", color="green")],
        [_btn("❌ رفض الطلب",  f"adm_recharge_reject_{rid}",  color="red")],
    )
    all_admins = list(config.ADMIN_IDS) + [a["tg_id"] for a in db.get_extra_admins()]
    for aid in all_admins:
        try:
            bot.send_photo(aid, photo_id, caption=caption,
                           reply_markup=markup, parse_mode="HTML")
        except Exception as e:
            print(f"[recharge_notify] {aid}: {e}")


# ── الأدمن يختار عدد النقاط للشحن ──────────────────────────
@bot.callback_query_handler(func=lambda c: c.data.startswith("adm_recharge_approve_"))
def cb_adm_recharge_approve(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    rid = int(call.data.split("_")[-1])
    r = db.get_recharge_request(rid)
    if not r:
        bot.answer_callback_query(call.id, "الطلب غير موجود")
        return
    if r["status"] != "pending":
        bot.answer_callback_query(call.id, "الطلب معالج مسبقاً!", show_alert=True)
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
        return
    set_state(call.from_user.id, "adm_recharge_set_pts", rid=rid)
    user = db.get_user(r["user_id"])
    try:
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
    except:
        pass
    send(call.message.chat.id,
        f"<b>💵 شحن طلب #{rid}</b>\n\n"
        f"المستخدم: {user['full_name'] if user else r['user_id']}\n"
        f"رصيده الحالي: <b>{user['points']:,}</b> نقطة\n\n"
        f"كم نقطة تريد شحنها؟\n"
        f"<i>(مثال: 100 أو 500 أو 1000)</i>")


@bot.callback_query_handler(func=lambda c: c.data.startswith("adm_recharge_reject_"))
def cb_adm_recharge_reject(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    rid = int(call.data.split("_")[-1])
    r = db.reject_recharge(rid)
    if not r or r["status"] != "pending":
        bot.answer_callback_query(call.id, "الطلب معالج مسبقاً!", show_alert=True)
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
        return
    bot.answer_callback_query(call.id, "❌ تم رفض الطلب")
    try:
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        bot.edit_message_caption(
            call.message.caption + f"\n\n<b>❌ رفضه: {call.from_user.first_name}</b>",
            call.message.chat.id, call.message.message_id, parse_mode="HTML")
    except:
        pass
    try:
        bot.send_message(r["user_id"],
            f"<b>❌ تم رفض طلب الشحن #{rid}</b>\n\n"
            f"<i>تواصل مع الدعم إذا كنت تعتقد أن هذا خطأ.</i>")
    except:
        pass

# ── قائمة الباقات المتاحة للشراء بالنجوم ──────────────────────
STARS_PACKAGES = [
    (50,   "باقة صغيرة"),
    (100,  "باقة متوسطة"),
    (250,  "باقة كبيرة"),
    (500,  "باقة ممتازة"),
    (1000, "باقة VIP"),
]


@bot.callback_query_handler(func=lambda c: c.data == "charge_stars")
def cb_charge_stars(call: CallbackQuery):
    spp = int(db.get_config("stars_per_point", "10"))
    rows = []
    for stars, label in STARS_PACKAGES:
        pts = stars * spp
        rows.append([_btn(
            f"⭐ {stars:,} نجمة  ←  {pts:,} نقطة  |  {label}",
            f"buy_stars_{stars}", color="blue"
        )])
    rows.append([_btn("◀️ رجوع", "back_main", color="blue")])
    edit(call,
        f"<b>⭐ الشحن التلقائي بالنجوم</b>\n\n"
        f"<b>━━━━━━━━━━━━━━━</b>\n"
        f"نسبة التحويل: <b>1 نجمة = {spp} نقطة</b>\n"
        f"<b>━━━━━━━━━━━━━━━</b>\n\n"
        f"اختر الباقة وادفع مباشرة من تيليجرام ✅\n"
        f"<i>النقاط تُضاف فوراً بعد الدفع</i>",
        mk(*rows))


@bot.callback_query_handler(func=lambda c: c.data.startswith("buy_stars_"))
def cb_buy_stars_package(call: CallbackQuery):
    try:
        stars = int(call.data.split("_")[-1])
    except:
        return
    spp = int(db.get_config("stars_per_point", "10"))
    pts = stars * spp
    label = next((l for s, l in STARS_PACKAGES if s == stars), f"{stars} نجمة")
    try:
        prices = [LabeledPrice(label=f"{pts:,} نقطة", amount=stars)]
        bot.send_invoice(
            chat_id=call.message.chat.id,
            title=f"⭐ {label}",
            description=f"شحن {pts:,} نقطة مقابل {stars:,} نجمة تيليجرام",
            invoice_payload=f"stars_{stars}_{call.from_user.id}",
            provider_token="",          # فارغ للنجوم
            currency="XTR",             # عملة النجوم
            prices=prices,
            start_parameter="stars_pay",
        )
        bot.answer_callback_query(call.id)
    except Exception as e:
        bot.answer_callback_query(call.id, f"خطأ: {e}", show_alert=True)


@bot.pre_checkout_query_handler(func=lambda q: True)
def pre_checkout(query):
    """الموافقة على الدفع تلقائياً"""
    bot.answer_pre_checkout_query(query.id, ok=True)


@bot.message_handler(content_types=["successful_payment"])
def successful_stars_payment(msg: Message):
    """استقبال الدفع الناجح وإضافة النقاط تلقائياً"""
    payment = msg.successful_payment
    payload = payment.invoice_payload  # "stars_{stars}_{uid}"

    if not payload.startswith("stars_"):
        return

    try:
        parts   = payload.split("_")
        stars   = int(parts[1])
        uid     = int(parts[2])
    except:
        return

    spp  = int(db.get_config("stars_per_point", "10"))
    pts  = stars * spp
    db.add_points(uid, pts)

    user = db.get_user(uid)
    send(msg.chat.id,
        f"<b>✅ تم الشحن التلقائي!</b>\n\n"
        f"<b>━━━━━━━━━━━━━━━</b>\n"
        f"النجوم المدفوعة: <b>⭐ {stars:,}</b>\n"
        f"النقاط المضافة: <b>+{pts:,} نقطة</b> 🎉\n"
        f"رصيدك الجديد: <b>{user['points']:,}</b> نقطة\n"
        f"<b>━━━━━━━━━━━━━━━</b>",
        kb.back("back_main"))

    # إشعار الأدمن
    all_admins = list(config.ADMIN_IDS) + [a["tg_id"] for a in db.get_extra_admins()]
    for aid in all_admins:
        try:
            bot.send_message(aid,
                f"<b>⭐ شحن نجوم تلقائي</b>\n\n"
                f"المستخدم: {user['full_name']} (<code>{uid}</code>)\n"
                f"النجوم: {stars:,} ⭐\n"
                f"النقاط: +{pts:,}\n"
                f"التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        except:
            pass


@bot.message_handler(func=lambda m: get_state(m.from_user.id).get("state") == "fund_link")
def msg_fund_link(msg: Message):
    link = (msg.text or "").strip()
    if not (link.startswith("http") or link.startswith("@") or "t.me" in link):
        send(msg.chat.id, "⚠️ الرابط غير صحيح!")
        return
    d = get_state(msg.from_user.id)["data"]
    set_state(msg.from_user.id, "fund_qty", **d, link=link)
    send(msg.chat.id,
        f"الرابط: <code>{link}</code>\n\n"
        f"<b>الخطوة 2:</b> أرسل عدد الأعضاء (من {d['svc_min']} إلى {d['svc_max']}):",
        kb.back())


@bot.message_handler(func=lambda m: get_state(m.from_user.id).get("state") == "fund_qty")
def msg_fund_qty(msg: Message):
    try:
        qty = int((msg.text or "").strip().replace(",", ""))
    except:
        send(msg.chat.id, "⚠️ أرسل رقماً!")
        return
    d = get_state(msg.from_user.id)["data"]
    mn = int(d.get("svc_min", 100))
    mx = int(d.get("svc_max", 100000))
    if qty < mn or qty > mx:
        send(msg.chat.id, f"⚠️ الكمية بين {mn:,} و {mx:,}!")
        return
    p1k = int(d.get("p1k", 10))
    pts = math.ceil(qty * p1k / 1000)
    user = db.get_user(msg.from_user.id)
    enough = user["points"] >= pts
    warn = "" if enough else f"\n\n<b>⚠️ نقاطك غير كافية!</b> ينقصك <b>{pts - user['points']:,}</b> نقطة."
    set_state(msg.from_user.id, "fund_confirm", **d, qty=qty, pts_needed=pts)
    send(msg.chat.id,
        f"<b>تأكيد الطلب</b>\n\n"
        f"<b>━━━━━━━━━━━━━━━</b>\n"
        f"الرابط: <code>{d['link']}</code>\n"
        f"الكمية: <b>{qty:,}</b> عضو\n"
        f"التكلفة: <b>{pts:,}</b> نقطة\n"
        f"رصيدك: <b>{user['points']:,}</b>\n"
        f"<b>━━━━━━━━━━━━━━━</b>{warn}",
        kb.confirm_keyboard() if enough else kb.back())


def _do_fund_order(call, d):
    pts = d["pts_needed"]
    qty = d["qty"]
    link = d["link"]
    svc_id = d["svc_id"]
    if not db.deduct_points(call.from_user.id, pts):
        bot.answer_callback_query(call.id, "نقاطك غير كافية!", show_alert=True)
        return
    rate = float(db.get_config("rate_per_1000", "0.5"))
    charge = round((qty / 1000) * rate, 5)
    svc_name = db.get_config("service_name", "تمويل")
    oid = db.create_order(call.from_user.id, svc_id, svc_name, link, qty,
                          charge, pts, None, "تمويل قناة")
    clear_state(call.from_user.id)
    user = db.get_user(call.from_user.id)
    notify_order_channels(oid, dict(user), svc_name, "تمويل قناة", link, qty, pts)

    auto = db.get_config("auto_approve_orders", "0") == "1"
    if auto:
        db.approve_order(oid)
        enqueue_service_order(oid)
        edit(call,
            f"<b>✅ تم إرسال الطلب وجارٍ التنفيذ!</b>\n\n"
            f"رقم الطلب: <b>#{oid}</b>\n"
            f"{qty:,} وحدة | {pts:,} نقطة\n"
            f"رصيدك: {user['points']:,}\n\n"
            f"<i>سيصلك إشعار عند الاكتمال</i>",
            kb.back())
    else:
        _notify_admin_approve_order(oid, dict(user), svc_name, "تمويل قناة", link, qty, pts, order_type="fund")
        edit(call,
            f"<b>⏳ تم إرسال طلبك!</b>\n\n"
            f"رقم الطلب: <b>#{oid}</b>\n"
            f"{qty:,} وحدة | {pts:,} نقطة\n"
            f"رصيدك: {user['points']:,}\n\n"
            f"<i>طلبك قيد مراجعة الأدمن، سيصلك إشعار قريباً</i>",
            kb.back())


# ══════════════════════════════════════════════════════════════════
#   12. لوحة الأدمن
# ══════════════════════════════════════════════════════════════════
@bot.message_handler(commands=["admin"])
def cmd_admin(msg: Message):
    if not is_admin(msg.from_user.id):
        send(msg.chat.id, "ليس لديك صلاحية.")
        return
    _show_admin(msg.chat.id)


def _show_admin(cid):
    total_u = db.get_users_count()
    total_o, today_o, rev, trev, tpts = db.get_orders_stats()
    bot.send_message(cid,
        f"<b>لوحة الأدمن — {config.BOT_NAME}</b>\n\n"
        f"<b>━━━━━━━━━━━━━━━</b>\n"
        f"المستخدمون: <b>{total_u}</b>\n"
        f"الطلبات: <b>{total_o}</b>  (اليوم: {today_o})\n"
        f"النقاط المستخدمة: <b>{tpts:,}</b>\n"
        f"الأرباح: <b>{rev:.2f}$</b>\n"
        f"<b>━━━━━━━━━━━━━━━</b>",
        reply_markup=kb.developer_panel())


@bot.callback_query_handler(func=lambda c: c.data == "developer_panel")
def cb_developer_panel(call: CallbackQuery):
    if int(call.from_user.id) != DEVELOPER_ID:
        bot.answer_callback_query(call.id, "ليس لديك صلاحية.", show_alert=True)
        return
    clear_state(call.from_user.id)
    total_u = db.get_users_count()
    total_o, today_o, rev, trev, tpts = db.get_orders_stats()
    edit(call,
        f"<b>👨‍💻 لوحة المطور</b>\n\n"
        f"المستخدمون: {total_u} | الطلبات: {total_o} (اليوم {today_o})\n"
        f"النقاط: {tpts:,} | الأرباح: {rev:.2f}$",
        kb.developer_panel())


@bot.callback_query_handler(func=lambda c: c.data == "adm_back")
def cb_adm_back(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    clear_state(call.from_user.id)
    total_u = db.get_users_count()
    total_o, today_o, rev, trev, tpts = db.get_orders_stats()
    edit(call,
        f"<b>لوحة الأدمن</b>\n\n"
        f"المستخدمون: {total_u} | الطلبات: {total_o} (اليوم {today_o})\n"
        f"النقاط: {tpts:,} | الأرباح: {rev:.2f}$",
        kb.developer_panel())


@bot.callback_query_handler(func=lambda c: c.data == "adm_close")
def cb_adm_close(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass


# ─── الإحصائيات ───────────────────────────────────────────────
@bot.callback_query_handler(func=lambda c: c.data == "adm_stats")
def cb_adm_stats(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    total_u = db.get_users_count()
    total_o, today_o, rev, trev, tpts = db.get_orders_stats()
    edit(call,
         f"<b>📊 الإحصائيات</b>\n\n"
         f"👥 المستخدمون: <b>{total_u:,}</b>\n"
         f"📦 إجمالي الطلبات: <b>{total_o:,}</b>\n"
         f"📅 طلبات اليوم: <b>{today_o:,}</b>\n"
         f"⭐ النقاط المستخدمة: <b>{tpts:,}</b>\n"
         f"💰 الإيرادات: <b>{rev:.2f}$</b>",
         kb.back("adm_back"))

# ─── قنوات الطلبات ────────────────────────────────────────────
@bot.callback_query_handler(func=lambda c: c.data == "adm_order_channels")
def cb_adm_order_channels(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    channels = db.get_order_channels()
    edit(call,
        f"<b>📣 قنوات الطلبات</b>\n\n"
        f"عدد: <b>{len(channels)}</b>\n\n"
        f"<i>عند تنفيذ أي طلب، تُرسل تفاصيله لهذه القنوات</i>",
        kb.admin_order_channels(channels))


@bot.callback_query_handler(func=lambda c: c.data == "adm_add_orch")
def cb_adm_add_orch(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    set_state(call.from_user.id, "adm_add_orch")
    edit(call,
        "<b>إضافة قناة طلبات</b>\n\n"
        "أرسل بهذا الشكل:\n"
        "<code>channel_id|الاسم</code>\n\n"
        "مثال: <code>-1001234567890|قناة طلبات MCV</code>\n"
        "أو: <code>@mychannel|قناة الطلبات</code>\n\n"
        "<i>يجب أن يكون البوت أدمن في القناة وله صلاحية نشر الرسائل</i>",
        kb.back("adm_order_channels"))


@bot.callback_query_handler(func=lambda c: c.data.startswith("adm_del_orch_"))
def cb_adm_del_orch(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    ch_id = call.data.replace("adm_del_orch_", "")
    db.remove_order_channel(ch_id)
    bot.answer_callback_query(call.id, "تم الحذف")
    cb_adm_order_channels(call)


# ─── قاعدة البيانات ──────────────────────────────────────────
@bot.callback_query_handler(func=lambda c: c.data == "adm_database")
def cb_adm_database(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    conn = db.get_conn()
    users_c = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    orders_c = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    apps_c = conn.execute("SELECT COUNT(*) FROM apps").fetchone()[0]
    svcs_c = conn.execute("SELECT COUNT(*) FROM app_services").fetchone()[0]
    conn.close()
    edit(call,
        f"<b>🗄️ قاعدة البيانات</b>\n\n"
        f"<b>━━━━━━━━━━━━━━━</b>\n"
        f"المستخدمون: <b>{users_c}</b>\n"
        f"الطلبات: <b>{orders_c}</b>\n"
        f"الأقسام: <b>{apps_c}</b>\n"
        f"الخدمات: <b>{svcs_c}</b>\n"
        f"<b>━━━━━━━━━━━━━━━</b>\n\n"
        f"<i>يمكنك تصدير الإعدادات واستيرادها</i>",
        kb.admin_database())


@bot.callback_query_handler(func=lambda c: c.data == "adm_db_export")
def cb_adm_db_export(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    try:
        json_data = db.export_db_json()
        # إرسال كملف
        import io
        f = io.BytesIO(json_data.encode("utf-8"))
        f.name = f"mcv_db_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        bot.answer_callback_query(call.id, "جارٍ التصدير...")
        bot.send_document(call.message.chat.id, f,
            caption=f"<b>✅ نسخة احتياطية من قاعدة البيانات</b>\n"
                    f"التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    except Exception as e:
        bot.answer_callback_query(call.id, f"خطأ: {e}", show_alert=True)


@bot.callback_query_handler(func=lambda c: c.data == "adm_db_import")
def cb_adm_db_import(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    set_state(call.from_user.id, "adm_db_import")
    edit(call,
        "<b>📥 استيراد قاعدة البيانات</b>\n\n"
        "أرسل ملف JSON الذي صدّرته سابقاً.\n\n"
        "<b>⚠️ تحذير:</b> سيتم استبدال بعض البيانات الحالية بالبيانات الجديدة.",
        kb.back("adm_database"))


@bot.callback_query_handler(func=lambda c: c.data == "adm_db_info")
def cb_adm_db_info(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    cfg = db.get_all_config()
    text = "<b>إعدادات البوت الحالية:</b>\n\n"
    for row in cfg:
        k = row["key"]
        v = row["value"]
        if "key" in k.lower() and len(str(v)) > 8:
            v = str(v)[:6] + "****"
        text += f"<code>{k}</code>: {v}\n"
    # تقسيم النص إذا كان طويلاً
    if len(text) > 3500:
        text = text[:3500] + "\n..."
    edit(call, text, kb.back("adm_database"))


# ─── إدارة الخدمة وربط الحسابات ─────────────────────────────
@bot.callback_query_handler(func=lambda c: c.data == "adm_cat_services")
def cb_adm_cat_services(call: CallbackQuery):
    if not is_admin(call.from_user.id): return
    edit(call, "<b>🛠️ الخدمات</b>\n\nاختر القسم الذي تريد العمل عليه.", kb.admin_services_menu())

@bot.callback_query_handler(func=lambda c: c.data == "adm_cat_channels")
def cb_adm_cat_channels(call: CallbackQuery):
    if not is_admin(call.from_user.id): return
    edit(call, "<b>📢 القنوات</b>\n\nإدارة القنوات المرتبطة بالبوت.", kb.admin_channels_menu())

@bot.callback_query_handler(func=lambda c: c.data == "adm_cat_store")
def cb_adm_cat_store(call: CallbackQuery):
    if not is_admin(call.from_user.id): return
    edit(call, "<b>🛍️ المتجر والطلبات</b>", kb.admin_store_menu())

@bot.callback_query_handler(func=lambda c: c.data == "adm_cat_rewards")
def cb_adm_cat_rewards(call: CallbackQuery):
    if not is_admin(call.from_user.id): return
    edit(call, "<b>🎁 النقاط والهدايا</b>", kb.admin_rewards_menu())

@bot.callback_query_handler(func=lambda c: c.data == "adm_cat_communication")
def cb_adm_cat_communication(call: CallbackQuery):
    if not is_admin(call.from_user.id): return
    edit(call, "<b>📣 الإذاعة والتنبيهات</b>", kb.admin_communication_menu())

@bot.callback_query_handler(func=lambda c: c.data == "adm_cat_settings")
def cb_adm_cat_settings(call: CallbackQuery):
    if not is_admin(call.from_user.id): return
    edit(call, "<b>⚙️ إعدادات البوت</b>", kb.admin_settings_menu())

@bot.callback_query_handler(func=lambda c: c.data == "adm_service_accounts")
def cb_adm_service_accounts(call: CallbackQuery):
    if not is_admin(call.from_user.id): return
    apps=db.get_apps(only_active=False)
    rows=[]
    for a in apps:
        nm=f"{a['emoji']} {a['name']}" if a.get('emoji') else a['name']
        rows.append([_btn(nm, f"adm_service_app_{a['id']}", color="blue")])
    rows.append([_btn("◀️ رجوع للخدمات", "adm_cat_services", color="blue")])
    edit(call, f"<b>⚙️ التحكم في الخدمة</b>\n\nالأقسام: <b>{len(apps)}</b>", mk(*rows))

@bot.callback_query_handler(func=lambda c: c.data.startswith("adm_service_app_"))
def cb_adm_service_app(call: CallbackQuery):
    if not is_admin(call.from_user.id): return
    try: app_id=int(call.data.rsplit('_',1)[1])
    except: return
    app=db.get_app(app_id)
    if not app: return bot.answer_callback_query(call.id,"القسم غير موجود",show_alert=True)
    services=db.get_app_services(app_id,only_active=False)
    rows=[]
    for s in services:
        nm=f"{s['emoji']} {s['name']}" if s.get('emoji') else s['name']
        rows.append([_btn(nm,f"adm_service_manage_{s['id']}",color="blue")])
    rows.append([_btn("◀️ رجوع للأقسام", "adm_service_accounts", color="blue")])
    nm=f"{app['emoji']} {app['name']}" if app.get('emoji') else app['name']
    edit(call,f"<b>{nm}</b>\n\nاختر الخدمة:",mk(*rows))

@bot.callback_query_handler(func=lambda c: c.data.startswith("adm_service_manage_"))
def cb_adm_service_manage(call: CallbackQuery):
    if not is_admin(call.from_user.id): return
    try: sid=int(call.data.rsplit('_',1)[1])
    except: return
    svc=db.get_service(sid)
    if not svc: return bot.answer_callback_query(call.id,"الخدمة غير موجودة",show_alert=True)
    nm=f"{svc['emoji']} {svc['name']}" if svc.get('emoji') else svc['name']
    edit(call,f"<b>⚙️ التحكم في الخدمة</b>\n\n<b>{nm}</b>",kb.admin_service_accounts_view(sid,svc['app_id']))

@bot.callback_query_handler(func=lambda c: c.data.startswith("adm_linked_accounts_"))
def cb_adm_linked_accounts(call: CallbackQuery):
    if not is_admin(call.from_user.id): return
    try: sid=int(call.data.rsplit('_',1)[1])
    except: return
    svc=db.get_service(sid)
    if not svc: return
    accounts=db.get_service_telegram_accounts(sid)
    edit(call,f"<b>👤 الحسابات المرتبطة</b>\n\nالعدد الحالي: <b>{len(accounts)}</b>",kb.admin_linked_accounts_view(sid,svc['app_id'],accounts,db.get_service_account_mode(svc)))

@bot.callback_query_handler(func=lambda c: c.data.startswith("adm_multi_accounts_"))
def cb_adm_multi_accounts(call: CallbackQuery):
    if not is_admin(call.from_user.id): return
    try: sid=int(call.data.rsplit('_',1)[1])
    except: return
    svc=db.get_service(sid)
    if not svc: return
    selected=db.get_service_telegram_accounts(sid); count=len(selected)
    if count<=0:
        return bot.answer_callback_query(call.id,"اربط حساباً واحداً على الأقل أولاً",show_alert=True)
    set_state(call.from_user.id,"adm_multi_count",svc_id=sid)
    edit(call,f"<b>👥 تفعيل الحسابات المتعددة</b>\n\nالحسابات المرتبطة فعلياً: <b>{count}</b>\n\nأرسل العدد نفسه لتأكيد الحسابات.\nمثال: <code>{count}</code>",mk([_btn("❌ إلغاء","adm_multi_cancel_%s"%sid,color="red")]))

@bot.callback_query_handler(func=lambda c: c.data.startswith("adm_multi_cancel_"))
def cb_adm_multi_cancel(call: CallbackQuery):
    if not is_admin(call.from_user.id): return
    try: sid=int(call.data.rsplit('_',1)[1])
    except: return
    clear_state(call.from_user.id); svc=db.get_service(sid)
    if svc: edit(call,"<b>⚙️ التحكم في الخدمة</b>",kb.admin_service_accounts_view(sid,svc['app_id']))

@bot.callback_query_handler(func=lambda c: c.data.startswith("adm_multi_confirm_"))
def cb_adm_multi_confirm(call: CallbackQuery):
    if not is_admin(call.from_user.id): return
    try: _,_,_,sid_s,count_s=call.data.split('_'); sid,count=int(sid_s),int(count_s)
    except: return
    svc=db.get_service(sid); selected=db.get_service_telegram_accounts(sid) if svc else []
    if not svc or count<=0 or len(selected)!=count:
        return bot.answer_callback_query(call.id,"العدد تغير. أعد التأكيد من جديد.",show_alert=True)
    db.set_service_account_mode(sid,"multi"); clear_state(call.from_user.id)
    bot.answer_callback_query(call.id,"تم تفعيل الحسابات المتعددة")
    edit(call,f"<b>✅ تم التفعيل</b>\n\nالخدمة: <b>{svc['name']}</b>\nالحسابات: <b>{count}</b>\n\nكل طلب لهذه الخدمة سيستخدم الحسابات المرتبطة المفعلة.",kb.admin_service_accounts_view(sid,svc['app_id']))

@bot.callback_query_handler(func=lambda c: c.data == "adm_apps")
def cb_adm_apps(call: CallbackQuery):
    if not is_admin(call.from_user.id): return
    apps=db.get_apps(only_active=False)
    edit(call,f"<b>🗂️ الأقسام والخدمات</b>\n\nعدد الأقسام: <b>{len(apps)}</b>",kb.admin_apps_keyboard(apps))

@bot.callback_query_handler(func=lambda c: c.data == "adm_add_service_direct")
def cb_adm_add_service_direct(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    try:
        app_id = _get_or_create_rush_app()
        set_state(call.from_user.id, "adm_add_svc", app_id=app_id)
        edit(
            call,
            "<b>➕ إضافة خدمة مباشرة</b>\n\n"
            "لا تحتاج لإضافة قسم أولاً. سيتم وضع الخدمة تلقائياً داخل <b>🐸 خدمات الرشق</b>.\n\n"
            "أرسل بالصيغة:\n"
            "<code>النقاط|اسم الخدمة|الحد الأدنى|الحد الأقصى</code>\n\n"
            "مثال:\n"
            "<code>10|تفاعلات تلجرام إيجابية ❤️‍🔥🥰👍|1|100</code>\n\n"
            "سيتم اكتشاف نوع الخدمة وإيموجيها تلقائياً.",
            kb.back("adm_cat_services")
        )
    except Exception as e:
        bot.answer_callback_query(call.id, f"خطأ: {str(e)[:120]}", show_alert=True)


@bot.callback_query_handler(func=lambda c: c.data == "adm_add_app")
def cb_adm_add_app(call: CallbackQuery):
    if not is_admin(call.from_user.id): return
    set_state(call.from_user.id,"adm_add_app")
    edit(call,"<b>➕ إضافة قسم</b>\n\nأرسل: <code>الاسم|الإيموجي</code>\nمثال: <code>تيك توك|📱</code>",kb.back("adm_apps"))

@bot.callback_query_handler(func=lambda c: c.data.startswith("adm_app_") and not c.data.startswith("adm_app_s"))
def cb_adm_view_app(call: CallbackQuery):
    if not is_admin(call.from_user.id): return
    try: app_id=int(call.data.rsplit('_',1)[1])
    except: return
    app=db.get_app(app_id)
    if not app: return bot.answer_callback_query(call.id,"القسم غير موجود",show_alert=True)
    services=db.get_app_services(app_id,only_active=False)
    nm=f"{app['emoji']} {app['name']}" if app.get('emoji') else app['name']
    edit(call,f"<b>{nm}</b>\n\nالخدمات: <b>{len(services)}</b>",kb.admin_app_view(app_id,services))

@bot.callback_query_handler(func=lambda c: c.data.startswith("adm_add_svc_"))
def cb_adm_add_svc(call: CallbackQuery):
    if not is_admin(call.from_user.id): return
    try: app_id=int(call.data.rsplit('_',1)[1])
    except: return
    set_state(call.from_user.id,"adm_add_svc",app_id=app_id)
    edit(call,"<b>➕ إضافة خدمة</b>\n\nأرسل:\n<code>النقاط|اسم الخدمة|الحد الأدنى|الحد الأقصى</code>\n\nسيتم اكتشاف نوع الخدمة وإيموجيها تلقائياً.",kb.back(f"adm_app_{app_id}"))

@bot.callback_query_handler(func=lambda c: c.data == "adm_noop_service_id")
def cb_adm_noop_service_id(call: CallbackQuery):
    try: bot.answer_callback_query(call.id,"الحساب مرتبط بهذه الخدمة")
    except: pass

@bot.callback_query_handler(func=lambda c: c.data.startswith("adm_assign_account_"))
def cb_adm_assign_account(call: CallbackQuery):
    if not is_admin(call.from_user.id): return
    try: sid=int(call.data.rsplit('_',1)[1])
    except: return
    svc=db.get_service(sid); owner_id=int(getattr(config,"TG_EXECUTION_USER_ID",0) or 0)
    if not svc: return
    accounts=db.list_telegram_accounts(owner_id) if owner_id else []
    existing_state=get_state(call.from_user.id)
    if existing_state.get("state")=="adm_account_selection" and int(existing_state.get("data",{}).get("sid",-1))==sid:
        selected=set(int(x) for x in existing_state.get("data",{}).get("selected",[]))
    else:
        selected={int(a['id']) for a in db.get_service_telegram_accounts(sid)}
        USER_STATE[call.from_user.id]={"state":"adm_account_selection","data":{"sid":sid,"selected":sorted(selected)}}
    rows=[]
    for a in accounts:
        aid=int(a['id']); mark='✅' if aid in selected else '⬜'; name=(a.get('first_name') or 'حساب').strip(); un=f" @{a['username']}" if a.get('username') else ''
        rows.append([_btn(f"{mark} {name}{un}",f"adm_toggle_svc_acc_{sid}_{aid}",color='green' if aid in selected else 'blue')])
    rows.append([_btn(f"☑️ تحديد الكل • {len(accounts)}",f"adm_select_all_svc_acc_{sid}",color="green")])
    rows.append([_btn(f"💾 تأكيد وحفظ • {len(selected)}",f"adm_save_svc_acc_{sid}",color="green")])
    rows.append([_btn("◀️ رجوع",f"adm_service_manage_{sid}",color="blue")])
    edit(call,f"<b>👥 حسابات التنفيذ</b>\n\nالخدمة: <b>{svc['name']}</b>\nحدد الحسابات المضافة أصلًا ثم اضغط <b>تأكيد وحفظ</b>.\n\nالمحدد الآن: <b>{len(selected)}</b>",mk(*rows))

@bot.callback_query_handler(func=lambda c: c.data.startswith("adm_toggle_svc_acc_"))
def cb_adm_toggle_svc_acc(call: CallbackQuery):
    if not is_admin(call.from_user.id): return
    try: parts=call.data.split('_'); sid,aid=int(parts[-2]),int(parts[-1])
    except: return
    state=get_state(call.from_user.id)
    if state.get("state")!="adm_account_selection" or int(state.get("data",{}).get("sid",-1))!=sid:
        return bot.answer_callback_query(call.id,"افتح حسابات التنفيذ من جديد",show_alert=True)
    selected=[int(x) for x in state.get("data",{}).get("selected",[])]
    owner_id=int(getattr(config,"TG_EXECUTION_USER_ID",0) or 0); accounts=db.list_telegram_accounts(owner_id) if owner_id else []
    if not any(int(a['id'])==aid for a in accounts): return
    if aid in selected: selected.remove(aid)
    else: selected.append(aid)
    state["data"]["selected"]=selected; USER_STATE[call.from_user.id]=state
    rows=[]
    for a in accounts:
        x=int(a['id']); mark='✅' if x in selected else '⬜'; name=(a.get('first_name') or 'حساب').strip(); un=f" @{a['username']}" if a.get('username') else ''
        rows.append([_btn(f"{mark} {name}{un}",f"adm_toggle_svc_acc_{sid}_{x}",color='green' if x in selected else 'blue')])
    rows.append([_btn(f"☑️ تحديد الكل • {len(accounts)}",f"adm_select_all_svc_acc_{sid}",color="green")])
    rows.append([_btn(f"💾 تأكيد وحفظ • {len(selected)}",f"adm_save_svc_acc_{sid}",color="green")])
    rows.append([_btn("◀️ رجوع",f"adm_service_manage_{sid}",color="blue")])
    bot.answer_callback_query(call.id)
    edit(call,f"<b>👥 حسابات التنفيذ</b>\n\nحدد الحسابات المضافة أصلًا ثم اضغط <b>تأكيد وحفظ</b>.\n\nالمحدد الآن: <b>{len(selected)}</b>",mk(*rows))

@bot.callback_query_handler(func=lambda c: c.data.startswith("adm_select_all_svc_acc_"))
def cb_adm_select_all_svc_acc(call: CallbackQuery):
    if not is_admin(call.from_user.id): return
    try: sid=int(call.data.rsplit('_',1)[1])
    except: return
    state=get_state(call.from_user.id)
    if state.get("state")!="adm_account_selection" or int(state.get("data",{}).get("sid",-1))!=sid:
        return bot.answer_callback_query(call.id,"افتح حسابات التنفيذ من جديد",show_alert=True)
    owner_id=int(getattr(config,"TG_EXECUTION_USER_ID",0) or 0); accounts=db.list_telegram_accounts(owner_id) if owner_id else []
    state["data"]["selected"]=[int(a['id']) for a in accounts]; USER_STATE[call.from_user.id]=state
    bot.answer_callback_query(call.id,"تم تحديد الكل")
    cb_adm_assign_account(call)

@bot.callback_query_handler(func=lambda c: c.data.startswith("adm_save_svc_acc_"))
def cb_adm_save_svc_acc(call: CallbackQuery):
    if not is_admin(call.from_user.id): return
    try: sid=int(call.data.rsplit('_',1)[1])
    except: return
    state=get_state(call.from_user.id)
    if state.get("state")!="adm_account_selection" or int(state.get("data",{}).get("sid",-1))!=sid:
        return bot.answer_callback_query(call.id,"افتح حسابات التنفيذ من جديد",show_alert=True)
    selected=state.get("data",{}).get("selected",[])
    svc=db.get_service(sid)
    if not svc: return
    saved=db.set_service_telegram_accounts(sid,selected); clear_state(call.from_user.id)
    bot.answer_callback_query(call.id,f"تم حفظ {len(saved)} حساب")
    edit(call,f"<b>✅ تم حفظ حسابات التنفيذ</b>\n\nالخدمة: <b>{svc['name']}</b>\nالحسابات المحددة: <b>{len(saved)}</b>",kb.admin_service_accounts_view(sid,svc['app_id']))

@bot.callback_query_handler(func=lambda c: c.data=='adm_reaction_targets')
def cb_adm_reaction_targets(call: CallbackQuery):
    if not is_admin(call.from_user.id): return
    services=[]
    for a in db.get_apps(only_active=False):
        services += [x for x in db.get_app_services(a['id'],only_active=False) if (x.get('service_type') or '') in ('قلب','تفاعل')]
    if not services:
        edit(call,'<b>📡 التفاعل التلقائي</b>\n\nلا توجد خدمات تفاعل.',kb.back('adm_back')); return
    rows=[]
    for x in services:
        mark='✅' if x.get('auto_react') else '❌'
        rows.append([_btn(f'{mark} {x["name"]}',f'adm_service_manage_{x["id"]}',color='green' if x.get('auto_react') else 'blue')])
    rows.append([_btn('◀️ رجوع','adm_back',color='blue')])
    edit(call,'<b>📡 خدمات التفاعل التلقائي</b>',mk(*rows))

@bot.callback_query_handler(func=lambda c: c.data.startswith("adm_del_app_"))
def cb_adm_del_app(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    try:
        db.delete_app(int(call.data.split("_")[-1]))
        bot.answer_callback_query(call.id, "تم الحذف")
        cb_adm_apps(call)
    except Exception as e:
        bot.answer_callback_query(call.id, f"خطأ: {e}")


# ─── المستخدمون ──────────────────────────────────────────────
@bot.callback_query_handler(func=lambda c: c.data == "adm_users")
def cb_adm_users(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    edit(call, f"<b>إدارة المستخدمين</b>\n\nالإجمالي: <b>{db.get_users_count()}</b>",
         kb.admin_users_kb())


@bot.callback_query_handler(func=lambda c: c.data == "adm_search_user")
def cb_adm_search(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    set_state(call.from_user.id, "adm_search_user")
    edit(call, "أرسل ID المستخدم:", kb.back("adm_users"))


@bot.callback_query_handler(func=lambda c: c.data.startswith("adm_ban_") or c.data.startswith("adm_unban_"))
def cb_adm_ban(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    parts = call.data.split("_")
    action = parts[1]
    uid = int(parts[2])
    db.update_user(uid, is_banned=1 if action == "ban" else 0)
    bot.answer_callback_query(call.id, "تم")


@bot.callback_query_handler(func=lambda c: c.data.startswith("adm_add_pts_") or c.data.startswith("adm_sub_pts_"))
def cb_adm_pts_action(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    parts = call.data.split("_")
    action = parts[1]  # add or sub
    uid = int(parts[3])
    set_state(call.from_user.id, f"adm_{action}_points", target_id=uid)
    edit(call, f"أرسل عدد النقاط ({'إضافة' if action == 'add' else 'خصم'}) للمستخدم <code>{uid}</code>:",
         kb.back("adm_back"))


# ─── إذاعة ───────────────────────────────────────────────────
@bot.callback_query_handler(func=lambda c: c.data == "adm_broadcast")
def cb_adm_broadcast(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    set_state(call.from_user.id, "adm_broadcast")
    edit(call,
        "<b>إذاعة جماعية</b>\n\n"
        "الإذاعة ستُرسل لجميع المستخدمين النشطين.\n\n"
        "أرسل الرسالة الآن (نص/صورة/فيديو):",
        kb.back("adm_back"))


# ─── شحن نقاط ────────────────────────────────────────────────
@bot.callback_query_handler(func=lambda c: c.data == "adm_topup")
def cb_adm_topup(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    set_state(call.from_user.id, "adm_topup_id")
    edit(call, "أرسل ID المستخدم:", kb.back("adm_back"))


# ─── قنوات إجبارية ───────────────────────────────────────────
@bot.callback_query_handler(func=lambda c: c.data == "adm_mandatory")
def cb_adm_mandatory(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    channels = db.get_mandatory_channels()
    txt = f"<b>قنوات الاشتراك الإجباري</b>\n\nعدد: <b>{len(channels)}</b>\n"
    rows = []
    for ch in channels:
        t = ch.get("target_members", 0)
        cm = ch.get("current_members", 0)
        lbl = ch['channel_name']
        if t > 0:
            lbl += f"  ({cm}/{t})"
        rows.append([_btn(f"🗑️ حذف  {lbl}", f"adm_del_mand_{ch['channel_id']}", color="red")])
    rows.append([_btn("➕ إضافة قناة", "adm_add_mand", color="green")])
    rows.append([_btn("◀️ رجوع", "adm_back")])
    edit(call, txt, mk(*rows))


@bot.callback_query_handler(func=lambda c: c.data == "adm_add_mand")
def cb_adm_add_mand(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    set_state(call.from_user.id, "adm_mand_step1")
    edit(call,
        "<b>إضافة قناة إجبارية — الخطوة 1/4</b>\n\n"
        "أرسل معرف القناة:\n"
        "مثال: <code>@mychannel</code> أو <code>-1001234567890</code>\n\n"
        "<i>يجب أن يكون البوت أدمن في القناة</i>",
        kb.back("adm_mandatory"))


@bot.callback_query_handler(func=lambda c: c.data.startswith("adm_del_mand_"))
def cb_adm_del_mand(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    ch_id = call.data.replace("adm_del_mand_", "")
    db.remove_mandatory_channel(ch_id)
    bot.answer_callback_query(call.id, "تم الحذف")
    cb_adm_mandatory(call)


# ─── قنوات النقاط ────────────────────────────────────────────
@bot.callback_query_handler(func=lambda c: c.data == "adm_points_ch")
def cb_adm_pts_ch(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    channels = db.get_points_channels()
    rows = []
    for ch in channels:
        rows.append([_btn(f"🗑️ حذف  {ch['channel_name']} (+{ch['points_reward']})",
                          f"adm_del_ptch_{ch['channel_id']}")])
    rows.append([_btn("➕ إضافة قناة نقاط", "adm_add_ptch", color="green")])
    rows.append([_btn("◀️ رجوع", "adm_back")])
    edit(call, f"<b>قنوات النقاط</b>\n\nعدد: <b>{len(channels)}</b>", mk(*rows))


@bot.callback_query_handler(func=lambda c: c.data == "adm_add_ptch")
def cb_adm_add_ptch(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    set_state(call.from_user.id, "adm_add_ptch")
    edit(call,
        "<b>إضافة قناة نقاط</b>\n\n"
        "<code>channel_id|الاسم|https://t.me/channel|النقاط</code>\n\n"
        "مثال: <code>@mychannel|قناتي|https://t.me/mychannel|50</code>",
        kb.back("adm_points_ch"))


@bot.callback_query_handler(func=lambda c: c.data.startswith("adm_del_ptch_"))
def cb_adm_del_ptch(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    ch_id = call.data.replace("adm_del_ptch_", "")
    db.remove_points_channel(ch_id)
    bot.answer_callback_query(call.id, "تم الحذف")
    cb_adm_pts_ch(call)


# ─── إعدادات الخدمة ──────────────────────────────────────────
@bot.callback_query_handler(func=lambda c: c.data == "adm_service_cfg")
def cb_adm_service_cfg(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    rows = [
        [_btn("🔧 تغيير معرف الخدمة", "adm_set_svc_id")],
        [_btn("💎 السعر لكل 1000 (نقاط)", "adm_set_p1k")],
        [_btn("📉 الحد الأدنى للكمية", "adm_set_svc_min")],
        [_btn("📈 الحد الأقصى للكمية", "adm_set_svc_max")],
        [_btn("◀️ رجوع", "adm_back")],
    ]
    edit(call,
        f"<b>إعدادات خدمة التمويل</b>\n\n"
        f"معرف الخدمة: <code>{db.get_config('service_id', '—')}</code>\n"
        f"السعر/1000: <b>{db.get_config('points_per_1000', '10')}</b> نقطة\n"
        f"الحد الأدنى: {db.get_config('service_min', '100')}\n"
        f"الحد الأقصى: {db.get_config('service_max', '100000')}",
        mk(*rows))


@bot.callback_query_handler(func=lambda c: c.data == "adm_menu_labels")
def cb_adm_menu_labels(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    rows = [
        [_btn("🎯 الخدمات", "adm_set_menu_services")],
        [_btn("💳 شحن مباشر", "adm_set_menu_fund")],
        [_btn("🎁 تجميع نقاط", "adm_set_menu_collect")],
        [_btn("📊 اداره الحساب", "adm_set_menu_account")],
        [_btn("🔑 استخدام كود", "adm_set_menu_use_code")],
        [_btn("🌐 تحويل نقاط", "adm_set_menu_transfer")],
        [_btn("🔎 متابعه طلب", "adm_set_menu_track_order")],
        [_btn("📦 جميع طلباتي", "adm_set_menu_my_orders")],
        [_btn("🤖 قنوات البوت", "adm_set_menu_channels")],
        [_btn("🔄 قناه الاثبتات", "adm_set_menu_updates")],
        [_btn("🛍️ متجر البوت", "adm_set_menu_store")],
        [_btn("📜 الشروط", "adm_set_menu_terms")],
        [_btn("◀️ رجوع", "adm_bot_settings", color="blue")],
    ]
    edit(call,
        "<b>تعديل عناوين القائمة الرئيسية</b>\n\n" \
        "اضغط على الزر لتغيير النص.",
        mk(*rows))


# ─── إعدادات النقاط ──────────────────────────────────────────
@bot.callback_query_handler(func=lambda c: c.data == "adm_pts_settings")
def cb_adm_pts_settings(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    rows = [
        [_btn("🌅 نقاط الهدية اليومية", "adm_set_daily_pts")],
        [_btn("🗓️ نقاط الهدية الأسبوعية", "adm_set_weekly_pts")],
        [_btn("🔗 نقاط الإحالة", "adm_set_ref_pts")],
        [_btn("👋 نقاط الترحيب", "adm_set_welcome_pts")],
        [_btn("⏱️ ساعات الانتظار للعجلة", "adm_set_wheel_hrs")],
        [_btn("🔒 حد الخدمات المجانية يومياً", "adm_set_free_limit")],
        [_btn("💳 معلومات شحن النقاط", "adm_set_points_charge_info")],
        [_btn("◀️ رجوع", "adm_back")],
    ]
    edit(call,
        f"<b>إعدادات النقاط</b>\n\n"
        f"الهدية اليومية: <b>{db.get_config('daily_gift_points', '5')}</b>\n"
        f"الهدية الأسبوعية: <b>{db.get_config('weekly_gift_points', '50')}</b>\n"
        f"نقاط الإحالة: <b>{db.get_config('referral_points', '50')}</b>\n"
        f"نقاط الترحيب: <b>{db.get_config('welcome_points', '10')}</b>\n"
        f"انتظار العجلة: <b>{db.get_config('wheel_cooldown_hrs', '6')}</b> ساعة\n"
        f"حد الخدمات المجانية يومياً: <b>{db.get_config('free_services_daily_limit', '3')}</b> مرة\n"
        f"معلومات شحن النقاط: {db.get_config('points_charge_info', 'لشحن النقاط تواصل مع الدعم')}",
        mk(*rows))


# ─── إعدادات البوت ───────────────────────────────────────────
@bot.callback_query_handler(func=lambda c: c.data == "adm_bot_settings")
def cb_adm_bot_settings(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    rows = [
        [_btn("📡 قناة التحديثات", "adm_set_updates_ch"),
         _btn("🛟 يوزر الدعم", "adm_set_support")],
        [_btn("⚡ إيقاف/تشغيل البوت", "adm_toggle_bot")],
        [_btn("📱 بيانات فودافون كاش", "adm_set_charge_vodafone"),
         _btn("⭐ نسبة النجوم", "adm_set_stars_per_point")],
        [_btn("✏️ تعديل أسماء القائمة", "adm_menu_labels", color="blue")],
        [_btn("📜 تعديل الشروط", "adm_set_terms", color="blue")],
        [_btn(
            f"🤖 التنفيذ: {'تلقائي ✅' if db.get_config('auto_approve_orders','0')=='1' else 'يدوي ⏳'}",
            "adm_toggle_auto_approve",
            color="green" if db.get_config("auto_approve_orders","0")=="1" else "red"
        )],
        [_btn("◀️ رجوع", "adm_back")],
    ]
    edit(call,
        f"<b>إعدادات البوت</b>\n\n"
        f"الحالة: {'✅ فعّال' if db.get_config('bot_active', '1') == '1' else '❌ متوقف'}\n"
        f"فودافون كاش: {db.get_config('charge_vodafone_info', 'فودافون كاش: 0123456789')}\n"
        f"نجوم: {db.get_config('charge_stars_info', 'نجوم: تواصل مع @support')}\n",
        mk(*rows))


@bot.callback_query_handler(func=lambda c: c.data == "adm_toggle_bot")
def cb_toggle_bot(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    cur = db.get_config("bot_active", "1")
    db.set_config("bot_active", "0" if cur == "1" else "1")
    bot.answer_callback_query(call.id, f"البوت {'متوقف' if cur == '1' else 'فعّال'} الآن")
    cb_adm_bot_settings(call)


@bot.callback_query_handler(func=lambda c: c.data == "adm_toggle_auto_approve")
def cb_toggle_auto_approve(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    cur = db.get_config("auto_approve_orders", "0")
    new = "1" if cur == "0" else "0"
    db.set_config("auto_approve_orders", new)
    status = "تلقائي ✅" if new == "1" else "يدوي ⏳"
    bot.answer_callback_query(call.id, f"وضع التنفيذ: {status}", show_alert=True)
    cb_adm_bot_settings(call)


@bot.callback_query_handler(func=lambda c: c.data == "adm_set_terms")
def cb_adm_set_terms(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    set_state(call.from_user.id, "adm_set_terms")
    edit(call,
        "<b>📜 تعديل الشروط والأحكام</b>\n\n"
        "أرسل نص الشروط الجديد (يدعم HTML):",
        kb.back("adm_bot_settings"))


# ─── عجلة الحظ (أدمن) ────────────────────────────────────────
@bot.callback_query_handler(func=lambda c: c.data == "adm_wheel")
def cb_adm_wheel(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    prizes = db.get_wheel_prizes(only_active=False)
    total_w = sum(float(p["weight"]) for p in prizes if p["is_active"])
    txt = (f"<b>إدارة عجلة الحظ</b>\n\n"
           f"عدد الجوائز: <b>{len(prizes)}</b>  |  "
           f"مجموع الأوزان: <b>{total_w:g}</b>\n\n"
           f"<b>━━━━━━━━━━━━━━━</b>\n")
    for p in prizes:
        st = "✅" if p["is_active"] else "❌"
        ch = (float(p["weight"]) / total_w * 100) if (p["is_active"] and total_w) else 0
        lbl = p.get("label") or ""
        em = p.get("emoji") or ""
        txt += f"  {st} {em} {p['points']} نقطة {lbl}  —  {ch:.1f}%\n"
    edit(call, txt, kb.admin_wheel(prizes))


@bot.callback_query_handler(func=lambda c: c.data == "adm_wheel_add")
def cb_adm_wheel_add(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    set_state(call.from_user.id, "adm_wheel_add")
    edit(call,
        "<b>إضافة جائزة للعجلة</b>\n\n"
        "<code>النقاط|الوزن|الإيموجي|التسمية</code>\n\n"
        "مثال: <code>100|5|🔵|جائزة رائعة</code>\n\n"
        "<i>الوزن = الاحتمالية. جوائز أكبر = وزن أقل.</i>",
        kb.back("adm_wheel"))


@bot.callback_query_handler(func=lambda c: c.data.startswith("adm_wheel_tog_"))
def cb_wheel_toggle(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    db.toggle_wheel_prize(int(call.data.split("_")[-1]))
    bot.answer_callback_query(call.id, "تم التبديل")
    cb_adm_wheel(call)


@bot.callback_query_handler(func=lambda c: c.data.startswith("adm_wheel_del_"))
def cb_wheel_del(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    db.delete_wheel_prize(int(call.data.split("_")[-1]))
    bot.answer_callback_query(call.id, "تم الحذف")
    cb_adm_wheel(call)


# ─── الخدمات المجانية (أدمن) ─────────────────────────────────
@bot.callback_query_handler(func=lambda c: c.data == "adm_free_svcs")
def cb_adm_free_svcs(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    svcs = db.get_free_services(only_active=False)
    edit(call, f"<b>الخدمات المجانية</b>\n\nعدد: <b>{len(svcs)}</b>", kb.admin_free_svcs(svcs))


@bot.callback_query_handler(func=lambda c: c.data == "adm_add_free_svc")
def cb_adm_add_free_svc(call: CallbackQuery):
    if not is_admin(call.from_user.id): return
    edit(call, "<b>الخدمات المجانية</b>\n\nالخدمات المجانية الخارجية متوقفة في النسخة المحلية.", kb.back("adm_free_svcs"))

@bot.callback_query_handler(func=lambda c: c.data.startswith("adm_free_svc_"))
def cb_adm_view_free(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    try:
        sid = int(call.data.split("_")[-1])
    except:
        return
    svc = db.get_free_service(sid)
    if not svc:
        bot.answer_callback_query(call.id, "غير موجودة")
        return
    edit(call,
        f"<b>{svc['name']}</b>\n\n"

        f"الحدود: {svc['min_qty']:,} — {svc['max_qty']:,}\n"
        f"الوصف: {svc['description'] or '—'}",
        kb.admin_free_svc_view(sid))


@bot.callback_query_handler(func=lambda c: c.data.startswith("adm_del_free_"))
def cb_adm_del_free(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    db.delete_free_service(int(call.data.split("_")[-1]))
    bot.answer_callback_query(call.id, "تم الحذف")
    cb_adm_free_svcs(call)


# ─── أكواد الدعوة ────────────────────────────────────────────
@bot.callback_query_handler(func=lambda c: c.data == "adm_invite_links")
def cb_adm_invites(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    links = db.get_invites()
    edit(call, f"<b>أكواد الدعوة</b>\n\nعدد: <b>{len(links)}</b>", kb.admin_invite_links(links))


@bot.callback_query_handler(func=lambda c: c.data == "adm_create_invite")
def cb_adm_create_invite(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    set_state(call.from_user.id, "adm_create_invite")
    edit(call,
        "<b>إنشاء كود دعوة</b>\n\n"
        "<code>الكود|النقاط|الحد_الأقصى</code>\n\n"
        "مثال: <code>SPECIAL2024|100|50</code>\n"
        "<i>الحد = 0 يعني بلا حد</i>",
        kb.back("adm_invite_links"))


@bot.callback_query_handler(func=lambda c: c.data.startswith("adm_del_invite_"))
def cb_adm_del_invite(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    code = call.data.replace("adm_del_invite_", "")
    db.delete_invite(code)
    bot.answer_callback_query(call.id, "تم الحذف")
    cb_adm_invites(call)


@bot.callback_query_handler(func=lambda c: c.data.startswith("adm_view_invite_"))
def cb_adm_view_invite(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    code = call.data.replace("adm_view_invite_", "")
    conn = db.get_conn()
    lnk = conn.execute("SELECT * FROM invite_links WHERE code=?", (code,)).fetchone()
    conn.close()
    if not lnk:
        bot.answer_callback_query(call.id, "الكود غير موجود")
        return
    bu = config.BOT_USERNAME.lstrip("@")
    url = f"https://t.me/{bu}?start=invite_{code}"
    uses = "∞" if lnk["max_uses"] == 0 else f"{lnk['current_uses']}/{lnk['max_uses']}"
    st = "✅ نشط" if lnk["is_active"] else "❌ متوقف"
    edit(call,
        f"<b>🎁 كود: {code}</b>\n\n"
        f"<b>━━━━━━━━━━━━━━━</b>\n"
        f"النقاط: <b>{lnk['points_reward']:,}</b> نقطة\n"
        f"الاستخدامات: <b>{uses}</b>\n"
        f"الحالة: {st}\n"
        f"<b>━━━━━━━━━━━━━━━</b>\n\n"
        f"🔗 رابط الهدية الجاهز:\n<code>{url}</code>",
        mk(
            [_btn("🗑️ حذف الكود", f"adm_del_invite_{code}", color="red")],
            [_btn("◀️ رجوع",       "adm_invite_links",        color="blue")],
        ))



# ── مُعالجات الإعدادات بالزر ──────────────────────────────────
_cfg_btn_map = {
    "adm_set_updates_ch":  ("updates_channel",      "adm_bot_settings"),
    "adm_set_support":     ("support_username",     "adm_bot_settings"),
    "adm_set_points_charge_info": ("points_charge_info", "adm_pts_settings"),
    "adm_set_charge_vodafone":    ("charge_vodafone_info", "adm_pts_settings"),
    "adm_set_charge_stars":       ("charge_stars_info", "adm_pts_settings"),
    "adm_set_stars_per_point":    ("stars_per_point",   "adm_bot_settings"),
    "adm_set_daily_pts":   ("daily_gift_points",    "adm_pts_settings"),
    "adm_set_weekly_pts":  ("weekly_gift_points",   "adm_pts_settings"),
    "adm_set_ref_pts":     ("referral_points",      "adm_pts_settings"),
    "adm_set_welcome_pts": ("welcome_points",       "adm_pts_settings"),
    "adm_set_wheel_hrs":   ("wheel_cooldown_hrs",   "adm_pts_settings"),
    "adm_set_free_limit":  ("free_services_daily_limit", "adm_pts_settings"),
    "adm_set_svc_id":      ("service_id",           "adm_service_cfg"),
    "adm_set_p1k":         ("points_per_1000",      "adm_service_cfg"),
    "adm_set_svc_min":     ("service_min",          "adm_service_cfg"),
    "adm_set_svc_max":     ("service_max",          "adm_service_cfg"),
    "adm_set_menu_services": ("menu_services_label", "adm_menu_labels"),
    "adm_set_menu_fund":     ("menu_fund_label", "adm_menu_labels"),
    "adm_set_menu_collect":  ("menu_collect_points_label", "adm_menu_labels"),
    "adm_set_menu_account":  ("menu_account_label", "adm_menu_labels"),
    "adm_set_menu_use_code": ("menu_use_code_label", "adm_menu_labels"),
    "adm_set_menu_transfer": ("menu_transfer_label", "adm_menu_labels"),
    "adm_set_menu_track_order": ("menu_track_order_label", "adm_menu_labels"),
    "adm_set_menu_my_orders": ("menu_my_orders_label", "adm_menu_labels"),
    "adm_set_menu_channels": ("menu_channels_label", "adm_menu_labels"),
    "adm_set_menu_updates":  ("menu_updates_label", "adm_menu_labels"),
    "adm_set_menu_store":    ("menu_store_label", "adm_menu_labels"),
    "adm_set_menu_terms":    ("menu_terms_label", "adm_menu_labels"),
}
_cfg_labels = {
    "adm_set_updates_ch":  "رابط قناة التحديثات",
    "adm_set_support":     "يوزر الدعم",
    "adm_set_points_charge_info": "معلومات شحن النقاط",
    "adm_set_charge_vodafone": "بيانات فودافون كاش",
    "adm_set_charge_stars":    "بيانات النجوم",
    "adm_set_stars_per_point": "نقاط لكل نجمة (مثال: 10)",
    "adm_set_daily_pts":   "نقاط الهدية اليومية",
    "adm_set_weekly_pts":  "نقاط الهدية الأسبوعية",
    "adm_set_ref_pts":     "نقاط الإحالة",
    "adm_set_welcome_pts": "نقاط الترحيب",
    "adm_set_wheel_hrs":   "ساعات انتظار العجلة",
    "adm_set_free_limit":  "حد الخدمات المجانية يومياً",
    "adm_set_svc_id":      "معرف الخدمة",
    "adm_set_p1k":         "السعر لكل 1000 (نقاط)",
    "adm_set_svc_min":     "الحد الأدنى للكمية",
    "adm_set_svc_max":     "الحد الأقصى للكمية",
    "adm_set_menu_services": "عنوان زر الخدمات",
    "adm_set_menu_fund":     "عنوان زر شحن مباشر",
    "adm_set_menu_collect":  "عنوان زر تجميع نقاط",
    "adm_set_menu_account":  "عنوان زر اداره الحساب",
    "adm_set_menu_use_code": "عنوان زر استخدام كود",
    "adm_set_menu_transfer": "عنوان زر تحويل نقاط",
    "adm_set_menu_track_order": "عنوان زر متابعة طلب",
    "adm_set_menu_my_orders": "عنوان زر جميع طلباتي",
    "adm_set_menu_channels": "عنوان زر قنوات البوت",
    "adm_set_menu_updates":  "عنوان زر قناه الاثبتات",
    "adm_set_menu_store":    "عنوان زر متجر البوت",
    "adm_set_menu_terms":    "عنوان زر الشروط",
}


def _make_cfg_handler(ev):
    @bot.callback_query_handler(func=lambda c, e=ev: c.data == e)
    def _h(call: CallbackQuery, _ev=ev):
        if not is_admin(call.from_user.id):
            return
        set_state(call.from_user.id, _ev)
        lbl = _cfg_labels.get(_ev, "الإعداد")
        edit(call, f"أرسل القيمة الجديدة لـ <b>{lbl}</b>:", kb.back("adm_back"))


for _ev in _cfg_btn_map:
    _make_cfg_handler(_ev)


# ═══════════════════════════════════════════════════════
# ══════════════════════════════════════════════════════════════════
#   MIRX — نقطة الدخول المبكرة
# ══════════════════════════════════════════════════════════════════
# يجب تسجيل هذا الـ handler قبل msg_router لأن msg_router عام ويطابق
# كل الرسائل النصية، وبالتالي كان يلتقط /mirx قبل وصوله للوحة الجديدة.
@bot.message_handler(commands=["mirx"])
def mirx_command(msg: Message):
    """فتح لوحة MIRX الجديدة مباشرة من /mirx."""
    if not mirx_guard(msg.from_user.id):
        send(msg.chat.id, "❌ أمر MIRX متاح للمطور فقط.")
        return
    clear_state(msg.from_user.id)
    try:
        bot.send_message(
            msg.chat.id,
            mirx_home_text(),
            reply_markup=mirx_home_keyboard(),
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"[MIRX OPEN ERROR] {e}")
        try:
            bot.send_message(msg.chat.id, "❌ تعذر فتح لوحة MIRX. حاول مرة أخرى.")
        except Exception:
            pass


# ══════════════════════════════════════════════════════════════════
#   13. معالج الرسائل النصية (Router)
# ══════════════════════════════════════════════════════════════════
@bot.message_handler(func=lambda m: True, content_types=["text", "photo", "video", "document"])
def msg_router(msg: Message):
    uid = msg.from_user.id

    # ضمان تشغيل /king حتى لو Telegram أرسل الأمر بصيغة مختلفة
    # أو لم يلتقطه command handler؛ لا يغير أي أمر آخر.
    _txt = (getattr(msg, "text", None) or "").strip()
    if _txt.lower().split()[0].split("@")[0] == "/king" if _txt else False:
        if _txt.lower() == "/king" or _txt.lower().startswith("/king@"):
            _open_king(msg)
            return

    state = get_state(uid)
    s = state.get("state")
    d = state.get("data", {})

    # ─── MIRX: مسار موحّد لإضافة حساب Telegram ─────────────────
    # كل خطوات إضافة الحساب بتتم عبر mirx_tg_flow_router الجديد،
    # وليس عبر الدوال القديمة اللي كانت بتقفل الاتصال وبتضيّع
    # الـ phone_code_hash بين الرسائل.
    _mirx_tg_steps = ("api_id", "api_hash", "phone", "code", "2fa")
    if uid in _MIRX_TG_SESSIONS and _MIRX_TG_SESSIONS[uid].get("step") in _mirx_tg_steps:
        return mirx_tg_flow_router(msg)

    _mirx_state_handlers = {
        "mirx_add_app": "mirx_message_add_app",
        "mirx_add_service": "mirx_message_add_service",
        "mirx_add_mandatory": "mirx_message_add_mandatory",
        "mirx_add_points_channel": "mirx_message_add_points_channel",
        "mirx_add_order_channel": "mirx_message_add_order_channel",
        "mirx_search_user": "mirx_message_search_user",
        "mirx_broadcast": "mirx_message_broadcast",
        "mirx_change_low_alert": "mirx_message_change_low_alert",
        "mirx_change_support": "mirx_message_change_support",
        "mirx_multi_wait_word": "mirx_msg_multi_wait_word",
        "mirx_multi_confirm": "mirx_msg_multi_confirm",
    }
    if s in _mirx_state_handlers:
        _h = globals().get(_mirx_state_handlers[s])
        if _h is not None:
            return _h(msg)

    if config.TRACK_MESSAGES and not is_admin(uid):
        # Forward message to admins for tracking
        for admin_id in config.ADMIN_IDS:
            try:
                if msg.content_type == "text":
                    bot.send_message(
                        admin_id, 
                        f"📩 من المستخدم: {msg.from_user.first_name or 'غير معروف'} (@{msg.from_user.username or 'لا يوجد'}) - ID: {uid}\n\n{msg.text}"
                    )
                else:
                    bot.copy_message(
                        admin_id, 
                        msg.chat.id, 
                        msg.message_id, 
                        caption=f"📩 من المستخدم: {msg.from_user.first_name or 'غير معروف'} (@{msg.from_user.username or 'لا يوجد'}) - ID: {uid}"
                    )
            except Exception:
                pass  # Ignore forwarding errors

    # ─── المستخدم: كود دعوة ──────────────────────────────────
    if s == "waiting_invite_code":
        code = (msg.text or "").strip().upper()
        ok, pts, err = db.claim_invite(uid, code)
        if ok:
            send(msg.chat.id, f"<b>✅ تم تفعيل الكود!</b>\n\nحصلت على <b>{pts}</b> نقطة!", kb.back())
        else:
            send(msg.chat.id, f"<b>❌ خطأ:</b> {err}", kb.back())
        clear_state(uid)
        return

    if not is_admin(uid):
        return

    # ═══════════════ الأدمن ══════════════════════════════════

    if s == "adm_multi_count":
        try:
            sid = int(d.get("svc_id"))
            requested = int((msg.text or "").strip())
        except Exception:
            send(msg.chat.id, "❌ اكتب عدد الحسابات كرقم فقط، مثل: <code>7</code>")
            return
        svc = db.get_service(sid)
        selected = db.get_service_telegram_accounts(sid) if svc else []
        actual = len(selected)
        if not svc:
            clear_state(uid)
            return
        if requested != actual or requested <= 0:
            send(msg.chat.id,
                 f"❌ العدد غير مطابق.\n\n"
                 f"عدد الحسابات المرتبطة فعلياً: <b>{actual}</b>\n"
                 f"أنت كتبت: <b>{requested}</b>\n\n"
                 f"اكتب العدد الصحيح: <code>{actual}</code>")
            return
        set_state(uid, "adm_multi_wait_confirm", svc_id=sid, count=actual)
        send(msg.chat.id,
             f"<b>🔎 تم التحقق من العدد</b>\n\n"
             f"الخدمة: <b>{svc.get('name','الخدمة')}</b>\n"
             f"الحسابات المضافة: <b>{actual}</b>\n\n"
             f"هل تريد تأكيد تفعيل <b>{actual}</b> حسابات كمتعدد لهذه الخدمة؟",
             mk([_btn(f"✅ نعم، فعّل {actual} حساب", f"adm_multi_confirm_{sid}_{actual}", color="green"),
                 _btn("❌ لا", f"adm_multi_cancel_{sid}", color="red")]))
        return

    if s == "adm_multi_wait_confirm":
        send(msg.chat.id, "استخدم أزرار التأكيد الموجودة أمامك.")
        return

    if s == "adm_edit_app":
        try:
            app_id = d.get("app_id")
            new_name = (msg.text or "").strip()
            if not new_name:
                raise ValueError("الاسم فارغ")
            db.update_app(app_id, name=new_name)
            send(msg.chat.id,
                 f"✅ تم تحديث اسم القسم إلى: {new_name}",
                 kb.admin_app_view(app_id, db.get_app_services(app_id, only_active=False)))
        except Exception as e:
            send(msg.chat.id, f"❌ خطأ: {e}\n<code>النقاط|اسم الخدمة|الحد الأدنى|الحد الأقصى</code>")
        return

    if s == "adm_edit_svc":
        try:
            sid = d.get("svc_id")
            new_name = (msg.text or "").strip()
            if not new_name:
                raise ValueError("الاسم فارغ")
            db.update_service(sid, name=new_name)
            svc = db.get_service(sid)
            send(msg.chat.id,
                 f"✅ تم تحديث اسم الخدمة إلى: {new_name}",
                 kb.admin_svc_view(sid, svc["app_id"]))
        except Exception as e:
            send(msg.chat.id, f"❌ خطأ: {e}\n<code>النقاط|اسم الخدمة|الحد الأدنى|الحد الأقصى</code>")
        return

    if s == "adm_edit_free_apiid":
        try:
            sid = d.get("svc_id")
            new_val = (msg.text or "").strip()
            if not new_val:
                raise ValueError("القيمة فارغة")
            db.update_free_service(sid, api_service_id=new_val)
            send(msg.chat.id,
                 f"✅ تم تحديث معرف الخدمة إلى: <code>{new_val}</code>",
                 kb.admin_free_svc_view(sid))
        except Exception as e:
            send(msg.chat.id, f"❌ خطأ: {e}\n<code>النقاط|اسم الخدمة|الحد الأدنى|الحد الأقصى</code>")
        return

    if s == "adm_add_app":
        try:
            raw = (msg.text or "").strip()
            if not raw:
                raise ValueError("اسم القسم فارغ")
            parts = raw.split("|", 1)
            if len(parts) == 2:
                name = parts[0].strip()
                emoji = parts[1].strip() or "📱"
            else:
                # يقبل مباشرة: 🚀 خدمات تيليجرام — رشق وتفاعل
                # ويستخرج الإيموجي الأول حتى لا يظهر مكررًا في الزر.
                name = raw
                emoji = "📱"
                for lead in ("🚀", "📱", "🎯", "💎", "🔥", "⭐", "👥", "👁️", "👍", "🛠️", "⚙️"):
                    if raw.startswith(lead):
                        emoji = lead
                        name = raw[len(lead):].strip() or raw
                        break
            if not name:
                raise ValueError("اسم القسم فارغ")
            # إضافة القسم بعملية كتابة واحدة ثم الرد فوراً؛ لا نعيد تحميل كل الأقسام هنا.
            app_id = db.add_app(name, emoji)
            send(msg.chat.id,
                 f"<b>✅ تم إضافة القسم</b>\n\n"
                 f"{emoji} <b>{name}</b>\n"
                 f"رقم القسم (ID): <code>{app_id}</code>\n\n"
                 f"الآن اضغط على <b>◀️ رجوع للأقسام</b> ثم اختر القسم وأضف الخدمة.",
                 kb.back("adm_apps"))
        except Exception as e:
            send(msg.chat.id, f"❌ خطأ: {e}\n<code>اسم القسم|الإيموجي</code> أو أرسل الاسم مع الإيموجي في أوله.")
        return

    if s == "adm_add_svc":
        try:
            parts=(msg.text or "").strip().split("|",3)
            if len(parts) != 4:
                raise ValueError("استخدم: النقاط|اسم الخدمة|الحد الأدنى|الحد الأقصى")
            pts=int(parts[0].strip()); custom_name=parts[1].strip()
            mn=int(parts[2].strip()); mx=int(parts[3].strip())
            if not custom_name: raise ValueError("اسم الخدمة فارغ")
            if pts<=0 or mn<1 or mx<mn: raise ValueError("تحقق من النقاط والحدود")

            service_type, emoji, pool = _detect_service_meta(custom_name)
            app_id=int(d.get("app_id") or 0)
            if not app_id:
                app_id=_get_or_create_rush_app()

            public_id=db.add_service(
                app_id, custom_name, emoji, pts, mn, mx,
                service_type, emoji,
                "random" if pool and len(pool.split(","))>1 else "fixed",
                pool, 0, ""
            )
            clear_state(uid)
            app=db.get_app(app_id)
            app_name=(f"{app.get('emoji') or '📦'} {app.get('name') or 'القسم'}") if app else "القسم"
            styled=_service_display_name({"name":custom_name})
            send(
                msg.chat.id,
                f"<b>✅ تمت إضافة الخدمة</b>\n\n"
                f"{styled}\n\n"
                f"📁 القسم: <b>{app_name}</b>\n"
                f"🧩 النوع المكتشف: <b>{service_type}</b>\n"
                f"🆔 ID الخدمة: <code>{public_id}</code>\n"
                f"💎 السعر: <b>{pts}</b> / 1000\n"
                f"📦 الحدود: <b>{mn:,} — {mx:,}</b>",
                kb.back("adm_cat_services")
            )
        except Exception as e:
            send(msg.chat.id, f"❌ خطأ: {str(e)[:180]}\n<code>النقاط|اسم الخدمة|الحد الأدنى|الحد الأقصى</code>")
        return

    if s == "adm_add_orch":
        try:
            parts = [p.strip() for p in (msg.text or "").strip().split("|")]
            if len(parts) < 2:
                raise ValueError("لازم: channel_id|الاسم")
            ch_id = parts[0]
            name = parts[1]
            ok = db.add_order_channel(ch_id, name)
            if ok:
                # اختبار الإرسال
                try:
                    bot.send_message(ch_id, "<b>✅ تم ربط قناة الطلبات بالبوت!</b>\n\nستظهر تفاصيل الطلبات هنا.")
                except Exception as test_e:
                    send(msg.chat.id, f"<b>⚠️ تمت الإضافة لكن فشل اختبار الإرسال!</b>\n\nتأكد أن البوت أدمن في القناة.\n\nخطأ: {test_e}")
                    clear_state(uid)
                    return
                send(msg.chat.id, f"<b>✅ تمت إضافة القناة!</b>\n{name}", kb.back("adm_order_channels"))
            else:
                send(msg.chat.id, "القناة موجودة مسبقاً!", kb.back("adm_order_channels"))
        except Exception as e:
            send(msg.chat.id, f"❌ خطأ: {e}\n<code>النقاط|اسم الخدمة|الحد الأدنى|الحد الأقصى</code>")
        return

    if s == "adm_db_import":
        # استيراد من ملف JSON
        if msg.document:
            try:
                file_info = bot.get_file(msg.document.file_id)
                downloaded = bot.download_file(file_info.file_path)
                json_str = downloaded.decode("utf-8")
                ok, result_msg = db.import_db_json(json_str)
                send(msg.chat.id,
                    f"{'✅' if ok else '❌'} {result_msg}",
                    kb.back("adm_database"))
            except Exception as e:
                send(msg.chat.id, f"❌ خطأ في قراءة الملف: {e}", kb.back("adm_database"))
        elif msg.text:
            try:
                ok, result_msg = db.import_db_json(msg.text.strip())
                send(msg.chat.id,
                    f"{'✅' if ok else '❌'} {result_msg}",
                    kb.back("adm_database"))
            except Exception as e:
                send(msg.chat.id, f"❌ خطأ في الاستيراد: {e}", kb.back("adm_database"))
            send(msg.chat.id, "أرسل ملف JSON أو انسخ محتواه.", kb.back("adm_database"))
        clear_state(uid)
        return

    if s == "adm_wheel_add":
        try:
            parts = [p.strip() for p in (msg.text or "").strip().split("|")]
            if len(parts) < 2:
                raise ValueError("لازم: النقاط|الوزن")
            pts = int(parts[0])
            weight = float(parts[1])
            emoji = parts[2] if len(parts) > 2 else ""
            label = parts[3] if len(parts) > 3 else ""
            if pts <= 0 or weight <= 0:
                raise ValueError("القيم لازم أكبر من صفر")
            db.add_wheel_prize(pts, weight, emoji, label)
            send(msg.chat.id,
                f"✅ تمت الإضافة: <b>{pts:,}</b> نقطة | وزن {weight:g} {emoji} {label}",
                kb.back("adm_wheel"))
        except Exception as e:
            send(msg.chat.id, f"❌ خطأ: {e}\n<code>النقاط|اسم الخدمة|الحد الأدنى|الحد الأقصى</code>")
        return

    if s == "adm_add_store_product":
        try:
            parts = [p.strip() for p in (msg.text or "").strip().split("|")]
            if len(parts) < 2:
                raise ValueError("لازم: الاسم|السعر")
            name  = parts[0]
            price = int(parts[1])
            emoji = parts[2] if len(parts) > 2 else "🛍️"
            desc  = parts[3] if len(parts) > 3 else ""
            stock = int(parts[4]) if len(parts) > 4 else -1
            if price <= 0:
                raise ValueError("السعر لازم أكبر من صفر")
            db.add_store_product(name, desc, emoji, price, stock)
            send(msg.chat.id,
                f"<b>✅ تمت إضافة المنتج!</b>\n\n"
                f"{emoji} <b>{name}</b>\n"
                f"السعر: <b>{price:,}</b> نقطة\n"
                f"المخزون: {'غير محدود' if stock == -1 else stock}",
                kb.back("adm_store"))
        except Exception as e:
            send(msg.chat.id,
                f"❌ خطأ: {e}\n<code>الاسم|السعر|الإيموجي|الوصف|المخزون</code>")
        clear_state(uid)
        return

    if s == "adm_create_invite":
        try:
            parts = (msg.text or "").strip().split("|")
            if len(parts) < 3:
                raise ValueError("لازم 3 حقول")
            code = parts[0].strip().upper()
            pts = int(parts[1])
            mx = int(parts[2])
            ok = db.create_invite(code, pts, mx)
            if ok:
                bu = config.BOT_USERNAME.lstrip("@")
                url = f"https://t.me/{bu}?start=invite_{code}"
                send(msg.chat.id,
                    f"<b>✅ تم الإنشاء!</b>\n\n"
                    f"الكود: <code>{code}</code>\n"
                    f"النقاط: {pts:,}\n"
                    f"الحد: {'∞' if mx == 0 else mx}\n\n"
                    f"الرابط:\n<code>{url}</code>",
                    kb.back("adm_invite_links"))
            else:
                send(msg.chat.id, "❌ الكود موجود مسبقاً!", kb.back("adm_invite_links"))
        except Exception as e:
            send(msg.chat.id, f"❌ خطأ: {e}\n<code>النقاط|اسم الخدمة|الحد الأدنى|الحد الأقصى</code>")
        return

    # ─── تغيير الإعدادات ───────────────────────────────────
    cfg_map = {
        "adm_set_updates_ch":  ("updates_channel",      "adm_bot_settings"),
        "adm_set_support":     ("support_username",     "adm_bot_settings"),
        "adm_set_points_charge_info": ("points_charge_info", "adm_pts_settings"),
        "adm_set_charge_vodafone":    ("charge_vodafone_info", "adm_pts_settings"),
        "adm_set_charge_stars":       ("charge_stars_info", "adm_pts_settings"),
        "adm_set_stars_per_point":    ("stars_per_point",   "adm_bot_settings"),
        "adm_set_daily_pts":   ("daily_gift_points",    "adm_pts_settings"),
        "adm_set_weekly_pts":  ("weekly_gift_points",   "adm_pts_settings"),
        "adm_set_ref_pts":     ("referral_points",      "adm_pts_settings"),
        "adm_set_welcome_pts": ("welcome_points",       "adm_pts_settings"),
        "adm_set_wheel_hrs":   ("wheel_cooldown_hrs",   "adm_pts_settings"),
        "adm_set_free_limit":  ("free_services_daily_limit", "adm_pts_settings"),
        "adm_set_svc_id":      ("service_id",           "adm_service_cfg"),
        "adm_set_p1k":         ("points_per_1000",      "adm_service_cfg"),
        "adm_set_svc_min":     ("service_min",          "adm_service_cfg"),
        "adm_set_svc_max":     ("service_max",          "adm_service_cfg"),
        "adm_set_menu_services": ("menu_services_label", "adm_menu_labels"),
        "adm_set_menu_fund":     ("menu_fund_label", "adm_menu_labels"),
        "adm_set_menu_collect":  ("menu_collect_points_label", "adm_menu_labels"),
        "adm_set_menu_account":  ("menu_account_label", "adm_menu_labels"),
        "adm_set_menu_use_code": ("menu_use_code_label", "adm_menu_labels"),
        "adm_set_menu_transfer": ("menu_transfer_label", "adm_menu_labels"),
        "adm_set_menu_track_order": ("menu_track_order_label", "adm_menu_labels"),
        "adm_set_menu_my_orders": ("menu_my_orders_label", "adm_menu_labels"),
        "adm_set_menu_channels": ("menu_channels_label", "adm_menu_labels"),
        "adm_set_menu_updates":  ("menu_updates_label", "adm_menu_labels"),
        "adm_set_menu_store":    ("menu_store_label", "adm_menu_labels"),
        "adm_set_menu_terms":    ("menu_terms_label", "adm_menu_labels"),
    }
    if s in cfg_map:
        key, back_cb = cfg_map[s]
        val = (msg.text or "").strip()
        db.set_config(key, val)
        send(msg.chat.id, f"✅ تم التحديث: <b>{val}</b>", kb.back(back_cb))
        clear_state(uid)
        return


# ══════════════════════════════════════════════════════════════════
#   تنفيذ خدمات Telegram بالحساب المركزي
# ══════════════════════════════════════════════════════════════════
def _parse_telegram_message_link(link):
    """تحليل روابط منشورات Telegram العامة وروابط /c الداخلية."""
    raw = (link or "").strip()
    if raw.startswith("@"):
        raise ValueError("أرسل رابط منشور كامل مثل https://t.me/channel/123")
    if not raw.startswith(("http://", "https://")):
        raw = "https://" + raw.lstrip("/")

    parsed = urlparse(raw)
    host = (parsed.netloc or "").lower().split(":")[0]
    if host not in ("t.me", "telegram.me", "www.t.me", "www.telegram.me"):
        raise ValueError("الرابط يجب أن يكون رابط Telegram من نوع t.me")

    parts = [p for p in parsed.path.split("/") if p]
    if parts and parts[0] == "s":
        parts = parts[1:]
    if len(parts) < 2:
        raise ValueError("الرابط لا يحتوي على رقم المنشور")

    if parts[0] == "c":
        if len(parts) < 3 or not parts[1].isdigit() or not parts[2].isdigit():
            raise ValueError("رابط t.me/c غير صحيح")
        peer = int("-100" + parts[1])
        msg_id = int(parts[2])
    else:
        username = parts[0]
        if username.startswith("+") or username.startswith("joinchat"):
            raise ValueError("روابط الدعوة الخاصة ليست روابط منشورات مدعومة")
        if not parts[1].isdigit():
            raise ValueError("رقم المنشور غير صحيح")
        peer = username
        msg_id = int(parts[1])

    if msg_id <= 0:
        raise ValueError("رقم المنشور غير صحيح")
    return peer, msg_id


def _execute_telegram_reaction(o, svc, account=None, emoji=None):
    """تنفيذ تفاعل Telegram فعلي من حساب محدد مرتبط بالخدمة."""
    service_type = (svc.get("service_type") or "").strip()
    if service_type not in ("قلب", "تفاعل"):
        raise RuntimeError(f"الخدمة ليست خدمة تفاعل Telegram: {service_type or 'غير محدد'}")

    if account is None:
        account = db.get_service_telegram_account(svc)
    if not account:
        raise RuntimeError("لا يوجد حساب Telegram مفعّل مرتبط بهذه الخدمة.")

    session_path = account["session_path"]
    api_id = account["api_id"] or config.TG_API_ID
    api_hash = account["api_hash"] or config.TG_API_HASH
    if not session_path or not api_id or not api_hash:
        raise RuntimeError("بيانات Session / API لحساب التنفيذ غير مكتملة.")

    # استخدم الإيموجي المحدد فعلياً للخدمة، مع احترام reaction_pool
    # وreaction_mode (ثابت/عشوائي) بدلاً من تجاهل إعدادات الخدمة.
    if not emoji:
        emoji = _pick_reaction_emoji(svc)
    if not emoji:
        raise RuntimeError("الخدمة لا تحتوي على إيموجي تفاعل محدد.")

    peer, msg_id = _parse_telegram_message_link(o["link"])
    client = None
    try:
        client = _tg_connect(session_path, api_id, api_hash)
        if not client.is_user_authorized():
            raise RuntimeError("Session حساب التنفيذ غير مسجل الدخول. أعد ربط الحساب.")

        # نستورد الدوال والأنواع هنا حتى يبقى تحميل Telethon متوافقاً مع النسخ الموجودة.
        from telethon import functions, types
        try:
            entity = client.get_entity(peer)
        except Exception as e:
            raise RuntimeError(f"تعذر الوصول للمنشور العام {peer}/{msg_id} بالحساب المضاف: {e}")
        # هذا هو طلب Telegram الحقيقي لإضافة Reaction من الحساب الحالي.
        # لا نستخدم Bot API ولا مزود مشاهدات خارجي هنا.
        client(functions.messages.SendReactionRequest(
            peer=entity,
            msg_id=msg_id,
            reaction=[types.ReactionEmoji(emoticon=emoji)],
            add_to_recent=False,
        ))

        # SendReactionRequest نفسه هو تأكيد Telegram بأن طلب التفاعل قُبل.
        # لا نعتمد على قراءة عدّاد reactions مباشرة بعد الإرسال، لأن Telegram
        # قد يتأخر في تحديث العداد/الكاش، وده كان سبب ظهور فشل وهمي لحسابات
        # إضافية رغم أن طلب الإرسال نفسه تم قبوله.
        # نعمل قراءة اختيارية للتشخيص فقط ولا نحوّل تأخر التحديث إلى فشل للطلب.
        try:
            client.get_messages(entity, ids=msg_id)
        except Exception:
            pass

        return emoji
    finally:
        if client:
            try:
                client.disconnect()
            except Exception:
                pass


# ══════════════════════════════════════════════════════════════════
#   محرك تنفيذ الخدمات — مسار مستقل عن واجهة البوت وقاعدة الطلبات
# ══════════════════════════════════════════════════════════════════
# إنشاء الطلب يتم في مسار البوت فقط، ثم يوضع رقم الطلب في Queue.
# الـWorker هو المسؤول عن التنفيذ الفعلي ولا يحبس معالج الرسائل/الأزرار.
_SERVICE_EXECUTION_QUEUE = queue.Queue()
_SERVICE_EXECUTION_STOP = object()

def enqueue_service_order(oid):
    try:
        _SERVICE_EXECUTION_QUEUE.put_nowait(int(oid))
    except Exception as e:
        print(f"[SERVICE QUEUE] enqueue error: {e}")

def _service_execution_worker():
    while True:
        oid = _SERVICE_EXECUTION_QUEUE.get()
        try:
            if oid is _SERVICE_EXECUTION_STOP:
                return
            oid = int(oid)
            # FIFO حقيقي: لا يبدأ الطلب التالي إلا بعد حسم حالة الطلب الحالي.
            if not db.claim_order_for_execution(oid):
                print(f"[SERVICE QUEUE] order #{oid} skipped: already claimed/finished")
                continue
            _execute_local_order_after_approval(oid)
        except Exception as e:
            print(f"[SERVICE WORKER] order #{oid}: {type(e).__name__}: {e}")
            try:
                if db.fail_order_and_refund(int(oid)):
                    row = db.get_order(int(oid))
                    if row:
                        bot.send_message(row["user_id"], f"<b>❌ فشل تنفيذ الطلب #{row.get('public_id') or row['id']}</b>\n\nتم استرداد نقاطك.")
            except Exception as refund_error:
                print(f"[SERVICE WORKER] refund error #{oid}: {refund_error}")
        finally:
            _SERVICE_EXECUTION_QUEUE.task_done()

# Worker واحد فقط حتى يكون ترتيب التنفيذ: الأول ثم الثاني ثم الثالث.
for _i in range(1):
    threading.Thread(target=_service_execution_worker, name=f"service-worker-{_i+1}", daemon=True).start()

# استرجاع أي طلبات مؤكدة بقيت pending بسبب Restart أو انقطاع لحظة الإدراج في الـQueue.
try:
    for _row in db.get_pending_execution_orders(100):
        enqueue_service_order(int(_row["id"]))
except Exception as _recovery_error:
    print(f"[SERVICE QUEUE] startup recovery error: {_recovery_error}")

def _completion_notice_worker():
    """يرسل إشعار الإكمال بعد 60 ثانية بشكل مستمر وقابل للاستمرار بعد Restart."""
    while True:
        try:
            rows = db.get_due_completion_notices(50)
            for row in rows:
                try:
                    public_oid = row.get("public_id") or str(row["id"])
                    text = (
                        f"<b>🎉 اكتمل طلبك</b>\n"
                        f"🧾 اسم الخدمة: <b>{row['service_name']}</b>\n"
                        f"🔗 الرابط: <code>{row['link']}</code>\n"
                        f"🪙 السعر: <b>{int(row['points_used'] or 0):,}</b> نقطة\n"
                        f"🗓 التاريخ: <b>{datetime.now().strftime('%Y-%m-%d %H:%M')}</b>\n"
                        f"🆔 الطلب: <b>{public_oid}</b>"
                    )
                    bot.send_message(row["user_id"], text)
                    db.mark_notified(row["id"])
                except Exception as e:
                    print(f"[ORDER NOTICE] #{row.get('id')}: {e}")
        except Exception as e:
            print(f"[ORDER NOTICE WORKER] {e}")
        time.sleep(5)

threading.Thread(target=_completion_notice_worker, name="order-completion-notice", daemon=True).start()

_REACTION_ROTATION_INDEX = {}
_REACTION_ROTATION_LOCK = threading.Lock()

def _execute_local_order_after_approval(oid):
    """تنفيذ طلب Reaction فعلياً بالحساب أو الحسابات المرتبطة بالخدمة."""
    o=db.get_order(oid)
    if not o:
        raise RuntimeError("الطلب غير موجود في قاعدة البيانات.")
    svc=db.get_service(o["service_id"])
    if not svc or (svc.get("service_type") or "").strip() not in ("قلب","تفاعل"):
        raise RuntimeError("الخدمة غير صالحة أو غير متاحة للتنفيذ.")
    try:
        accounts=db.get_service_telegram_accounts(svc["id"])
        if not accounts:
            legacy=db.get_service_telegram_account(svc); accounts=[legacy] if legacy else []
        if not accounts: raise RuntimeError("لا يوجد حساب Telegram مرتبط بهذه الخدمة.")
        mode = db.get_service_account_mode(svc)
        # وضع multi: نفّذ على كل الحسابات المحددة بالتوازي.
        # وضع single: نفّذ على أول حساب فقط.
        run_accounts = list(accounts) if mode == "multi" else list(accounts[:1])
        qty=len(run_accounts)
        used=[]; errors=[]

        # في الطلب المتعدد: كل حساب يأخذ Reaction مختلفاً من reaction_pool
        # قدر الإمكان. لا نسمح للحسابين أن يرسلا نفس الإيموجي إذا كانت القائمة
        # تحتوي على أكثر من خيار. لو الحسابات أكثر من الإيموجيات، نعيد الدورة فقط
        # بعد استنفاد كل الخيارات المتاحة.
        # القائمة الكاملة للتفاعلات الظاهرة في صور Telegram التي حددها المطور.
        # تستخدم كقائمة افتراضية للخدمات متعددة الحسابات، مع بقاء إمكانية
        # تخصيص reaction_pool للخدمة إذا أراد المطور قائمة مختلفة.
        default_reaction_pool = list(MIRX_DEFAULT_REACTION_EMOJIS)
        pool = _reaction_tokens(svc.get("reaction_pool") or "")
        # استبدال القالب القديم القصير بالقائمة الكاملة الجديدة.
        legacy_pool = {"❤️","👍","😂","😍","🔥","🥰","😎","👏"}
        if not pool or set(pool) == legacy_pool:
            pool = list(default_reaction_pool)
        elif not pool and svc.get("reaction_emoji"):
            pool = _reaction_tokens(svc.get("reaction_emoji"))
        # لو الخدمة القديمة كانت محفوظة بقائمة افتراضية، لكن اسمها يحتوي
        # على مجموعة محددة مثل 👍🥰❤️‍🔥🔥😍، استخدم المجموعة المكتوبة في الاسم.
        known = ["⭐","❤️","👍","👎","🔥","🥰","👏","😁","🤔","🤯","😱","🤬","😢","🎉","🤩","🤢","💩","🙏","👌","🕊️","🤡","🤧","😍","🐳","❤️‍🔥","🌚","🌭","💯","🤣","⚡","🍌","🏆","💔","😐","😑","🍓","🍾","💋","☝️","😈","😴","😭","🤓","👻","👨‍💻","👀","🎃","🙈","😇","😨","🤝","📝","😊","🤦","🎅","🎄","☃️","💅","😛","🗿","🆒","💘","🙉","🦄","😘","💊","🙊","😎","👾","🤷‍♂️","🤷","🤷‍♀️","😠"]
        named_pool = [em for em in known if em in str(svc.get("name") or "")]
        if len(named_pool) >= 2:
            pool = named_pool
        if not pool:
            pool = ["❤️"]
        # تدوير الإيموجيات بين الطلبات: كل حساب يأخذ إيموجياً مختلفاً قدر الإمكان،
        # والطلب التالي يبدأ من موضع مختلف حتى لا يكرر نفس الإيموجي لكل حساب كل مرة.
        if len(pool) > 1:
            pool = list(dict.fromkeys(pool))
        if len(pool) == 1:
            assigned_emojis = {account["id"]: pool[0] for account in run_accounts}
        else:
            with _REACTION_ROTATION_LOCK:
                start = _REACTION_ROTATION_INDEX.get(int(svc["id"]), 0) % len(pool)
                assigned_emojis = {
                    account["id"]: pool[(start + i) % len(pool)]
                    for i, account in enumerate(run_accounts)
                }
                _REACTION_ROTATION_INDEX[int(svc["id"])] = (start + len(run_accounts)) % len(pool)

        # الحسابات مستقلة، لذلك ننفذ التفاعلات بالتوازي لتقليل زمن الطلب
        # مع إبقاء كل حساب مستخدماً مرة واحدة داخل نفس الطلب.
        workers=max(1, min(len(run_accounts), 16))
        with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="tg-react") as pool_exec:
            future_map={pool_exec.submit(_execute_telegram_reaction, o, svc, account, assigned_emojis.get(account["id"])): account for account in run_accounts}
            for future in as_completed(future_map):
                account=future_map[future]
                label=account.get("first_name") or account.get("username") or str(account.get("id"))
                try:
                    emoji=future.result()
                    used.append((label,emoji))
                except Exception as e:
                    errors.append(f"{label}: {str(e)[:180]}")
        done=len(used)
        if done==qty:
            db.update_order(oid,"completed",f"telegram:{o['id']}")
            emojis=", ".join(x[1] for x in used)
            public_oid = o.get("public_id") if hasattr(o, "get") else None
            public_oid = public_oid or str(oid)
            # رسالة الإكمال لا تعتمد على Timer داخل الطلب؛
            # العامل الدائم أدناه سيجد الطلب بعد 60 ثانية حتى لو حصل Restart للبوت.
            return
        if done>0:
            p1k=int(svc.get("points_per_1000") or 0); charged=math.ceil(done*p1k/1000) if p1k else 0; refund=max(0,int(o["points_used"])-charged)
            if refund: db.add_points(o["user_id"],refund)
            db.update_order(oid,"partial",f"telegram:{done}/{qty}")
            bot.send_message(o["user_id"],f"<b>⚠️ تم تنفيذ جزء من الطلب</b>\n\nالمطلوب: <b>{qty}</b>\nتم التنفيذ: <b>{done}</b>\nتم استرداد: <b>{refund:,}</b> نقطة\n\n<code>{' | '.join(errors)[:800]}</code>")
            return
        raise RuntimeError("\n".join(errors) or "فشل تنفيذ التفاعلات من حسابات Telegram.")
    except Exception as e:
        refunded = False
        try:
            refunded = db.fail_order_and_refund(oid)
        except Exception as refund_error:
            print(f"[ORDER] failed to refund/cancel #{oid}: {refund_error}")
        if refunded:
            try:
                bot.send_message(o["user_id"],f"<b>❌ فشل تنفيذ الطلب #{oid}</b>\n\n<code>{str(e)[:700]}</code>\n\nتم استرداد نقاطك.")
            except Exception:
                pass


# منع تنفيذ أكثر من Reaction تلقائي لنفس المنشور.
_AUTO_REACTION_SEEN = set()
_AUTO_REACTION_SEEN_LOCK = threading.Lock()
_AUTO_REACTION_SEEN_MAX = 5000


def _reaction_tokens(value):
    """تجميع الإيموجي كـUnicode grapheme مبسط، حتى لا تتحول ❤️ إلى عنصرين."""
    import unicodedata
    text = (value or "").replace(",", "").strip()
    if not text:
        return []

    def is_modifier(ch):
        cp = ord(ch)
        return 0x1F3FB <= cp <= 0x1F3FF

    def is_variation(ch):
        cp = ord(ch)
        return 0xFE00 <= cp <= 0xFE0F

    def is_regional(ch):
        cp = ord(ch)
        return 0x1F1E6 <= cp <= 0x1F1FF

    out=[]
    current=""
    regional_count=0
    for ch in text:
        if ch.isspace():
            continue
        cp=ord(ch)
        if not current:
            current=ch
            regional_count=1 if is_regional(ch) else 0
            continue
        if ch == "\u200d" or current.endswith("\u200d"):
            current += ch
            continue
        if is_variation(ch) or is_modifier(ch) or unicodedata.combining(ch):
            current += ch
            continue
        if is_regional(ch) and regional_count == 1:
            current += ch
            regional_count=2
            continue
        out.append(current)
        current=ch
        regional_count=1 if is_regional(ch) else 0
    if current:
        out.append(current)
    return out


_LAST_REACTION_EMOJI = {}
_LAST_REACTION_EMOJI_LOCK = threading.Lock()

def _pick_reaction_emoji(svc):
    """اختيار Reaction واحد فقط لكل منشور، مع منع تكرار نفس الإيموجي مباشرة."""
    pool = _reaction_tokens(svc.get("reaction_pool") or "")
    if not pool and svc.get("reaction_emoji"):
        pool = _reaction_tokens(svc.get("reaction_emoji"))
    if not pool:
        pool = ["❤️"]

    mode = (svc.get("reaction_mode") or "random").strip().lower()
    sid = int(svc.get("id") or 0)
    if mode != "random" or len(pool) == 1:
        chosen = pool[0]
    else:
        with _LAST_REACTION_EMOJI_LOCK:
            previous = _LAST_REACTION_EMOJI.get(sid)
            choices = [x for x in pool if x != previous] or pool
            chosen = random.choice(choices)
            _LAST_REACTION_EMOJI[sid] = chosen
    return chosen


def _claim_auto_reaction(service_id, chat_id, message_id):
    key = (int(service_id), int(chat_id), int(message_id))
    with _AUTO_REACTION_SEEN_LOCK:
        if key in _AUTO_REACTION_SEEN:
            return False
        _AUTO_REACTION_SEEN.add(key)
        if len(_AUTO_REACTION_SEEN) > _AUTO_REACTION_SEEN_MAX:
            # حذف جزء من الأقدم عملياً بدون إبقاء الذاكرة تكبر بلا حدود.
            for old_key in list(_AUTO_REACTION_SEEN)[:1000]:
                _AUTO_REACTION_SEEN.discard(old_key)
        return True


def _auto_react_new_message(client, event, account_id=None):
    try:
        targets=db.get_reaction_targets()
        for t in targets:
            svc=db.get_service(t["service_id"])
            if not svc or not svc.get("auto_react") or not t.get("chat"):
                continue
            # التفاعل التلقائي محصور بخدمات قلب/تفاعل فقط.
            if (svc.get("service_type") or "").strip() not in ("قلب", "تفاعل"):
                continue

            # إذا حُدد حساب للخدمة، لا ينفذها أي حساب آخر.
            assigned = svc.get("telegram_account_id")
            if assigned:
                if account_id is None or int(assigned) != int(account_id):
                    continue
            else:
                # بدون حساب محدد: الحساب المركزي فقط، حتى لا يضع عدة حسابات
                # Reaction على نفس المنشور.
                central = db.get_execution_telegram_account()
                if not central or account_id is None or int(central["id"]) != int(account_id):
                    continue

            target=client.get_entity(t["chat"])
            if getattr(event,"chat_id",None) != getattr(target,"id",None):
                continue
            if not _claim_auto_reaction(t["service_id"], getattr(target,"id",0), event.id):
                continue

            # اختيار واحد فقط لكل منشور، مع إيموجي مختلف عن السابق قدر الإمكان.
            emoji=_pick_reaction_emoji(svc)

            # التنفيذ بطيء ومتسلسل حتى لا تتتابع التفاعلات بسرعة.
            try:
                delay = float(db.get_config("REACTION_EXECUTION_DELAY_SECONDS", "0.5"))
            except Exception:
                delay = 0.5
            delay = max(0.0, min(delay, 1.0))
            if delay:
                time.sleep(delay)

            from telethon import functions, types
            client(functions.messages.SendReactionRequest(
                peer=target,
                msg_id=event.id,
                reaction=[types.ReactionEmoji(emoticon=emoji)],
                add_to_recent=True
            ))
            print(f"[AUTO-REACTION] {t['chat']} #{event.id} -> {emoji}")
            break
    except Exception as e:
        print(f"[AUTO-REACTION] {e}")

def start_reaction_monitor():
    """مراقبة المنشورات الجديدة مع حساب واحد فقط لكل خدمة."""
    while True:
        clients=[]
        try:
            owner_id=int(getattr(config,"TG_EXECUTION_USER_ID",0) or 0)
            accounts=db.list_telegram_accounts(owner_id) if owner_id else []
            if not accounts:
                time.sleep(30); continue
            from telethon import events
            for account in accounts:
                client=_tg_connect(account["session_path"],account["api_id"],account["api_hash"])
                if not client.is_user_authorized():
                    client.disconnect(); continue
                aid=int(account["id"])
                @client.on(events.NewMessage)
                async def handler(event, _client=client, _aid=aid):
                    _auto_react_new_message(_client,event,_aid)
                clients.append(client)
            if not clients:
                time.sleep(30); continue
            print(f"[AUTO-REACTION] monitors started: {len(clients)}")
            while True:
                alive=False
                for c in clients:
                    try:
                        if c.is_connected():
                            alive=True
                            c.loop.run_until_complete(asyncio.sleep(1))
                    except Exception as e:
                        print(f"[AUTO-REACTION] client error: {e}")
                if not alive: break
        except Exception as e:
            print(f"[AUTO-REACTION] monitor stopped: {e}")
            time.sleep(30)
        finally:
            for c in clients:
                try: c.disconnect()
                except Exception: pass


@bot.callback_query_handler(func=lambda c: c.data.startswith("adm_approve_local_") or c.data.startswith("adm_approve_fund_"))
def cb_adm_approve_local(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    parts = call.data.split("_")
    oid = int(parts[-1])
    o = db.get_order(oid)
    if not o or o["pending_approval"] == 0:
        bot.answer_callback_query(call.id, "الطلب معالج مسبقاً!", show_alert=True)
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
        return
    db.approve_order(oid)
    bot.answer_callback_query(call.id, "✅ تمت الموافقة، جارٍ التنفيذ...")
    try:
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        bot.edit_message_text(
            call.message.text + f"\n\n<b>✅ وافق عليه: {call.from_user.first_name}</b>",
            call.message.chat.id, call.message.message_id, parse_mode="HTML")
    except:
        pass
    enqueue_service_order(oid)


@bot.callback_query_handler(func=lambda c: c.data.startswith("adm_reject_local_") or c.data.startswith("adm_reject_fund_"))
def cb_adm_reject_local(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    parts = call.data.split("_")
    oid = int(parts[-1])
    o = db.reject_order(oid)
    if not o or o["pending_approval"] == 0:
        bot.answer_callback_query(call.id, "الطلب معالج مسبقاً!", show_alert=True)
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
        return
    bot.answer_callback_query(call.id, "❌ تم الرفض واسترداد النقاط")
    try:
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        bot.edit_message_text(
            call.message.text + f"\n\n<b>❌ رفضه: {call.from_user.first_name}</b>",
            call.message.chat.id, call.message.message_id, parse_mode="HTML")
    except:
        pass
    try:
        bot.send_message(o["user_id"],
            f"<b>❌ تم رفض طلبك #{oid}</b>\n\n"
            f"الخدمة: {o['service_name']}\n"
            f"<i>تم استرداد {o['points_used']:,} نقطة لحسابك.</i>")
    except:
        pass


@bot.callback_query_handler(func=lambda c: c.data.startswith("adm_approve_store_"))
def cb_adm_approve_store(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    oid = int(call.data.split("_")[-1])
    o = db.get_store_order(oid)
    if not o or o["pending_approval"] == 0:
        bot.answer_callback_query(call.id, "الطلب معالج مسبقاً!", show_alert=True)
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
        return
    db.approve_store_order(oid)
    bot.answer_callback_query(call.id, "✅ تمت الموافقة! تواصل مع المستخدم لتسليم المنتج")
    try:
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        bot.edit_message_text(
            call.message.text + f"\n\n<b>✅ وافق عليه: {call.from_user.first_name}</b>",
            call.message.chat.id, call.message.message_id, parse_mode="HTML")
    except:
        pass
    try:
        bot.send_message(o["user_id"],
            f"<b>✅ تمت الموافقة على طلب المتجر #{oid}!</b>\n\n"
            f"المنتج: {o['product_name']}\n\n"
            f"<i>سيتواصل معك الأدمن قريباً لتسليمك المنتج.</i>")
    except:
        pass


@bot.callback_query_handler(func=lambda c: c.data.startswith("adm_reject_store_"))
def cb_adm_reject_store(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    oid = int(call.data.split("_")[-1])
    o = db.reject_store_order(oid)
    if not o or o["pending_approval"] == 0:
        bot.answer_callback_query(call.id, "الطلب معالج مسبقاً!", show_alert=True)
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
        return
    bot.answer_callback_query(call.id, "❌ تم الرفض واسترداد النقاط")
    try:
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        bot.edit_message_text(
            call.message.text + f"\n\n<b>❌ رفضه: {call.from_user.first_name}</b>",
            call.message.chat.id, call.message.message_id, parse_mode="HTML")
    except:
        pass
    try:
        bot.send_message(o["user_id"],
            f"<b>❌ تم رفض طلب المتجر #{oid}</b>\n\n"
            f"المنتج: {o['product_name']}\n"
            f"<i>تم استرداد {o['points_used']:,} نقطة لحسابك.</i>")
    except:
        pass


# ─── قائمة الطلبات المعلقة (للأدمن) ──────────────────────────
@bot.callback_query_handler(func=lambda c: c.data == "adm_pending_orders")
def cb_adm_pending_orders(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    local_pending = db.get_pending_orders()
    store_pending = db.get_pending_store_orders()
    total = len(local_pending) + len(store_pending)
    if total == 0:
        edit(call, "<b>📋 الطلبات المعلقة</b>\n\nلا توجد طلبات معلقة حالياً.", kb.back("adm_back"))
        return
    text = f"<b>📋 الطلبات المعلقة ({total})</b>\n\n<b>━━━━━━━━━━━━━━━</b>\n"
    if local_pending:
        text += f"<b>طلبات الخدمات ({len(local_pending)}):</b>\n"
        for o in local_pending[:5]:
            text += f"  #{o['id']} — {o['service_name']} | {o['quantity']:,} وحدة\n"
    if store_pending:
        text += f"\n<b>طلبات المتجر ({len(store_pending)}):</b>\n"
        for o in store_pending[:5]:
            text += f"  #{o['id']} — {o['product_name']}\n"
    edit(call, text, kb.back("adm_back"))


# ══════════════════════════════════════════════════════════════════
#   المتجر المستقل — للمستخدم
# ══════════════════════════════════════════════════════════════════
@bot.callback_query_handler(func=lambda c: c.data == "store")
def cb_store(call: CallbackQuery):
    """سوق ترويجكم: يعرض كل الخدمات المضافة من لوحة المطور تلقائياً."""
    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass
    try:
        services = db.get_all_services(only_active=True)
        user = db.get_user(call.from_user.id)
        points = int(user["points"] if user else 0)
        if not services:
            edit(call,
                 "<b>🧺 سـوق تـرويـجـكـم</b>\n\n"
                 "لا توجد خدمات مضافة حالياً.\n"
                 "عند إضافة أي خدمة من لوحة المطور ستظهر هنا تلقائياً.",
                 kb.back("back_main"))
            return
        rows = []
        for svc in services:
            nm = _service_display_name(svc)
            rows.append([_btn(nm, f"store_svc_{svc['id']}", color="blue")])
        rows.append([_btn("◀️ رجوع للقائمة", "back_main", color="blue")])
        edit(call,
             f"<b>🧺 سـوق تـرويـجـكـم</b>\n\n"
             f"🪙 رصـيـدك - {points:,} نـقـطـة\n\n"
             "اختر الخدمة التي تريد طلبها:",
             mk(*rows))
    except Exception as e:
        print(f"[STORE SERVICES] error: {e}")
        edit(call, "❌ تعذر تحميل خدمات السوق حالياً.", kb.back("back_main"))


@bot.callback_query_handler(func=lambda c: c.data.startswith("store_product_"))
def cb_store_product(call: CallbackQuery):
    try:
        pid = int(call.data.split("_")[-1])
    except:
        return
    product = db.get_store_product(pid)
    if not product:
        bot.answer_callback_query(call.id, "المنتج غير موجود")
        return
    user = db.get_user(call.from_user.id)
    enough = user["points"] >= product["price"]
    nm = f"{product['emoji']} {product['name']}"
    stock_txt = "∞ متاح" if product["stock"] == -1 else f"{product['stock']:,} متبقي"
    warn = "" if enough else f"\n\n<b>⚠️ نقاطك غير كافية!</b> ينقصك <b>{product['price'] - user['points']:,}</b> نقطة."
    edit(call,
        f"<b>{nm}</b>\n\n"
        f"<b>━━━━━━━━━━━━━━━</b>\n"
        f"الوصف: {product['description'] or '—'}\n"
        f"السعر: <b>{product['price']:,}</b> نقطة\n"
        f"المخزون: {stock_txt}\n"
        f"رصيدك: <b>{user['points']:,}</b> نقطة\n"
        f"<b>━━━━━━━━━━━━━━━</b>{warn}",
        mk(
            [_btn("🛒 شراء الآن", f"store_buy_{pid}", color="green")] if enough else [],
            [_btn("◀️ رجوع للمتجر", "store", color="blue")],
        ) if enough else mk([_btn("◀️ رجوع للمتجر", "store", color="blue")]))


@bot.callback_query_handler(func=lambda c: c.data.startswith("store_buy_"))
def cb_store_buy(call: CallbackQuery):
    try:
        pid = int(call.data.split("_")[-1])
    except:
        return
    product = db.get_store_product(pid)
    if not product:
        bot.answer_callback_query(call.id, "المنتج غير موجود")
        return
    user = db.get_user(call.from_user.id)
    if user["points"] < product["price"]:
        bot.answer_callback_query(call.id, "نقاطك غير كافية!", show_alert=True)
        return
    if not db.deduct_points(call.from_user.id, product["price"]):
        bot.answer_callback_query(call.id, "نقاطك غير كافية!", show_alert=True)
        return
    nm = f"{product['emoji']} {product['name']}"
    oid = db.create_store_order(call.from_user.id, pid, nm, product["price"])
    user = db.get_user(call.from_user.id)

    # إشعار الأدمن
    _notify_admin_approve_store_order(oid, dict(user), nm, product["price"])

    edit(call,
        f"<b>⏳ تم إرسال طلب الشراء!</b>\n\n"
        f"<b>━━━━━━━━━━━━━━━</b>\n"
        f"رقم الطلب: <b>#{oid}</b>\n"
        f"المنتج: {nm}\n"
        f"النقاط المدفوعة: {product['price']:,}\n"
        f"رصيدك المتبقي: {user['points']:,}\n"
        f"<b>━━━━━━━━━━━━━━━</b>\n\n"
        f"<i>سيتواصل معك الأدمن قريباً لتسليمك المنتج</i>",
        kb.back())


@bot.callback_query_handler(func=lambda c: c.data == "my_store_orders")
def cb_my_store_orders(call: CallbackQuery):
    orders = db.get_user_store_orders(call.from_user.id, limit=8)
    if not orders:
        edit(call, "<b>طلبات المتجر</b>\n\nلا توجد طلبات بعد.", kb.back())
        return
    icons = {"pending_approval": "⏳", "approved": "✅", "rejected": "❌"}
    text = "<b>طلبات المتجر</b>\n\n"
    for o in orders:
        ic = icons.get(o["status"], "•")
        text += f"{ic} <b>طلب #{o['id']}</b> — {o['product_name']}\n"
        text += f"    النقاط: {o['points_used']:,} | {str(o['created_at'])[:10]}\n\n"
    edit(call, text, kb.back())


# ══════════════════════════════════════════════════════════════════
#   إدارة المتجر — أدمن
# ══════════════════════════════════════════════════════════════════
@bot.callback_query_handler(func=lambda c: c.data == "adm_store")
def cb_adm_store(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    products = db.get_store_products(only_active=False)
    pending = db.get_pending_store_orders()
    edit(call,
        f"<b>🛍️ إدارة المتجر</b>\n\n"
        f"المنتجات: <b>{len(products)}</b>\n"
        f"طلبات معلقة: <b>{len(pending)}</b>",
        kb.admin_store_keyboard(products))


@bot.callback_query_handler(func=lambda c: c.data == "adm_add_store_product")
def cb_adm_add_store_product(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    set_state(call.from_user.id, "adm_add_store_product")
    edit(call,
        "<b>➕ إضافة منتج للمتجر</b>\n\n"
        "أرسل بهذا الشكل:\n"
        "<code>الاسم|السعر بالنقاط|الإيموجي|الوصف|المخزون</code>\n\n"
        "أمثلة:\n"
        "<code>حساب نتفليكس|500|🎬|اشتراك شهري|10</code>\n"
        "<code>كارت شحن|1000|💳|كارت 10 جنيه|-1</code>\n\n"
        "<i>المخزون -1 = غير محدود</i>",
        kb.back("adm_store"))


@bot.callback_query_handler(func=lambda c: c.data.startswith("adm_store_product_"))
def cb_adm_store_product_view(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    pid = int(call.data.split("_")[-1])
    p = db.get_store_product(pid)
    if not p:
        bot.answer_callback_query(call.id, "المنتج غير موجود")
        return
    st = "✅ نشط" if p["is_active"] else "❌ متوقف"
    stock_txt = "∞ غير محدود" if p["stock"] == -1 else str(p["stock"])
    edit(call,
        f"<b>{p['emoji']} {p['name']}</b>\n\n"
        f"الحالة: {st}\n"
        f"السعر: <b>{p['price']:,}</b> نقطة\n"
        f"المخزون: {stock_txt}\n"
        f"الوصف: {p['description'] or '—'}",
        mk(
            [_btn("✅/❌ تفعيل/تعطيل", f"adm_tog_store_{pid}", color="green")],
            [_btn("🗑️ حذف المنتج", f"adm_del_store_{pid}", color="red")],
            [_btn("◀️ رجوع للمتجر", "adm_store", color="blue")],
        ))


@bot.callback_query_handler(func=lambda c: c.data.startswith("adm_tog_store_"))
def cb_adm_tog_store(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    pid = int(call.data.split("_")[-1])
    db.toggle_store_product(pid)
    bot.answer_callback_query(call.id, "تم التبديل")
    call.data = f"adm_store_product_{pid}"
    cb_adm_store_product_view(call)


@bot.callback_query_handler(func=lambda c: c.data.startswith("adm_del_store_"))
def cb_adm_del_store(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    pid = int(call.data.split("_")[-1])
    db.delete_store_product(pid)
    bot.answer_callback_query(call.id, "تم الحذف")
    cb_adm_store(call)


@bot.callback_query_handler(func=lambda c: c.data == "adm_pending_recharges")
def cb_adm_pending_recharges(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    reqs = db.get_pending_recharges()
    if not reqs:
        edit(call, "<b>💵 طلبات الشحن المعلقة</b>\n\nلا توجد طلبات معلقة.", kb.back("adm_back"))
        return
    text = f"<b>💵 طلبات الشحن المعلقة ({len(reqs)})</b>\n\n<b>━━━━━━━━━━━━━━━</b>\n"
    for r in reqs[:8]:
        user = db.get_user(r["user_id"])
        nm = user["full_name"] if user else str(r["user_id"])
        text += f"  #{r['id']} — {nm} | {r['method']} | {str(r['created_at'])[:10]}\n"
    text += "\n<i>ستوصلك صور الإيصالات مباشرة في المحادثة</i>"
    edit(call, text, kb.back("adm_back"))


# ══════════════════════════════════════════════════════════════════
#   كوبونات الخصم — مستخدم
# ══════════════════════════════════════════════════════════════════
@bot.callback_query_handler(func=lambda c: c.data == "use_coupon")
def cb_use_coupon(call: CallbackQuery):
    set_state(call.from_user.id, "enter_coupon")
    edit(call,
        "<b>🎟️ كوبون الخصم</b>\n\n"
        "أرسل كود الكوبون:",
        kb.back())


@bot.message_handler(func=lambda m: get_state(m.from_user.id).get("state") == "enter_coupon")
def msg_enter_coupon(msg: Message):
    uid = msg.from_user.id
    code = (msg.text or "").strip().upper()
    coupon = db.get_coupon(code)
    if not coupon:
        send(msg.chat.id, "❌ الكوبون غير موجود أو منتهي الصلاحية!")
        return
    if db.user_used_coupon(uid, coupon["id"]):
        send(msg.chat.id, "❌ لقد استخدمت هذا الكوبون من قبل!")
        return
    if coupon["max_uses"] != -1 and coupon["used_count"] >= coupon["max_uses"]:
        send(msg.chat.id, "❌ انتهت الاستخدامات المتاحة لهذا الكوبون!")
        return
    # احفظ الكوبون في الـ state
    d = get_state(uid).get("data", {})
    d["active_coupon_id"]       = coupon["id"]
    d["active_coupon_code"]     = code
    d["active_coupon_discount"] = coupon["discount"]
    set_state(uid, "coupon_active", d)
    clear_state(uid)
    send(msg.chat.id,
        f"<b>✅ تم تفعيل الكوبون!</b>\n\n"
        f"الكود: <code>{code}</code>\n"
        f"الخصم: <b>{coupon['discount']}%</b>\n\n"
        f"<i>الخصم سيطبق على طلبك القادم تلقائياً</i>",
        kb.back())
    # خزّن في session
    set_state(uid, "has_coupon", coupon_id=coupon["id"],
              code=code, discount=coupon["discount"])


# ══════════════════════════════════════════════════════════════════
#   ليدربورد
# ══════════════════════════════════════════════════════════════════
@bot.callback_query_handler(func=lambda c: c.data == "leaderboard")
def cb_leaderboard(call: CallbackQuery):
    top_pts   = db.get_leaderboard_points(10)
    top_orders = db.get_leaderboard_orders(10)
    medals = ["🥇", "🥈", "🥉"] + ["🔹"] * 7

    text = "<b>🏆 لوحة الصدارة</b>\n\n"
    text += "<b>💎 أكثر رصيداً:</b>\n"
    for i, u in enumerate(top_pts):
        nm = u["full_name"] or u["username"] or str(u["tg_id"])
        text += f"{medals[i]} {nm} — <b>{u['points']:,}</b> نقطة\n"

    text += "\n<b>📦 أكثر طلبات:</b>\n"
    for i, o in enumerate(top_orders):
        user = db.get_user(o["user_id"])
        nm = user["full_name"] if user else str(o["user_id"])
        text += f"{medals[i]} {nm} — <b>{o['cnt']:,}</b> طلب\n"

    edit(call, text, kb.back())


# ══════════════════════════════════════════════════════════════════
#   تتبع الطلب
# ══════════════════════════════════════════════════════════════════
@bot.callback_query_handler(func=lambda c: c.data == "track_order")
def cb_track_order(call: CallbackQuery):
    set_state(call.from_user.id, "track_order")
    edit(call,
        "<b>🔍 تتبع الطلب</b>\n\n"
        "أرسل رقم الطلب:",
        kb.back())


@bot.message_handler(func=lambda m: get_state(m.from_user.id).get("state") == "track_order")
def msg_track_order(msg: Message):
    uid = msg.from_user.id
    try:
        oid = int((msg.text or "").strip().lstrip("#"))
    except:
        send(msg.chat.id, "❌ رقم الطلب غير صحيح!")
        return
    o = db.get_order(oid)
    clear_state(uid)
    if not o or o["user_id"] != uid:
        send(msg.chat.id, "❌ لم يتم العثور على الطلب!")
        return
    status_map = {
        "pending":    "⏳ في الانتظار",
        "inprogress": "🔄 جارٍ التنفيذ",
        "completed":  "✅ مكتمل",
        "canceled":   "❌ ملغي",
        "partial":    "⚠️ مكتمل جزئي",
    }
    approval = "⏳ ينتظر موافقة الأدمن" if o["pending_approval"] == 1 else "✅ موافق عليه"
    st = status_map.get(o["status"], o["status"])
    send(msg.chat.id,
        f"<b>🔍 طلب #{oid}</b>\n\n"
        f"<b>━━━━━━━━━━━━━━━</b>\n"
        f"الخدمة: {o['service_name']}\n"
        f"القسم: {o['app_name'] or '—'}\n"
        f"الرابط: <code>{o['link']}</code>\n"
        f"الكمية: {o['quantity']:,}\n"
        f"النقاط: {o['points_used']:,}\n"
        f"الحالة: {st}\n"
        f"الموافقة: {approval}\n"
        f"التاريخ: {str(o['created_at'])[:16]}\n"
        f"<b>━━━━━━━━━━━━━━━</b>",
        kb.back())


# ══════════════════════════════════════════════════════════════════
#   إدارة روابط الهدايا — أدمن
# ══════════════════════════════════════════════════════════════════
@bot.callback_query_handler(func=lambda c: c.data == "adm_gift_links")
def cb_adm_gift_links(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    links = db.get_all_gift_links()
    text = f"<b>🎁 روابط الهدايا ({len(links)})</b>\n\n"
    rows = []
    for gl in links:
        st = "✅" if gl["is_active"] else "❌"
        uses = "∞" if gl["max_uses"] == -1 else f"{gl['used_count']}/{gl['max_uses']}"
        note_txt = f"  ({gl['note']})" if gl.get("note") else ""
        rows.append([_btn(
            f"{st} +{gl['points']} نقطة  ({uses}){note_txt}",
            f"adm_gift_link_{gl['id']}", color="green" if gl["is_active"] else "red")])
    rows.append([_btn("➕ إنشاء رابط هدية", "adm_create_gift_link", color="green")])
    rows.append([_btn("◀️ رجوع", "adm_back", color="blue")])
    edit(call, text or "<b>🎁 لا توجد روابط هدايا</b>", mk(*rows))


@bot.callback_query_handler(func=lambda c: c.data == "adm_create_gift_link")
def cb_adm_create_gift_link(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    set_state(call.from_user.id, "adm_create_gift_link")
    edit(call,
        "<b>➕ إنشاء رابط هدية جديد</b>\n\n"
        "أرسل بهذا الشكل:\n"
        "<code>النقاط|عدد الاستخدامات|ملاحظة (اختياري)</code>\n\n"
        "أمثلة:\n"
        "<code>100|50|هدية عيد الفطر</code>  — 100 نقطة لـ 50 شخص\n"
        "<code>500|-1</code>  — 500 نقطة غير محدودة",
        kb.back("adm_gift_links"))


@bot.callback_query_handler(func=lambda c: c.data.startswith("adm_gift_link_"))
def cb_adm_gift_link_view(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    gid = int(call.data.split("_")[-1])
    gl = db.get_conn().execute("SELECT * FROM gift_links WHERE id=?", (gid,)).fetchone()
    db.get_conn().close()
    if not gl:
        bot.answer_callback_query(call.id, "الرابط غير موجود")
        return
    # re-fetch properly
    conn = db.get_conn()
    gl = conn.execute("SELECT * FROM gift_links WHERE id=?", (gid,)).fetchone()
    conn.close()
    st = "✅ نشط" if gl["is_active"] else "❌ متوقف"
    uses = "غير محدود" if gl["max_uses"] == -1 else f"{gl['used_count']}/{gl['max_uses']}"
    bu = config.BOT_USERNAME.lstrip("@")
    link_https = f"https://t.me/{bu}?start=gift_{gl['code']}"
    edit(call,
        f"<b>🎁 رابط الهدية</b>\n\n"
        f"النقاط: <b>{gl['points']:,}</b>\n"
        f"الحالة: {st}\n"
        f"الاستخدامات: {uses}\n"
        f"الملاحظة: {gl.get('note') or '—'}\n\n"
        f"<b>انسخ الرابط:</b>\n<code>{link_https}</code>",
        mk(
            [_btn("🎁 افتح الهدية في البوت", url=link_https)],
            [_btn("📢 إرسال الهدية للقناة", f"adm_send_gift_{gid}", color="green")],
            [_btn("✅/❌ تفعيل/إيقاف", f"adm_tog_gift_{gid}", color="green")],
            [_btn("🗑️ حذف",            f"adm_del_gift_{gid}", color="red")],
            [_btn("◀️ رجوع",           "adm_gift_links",      color="blue")],
        ))


@bot.callback_query_handler(func=lambda c: c.data.startswith("adm_tog_gift_"))
def cb_adm_tog_gift(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    gid = int(call.data.split("_")[-1])
    db.toggle_gift_link(gid)
    bot.answer_callback_query(call.id, "تم التبديل")
    call.data = f"adm_gift_link_{gid}"
    cb_adm_gift_link_view(call)


@bot.callback_query_handler(func=lambda c: c.data.startswith("adm_send_gift_"))
def cb_adm_send_gift(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    gid = int(call.data.split("_")[-1])
    conn = db.get_conn()
    gl = conn.execute("SELECT * FROM gift_links WHERE id=?", (gid,)).fetchone()
    conn.close()
    if not gl:
        bot.answer_callback_query(call.id, "الرابط غير موجود")
        return
    set_state(call.from_user.id, "adm_send_gift_to_channel", gid=gid)
    edit(call,
        "<b>📢 إرسال الهدية للقناة</b>\n\n"
        "أرسل <b>معرف القناة</b> أو <b>يوزرنيم القناة</b>:\n\n"
        "أمثلة:\n"
        "<code>@mychannel</code>\n"
        "<code>-1001234567890</code>",
        kb.back(f"adm_gift_link_{gid}"))


@bot.message_handler(func=lambda m: get_state(m.from_user.id).get("state") == "adm_send_gift_to_channel")
def msg_send_gift_to_channel(msg: Message):
    if not is_admin(msg.from_user.id):
        return
    uid = msg.from_user.id
    channel = (msg.text or "").strip()
    d = get_state(uid).get("data", {})
    gid = d.get("gid")
    conn = db.get_conn()
    gl = conn.execute("SELECT * FROM gift_links WHERE id=?", (gid,)).fetchone()
    conn.close()
    if not gl:
        send(msg.chat.id, "❌ الرابط غير موجود!")
        clear_state(uid)
        return
    bu = config.BOT_USERNAME.lstrip("@")
    link_tg = f"https://t.me/{bu}?start=gift_{gl['code']}"
    note = gl.get("note") or "هدية مجانية"
    try:
        bot.send_message(
            channel,
            f"<b>🎁 {note}</b>\n\n"
            f"احصل على <b>{gl['points']:,}</b> نقطة مجاناً!\n"
            f"اضغط الزر بالأسفل لاستلام هديتك الآن 👇",
            reply_markup=mk([_btn("🎁 استلم هديتك الآن!", url=link_tg)]),
            parse_mode="HTML"
        )
        clear_state(uid)
        send(msg.chat.id, f"<b>✅ تم إرسال الهدية للقناة بنجاح!</b>",
             mk([_btn("◀️ رجوع", f"adm_gift_link_{gid}", color="blue")]))
    except Exception as e:
        send(msg.chat.id,
            f"<b>❌ فشل الإرسال!</b>\n\n"
            f"تأكد إن البوت أدمن في القناة.\n"
            f"الخطأ: <code>{e}</code>",
            kb.back(f"adm_gift_link_{gid}"))
        clear_state(uid)


@bot.callback_query_handler(func=lambda c: c.data.startswith("adm_del_gift_"))
def cb_adm_del_gift(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    gid = int(call.data.split("_")[-1])
    db.delete_gift_link(gid)
    bot.answer_callback_query(call.id, "تم الحذف")
    cb_adm_gift_links(call)


# ══════════════════════════════════════════════════════════════════
#   إدارة الكوبونات — أدمن
# ══════════════════════════════════════════════════════════════════
@bot.callback_query_handler(func=lambda c: c.data == "adm_coupons")
def cb_adm_coupons(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    coupons = db.get_all_coupons()
    text = f"<b>🎟️ الكوبونات ({len(coupons)})</b>\n\n"
    rows = []
    for c in coupons:
        st = "✅" if c["is_active"] else "❌"
        uses = "∞" if c["max_uses"] == -1 else f"{c['used_count']}/{c['max_uses']}"
        rows.append([_btn(f"{st} {c['code']}  —  {c['discount']}%  ({uses})",
                          f"adm_coupon_{c['id']}", color="blue" if c["is_active"] else "red")])
    rows.append([_btn("➕ إضافة كوبون", "adm_add_coupon", color="green")])
    rows.append([_btn("◀️ رجوع", "adm_back", color="blue")])
    edit(call, text or "<b>🎟️ لا توجد كوبونات</b>", mk(*rows))


@bot.callback_query_handler(func=lambda c: c.data == "adm_add_coupon")
def cb_adm_add_coupon(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    set_state(call.from_user.id, "adm_add_coupon")
    edit(call,
        "<b>➕ إضافة كوبون جديد</b>\n\n"
        "أرسل بهذا الشكل:\n"
        "<code>الكود|نسبة الخصم%|عدد الاستخدامات</code>\n\n"
        "أمثلة:\n"
        "<code>SUMMER|20|100</code>  — خصم 20% لـ 100 شخص\n"
        "<code>VIP50|50|-1</code>  — خصم 50% غير محدود",
        kb.back("adm_coupons"))


@bot.callback_query_handler(func=lambda c: c.data.startswith("adm_coupon_"))
def cb_adm_coupon_view(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    cid = int(call.data.split("_")[-1])
    c = db.get_coupon_by_id(cid)
    if not c:
        bot.answer_callback_query(call.id, "الكوبون غير موجود")
        return
    st = "✅ نشط" if c["is_active"] else "❌ متوقف"
    uses = "غير محدود" if c["max_uses"] == -1 else f"{c['used_count']}/{c['max_uses']}"
    edit(call,
        f"<b>🎟️ {c['code']}</b>\n\n"
        f"الخصم: <b>{c['discount']}%</b>\n"
        f"الحالة: {st}\n"
        f"الاستخدامات: {uses}",
        mk(
            [_btn("✅/❌ تفعيل/إيقاف", f"adm_tog_coupon_{cid}", color="green")],
            [_btn("🗑️ حذف",            f"adm_del_coupon_{cid}", color="red")],
            [_btn("◀️ رجوع",           "adm_coupons",           color="blue")],
        ))


@bot.callback_query_handler(func=lambda c: c.data.startswith("adm_tog_coupon_"))
def cb_adm_tog_coupon(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    cid = int(call.data.split("_")[-1])
    db.toggle_coupon(cid)
    bot.answer_callback_query(call.id, "تم التبديل")
    call.data = f"adm_coupon_{cid}"
    cb_adm_coupon_view(call)


@bot.callback_query_handler(func=lambda c: c.data.startswith("adm_del_coupon_"))
def cb_adm_del_coupon(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    cid = int(call.data.split("_")[-1])
    db.delete_coupon(cid)
    bot.answer_callback_query(call.id, "تم الحذف")
    cb_adm_coupons(call)


# ── أدمن: إعدادات التقرير والتنبيهات ───────────────────────
@bot.callback_query_handler(func=lambda c: c.data == "adm_alerts_settings")
def cb_adm_alerts_settings(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    low = db.get_config("low_points_alert", "50")
    report = db.get_config("daily_report_enabled", "1")
    edit(call,
        f"<b>🔔 إعدادات التنبيهات والتقارير</b>\n\n"
        f"حد إشعار الرصيد المنخفض: <b>{low}</b> نقطة\n"
        f"التقرير اليومي: <b>{'✅ مفعّل' if report=='1' else '❌ متوقف'}</b>",
        mk(
            [_btn("✏️ تغيير حد الإشعار", "adm_set_low_alert",        color="blue")],
            [_btn(f"{'🔕 إيقاف' if report=='1' else '🔔 تفعيل'} التقرير اليومي",
                  "adm_toggle_daily_report", color="green" if report=="0" else "red")],
            [_btn("📊 إرسال تقرير الآن", "adm_send_report_now",       color="green")],
            [_btn("◀️ رجوع",             "adm_back",                  color="blue")],
        ))


@bot.callback_query_handler(func=lambda c: c.data == "adm_toggle_daily_report")
def cb_adm_toggle_daily_report(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    cur = db.get_config("daily_report_enabled", "1")
    db.set_config("daily_report_enabled", "0" if cur == "1" else "1")
    bot.answer_callback_query(call.id, "تم التبديل")
    cb_adm_alerts_settings(call)


@bot.callback_query_handler(func=lambda c: c.data == "adm_send_report_now")
def cb_adm_send_report_now(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    bot.answer_callback_query(call.id, "جارٍ الإرسال...")
    threading.Thread(target=send_daily_report, daemon=True).start()


@bot.callback_query_handler(func=lambda c: c.data == "adm_set_low_alert")
def cb_adm_set_low_alert(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    set_state(call.from_user.id, "adm_set_low_alert")
    edit(call,
        "<b>✏️ حد إشعار الرصيد المنخفض</b>\n\n"
        "أرسل الرقم (نقاط)، أو 0 لتعطيل الإشعار:",
        kb.back("adm_alerts_settings"))


def auto_update_orders():
    # لا توجد خدمة خارجية لمتابعة حالتها. الطلبات المحلية تُغلق عند التنفيذ.
    while True:
        time.sleep(300)



# ══════════════════════════════════════════════════════════════════
#   MIRX CONTROL CENTER — نظام لوحة مستقل بالكامل
#   لا يستخدم أي callback من نظام adm_* القديم.
#   جميع الدوال والـ callbacks هنا جديدة ومفصولة باسم mirx_*.
# ══════════════════════════════════════════════════════════════════

MIRX_CALLBACK = "mirx_"


def mirx_guard(uid):
    """صلاحية MIRX: نفس صلاحية لوحة الإدارة، بدون تعطيل callbacks."""
    try:
        # إذا كان المستخدم وصل للوحة من /king فهو قد يكون ضمن ADMIN_IDS
        # وليس بالضرورة مطابقاً لـ DEVELOPER_ID. منع هذا كان يجعل الأزرار
        # تظهر بشكل طبيعي لكن كل callback يرجع بصمت.
        return bool(_is_developer(uid))
    except Exception:
        try:
            return int(uid) == int(DEVELOPER_ID)
        except Exception:
            return False


def mirx_btn(text, callback, color="blue"):
    return _btn(text, callback, color=color)


def mirx_layout(*rows):
    return mk(*rows)


def mirx_home_keyboard():
    return mirx_layout(
        [mirx_btn("➕ إضافة خدمة", "adm_add_service_direct", "green")],
        [mirx_btn("⚙️ التحكم في الخدمة", "mirx_service_control", "green")],
        [mirx_btn("🧩 الخدمات والأقسام", "mirx_catalog", "blue"),
         mirx_btn("📱 حسابات التنفيذ", "mirx_accounts", "blue")],
        [mirx_btn("📡 التفاعل التلقائي", "mirx_reactions", "green"),
         mirx_btn("📢 القنوات", "mirx_channels", "blue")],
        [mirx_btn("🛍️ المتجر والطلبات", "mirx_store", "blue"),
         mirx_btn("🎁 النقاط والهدايا", "mirx_rewards", "green")],
        [mirx_btn("👥 المستخدمون", "mirx_users", "blue"),
         mirx_btn("📊 الإحصائيات", "mirx_stats", "blue")],
        [mirx_btn("📣 الإذاعة والتنبيهات", "mirx_communication", "green"),
         mirx_btn("⚙️ إعدادات البوت", "mirx_settings", "blue")],
        [mirx_btn("🗄️ قاعدة البيانات", "mirx_database", "red")],
        [mirx_btn("🔒 إغلاق MIRX", "mirx_close", "red")],
    )


def mirx_back_keyboard(target="home"):
    cb = "mirx_home" if target == "home" else target
    return mirx_layout([mirx_btn("◀️ رجوع", cb, "blue")])


def mirx_home_text():
    # لوحة MIRX تفتح بدون أي استعلام SQLite؛ الإحصائيات الثقيلة
    # لا يجوز أن تؤخر استقبال الأمر /mirx.
    return (
        "<b>👨‍💻 MIRX CONTROL CENTER</b>\n\n"
        "<b>━━━━━━━━━━━━━━━━</b>\n"
        "⚡ <b>الوضع السريع</b> — الاستقبال والتنفيذ الفوري\n"
        "<b>━━━━━━━━━━━━━━━━</b>\n\n"
        "اختر القسم المطلوب من القائمة الجديدة."
    )


def mirx_show(call, text, markup=None):
    """تحديث شاشة MIRX بدون إسقاط callback إذا فشل التعديل."""
    try:
        ok = edit(call, text, markup)
        if ok:
            return True
        # إذا كانت رسالة callback غير قابلة للتعديل، أرسل شاشة بديلة.
        try:
            bot.send_message(call.message.chat.id, text, reply_markup=markup, parse_mode="HTML")
            return True
        except Exception as e:
            print(f"[MIRX SHOW ERROR] {type(e).__name__}: {e}")
            return False
    except Exception as e:
        print(f"[MIRX SHOW ERROR] {type(e).__name__}: {e}")
        try:
            bot.send_message(call.message.chat.id, text, reply_markup=markup, parse_mode="HTML")
            return True
        except Exception as e2:
            print(f"[MIRX SHOW FALLBACK ERROR] {type(e2).__name__}: {e2}")
            return False


def mirx_ack(call, text=None, alert=False):
    """يُنهي حالة زر Telegram مرة واحدة فقط وبشكل آمن."""
    try:
        if text:
            bot.answer_callback_query(call.id, text, show_alert=alert)
        else:
            bot.answer_callback_query(call.id)
    except Exception as e:
        print(f"[MIRX ACK ERROR] {type(e).__name__}: {e}")


def mirx_safe_int(value):
    try:
        return int(value)
    except Exception:
        return None


def mirx_service_list_keyboard(apps):
    rows = []
    for app in apps:
        aid = int(app["id"])
        name = f"{app.get('emoji') or '📦'} {app['name']}"
        rows.append([mirx_btn(name, f"mirx_app_{aid}", "blue")])
    rows.append([mirx_btn("➕ إضافة خدمة مباشرة", "adm_add_service_direct", "green")])
    rows.append([mirx_btn("◀️ لوحة MIRX", "mirx_home", "blue")])
    return mirx_layout(*rows)


def mirx_services_keyboard(app_id, services):
    rows = []
    for svc in services:
        sid = int(svc["id"])
        name = _service_display_name(svc)
        rows.append([mirx_btn(name, f"mirx_service_{sid}", "blue")])
    rows.append([mirx_btn("➕ إضافة خدمة", f"mirx_add_service_{app_id}", "green")])
    rows.append([mirx_btn("🗑️ حذف القسم", f"mirx_delete_app_{app_id}", "red")])
    rows.append([mirx_btn("◀️ رجوع", "mirx_catalog", "blue")])
    return mirx_layout(*rows)


def mirx_service_control_keyboard(svc):
    sid = int(svc["id"])
    accounts = db.get_service_telegram_accounts(sid)
    count = len(accounts)
    auto = bool(svc.get("auto_react"))
    mode = db.get_service_account_mode(svc)
    mode_txt = "متعدد" if mode == "multi" else "واحد"
    return mirx_layout(
        [mirx_btn(f"➕ إضافة حسابات متعددة • {count}", f"mirx_add_tg_account_{sid}", "green")],
        [mirx_btn(f"👥 حسابات الخدمة • {count} • {mode_txt}", f"mirx_multi_accounts_{sid}", "blue")],
        [mirx_btn(f"📡 التفاعل التلقائي • {'مفعّل' if auto else 'متوقف'}", f"mirx_toggle_reaction_{sid}", "green" if auto else "blue")],
        [mirx_btn("🧪 تجربة الخدمة على منشور", f"mirx_test_service_{sid}", "green")],
        [mirx_btn("◀️ رجوع للخدمات", f"mirx_app_{svc['app_id']}", "blue")],
    )


def mirx_account_keyboard(sid, accounts, selected):
    rows = []
    selected = set(int(x) for x in selected)
    for idx, account in enumerate(accounts, 1):
        aid = int(account["id"])
        mark = "✅" if aid in selected else "⬜"
        name = (account.get("first_name") or "حساب بدون اسم").strip()
        username = f" @{account['username']}" if account.get("username") else ""
        rows.append([mirx_btn(
            f"{mark} {idx}. {name}{username}",
            f"mirx_toggle_account_{sid}_{aid}",
            "green" if aid in selected else "blue"
        )])
    rows.append([mirx_btn(f"☑️ تحديد الكل • {len(accounts)}", f"mirx_select_all_{sid}", "green")])
    rows.append([mirx_btn(f"➡️ متابعة وتأكيد • {len(selected)}", f"mirx_save_accounts_{sid}", "green")])
    rows.append([mirx_btn("◀️ رجوع للخدمة", f"mirx_service_{sid}", "blue")])
    return mirx_layout(*rows)


def mirx_section_text(title, body=""):
    return f"<b>{title}</b>\n\n{body}" if body else f"<b>{title}</b>"


@bot.callback_query_handler(func=lambda c: c.data == "mirx_home")
def mirx_callback_home(call: CallbackQuery):
    # إنهاء حالة الضغط فوراً حتى لا يظل زر تيليجرام عالقاً أثناء SQLite أو تحديث الرسالة.
    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass
    if not mirx_guard(call.from_user.id):
        return
    clear_state(call.from_user.id)
    mirx_show(call, mirx_home_text(), mirx_home_keyboard())


@bot.callback_query_handler(func=lambda c: c.data == "mirx_close")
def mirx_callback_close(call: CallbackQuery):
    # إنهاء حالة الضغط فوراً حتى لا يظل زر تيليجرام عالقاً أثناء SQLite أو تحديث الرسالة.
    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass
    if not mirx_guard(call.from_user.id):
        return
    clear_state(call.from_user.id)
    try:
        bot.answer_callback_query(call.id, "تم إغلاق لوحة MIRX")
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception:
        pass


@bot.callback_query_handler(func=lambda c: c.data == "mirx_service_control")
def mirx_callback_service_control(call: CallbackQuery):
    if not mirx_guard(call.from_user.id):
        mirx_ack(call, "❌ غير مصرح.", True)
        return
    mirx_ack(call)
    try:
        apps = db.get_apps(only_active=False)
        text = "<b>⚙️ التحكم في الخدمة</b>\n\nاختر القسم للوصول إلى خدماته وحسابات التنفيذ."
        mirx_show(call, text, mirx_service_list_keyboard(apps))
    except Exception as e:
        print(f"[MIRX SERVICE CONTROL ERROR] {type(e).__name__}: {e}")
        mirx_ack(call, "❌ تعذر تحميل الأقسام. راجع سجل التشغيل.", True)


@bot.callback_query_handler(func=lambda c: c.data == "mirx_catalog")
def mirx_callback_catalog(call: CallbackQuery):
    if not mirx_guard(call.from_user.id):
        mirx_ack(call, "❌ غير مصرح.", True)
        return
    mirx_ack(call)
    try:
        apps = db.get_apps(only_active=False)
        text = f"<b>🧩 الخدمات والأقسام</b>\n\nعدد الأقسام: <b>{len(apps)}</b>\nاختر القسم لإدارته."
        mirx_show(call, text, mirx_service_list_keyboard(apps))
    except Exception as e:
        print(f"[MIRX CATALOG ERROR] {type(e).__name__}: {e}")
        try:
            bot.send_message(call.message.chat.id, "❌ تعذر تحميل الخدمات والأقسام.\n\nافتح اللوحة مرة أخرى بعد لحظات.", reply_markup=mirx_back_keyboard("home"), parse_mode="HTML")
        except Exception as e2:
            print(f"[MIRX CATALOG FALLBACK ERROR] {type(e2).__name__}: {e2}")


@bot.callback_query_handler(func=lambda c: c.data.startswith("mirx_app_") and c.data[9:].isdigit())
def mirx_callback_app(call: CallbackQuery):
    # إنهاء حالة الضغط فوراً حتى لا يظل زر تيليجرام عالقاً أثناء SQLite أو تحديث الرسالة.
    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass
    if not mirx_guard(call.from_user.id):
        return
    aid = mirx_safe_int(call.data[9:])
    app = db.get_app(aid) if aid is not None else None
    if not app:
        bot.answer_callback_query(call.id, "القسم غير موجود.", show_alert=True)
        return
    services = db.get_app_services(aid, only_active=False)
    title = f"{app.get('emoji') or '📦'} {app['name']}"
    text = f"<b>{title}</b>\n\nالخدمات الموجودة: <b>{len(services)}</b>"
    mirx_show(call, text, mirx_services_keyboard(aid, services))


@bot.callback_query_handler(func=lambda c: c.data.startswith("mirx_service_") and c.data[13:].isdigit())
def mirx_callback_service(call: CallbackQuery):
    # إنهاء حالة الضغط فوراً حتى لا يظل زر تيليجرام عالقاً أثناء SQLite أو تحديث الرسالة.
    if not mirx_guard(call.from_user.id):
        return
    sid = mirx_safe_int(call.data[13:])
    svc = db.get_service(sid) if sid is not None else None
    if not svc:
        bot.answer_callback_query(call.id, "الخدمة غير موجودة.", show_alert=True)
        return
    accounts = db.get_service_telegram_accounts(sid)
    auto = "مفعّل" if svc.get("auto_react") else "متوقف"
    text = (
        "<b>⚙️ التحكم في الخدمة</b>\n\n"
        f"<b>الخدمة:</b> {svc['name']}\n"
        f"<b>النوع:</b> {svc.get('service_type') or 'عام'}\n"
        f"<b>الحسابات:</b> {len(accounts)}\n"
        f"<b>التفاعل:</b> {auto}"
    )
    mirx_show(call, text, mirx_service_control_keyboard(svc))


# ══════════════════════════════════════════════════════════════════
#   MIRX — إضافة حساب مباشرةً للخدمة + تعدد الحسابات
#   هذا المسار مستقل عن tg_add_account القديم.
# ══════════════════════════════════════════════════════════════════

def _mirx_attach_account(service_id, owner_id, phone):
    """إرفاق الحساب الجديد بالخدمة تلقائياً، مع إعداد قائمة الإيموجيات الافتراضية مرة واحدة."""
    accounts = db.list_telegram_accounts(owner_id)
    target = None
    clean_phone = (phone or "").replace(" ", "")
    for a in accounts:
        if (a.get("phone") or "").replace(" ", "") == clean_phone:
            target = a
            break
    if not target:
        return None

    current = [int(a["id"]) for a in db.get_service_telegram_accounts(service_id)]
    aid = int(target["id"])
    if aid not in current:
        current.append(aid)
        db.set_service_telegram_accounts(service_id, current)

    # بمجرد ربط الحساب: فعّل وضع الحسابات المتعددة تلقائياً
    # واحفظ قائمة الـ20 إيموجي الافتراضية للخدمة إذا لم تكن موجودة.
    svc = db.get_service(service_id)
    if svc:
        pool = str(svc.get("reaction_pool") or "").strip()
        service_type = str(svc.get("service_type") or "").strip()
        if service_type in ("تفاعل", "قلب") and not pool:
            db.update_service(
                service_id,
                reaction_emoji=MIRX_DEFAULT_REACTION_EMOJIS[0],
                reaction_mode="multi",
                reaction_pool=MIRX_DEFAULT_REACTION_POOL,
                auto_react=svc.get("auto_react") if svc.get("auto_react") is not None else 0,
            )
        elif service_type in ("تفاعل", "قلب"):
            db.set_service_account_mode(service_id, "multi")

    return target


def _mirx_multi_prompt(call, sid):
    svc = db.get_service(sid)
    if not svc:
        bot.answer_callback_query(call.id, "الخدمة غير موجودة.", show_alert=True)
        return
    accounts = db.get_service_telegram_accounts(sid)
    count = len(accounts)
    if count <= 0:
        bot.answer_callback_query(call.id, "أضف حساباً واحداً على الأقل أولاً.", show_alert=True)
        return
    set_state(call.from_user.id, "mirx_multi_wait_word", svc_id=sid, expected=count)
    mirx_show(
        call,
        f"<b>🔢 تعدد الحسابات</b>\n\n"
        f"الخدمة: <b>{svc['name']}</b>\n"
        f"الحسابات المضافة فعلياً: <b>{count}</b>\n\n"
        f"أرسل بالصيغة:\n<code>تعدد {count}</code>\n\n"
        "سيتم التحقق من العدد قبل التفعيل.",
        mirx_layout([mirx_btn("❌ إلغاء", f"mirx_multi_cancel_{sid}", "red")])
    )
def mirx_callback_add_multi_account_legacy(call: CallbackQuery):
    # تأكيد الضغط فوراً حتى لا يظل زر Telegram في حالة تحميل أثناء تجهيز جلسة الحساب.
    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass
    if not mirx_guard(call.from_user.id):
        try:
            bot.answer_callback_query(call.id, "❌ غير مصرح لك.", show_alert=True)
        except Exception:
            pass
        return
    sid = mirx_safe_int(call.data[23:])
    svc = db.get_service(sid) if sid is not None else None
    if not svc:
        bot.answer_callback_query(call.id, "الخدمة غير موجودة.", show_alert=True)
        return

    uid = call.from_user.id
    # استخدم نفس مسار الجلسة المستقل الجديد بدلاً من إنشاء state ناقص.
    _mirx_tg_start_session(uid, svc)

    mirx_show(
        call,
        "<b>➕ إضافة حساب Telegram للخدمة</b>\n\n"
        f"🔗 الخدمة: <b>{svc['name']}</b>\n\n"
        "<b>🔹 الخطوة 1 من 4 — API ID</b>\n\n"
        "أرسل <b>API ID</b> من my.telegram.org\n"
        "مثال: <code>12345678</code>",
        mirx_layout([mirx_btn("❌ إلغاء", f"mirx_multi_cancel_{sid}", "red")])
    )

@bot.callback_query_handler(func=lambda c: c.data.startswith("mirx_multi_accounts_") and c.data[20:].isdigit())
def mirx_callback_multi_accounts(call: CallbackQuery):
    if not mirx_guard(call.from_user.id):
        return
    sid = mirx_safe_int(call.data[20:])
    svc = db.get_service(sid) if sid is not None else None
    if not svc:
        bot.answer_callback_query(call.id, "الخدمة غير موجودة.", show_alert=True)
        return
    owner = int(getattr(config, "TG_EXECUTION_USER_ID", 0) or 0)
    available = db.list_telegram_accounts(owner) if owner else []
    linked = db.get_service_telegram_accounts(sid)
    # زر حسابات الخدمة يبدأ الآن بطلب العدد فقط؛ لا يضيف حساب Telegram جديداً.
    set_state(call.from_user.id, "mirx_service_account_count", sid=sid, available=len(available))
    mirx_show(
        call,
        f"<b>👥 حسابات الخدمة</b>\n\n"
        f"الخدمة: <b>{svc['name']}</b>\n"
        f"الحسابات الموجودة لديك: <b>{len(available)}</b>\n"
        f"المرتبطة حالياً بالخدمة: <b>{len(linked)}</b>\n\n"
        "🔢 أرسل الآن <b>عدد الحسابات</b> التي تريد ربطها بالخدمة.\n"
        "مثال: <code>7</code>",
        mirx_layout(
            [mirx_btn("❌ إلغاء", f"mirx_service_{sid}", "red")],
        )
    )

@bot.message_handler(func=lambda m: get_state(m.from_user.id).get("state") == "mirx_service_account_count")
def mirx_message_service_account_count(msg: Message):
    if not mirx_guard(msg.from_user.id):
        return
    uid = msg.from_user.id
    state = get_state(uid)
    data = state.get("data", {})
    sid = mirx_safe_int(data.get("sid"))
    svc = db.get_service(sid) if sid is not None else None
    try:
        requested = int((msg.text or "").strip())
    except Exception:
        requested = 0
    owner = int(getattr(config, "TG_EXECUTION_USER_ID", 0) or 0)
    available = db.list_telegram_accounts(owner) if owner else []
    if not svc:
        clear_state(uid)
        send(msg.chat.id, "❌ الخدمة غير موجودة.", mirx_home_keyboard())
        return
    if requested <= 0:
        send(msg.chat.id, "❌ أرسل عددًا صحيحًا أكبر من صفر، مثل <code>7</code>.")
        return
    if requested > len(available):
        send(msg.chat.id,
             f"❌ طلبت <b>{requested}</b> حساب، لكن المتاح لديك <b>{len(available)}</b> فقط.\n"
             f"أرسل عددًا من 1 إلى {len(available)}.")
        return

    # نختار من الحسابات المضافة بالفعل فقط. الحسابات المرتبطة حاليًا لها أولوية،
    # ثم نكمل من بقية الحسابات حتى نصل للعدد المطلوب. لا يتم إنشاء حساب جديد هنا.
    linked_ids = [int(a["id"]) for a in db.get_service_telegram_accounts(sid)]
    linked_set = set(linked_ids)
    preferred = [a for a in available if int(a["id"]) in linked_set]
    remaining = [a for a in available if int(a["id"]) not in linked_set]
    selected_accounts = (preferred + remaining)[:requested]
    selected = [int(a["id"]) for a in selected_accounts]
    USER_STATE[uid] = {
        "state": "mirx_multi_confirm_selection",
        "data": {"sid": sid, "selected": selected, "requested": requested},
    }
    lines = []
    for i, a in enumerate(selected_accounts, 1):
        name = (a.get("first_name") or a.get("username") or "حساب").strip()
        username = f" @{a['username']}" if a.get("username") else ""
        lines.append(f"<b>{i}.</b> 📱 {name}{username}")
    mirx_show(
        msg,
        f"<b>🔎 تأكيد ربط الحسابات</b>\n\n"
        f"الخدمة: <b>{svc['name']}</b>\n"
        f"العدد المطلوب: <b>{requested}</b>\n\n"
        + "\n".join(lines) +
        "\n\nهل تريد ربط هذه الحسابات بالخدمة وتفعيل التعدد؟",
        mirx_layout(
            [mirx_btn(f"✅ نعم، اربط {requested} حساب", f"mirx_confirm_accounts_{sid}", "green")],
            [mirx_btn("❌ لا، أرسل عددًا آخر", f"mirx_multi_accounts_{sid}", "red")],
            [mirx_btn("◀️ رجوع للخدمة", f"mirx_service_{sid}", "blue")],
        )
    )

@bot.callback_query_handler(func=lambda c: c.data.startswith("mirx_multi_enable_") and c.data[18:].isdigit())
def mirx_callback_multi_enable(call: CallbackQuery):
    if not mirx_guard(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ غير مصرح.", show_alert=True)
        return
    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass
    sid = mirx_safe_int(call.data[18:])
    if sid is None:
        return
    _mirx_multi_prompt(call, sid)

@bot.callback_query_handler(func=lambda c: c.data.startswith("mirx_multi_cancel_") and c.data[18:].isdigit())
def mirx_callback_multi_cancel(call: CallbackQuery):
    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass
    if not mirx_guard(call.from_user.id):
        return
    uid = call.from_user.id
    sid = mirx_safe_int(call.data[18:])
    # تنظيف كامل: حالة إضافة الحساب + الحالة العامة
    _mirx_tg_reset(uid)
    clear_state(uid)
    svc = db.get_service(sid) if sid is not None else None
    if svc:
        mirx_show(call, "<b>⚙️ التحكم في الخدمة</b>", mirx_service_control_keyboard(svc))
    else:
        mirx_show(call, "<b>⚙️ التحكم في الخدمة</b>", mirx_back_keyboard("mirx_service_control"))


@bot.callback_query_handler(func=lambda c: c.data.startswith("mirx_multi_confirm_") and len(c.data.split("_")) == 5)
def mirx_callback_multi_confirm(call: CallbackQuery):
    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass
    if not mirx_guard(call.from_user.id):
        return
    uid = call.from_user.id
    parts = call.data.split("_")
    sid = mirx_safe_int(parts[3])
    expected = mirx_safe_int(parts[4])
    if sid is None or expected is None:
        return
    svc = db.get_service(sid)
    accounts = db.get_service_telegram_accounts(sid) if svc else []
    actual = len(accounts)
    if not svc or actual != expected or expected <= 0:
        bot.answer_callback_query(call.id, f"❌ العدد تغير. الموجود الآن: {actual}", show_alert=True)
        return
    # تنظيف كامل لكلا النظامين
    _mirx_tg_reset(uid)
    clear_state(uid)
    mirx_show(
        call,
        f"<b>✅ تم تأكيد تعدد الحسابات</b>\n\n"
        f"الخدمة: <b>{svc['name']}</b>\n"
        f"الحسابات المضافة: <b>{actual}</b>\n\n"
        "كل طلب تفاعل لهذه الخدمة سيستخدم الحسابات المرتبطة بها.",
        mirx_service_control_keyboard(svc)
    )

# ══════════════════════════════════════════════════════════════════
#   MIRX — إضافة حساب Telegram (نسخة موحّدة مستقرة)
#   المشكلة القديمة: كل خطوة كانت بتفتح client جديد، والـ
#   phone_code_hash كان بيضيع + الـ client بيتقفل بعد طلب الكود.
#   الحل: نحفظ نفس الـ client في dict واحد طول مراحل التسجيل.
# ══════════════════════════════════════════════════════════════════


# uid -> جلسة مستقلة لإضافة حساب Telegram.
# كل عمليات Telethon الخاصة بالمستخدم تُنفّذ داخل Thread واحد ثابت،
# حتى لا ينتقل نفس TelegramClient بين event loops / threads مختلفة.
_MIRX_TG_SESSIONS = {}
_MIRX_TG_LOCK = threading.RLock()


def _tg_session_path(uid, phone, api_id):
    """مسار Session ثابت وآمن نسبياً لكل حساب مضاف."""
    base = os.path.abspath(config.TG_SESSIONS_DIR or "telegram_sessions")
    os.makedirs(base, exist_ok=True)
    raw = f"{int(uid)}:{int(api_id)}:{phone}".encode("utf-8")
    key = hashlib.sha256(raw).hexdigest()[:24]
    return os.path.join(base, f"mirx_{int(uid)}_{key}")


def _tg_connect(session_path, api_id, api_hash):
    """إنشاء/فتح TelegramClient بالطريقة المتوافقة مع Telethon sync."""
    if TelegramClient is None:
        ok, error = _load_telethon(auto_install=False)
        if not ok or TelegramClient is None:
            raise RuntimeError(f"Telethon غير متاحة: {error or 'تعذر تحميل المكتبة'}")
    client = TelegramClient(session_path, int(api_id), str(api_hash))
    client.connect()
    return client


def _mirx_tg_get(uid):
    with _MIRX_TG_LOCK:
        return _MIRX_TG_SESSIONS.get(int(uid)) or {}


def _mirx_tg_set(uid, **kw):
    with _MIRX_TG_LOCK:
        sess = _MIRX_TG_SESSIONS.setdefault(int(uid), {})
        sess.update(kw)
        return sess


def _mirx_tg_is_current(uid, sess):
    with _MIRX_TG_LOCK:
        return _MIRX_TG_SESSIONS.get(int(uid)) is sess


def _mirx_tg_executor(sess):
    executor = sess.get("executor")
    if executor is None:
        executor = ThreadPoolExecutor(
            max_workers=1,
            thread_name_prefix=f"mirx-tg-{sess.get('uid', 'user')}",
        )
        sess["executor"] = executor
    return executor


def _mirx_tg_close_client(client):
    if client is None:
        return
    try:
        if client.is_connected():
            client.disconnect()
    except Exception:
        pass


def _mirx_tg_reset(uid):
    """تنظيف جلسة الحساب بالكامل وإغلاق العامل والاتصال القديم."""
    uid = int(uid)
    with _MIRX_TG_LOCK:
        sess = _MIRX_TG_SESSIONS.pop(uid, None)

    if not sess:
        return

    client = sess.get("client")
    executor = sess.get("executor")

    if executor is not None and client is not None:
        try:
            executor.submit(_mirx_tg_close_client, client)
        except Exception:
            _mirx_tg_close_client(client)
    else:
        _mirx_tg_close_client(client)

    if executor is not None:
        try:
            executor.shutdown(wait=False)
        except Exception:
            pass


def _mirx_tg_start_session(uid, svc):
    """بدء مسار إضافة مستقل تماماً عن باقي حالات MIRX."""
    uid = int(uid)
    sid = int(svc["id"])
    _mirx_tg_reset(uid)

    sess = {
        "uid": uid,
        "step": "api_id",
        "svc_id": sid,
        "svc_name": svc.get("name") or "",
        "attempts": 0,
        "executor": None,
        "client": None,
        "phone": "",
        "api_id": 0,
        "api_hash": "",
        "session_path": "",
        "phone_code_hash": "",
    }
    with _MIRX_TG_LOCK:
        _MIRX_TG_SESSIONS[uid] = sess
    return sess


def _mirx_tg_safe_error(exc):
    """رسالة خطأ مفيدة بدون طباعة بيانات API السرية."""
    name = type(exc).__name__
    raw = str(exc or "").strip().replace("\n", " ")
    if len(raw) > 240:
        raw = raw[:240] + "..."
    return f"{name}: {raw}" if raw else name


def _mirx_tg_request_code_worker(sess, phone):
    """connect → check → send_code_request داخل نفس worker."""
    api_id = int(sess["api_id"])
    api_hash = sess["api_hash"]
    uid = int(sess["uid"])
    session_path = _tg_session_path(uid, phone, api_id)

    client = _tg_connect(session_path, api_id, api_hash)

    if client.is_user_authorized():
        me = client.get_me()
        return {
            "kind": "already_authorized",
            "client": client,
            "me": me,
            "phone": phone,
            "session_path": session_path,
        }

    sent = client.send_code_request(phone)
    return {
        "kind": "code_sent",
        "client": client,
        "phone": phone,
        "session_path": session_path,
        "phone_code_hash": sent.phone_code_hash,
    }


def _mirx_tg_on_request_done(uid, sess, future, chat_id):
    try:
        result = future.result()
    except Exception as exc:
        if not _mirx_tg_is_current(uid, sess):
            return
        _mirx_tg_set(uid, step="phone", client=None, future=None)
        send(
            chat_id,
            "<b>❌ تعذر طلب كود التحقق</b>\n\n"
            f"<code>{_mirx_tg_safe_error(exc)}</code>\n\n"
            "تأكد من API ID وAPI HASH ورقم الهاتف، ثم أرسل الرقم مرة أخرى.",
        )
        return

    if not _mirx_tg_is_current(uid, sess):
        _mirx_tg_close_client(result.get("client"))
        return

    client = result.get("client")
    sess["client"] = client
    sess["future"] = None
    sess["phone"] = result["phone"]
    sess["session_path"] = result["session_path"]

    if result["kind"] == "already_authorized":
        try:
            me = result["me"]
            db.upsert_telegram_account(
                uid,
                result["phone"],
                me.id,
                me.username or "",
                me.first_name or "",
                result["session_path"],
                int(sess["api_id"]),
                sess["api_hash"],
            )
            svc_id = int(sess.get("svc_id") or 0)
            if svc_id:
                _mirx_attach_account(svc_id, uid, result["phone"])
            svc = db.get_service(svc_id) if svc_id else None
            send(
                chat_id,
                "<b>✅ الحساب مسجل دخول بالفعل وتم ربطه بالخدمة</b>\n\n"
                f"👤 الاسم: <b>{me.first_name or '—'}</b>\n"
                f"🆔 Username: @{me.username or '—'}\n"
                f"📱 الرقم: <code>{result['phone']}</code>",
                mirx_service_control_keyboard(svc) if svc else mirx_home_keyboard(),
            )
        except Exception as exc:
            send(
                chat_id,
                "<b>❌ تم الاتصال بالحساب لكن تعذر حفظه</b>\n\n"
                f"<code>{_mirx_tg_safe_error(exc)}</code>",
            )
        finally:
            _mirx_tg_reset(uid)
        return

    sess["phone_code_hash"] = result["phone_code_hash"]
    sess["step"] = "code"
    sess["attempts"] = 0

    send(
        chat_id,
        "<b>📩 تم إرسال كود التحقق بنجاح</b>\n\n"
        f"📱 الرقم: <code>{result['phone']}</code>\n\n"
        "<b>🔹 الخطوة 4 من 4 — كود التحقق</b>\n\n"
        "أرسل الكود الذي وصلك على Telegram.",
    )


def _mirx_tg_submit_request_code(uid, sess, chat_id, phone):
    sess["step"] = "requesting_code"
    sess["future"] = None
    executor = _mirx_tg_executor(sess)
    future = executor.submit(_mirx_tg_request_code_worker, sess, phone)
    sess["future"] = future
    future.add_done_callback(
        lambda f: _mirx_tg_on_request_done(uid, sess, f, chat_id)
    )


def _mirx_tg_verify_code_worker(sess, code):
    client = sess.get("client")
    if client is None:
        raise RuntimeError("جلسة Telegram غير موجودة. أعد إرسال رقم الهاتف.")
    if not client.is_connected():
        client.connect()
    client.sign_in(
        phone=sess["phone"],
        code=code,
        phone_code_hash=sess["phone_code_hash"],
    )
    return client.get_me()


def _mirx_tg_on_verify_done(uid, sess, future, chat_id):
    try:
        me = future.result()
    except SessionPasswordNeededError:
        if not _mirx_tg_is_current(uid, sess):
            return
        sess["future"] = None
        sess["step"] = "2fa"
        send(
            chat_id,
            "<b>🔐 الحساب محمي بكلمة مرور 2FA</b>\n\n"
            "أرسل كلمة مرور التحقق بخطوتين.",
        )
        return
    except PhoneCodeInvalidError:
        if not _mirx_tg_is_current(uid, sess):
            return
        attempts = int(sess.get("attempts", 0)) + 1
        sess["attempts"] = attempts
        sess["future"] = None
        if attempts >= 3:
            _mirx_tg_reset(uid)
            send(chat_id, "❌ تم تجاوز 3 محاولات. ابدأ إضافة الحساب من جديد.")
        else:
            sess["step"] = "code"
            send(chat_id, f"❌ الكود غير صحيح. المحاولة {attempts}/3.")
        return
    except PhoneCodeExpiredError:
        if _mirx_tg_is_current(uid, sess):
            _mirx_tg_reset(uid)
            send(chat_id, "❌ انتهت صلاحية الكود. ابدأ من جديد وأرسل رقم الهاتف مرة أخرى.")
        return
    except Exception as exc:
        if _mirx_tg_is_current(uid, sess):
            sess["future"] = None
            sess["step"] = "code"
            send(
                chat_id,
                "<b>❌ فشل تسجيل الدخول</b>\n\n"
                f"<code>{_mirx_tg_safe_error(exc)}</code>\n\n"
                "يمكنك إرسال الكود مرة أخرى.",
            )
        return

    if _mirx_tg_is_current(uid, sess):
        _mirx_tg_finish(uid, chat_id, sess, me)


def _mirx_tg_submit_verify_code(uid, sess, chat_id, code):
    sess["step"] = "verifying_code"
    executor = _mirx_tg_executor(sess)
    future = executor.submit(_mirx_tg_verify_code_worker, sess, code)
    sess["future"] = future
    future.add_done_callback(
        lambda f: _mirx_tg_on_verify_done(uid, sess, f, chat_id)
    )


def _mirx_tg_2fa_worker(sess, password):
    client = sess.get("client")
    if client is None:
        raise RuntimeError("جلسة Telegram غير موجودة. ابدأ من جديد.")
    if not client.is_connected():
        client.connect()
    client.sign_in(password=password)
    return client.get_me()


def _mirx_tg_on_2fa_done(uid, sess, future, chat_id):
    try:
        me = future.result()
    except Exception as exc:
        if not _mirx_tg_is_current(uid, sess):
            return
        sess["future"] = None
        sess["step"] = "2fa"
        send(
            chat_id,
            "<b>❌ تعذر إكمال تسجيل الدخول بـ 2FA</b>\n\n"
            f"<code>{_mirx_tg_safe_error(exc)}</code>\n\n"
            "أرسل كلمة المرور مرة أخرى.",
        )
        return
    if _mirx_tg_is_current(uid, sess):
        _mirx_tg_finish(uid, chat_id, sess, me)


def _mirx_tg_submit_2fa(uid, sess, chat_id, password):
    sess["step"] = "verifying_2fa"
    executor = _mirx_tg_executor(sess)
    future = executor.submit(_mirx_tg_2fa_worker, sess, password)
    sess["future"] = future
    future.add_done_callback(
        lambda f: _mirx_tg_on_2fa_done(uid, sess, f, chat_id)
    )


@bot.callback_query_handler(
    func=lambda c: c.data.startswith("mirx_add_tg_account_") and c.data[20:].isdigit()
)
def mirx_callback_add_tg_account(call: CallbackQuery):
    """زر مستقل: يبدأ إضافة الحساب مباشرة ولا يعتمد على state قديم."""
    uid = int(call.from_user.id)
    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass

    if not mirx_guard(uid):
        try:
            bot.answer_callback_query(call.id, "❌ غير مصرح لك.", show_alert=True)
        except Exception:
            pass
        return

    sid = mirx_safe_int(call.data[20:])
    svc = db.get_service(sid) if sid is not None else None
    if not svc:
        send(call.message.chat.id, "❌ الخدمة غير موجودة.")
        return

    _mirx_tg_start_session(uid, svc)
    send(
        call.message.chat.id,
        "<b>➕ إضافة حساب Telegram</b>\n\n"
        f"🔗 الخدمة: <b>{svc['name']}</b>\n\n"
        "<b>🔹 الخطوة 1 من 4 — API ID</b>\n\n"
        "أرسل <b>API ID</b> من <code>my.telegram.org</code>.\n"
        "مثال: <code>12345678</code>",
        mirx_layout(
            [mirx_btn("❌ إلغاء", f"mirx_multi_cancel_{sid}", "red")]
        ),
    )


def mirx_tg_flow_router(msg: Message):
    """
    المسار الموحد الجديد:
    API ID → API HASH → الهاتف → طلب الكود → الكود → 2FA اختياري.
    كل اتصال Telethon يبقى داخل worker واحد لتفادي مشاكل event loop.
    """
    uid = int(msg.from_user.id)
    sess = _mirx_tg_get(uid)
    step = sess.get("step")
    text = (msg.text or "").strip()

    if not sess or step is None:
        return

    if step == "api_id":
        try:
            api_id = int(text)
            if api_id <= 0 or api_id > 2147483647:
                raise ValueError
        except Exception:
            send(
                msg.chat.id,
                "❌ API ID غير صحيح.\n\n"
                "أرسل الرقم فقط من my.telegram.org\n"
                "مثال: <code>12345678</code>",
            )
            return
        sess["api_id"] = api_id
        sess["step"] = "api_hash"
        send(
            msg.chat.id,
            "<b>🔹 الخطوة 2 من 4 — API HASH</b>\n\n"
            "أرسل <b>API HASH</b> من نفس صفحة my.telegram.org.",
        )
        return

    if step == "api_hash":
        api_hash = text
        if len(api_hash) < 16 or len(api_hash) > 200 or any(ch.isspace() for ch in api_hash):
            send(
                msg.chat.id,
                "❌ API HASH غير صحيح.\n\n"
                "أرسله كما هو من my.telegram.org بدون مسافات.",
            )
            return
        sess["api_hash"] = api_hash
        sess["step"] = "phone"
        send(
            msg.chat.id,
            "<b>🔹 الخطوة 3 من 4 — رقم الهاتف</b>\n\n"
            "أرسل رقم الحساب بالصيغة الدولية مع <b>+</b>\n"
            "مثال: <code>+201012345678</code>",
        )
        return

    if step == "phone":
        phone = text.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
        if not (phone.startswith("+") and phone[1:].isdigit() and 8 <= len(phone[1:]) <= 15):
            send(
                msg.chat.id,
                "❌ رقم الهاتف غير صحيح.\n\n"
                "استخدم الصيغة الدولية مع <b>+</b>.\n"
                "مثال: <code>+201012345678</code>",
            )
            return

        if sess.get("future") is not None and not sess["future"].done():
            send(msg.chat.id, "⏳ يوجد طلب اتصال جارٍ بالفعل، انتظر النتيجة.")
            return

        sess["phone"] = phone
        sess["attempts"] = 0
        send(
            msg.chat.id,
            "⏳ <b>جاري طلب كود التحقق من Telegram...</b>\n\n"
            f"📱 الرقم: <code>{phone}</code>\n\n"
            "لن تحتاج لإرسال الرقم مرة أخرى إلا إذا فشل الاتصال.",
        )
        try:
            _mirx_tg_submit_request_code(uid, sess, msg.chat.id, phone)
        except Exception as exc:
            sess["step"] = "phone"
            send(
                msg.chat.id,
                "<b>❌ تعذر بدء الاتصال</b>\n\n"
                f"<code>{_mirx_tg_safe_error(exc)}</code>",
            )
        return

    if step == "requesting_code":
        send(msg.chat.id, "⏳ جاري طلب كود التحقق، انتظر لحظات.")
        return

    if step == "code":
        code = text.replace(" ", "").replace("-", "")
        if not code.isdigit() or not 4 <= len(code) <= 8:
            send(msg.chat.id, "❌ كود التحقق غير صحيح. أرسل الأرقام فقط.")
            return

        if not sess.get("phone_code_hash") or not sess.get("phone"):
            _mirx_tg_reset(uid)
            send(msg.chat.id, "❌ جلسة التحقق انتهت. ابدأ من جديد.")
            return

        if sess.get("future") is not None and not sess["future"].done():
            send(msg.chat.id, "⏳ يوجد تحقق جارٍ بالفعل.")
            return

        try:
            _mirx_tg_submit_verify_code(uid, sess, msg.chat.id, code)
            send(msg.chat.id, "⏳ <b>جاري التحقق من الكود...</b>")
        except Exception as exc:
            sess["step"] = "code"
            send(
                msg.chat.id,
                "<b>❌ تعذر بدء التحقق</b>\n\n"
                f"<code>{_mirx_tg_safe_error(exc)}</code>",
            )
        return

    if step == "verifying_code":
        send(msg.chat.id, "⏳ جاري التحقق من الكود، انتظر النتيجة.")
        return

    if step == "2fa":
        password = text
        if not password:
            send(msg.chat.id, "❌ أرسل كلمة مرور 2FA.")
            return
        if sess.get("future") is not None and not sess["future"].done():
            send(msg.chat.id, "⏳ يوجد تحقق جارٍ بالفعل.")
            return
        try:
            _mirx_tg_submit_2fa(uid, sess, msg.chat.id, password)
            send(msg.chat.id, "⏳ <b>جاري التحقق من كلمة مرور 2FA...</b>")
        except Exception as exc:
            sess["step"] = "2fa"
            send(
                msg.chat.id,
                "<b>❌ تعذر بدء تحقق 2FA</b>\n\n"
                f"<code>{_mirx_tg_safe_error(exc)}</code>",
            )
        return

    if step == "verifying_2fa":
        send(msg.chat.id, "⏳ جاري التحقق من كلمة مرور 2FA، انتظر النتيجة.")
        return


def _mirx_tg_finish(uid, chat_id, sess, me=None):
    """حفظ الحساب بعد نجاح Telegram فقط، ثم إغلاق worker والاتصال."""
    try:
        client = sess.get("client")
        if client is None:
            raise RuntimeError("جلسة Telegram غير موجودة.")
        if me is None:
            me = client.get_me()
        if not client.is_connected() or not client.is_user_authorized():
            raise RuntimeError("الحساب لم يصبح مصرحاً له بعد.")

        svc_id = int(sess.get("svc_id") or 0)
        phone = sess["phone"]
        session_path = sess["session_path"]
        api_id = int(sess["api_id"])
        api_hash = sess["api_hash"]

        db.upsert_telegram_account(
            uid, phone, me.id, me.username or "", me.first_name or "",
            session_path, api_id, api_hash,
        )

        if svc_id:
            _mirx_attach_account(svc_id, uid, phone)

        svc = db.get_service(svc_id) if svc_id else None
        acc_count = len(db.get_service_telegram_accounts(svc_id)) if svc_id else 0
        _mirx_tg_reset(uid)

        if svc and svc_id:
            send(
                chat_id,
                "<b>✅ تم تسجيل الدخول وربط الحساب بنجاح</b>\n\n"
                f"👤 الاسم: <b>{me.first_name or '—'}</b>\n"
                f"🆔 Username: @{me.username or '—'}\n"
                f"📱 الرقم: <code>{phone}</code>\n"
                f"🔗 الخدمة: <b>{svc['name']}</b>\n"
                f"👥 <b>عدد الحسابات المرتبطة الآن: {acc_count}</b>\n\n"
                "يمكنك الآن إضافة حساب آخر أو فتح حسابات الخدمة.",
                mirx_layout(
                    [mirx_btn("➕ إضافة حساب آخر", f"mirx_add_tg_account_{svc_id}", "green")],
                    [mirx_btn("👥 حسابات الخدمة", f"mirx_multi_accounts_{svc_id}", "blue")],
                    [mirx_btn("⚙️ رجوع للخدمة", f"mirx_service_{svc_id}", "blue")],
                ),
            )
        else:
            send(
                chat_id,
                "<b>✅ تم تسجيل الدخول بنجاح</b>\n\n"
                f"👤 الاسم: <b>{me.first_name or '—'}</b>\n"
                f"🆔 Username: @{me.username or '—'}\n"
                f"📱 الرقم: <code>{phone}</code>",
                mirx_layout([mirx_btn("◀️ لوحة MIRX", "mirx_home", "blue")]),
            )
    except Exception as exc:
        _mirx_tg_reset(uid)
        send(
            chat_id,
            "<b>❌ فشل حفظ الحساب بعد تسجيل الدخول</b>\n\n"
            f"<code>{_mirx_tg_safe_error(exc)}</code>",
        )

@bot.message_handler(func=lambda m: get_state(m.from_user.id).get("state") == "mirx_multi_wait_word")
def mirx_msg_multi_wait_word(msg: Message):
    uid = msg.from_user.id
    if not mirx_guard(uid):
        return
    d = get_state(uid).get("data", {})
    sid = int(d.get("svc_id") or 0)
    expected = int(d.get("expected") or 0)
    text = (msg.text or "").strip()
    parts = text.split()
    if len(parts) != 2 or parts[0] != "تعدد" or not parts[1].isdigit():
        send(msg.chat.id, f"❌ الصيغة الصحيحة: <code>تعدد {expected}</code>")
        return
    requested = int(parts[1])
    actual = len(db.get_service_telegram_accounts(sid)) if sid else 0
    if actual <= 0:
        # لا يوجد حسابات أصلاً → أنهِ الجلسة ونظّف
        clear_state(uid)
        _mirx_tg_reset(uid)
        send(msg.chat.id, "❌ لا توجد حسابات مضافة لهذه الخدمة. أضف حساباً أولاً.")
        return
    if requested != actual:
        send(msg.chat.id,
             f"❌ العدد غير مطابق.\n\nالحسابات المضافة فعلياً: <b>{actual}</b>\n"
             f"أنت كتبت: <b>{requested}</b>\n\nاكتب: <code>تعدد {actual}</code>")
        set_state(uid, "mirx_multi_wait_word", svc_id=sid, expected=actual)
        return
    set_state(uid, "mirx_multi_confirm", svc_id=sid, expected=actual)
    svc = db.get_service(sid)
    send(msg.chat.id,
         f"<b>🔎 تم التحقق من العدد</b>\n\n"
         f"الخدمة: <b>{svc['name'] if svc else '—'}</b>\n"
         f"الحسابات المضافة: <b>{actual}</b>\n\n"
         f"هل تريد تفعيل تعدد الحسابات بهذه الخدمة؟",
         mirx_layout(
             [mirx_btn(f"✅ نعم، فعّل {actual} حساب", f"mirx_multi_confirm_{sid}_{actual}", "green"),
              mirx_btn("❌ لا", f"mirx_multi_cancel_{sid}", "red")]
         ))


@bot.message_handler(func=lambda m: get_state(m.from_user.id).get("state") == "mirx_multi_confirm")
def mirx_msg_multi_confirm(msg: Message):
    send(msg.chat.id, "استخدم زر التأكيد الموجود في الرسالة.")


@bot.callback_query_handler(func=lambda c: c.data.startswith("mirx_service_accounts_") and c.data[22:].isdigit())
def mirx_callback_service_accounts(call: CallbackQuery):
    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass
    if not mirx_guard(call.from_user.id):
        return
    sid = mirx_safe_int(call.data[22:])
    svc = db.get_service(sid) if sid is not None else None
    if not svc:
        bot.answer_callback_query(call.id, "الخدمة غير موجودة.", show_alert=True)
        return
    accounts = db.get_service_telegram_accounts(sid)
    if not accounts:
        text = "<b>👤 الحسابات المرتبطة</b>\n\nلا توجد حسابات مرتبطة بهذه الخدمة حالياً."
    else:
        lines = []
        for a in accounts:
            name = (a.get("first_name") or "حساب").strip()
            username = f" @{a['username']}" if a.get("username") else ""
            lines.append(f"• 📱 {name}{username}")
        text = "<b>👤 الحسابات المرتبطة</b>\n\n" + "\n".join(lines)
    mirx_show(call, text, mirx_layout(
        [mirx_btn("➕ إضافة حساب آخر", f"mirx_add_tg_account_{sid}", "green")],
        [mirx_btn("🔗 اختيار من الحسابات الموجودة", f"mirx_assign_{sid}", "blue")],
        [mirx_btn("🗑️ حذف حساب مضاف", f"mirx_remove_account_{sid}", "red")],
        [mirx_btn("🔢 تعدد الحسابات", f"mirx_multi_enable_{sid}", "green")],
        [mirx_btn("◀️ رجوع للخدمة", f"mirx_service_{sid}", "blue")]
    ))

@bot.callback_query_handler(func=lambda c: c.data.startswith("mirx_remove_account_") and c.data[20:].isdigit())
def mirx_callback_remove_account_menu(call: CallbackQuery):
    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass
    if not mirx_guard(call.from_user.id):
        return
    sid = mirx_safe_int(call.data[20:])
    svc = db.get_service(sid) if sid is not None else None
    accounts = db.get_service_telegram_accounts(sid) if svc else []
    if not svc:
        bot.answer_callback_query(call.id, "الخدمة غير موجودة.", show_alert=True)
        return
    if not accounts:
        bot.answer_callback_query(call.id, "لا يوجد حساب مضاف لهذه الخدمة.", show_alert=True)
        return
    rows = []
    for i, a in enumerate(accounts, 1):
        name = (a.get("first_name") or a.get("username") or "حساب").strip()
        username = f" @{a['username']}" if a.get("username") else ""
        rows.append([mirx_btn(f"🗑️ {i}. {name}{username}", f"mirx_remove_account_pick_{sid}_{int(a['id'])}", "red")])
    rows.append([mirx_btn("◀️ رجوع للحسابات", f"mirx_service_accounts_{sid}", "blue")])
    mirx_show(call,
              f"<b>🗑️ حذف حساب مضاف</b>\n\nالخدمة: <b>{svc['name']}</b>\n\nاختر الحساب الذي تريد فصله من هذه الخدمة:",
              mirx_layout(*rows))


@bot.callback_query_handler(func=lambda c: c.data.startswith("mirx_remove_account_pick_") and len(c.data.split("_")) == 6)
def mirx_callback_remove_account_pick(call: CallbackQuery):
    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass
    if not mirx_guard(call.from_user.id):
        return
    parts = call.data.split("_")
    sid = mirx_safe_int(parts[4])
    aid = mirx_safe_int(parts[5])
    if sid is None or aid is None:
        return
    svc = db.get_service(sid)
    accounts = db.get_service_telegram_accounts(sid) if svc else []
    account = next((a for a in accounts if int(a["id"]) == aid), None)
    if not svc or not account:
        bot.answer_callback_query(call.id, "الحساب غير مرتبط بهذه الخدمة.", show_alert=True)
        return
    name = (account.get("first_name") or account.get("username") or "الحساب").strip()
    mirx_show(call,
              f"<b>⚠️ تأكيد حذف الحساب</b>\n\nهل تريد فصل <b>{name}</b> من الخدمة؟\n\nلن يتم حذف حساب Telegram نفسه، وسيظل متاحاً لإضافته لخدمات أخرى.",
              mirx_layout(
                  [mirx_btn("✅ نعم، احذف من الخدمة", f"mirx_remove_account_confirm_{sid}_{aid}", "red")],
                  [mirx_btn("❌ إلغاء", f"mirx_service_accounts_{sid}", "blue")],
              ))


@bot.callback_query_handler(func=lambda c: c.data.startswith("mirx_remove_account_confirm_") and len(c.data.split("_")) == 6)
def mirx_callback_remove_account_confirm(call: CallbackQuery):
    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass
    if not mirx_guard(call.from_user.id):
        return
    parts = call.data.split("_")
    sid = mirx_safe_int(parts[4])
    aid = mirx_safe_int(parts[5])
    if sid is None or aid is None:
        return
    accounts = db.get_service_telegram_accounts(sid)
    if not any(int(a["id"]) == aid for a in accounts):
        bot.answer_callback_query(call.id, "الحساب غير موجود ضمن الخدمة.", show_alert=True)
        return
    db.remove_service_telegram_account(sid, aid)
    remaining = db.get_service_telegram_accounts(sid)
    if not remaining:
        db.set_service_account_mode(sid, "single")
    bot.answer_callback_query(call.id, "✅ تم حذف الحساب من الخدمة")
    svc = db.get_service(sid)
    if svc:
        names = []
        for a in remaining:
            name = (a.get("first_name") or a.get("username") or "حساب").strip()
            username = f" @{a['username']}" if a.get("username") else ""
            names.append(f"• 📱 {name}{username}")
        text = "<b>👤 الحسابات المرتبطة</b>\n\n" + ("\n".join(names) if names else "لا توجد حسابات مرتبطة بهذه الخدمة حالياً.")
        mirx_show(call, text, mirx_layout(
            [mirx_btn("➕ إضافة حساب آخر", f"mirx_add_tg_account_{sid}", "green")],
            [mirx_btn("🔗 اختيار من الحسابات الموجودة", f"mirx_assign_{sid}", "blue")],
            [mirx_btn("🗑️ حذف حساب مضاف", f"mirx_remove_account_{sid}", "red")],
            [mirx_btn("🔢 تعدد الحسابات", f"mirx_multi_enable_{sid}", "green")],
            [mirx_btn("◀️ رجوع للخدمة", f"mirx_service_{sid}", "blue")]
        ))


@bot.callback_query_handler(func=lambda c: c.data.startswith("mirx_assign_") and c.data[12:].isdigit())
def mirx_callback_assign(call: CallbackQuery):
    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass
    if not mirx_guard(call.from_user.id):
        return
    uid = call.from_user.id
    sid = mirx_safe_int(call.data[12:])
    svc = db.get_service(sid) if sid is not None else None
    if not svc:
        bot.answer_callback_query(call.id, "الخدمة غير موجودة.", show_alert=True)
        return
    # نظّف أي جلسة إضافة حساب قديمة قبل بدء اختيار الحسابات
    _mirx_tg_reset(uid)
    owner = int(getattr(config, "TG_EXECUTION_USER_ID", 0) or 0)
    accounts = db.list_telegram_accounts(owner) if owner else []
    selected = [int(a["id"]) for a in db.get_service_telegram_accounts(sid)]
    USER_STATE[uid] = {
        "state": "mirx_account_selection",
        "data": {"sid": sid, "selected": selected},
    }
    mirx_show(
        call,
        f"<b>🔗 حسابات التنفيذ</b>\n\n"
        f"الخدمة: <b>{svc['name']}</b>\n"
        f"المتاح: <b>{len(accounts)}</b> | المحدد: <b>{len(selected)}</b>\n\n"
        f"حدد الحسابات ثم اضغط <b>تأكيد وحفظ</b>.",
        mirx_account_keyboard(sid, accounts, selected)
    )


@bot.callback_query_handler(func=lambda c: c.data.startswith("mirx_toggle_account_") and len(c.data.split("_")) == 5)
def mirx_callback_toggle_account(call: CallbackQuery):
    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass
    if not mirx_guard(call.from_user.id):
        return
    uid = call.from_user.id
    parts = call.data.split("_")
    sid = mirx_safe_int(parts[3])
    aid = mirx_safe_int(parts[4])
    state = get_state(uid)
    if sid is None or aid is None or state.get("state") != "mirx_account_selection":
        bot.answer_callback_query(call.id, "انتهت جلسة الاختيار، افتحها من جديد.", show_alert=True)
        return
    data = state.get("data", {})
    if int(data.get("sid", -1)) != sid:
        bot.answer_callback_query(call.id, "الجلسة غير صالحة.", show_alert=True)
        return
    selected = [int(x) for x in data.get("selected", [])]
    if aid in selected:
        selected.remove(aid)
    else:
        selected.append(aid)
    data["selected"] = selected
    USER_STATE[uid] = {"state": "mirx_account_selection", "data": data}
    owner = int(getattr(config, "TG_EXECUTION_USER_ID", 0) or 0)
    accounts = db.list_telegram_accounts(owner) if owner else []
    mirx_show(
        call,
        f"<b>🔗 حسابات التنفيذ</b>\n\n"
        f"تم تحديث الاختيار.\n"
        f"المتاح: <b>{len(accounts)}</b> | المحدد: <b>{len(selected)}</b>",
        mirx_account_keyboard(sid, accounts, selected)
    )


@bot.callback_query_handler(func=lambda c: c.data.startswith("mirx_select_all_") and c.data[16:].isdigit())
def mirx_callback_select_all(call: CallbackQuery):
    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass
    if not mirx_guard(call.from_user.id):
        return
    uid = call.from_user.id
    sid = mirx_safe_int(call.data[16:])
    state = get_state(uid)
    if sid is None or state.get("state") != "mirx_account_selection" \
            or int(state.get("data", {}).get("sid", -1)) != sid:
        bot.answer_callback_query(call.id, "افتح اختيار الحسابات من جديد.", show_alert=True)
        return
    owner = int(getattr(config, "TG_EXECUTION_USER_ID", 0) or 0)
    accounts = db.list_telegram_accounts(owner) if owner else []
    selected = [int(a["id"]) for a in accounts]
    state["data"]["selected"] = selected
    USER_STATE[uid] = state
    mirx_show(
        call,
        f"<b>🔗 حسابات التنفيذ</b>\n\n"
        f"تم تحديد كل الحسابات: <b>{len(selected)}</b>\n\n"
        f"اضغط <b>تأكيد وحفظ</b>.",
        mirx_account_keyboard(sid, accounts, selected)
    )


@bot.callback_query_handler(func=lambda c: c.data.startswith("mirx_save_accounts_") and c.data[19:].isdigit())
def mirx_callback_save_accounts(call: CallbackQuery):
    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass
    if not mirx_guard(call.from_user.id):
        return
    uid = call.from_user.id
    sid = mirx_safe_int(call.data[19:])
    state = get_state(uid)
    if sid is None or state.get("state") != "mirx_account_selection":
        bot.answer_callback_query(call.id, "افتح اختيار الحسابات من جديد.", show_alert=True)
        return
    selected = [int(x) for x in state.get("data", {}).get("selected", [])]
    if not selected:
        bot.answer_callback_query(call.id, "اختر حساباً واحداً على الأقل.", show_alert=True)
        return
    state["state"] = "mirx_multi_confirm_selection"
    state["data"]["sid"] = sid
    state["data"]["selected"] = selected
    USER_STATE[uid] = state
    svc = db.get_service(sid)
    owner = int(getattr(config, "TG_EXECUTION_USER_ID", 0) or 0)
    accounts = db.list_telegram_accounts(owner) if owner else []
    by_id = {int(a["id"]): a for a in accounts}
    names = []
    for n, aid in enumerate(selected, 1):
        a = by_id.get(aid)
        if a:
            name = (a.get("first_name") or a.get("username") or "حساب").strip()
            names.append(f"<b>{n}.</b> 📱 {name}")
    body = "\n".join(names) or "لا توجد حسابات صالحة."
    mirx_show(
        call,
        f"<b>🔎 تأكيد حسابات الخدمة</b>\n\n"
        f"الخدمة: <b>{svc['name'] if svc else '—'}</b>\n"
        f"الحسابات المختارة: <b>{len(selected)}</b>\n\n{body}\n\n"
        f"هل تريد تأكيد هذه الحسابات وتفعيل <b>تعدد الحسابات</b>؟",
        mirx_layout(
            [mirx_btn(f"✅ نعم، فعّل المتعدد • {len(selected)}", f"mirx_confirm_accounts_{sid}", "green")],
            [mirx_btn("❌ لا، رجوع للاختيار", f"mirx_assign_{sid}", "red")],
            [mirx_btn("◀️ رجوع للخدمة", f"mirx_service_{sid}", "blue")],
        )
    )

@bot.callback_query_handler(func=lambda c: c.data.startswith("mirx_confirm_accounts_") and c.data[22:].isdigit())
def mirx_callback_confirm_accounts(call: CallbackQuery):
    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass
    if not mirx_guard(call.from_user.id):
        return
    uid = call.from_user.id
    sid = mirx_safe_int(call.data[22:])
    state = get_state(uid)
    if sid is None or state.get("state") != "mirx_multi_confirm_selection":
        bot.answer_callback_query(call.id, "انتهت جلسة التأكيد، افتحها من جديد.", show_alert=True)
        return
    data = state.get("data", {})
    if int(data.get("sid", -1)) != sid:
        bot.answer_callback_query(call.id, "الجلسة غير صالحة.", show_alert=True)
        return
    selected = [int(x) for x in data.get("selected", [])]
    if not selected:
        bot.answer_callback_query(call.id, "لا توجد حسابات محددة.", show_alert=True)
        return
    try:
        saved = db.set_service_telegram_accounts(sid, selected)
        if len(saved) != len(selected):
            raise ValueError(f"تم العثور على {len(saved)} حساب صالح فقط من أصل {len(selected)}")
        db.set_service_account_mode(sid, "multi")
        # تنظيف كامل لكلا النظامين
        _mirx_tg_reset(uid)
        clear_state(uid)
        svc = db.get_service(sid)
        bot.answer_callback_query(call.id, f"✅ تم تفعيل المتعدد على {len(saved)} حساب")
        if svc:
            accounts = db.get_service_telegram_accounts(sid)
            mirx_show(
                call,
                f"<b>✅ تم تفعيل تعدد الحسابات</b>\n\n"
                f"الخدمة: <b>{svc['name']}</b>\n"
                f"الحسابات المستخدمة: <b>{len(accounts)}</b>\n\n"
                f"كل طلب جديد للخدمة سيستخدم الحسابات المحددة بالتوازي.",
                mirx_service_control_keyboard(svc)
            )
        else:
            mirx_show(call, "<b>✅ تم الحفظ</b>", mirx_back_keyboard("mirx_home"))
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ فشل الحفظ: {str(e)[:100]}", show_alert=True)

@bot.callback_query_handler(func=lambda c: c.data.startswith("mirx_toggle_reaction_") and c.data[21:].isdigit())
def mirx_callback_toggle_reaction(call: CallbackQuery):
    if not mirx_guard(call.from_user.id):
        return
    sid = mirx_safe_int(call.data[21:])
    svc = db.get_service(sid) if sid is not None else None
    if not svc:
        bot.answer_callback_query(call.id, "الخدمة غير موجودة.", show_alert=True)
        return
    new_value = 0 if svc.get("auto_react") else 1
    conn = None
    try:
        conn = db.get_conn()
        conn.execute("UPDATE app_services SET auto_react=? WHERE id=?", (new_value, sid))
        conn.commit()
    except Exception as e:
        print(f"[MIRX TOGGLE REACTION] {e}")
        try:
            if conn:
                conn.rollback()
        except Exception:
            pass
        bot.answer_callback_query(call.id, "❌ فشل التحديث.", show_alert=True)
        return
    finally:
        try:
            if conn:
                conn.close()
        except Exception:
            pass
    bot.answer_callback_query(call.id, "✅ تم تحديث حالة التفاعل")
    svc = db.get_service(sid)
    if svc:
        accounts = db.get_service_telegram_accounts(sid)
        auto = "مفعّل" if svc.get("auto_react") else "متوقف"
        text = (
            "<b>⚙️ التحكم في الخدمة</b>\n\n"
            f"<b>الخدمة:</b> {svc['name']}\n"
            f"<b>النوع:</b> {svc.get('service_type') or 'عام'}\n"
            f"<b>الحسابات:</b> {len(accounts)}\n"
            f"<b>التفاعل:</b> {auto}"
        )
        mirx_show(call, text, mirx_service_control_keyboard(svc))

@bot.callback_query_handler(func=lambda c: c.data.startswith("mirx_test_service_") and c.data[18:].isdigit())
def mirx_callback_test_service(call: CallbackQuery):
    if not mirx_guard(call.from_user.id):
        return
    sid = mirx_safe_int(call.data[18:])
    svc = db.get_service(sid) if sid is not None else None
    if not svc:
        bot.answer_callback_query(call.id, "الخدمة غير موجودة.", show_alert=True)
        return
    if (svc.get("service_type") or "").strip() not in ("قلب", "تفاعل"):
        bot.answer_callback_query(call.id, "التجربة متاحة لخدمات التفاعل فقط.", show_alert=True)
        return
    accounts = db.get_service_telegram_accounts(sid)
    if not accounts:
        bot.answer_callback_query(call.id, "أضف حساب Telegram للخدمة أولاً.", show_alert=True)
        return
    set_state(call.from_user.id, "mirx_test_svc_link", svc_id=sid)
    mirx_show(
        call,
        f"<b>🧪 تجربة الخدمة: {svc['name']}</b>\n\n"
        "أرسل <b>رابط المنشور فقط</b> وسيتم تنفيذ التفاعل الحقيقي من الحساب/الحسابات المحددة للخدمة.\n\n"
        "<b>منشور عام:</b>\n<code>https://t.me/channel/123</code>\n\n"
        "<b>منشور خاص:</b>\n<code>https://t.me/c/1234567890/123</code>",
        mirx_layout([mirx_btn("❌ إلغاء", f"mirx_service_{sid}", "red")])
    )


@bot.message_handler(func=lambda m: get_state(m.from_user.id).get("state") == "mirx_test_svc_link")
def mirx_msg_test_svc_link(msg: Message):
    uid = msg.from_user.id
    if not mirx_guard(uid):
        return
    link = (msg.text or "").strip()
    d = get_state(uid).get("data", {})
    sid = int(d.get("svc_id") or 0)
    svc = db.get_service(sid) if sid else None
    if not svc:
        clear_state(uid)
        send(msg.chat.id, "❌ الخدمة غير موجودة.")
        return
    try:
        _peer, msg_id = _parse_telegram_message_link(link)
    except Exception as e:
        send(msg.chat.id, "❌ رابط المنشور غير صحيح.\n\n"
             "مثال عام: <code>https://t.me/channel/123</code>\n"
             "مثال خاص: <code>https://t.me/c/1234567890/123</code>\n\n"
             f"الخطأ: <code>{str(e)[:250]}</code>")
        return
    accounts = db.get_service_telegram_accounts(sid)
    if not accounts:
        clear_state(uid)
        send(msg.chat.id, "❌ لا يوجد حساب مرتبط بالخدمة.")
        return
    mode = db.get_service_account_mode(svc)
    run_accounts = list(accounts) if mode == "multi" else list(accounts[:1])
    set_state(uid, "mirx_test_svc_running", svc_id=sid, link=link)
    send(msg.chat.id,
         f"⏳ جاري تجربة الخدمة على المنشور...\n\n"
         f"الخدمة: <b>{svc['name']}</b>\n"
         f"الوضع: <b>{'متعدد' if mode == 'multi' else 'واحد'}</b>\n"
         f"عدد الحسابات: <b>{len(run_accounts)}</b>\n"
         f"الرابط: <code>{link}</code>\n"
         f"المنشور: <code>{msg_id}</code>")

    def _run_test():
        used = []
        errors = []
        try:
            fake_order = {"link": link, "id": 0}
            workers = max(1, min(len(run_accounts), 16))
            with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="mirx-test") as pool:
                futures = {pool.submit(_execute_telegram_reaction, fake_order, svc, account): account for account in run_accounts}
                for future in as_completed(futures):
                    account = futures[future]
                    label = account.get("first_name") or account.get("username") or str(account.get("id"))
                    try:
                        emoji = future.result()
                        used.append(f"{label}: {emoji}")
                    except Exception as e:
                        errors.append(f"{label}: {str(e)[:180]}")
            if errors:
                send(msg.chat.id,
                     "<b>⚠️ التجربة اكتملت مع أخطاء</b>\n\n"
                     + ("\n".join(f"❌ {x}" for x in errors))
                     + ("\n\n" + "\n".join(f"✅ {x}" for x in used) if used else ""))
            else:
                send(msg.chat.id,
                     f"<b>✅ تم اختبار الخدمة بنجاح</b>\n\n"
                     f"تم التنفيذ من <b>{len(used)}</b> حساب/حسابات.\n"
                     + "\n".join(f"• {x}" for x in used))
        except Exception as e:
            send(msg.chat.id, f"<b>❌ فشلت التجربة</b>\n\n<code>{str(e)[:700]}</code>")
        finally:
            clear_state(uid)

    threading.Thread(target=_run_test, daemon=True).start()


@bot.callback_query_handler(func=lambda c: c.data.startswith("mirx_check_service_") and c.data[19:].isdigit())
def mirx_callback_check_service(call: CallbackQuery):
    # إنهاء حالة الضغط فوراً حتى لا يظل زر تيليجرام عالقاً أثناء SQLite أو تحديث الرسالة.
    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass
    if not mirx_guard(call.from_user.id):
        return
    sid = mirx_safe_int(call.data[19:])
    svc = db.get_service(sid) if sid is not None else None
    if not svc:
        bot.answer_callback_query(call.id, "الخدمة غير موجودة.", show_alert=True)
        return
    accounts = db.get_service_telegram_accounts(sid)
    issues = []
    if not svc.get("is_active"):
        issues.append("الخدمة متوقفة")
    if not accounts:
        issues.append("لا يوجد حساب تنفيذ مرتبط")
    if issues:
        text = "<b>🧪 فحص الخدمة</b>\n\n❌ " + "\n❌ ".join(issues)
    else:
        text = (
            "<b>🧪 فحص الخدمة</b>\n\n"
            "✅ تعريف الخدمة سليم\n"
            f"✅ حسابات التنفيذ: <b>{len(accounts)}</b>\n"
            f"✅ الحالة: <b>{'مفعّلة' if svc.get('is_active') else 'متوقفة'}</b>"
        )
    mirx_show(call, text, mirx_back_keyboard(f"mirx_service_{sid}"))

@bot.callback_query_handler(func=lambda c: c.data.startswith("mirx_delete_service_") and c.data[20:].isdigit())
def mirx_callback_delete_service(call: CallbackQuery):
    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass
    if not mirx_guard(call.from_user.id):
        return
    sid = mirx_safe_int(call.data[20:])
    svc = db.get_service(sid) if sid is not None else None
    if not svc:
        bot.answer_callback_query(call.id, "الخدمة غير موجودة.", show_alert=True)
        return
    try:
        # فك ارتباط كل الحسابات قبل حذف الخدمة
        db.set_service_telegram_accounts(sid, [])
        db.set_service_account_mode(sid, "single")
        # تنظيف أي جلسة إضافة حساب نشطة
        _mirx_tg_reset(call.from_user.id)
        clear_state(call.from_user.id)
        db.delete_service(sid)
    except Exception as e:
        print(f"[MIRX DELETE SERVICE] {e}")
        bot.answer_callback_query(call.id, f"❌ فشل الحذف: {str(e)[:80]}", show_alert=True)
        return
    bot.answer_callback_query(call.id, "✅ تم حذف الخدمة")
    aid = int(svc["app_id"])
    app = db.get_app(aid)
    services = db.get_app_services(aid, only_active=False) if app else []
    if app:
        title = f"{app.get('emoji') or '📦'} {app['name']}"
        text = f"<b>{title}</b>\n\nالخدمات الموجودة: <b>{len(services)}</b>"
        mirx_show(call, text, mirx_services_keyboard(aid, services))
    else:
        mirx_show(
            call,
            "<b>🧩 الخدمات والأقسام</b>\n\nاختر القسم لإدارته.",
            mirx_service_list_keyboard(db.get_apps(only_active=False))
        )

@bot.callback_query_handler(func=lambda c: c.data == "mirx_accounts")
def mirx_callback_accounts(call: CallbackQuery):
    if not mirx_guard(call.from_user.id):
        mirx_ack(call, "❌ غير مصرح.", True)
        return
    mirx_ack(call)
    try:
        owner = int(getattr(config, "TG_EXECUTION_USER_ID", 0) or 0)
        accounts = db.list_telegram_accounts(owner) if owner else []
        lines = []
        for a in accounts:
            name = (a.get("first_name") or "حساب").strip()
            username = f" @{a['username']}" if a.get("username") else ""
            lines.append(f"• 📱 <b>{name}</b>{username}")
        body = "لا توجد حسابات تنفيذ نشطة." if not lines else "\n".join(lines)
        mirx_show(call, f"<b>📱 حسابات التنفيذ</b>\n\n{body}", mirx_layout(
            [mirx_btn("➕ إضافة حساب", "tg_add_account", "green")],
            [mirx_btn("◀️ لوحة MIRX", "mirx_home", "blue")]
        ))
    except Exception as e:
        print(f"[MIRX ACCOUNTS ERROR] {type(e).__name__}: {e}")
        try:
            bot.send_message(call.message.chat.id, "❌ تعذر تحميل حسابات التنفيذ.", reply_markup=mirx_back_keyboard("home"), parse_mode="HTML")
        except Exception as e2:
            print(f"[MIRX ACCOUNTS FALLBACK ERROR] {type(e2).__name__}: {e2}")


@bot.callback_query_handler(func=lambda c: c.data == "mirx_reactions")
def mirx_callback_reactions(call: CallbackQuery):
    if not mirx_guard(call.from_user.id):
        mirx_ack(call, "❌ غير مصرح.", True)
        return
    mirx_ack(call)
    try:
        services = []
        for app in db.get_apps(only_active=False):
            services.extend([s for s in db.get_app_services(app["id"], only_active=False)
                             if (s.get("service_type") or "") in ("قلب", "تفاعل")])
        rows = []
        for svc in services:
            state = "🟢" if svc.get("auto_react") else "⚪"
            rows.append([mirx_btn(f"{state} {svc['name']}", f"mirx_service_{svc['id']}", "green" if svc.get("auto_react") else "blue")])
        if not rows:
            rows.append([mirx_btn("لا توجد خدمات تفاعل", "mirx_noop", "red")])
        rows.append([mirx_btn("◀️ لوحة MIRX", "mirx_home", "blue")])
        mirx_show(call, "<b>📡 التفاعل التلقائي</b>\n\nاختر الخدمة لإدارة التفاعل.", mirx_layout(*rows))
    except Exception as e:
        print(f"[MIRX REACTIONS ERROR] {type(e).__name__}: {e}")
        try:
            bot.send_message(call.message.chat.id, "❌ تعذر تحميل خدمات التفاعل.", reply_markup=mirx_back_keyboard("home"), parse_mode="HTML")
        except Exception as e2:
            print(f"[MIRX REACTIONS FALLBACK ERROR] {type(e2).__name__}: {e2}")


@bot.callback_query_handler(func=lambda c: c.data == "mirx_noop")
def mirx_callback_noop(call: CallbackQuery):
    if mirx_guard(call.from_user.id):
        bot.answer_callback_query(call.id, "لا يوجد إجراء هنا.")


@bot.callback_query_handler(func=lambda c: c.data == "mirx_channels")
def mirx_callback_channels(call: CallbackQuery):
    if not mirx_guard(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ غير مصرح.", show_alert=True)
        return
    mandatory = db.get_mandatory_channels()
    points = db.get_points_channels()
    orders = db.get_order_channels()
    text = (
        "<b>📢 القنوات</b>\n\n"
        f"📢 إجبارية: <b>{len(mandatory)}</b>\n"
        f"💎 نقاط: <b>{len(points)}</b>\n"
        f"📣 طلبات: <b>{len(orders)}</b>"
    )
    mirx_show(call, text, mirx_layout(
        [mirx_btn("📢 القنوات الإجبارية", "mirx_mandatory", "blue")],
        [mirx_btn("💎 قنوات النقاط", "mirx_points_channels", "blue")],
        [mirx_btn("📣 قنوات الطلبات", "mirx_order_channels", "blue")],
        [mirx_btn("◀️ لوحة MIRX", "mirx_home", "blue")]
    ))


@bot.callback_query_handler(func=lambda c: c.data == "mirx_store")
def mirx_callback_store(call: CallbackQuery):
    if not mirx_guard(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ غير مصرح.", show_alert=True)
        return
    products = db.get_store_products(only_active=False)
    pending = db.get_pending_store_orders()
    recharges = db.get_pending_recharges()
    text = (
        "<b>🛍️ المتجر والطلبات</b>\n\n"
        f"🛍️ المنتجات: <b>{len(products)}</b>\n"
        f"📋 طلبات المتجر المعلقة: <b>{len(pending)}</b>\n"
        f"💳 الشحن المعلق: <b>{len(recharges)}</b>"
    )
    mirx_show(call, text, mirx_layout(
        [mirx_btn("🛍️ إدارة المتجر", "mirx_store_products", "blue")],
        [mirx_btn("📋 الطلبات المعلقة", "mirx_pending_orders", "green")],
        [mirx_btn("💳 الشحن المعلق", "mirx_pending_recharges", "green")],
        [mirx_btn("◀️ لوحة MIRX", "mirx_home", "blue")]
    ))


@bot.callback_query_handler(func=lambda c: c.data == "mirx_rewards")
def mirx_callback_rewards(call: CallbackQuery):
    if not mirx_guard(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ غير مصرح.", show_alert=True)
        return
    mirx_show(call, "<b>🎁 النقاط والهدايا</b>\n\nإدارة المكافآت والأكواد والهدايا من هنا.", mirx_layout(
        [mirx_btn("🎡 عجلة الحظ", "mirx_wheel", "green")],
        [mirx_btn("🎁 الخدمات المجانية", "mirx_free_services", "green")],
        [mirx_btn("🎟️ أكواد الدعوة", "mirx_invites", "blue")],
        [mirx_btn("🎁 روابط الهدايا", "mirx_gifts", "green")],
        [mirx_btn("🎫 الكوبونات", "mirx_coupons", "blue")],
        [mirx_btn("⭐ إعدادات النقاط", "mirx_points_settings", "blue")],
        [mirx_btn("◀️ لوحة MIRX", "mirx_home", "blue")]
    ))


@bot.callback_query_handler(func=lambda c: c.data == "mirx_users")
def mirx_callback_users(call: CallbackQuery):
    if not mirx_guard(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ غير مصرح.", show_alert=True)
        return
    total = db.get_users_count()
    mirx_show(call, f"<b>👥 المستخدمون</b>\n\nإجمالي المستخدمين: <b>{total:,}</b>", mirx_layout(
        [mirx_btn("🔎 البحث عن مستخدم", "mirx_search_user", "blue")],
        [mirx_btn("◀️ لوحة MIRX", "mirx_home", "blue")]
    ))


@bot.callback_query_handler(func=lambda c: c.data == "mirx_stats")
def mirx_callback_stats(call: CallbackQuery):
    if not mirx_guard(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ غير مصرح.", show_alert=True)
        return
    total_u = db.get_users_count()
    total_o, today_o, rev, today_rev, pts = db.get_orders_stats()
    text = (
        "<b>📊 الإحصائيات</b>\n\n"
        f"👥 المستخدمون: <b>{total_u:,}</b>\n"
        f"📦 الطلبات: <b>{total_o:,}</b>\n"
        f"📅 طلبات اليوم: <b>{today_o:,}</b>\n"
        f"⭐ النقاط المستخدمة: <b>{pts:,}</b>\n"
        f"💰 الإيرادات: <b>{rev:.2f}$</b>\n"
        f"💵 إيرادات اليوم: <b>{today_rev:.2f}$</b>"
    )
    mirx_show(call, text, mirx_back_keyboard("home"))


@bot.callback_query_handler(func=lambda c: c.data == "mirx_communication")
def mirx_callback_communication(call: CallbackQuery):
    if not mirx_guard(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ غير مصرح.", show_alert=True)
        return
    mirx_show(call, "<b>📣 الإذاعة والتنبيهات</b>", mirx_layout(
        [mirx_btn("📣 إذاعة جماعية", "mirx_broadcast", "green")],
        [mirx_btn("🔔 التنبيهات والتقارير", "mirx_alerts", "blue")],
        [mirx_btn("◀️ لوحة MIRX", "mirx_home", "blue")]
    ))


@bot.callback_query_handler(func=lambda c: c.data == "mirx_settings")
def mirx_callback_settings(call: CallbackQuery):
    if not mirx_guard(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ غير مصرح.", show_alert=True)
        return
    active = db.get_config("bot_active", "1")
    support = db.get_config("support_username", "@support")
    mirx_show(call, f"<b>⚙️ إعدادات البوت</b>\n\nالحالة: <b>{'مفعّل' if active == '1' else 'متوقف'}</b>\nالدعم: <code>{support}</code>", mirx_layout(
        [mirx_btn("📡 التحديثات / الدعم", "mirx_bot_settings", "blue")],
        [mirx_btn("⭐ إعدادات النقاط", "mirx_points_settings", "blue")],
        [mirx_btn("◀️ لوحة MIRX", "mirx_home", "blue")]
    ))


@bot.callback_query_handler(func=lambda c: c.data == "mirx_database")
def mirx_callback_database(call: CallbackQuery):
    if not mirx_guard(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ غير مصرح.", show_alert=True)
        return
    conn = db.get_conn()
    try:
        counts = {}
        for table in ("users", "orders", "apps", "app_services", "telegram_accounts"):
            counts[table] = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    finally:
        conn.close()
    text = (
        "<b>🗄️ قاعدة البيانات</b>\n\n"
        f"👥 users: <b>{counts['users']:,}</b>\n"
        f"📦 orders: <b>{counts['orders']:,}</b>\n"
        f"🧩 apps: <b>{counts['apps']:,}</b>\n"
        f"⚙️ services: <b>{counts['app_services']:,}</b>\n"
        f"📱 Telegram accounts: <b>{counts['telegram_accounts']:,}</b>"
    )
    mirx_show(call, text, mirx_layout(
        [mirx_btn("📤 تصدير البيانات", "mirx_export", "green")],
        [mirx_btn("📥 استيراد البيانات", "mirx_import", "blue")],
        [mirx_btn("ℹ️ الإعدادات الحالية", "mirx_db_info", "blue")],
        [mirx_btn("◀️ لوحة MIRX", "mirx_home", "blue")]
    ))


@bot.callback_query_handler(func=lambda c: c.data.startswith("mirx_delete_app_") and c.data[16:].isdigit())
def mirx_callback_delete_app(call: CallbackQuery):
    if not mirx_guard(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ غير مصرح.", show_alert=True)
        return
    aid = mirx_safe_int(call.data[15:])
    app = db.get_app(aid) if aid is not None else None
    if not app:
        bot.answer_callback_query(call.id, "القسم غير موجود.", show_alert=True)
        return
    try:
        db.delete_app(aid)
        bot.answer_callback_query(call.id, "تم حذف القسم")
        fake = call
        fake.data = "mirx_catalog"
        mirx_callback_catalog(fake)
    except Exception as e:
        bot.answer_callback_query(call.id, f"فشل الحذف: {str(e)[:80]}", show_alert=True)


@bot.callback_query_handler(func=lambda c: c.data == "mirx_add_app")
def mirx_callback_add_app(call: CallbackQuery):
    if not mirx_guard(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ غير مصرح.", show_alert=True)
        return
    set_state(call.from_user.id, "mirx_add_app")
    mirx_show(call, "<b>➕ إضافة قسم جديد</b>\n\nأرسل: <code>اسم القسم|الإيموجي</code>", mirx_back_keyboard("mirx_catalog"))


@bot.message_handler(func=lambda m: get_state(m.from_user.id).get("state") == "mirx_add_app")
def mirx_message_add_app(msg: Message):
    if not mirx_guard(msg.from_user.id):
        return
    raw = (msg.text or "").strip()
    parts = raw.split("|", 1)
    if not parts or not parts[0].strip():
        send(msg.chat.id, "❌ الصيغة: اسم القسم|الإيموجي")
        return
    name = parts[0].strip()
    emoji = parts[1].strip() if len(parts) > 1 else "📦"
    # قبول الاسم الكامل مع الإيموجي في أوله.
    if len(parts) == 1:
        for lead in ("🚀", "📱", "🎯", "💎", "🔥", "⭐", "👥", "👁️", "👍", "🛠️", "⚙️"):
            if name.startswith(lead):
                emoji = lead
                name = name[len(lead):].strip() or name
                break
    clear_state(msg.from_user.id)
    # رد فوري ثم كتابة SQLite في Thread مستقل حتى لا تتوقف استقبال الرسائل.
    send(msg.chat.id, "⚡ جاري إضافة القسم...", mirx_home_keyboard())
    def _job():
        try:
            app_id = db.add_app(name, emoji or "📦")
            bot.send_message(
                msg.chat.id,
                f"<b>✅ تم إضافة القسم</b>\n\n{emoji or '📦'} <b>{name}</b>\nID: <code>{app_id}</code>",
                reply_markup=mirx_home_keyboard()
            )
        except Exception as e:
            bot.send_message(msg.chat.id, f"❌ تعذر إضافة القسم: <code>{str(e)[:160]}</code>")
    threading.Thread(target=_job, daemon=True, name="mirx-add-app",).start()


@bot.callback_query_handler(func=lambda c: c.data.startswith("mirx_add_service_") and c.data[17:].isdigit())
def mirx_callback_add_service(call: CallbackQuery):
    if not mirx_guard(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ غير مصرح.", show_alert=True)
        return
    aid = mirx_safe_int(call.data[17:])
    if aid is None or not db.get_app(aid):
        bot.answer_callback_query(call.id, "القسم غير موجود.", show_alert=True)
        return
    set_state(call.from_user.id, "mirx_add_service", app_id=aid)
    mirx_show(call, "<b>➕ إضافة خدمة جديدة</b>\n\nأرسل:\n<code>النقاط|اسم الخدمة|الحد الأدنى|الحد الأقصى</code>", mirx_back_keyboard(f"mirx_app_{aid}"))


@bot.message_handler(func=lambda m: get_state(m.from_user.id).get("state") == "mirx_add_service")
def mirx_message_add_service(msg: Message):
    if not mirx_guard(msg.from_user.id):
        return
    state = get_state(msg.from_user.id)
    aid = int(state.get("data", {}).get("app_id", 0) or 0)
    try:
        parts = (msg.text or "").strip().split("|", 3)
        if len(parts) < 2:
            raise ValueError("استخدم: النقاط|اسم الخدمة|الحد الأدنى|الحد الأقصى")
        pts = int(parts[0].strip())
        name = parts[1].strip()
        mn = int(parts[2].strip()) if len(parts) > 2 and parts[2].strip() else 1
        mx = int(parts[3].strip()) if len(parts) > 3 and parts[3].strip() else mn
        if not name or pts <= 0 or mn < 1 or mx < mn:
            raise ValueError("تحقق من البيانات والأرقام")
        low = name.lower()
        if any(x in low for x in ("قلب", "تفاعل", "reaction", "react")):
            stype, emoji = "تفاعل", "❤️"
            # لو اسم الخدمة نفسه يحتوي على مجموعة Reactions، احفظها كما كتبها المطور.
            known = ["❤️‍🔥", "❤️", "👍", "🥰", "🔥", "😍", "😂", "😎", "👏", "😡", "😢", "🤔", "🤯", "🥳", "💯"]
            found = []
            for em in known:
                if em in name and em not in found:
                    found.append(em)
            pool = ",".join(found) if found else (
                "⭐,❤️,👍,👎,🔥,🥰,👏,😁,🤔,🤯,😱,🤬,😢,🎉,🤩,🤢,💩,🙏,👌,🕊️,🤡,🤧,😍,🐳,❤️‍🔥,🌚,"
                "🌭,💯,🤣,⚡,🍌,🏆,💔,😐,😑,🍓,🍾,💋,☝️,😈,😴,😭,🤓,👻,👨‍💻,👀,🎃,🙈,😇,😨,🤝,📝,😊,"
                "🤦,🎅,🎄,☃️,💅,😛,🗿,🆒,💘,🙉,🦄,😘,💊,🙊,😎,👾,🤷‍♂️,🤷,🤷‍♀️,😠"
            )
            if found:
                emoji = found[0]
            # أي خدمة تفاعل جديدة تحصل على قائمة الـ20 الافتراضية تلقائياً.
            if stype == "تفاعل" and not pool:
                pool = MIRX_DEFAULT_REACTION_POOL
        elif any(x in low for x in ("مشاهدات", "views", "view")):
            stype, emoji, pool = "مشاهدات", "👁️", ""
        elif any(x in low for x in ("أعضاء", "عضو", "members", "member")):
            stype, emoji, pool = "أعضاء", "👥", ""
        else:
            stype, emoji, pool = "أخرى", "⚙️", ""
        clear_state(msg.from_user.id)
        send(msg.chat.id, "⚡ جاري إضافة الخدمة...", mirx_home_keyboard())
        def _job():
            try:
                public_id = db.add_service(aid, name, emoji, pts, mn, mx, service_type=stype,
                                            reaction_emoji=emoji if stype == "تفاعل" else "", reaction_pool=pool)
                bot.send_message(msg.chat.id,
                                 f"<b>✅ تمت إضافة الخدمة فوراً.</b>\n\n🆔 ID الخدمة: <code>{public_id}</code>",
                                 reply_markup=mirx_home_keyboard())
            except Exception as e:
                bot.send_message(msg.chat.id, f"❌ تعذر إنشاء الخدمة: <code>{str(e)[:150]}</code>")
        threading.Thread(target=_job, daemon=True).start()
    except Exception as e:
        clear_state(msg.from_user.id)
        send(msg.chat.id, f"❌ تعذر إنشاء الخدمة: {str(e)[:150]}")


# ─── MIRX: القنوات ─────────────────────────────────────────────
@bot.callback_query_handler(func=lambda c: c.data == "mirx_mandatory")
def mirx_callback_mandatory(call: CallbackQuery):
    if not mirx_guard(call.from_user.id): return
    rows = db.get_mandatory_channels()
    lines = [f"• {x['channel_name']} — <code>{x['channel_id']}</code>" for x in rows]
    body = "لا توجد قنوات إجبارية." if not lines else "\n".join(lines)
    mirx_show(call, f"<b>📢 القنوات الإجبارية</b>\n\n{body}", mirx_layout(
        [mirx_btn("➕ إضافة قناة", "mirx_add_mandatory", "green")],
        [mirx_btn("◀️ رجوع للقنوات", "mirx_channels", "blue")]
    ))


@bot.callback_query_handler(func=lambda c: c.data == "mirx_points_channels")
def mirx_callback_points_channels(call: CallbackQuery):
    if not mirx_guard(call.from_user.id): return
    rows = db.get_points_channels()
    lines = [f"• {x['channel_name']} — +{x['points_reward']} نقطة" for x in rows]
    body = "لا توجد قنوات نقاط." if not lines else "\n".join(lines)
    mirx_show(call, f"<b>💎 قنوات النقاط</b>\n\n{body}", mirx_layout(
        [mirx_btn("➕ إضافة قناة", "mirx_add_points_channel", "green")],
        [mirx_btn("◀️ رجوع للقنوات", "mirx_channels", "blue")]
    ))


@bot.callback_query_handler(func=lambda c: c.data == "mirx_order_channels")
def mirx_callback_order_channels(call: CallbackQuery):
    if not mirx_guard(call.from_user.id): return
    rows = db.get_order_channels()
    lines = [f"• {x['channel_name']} — <code>{x['channel_id']}</code>" for x in rows]
    body = "لا توجد قنوات طلبات." if not lines else "\n".join(lines)
    mirx_show(call, f"<b>📣 قنوات الطلبات</b>\n\n{body}", mirx_layout(
        [mirx_btn("➕ إضافة قناة", "mirx_add_order_channel", "green")],
        [mirx_btn("◀️ رجوع للقنوات", "mirx_channels", "blue")]
    ))


@bot.callback_query_handler(func=lambda c: c.data == "mirx_add_mandatory")
def mirx_callback_add_mandatory(call: CallbackQuery):
    if not mirx_guard(call.from_user.id): return
    set_state(call.from_user.id, "mirx_add_mandatory")
    mirx_show(call, "<b>➕ إضافة قناة إجبارية</b>\n\nأرسل:\n<code>channel_id|اسم القناة|الرابط|الحد</code>", mirx_back_keyboard("mirx_mandatory"))


@bot.message_handler(func=lambda m: get_state(m.from_user.id).get("state") == "mirx_add_mandatory")
def mirx_message_add_mandatory(msg: Message):
    if not mirx_guard(msg.from_user.id): return
    try:
        p = (msg.text or "").strip().split("|", 3)
        if len(p) < 3: raise ValueError("الصيغة غير صحيحة")
        target = int(p[3]) if len(p) > 3 and p[3].strip() else 0
        if not db.add_mandatory_channel(p[0].strip(), p[1].strip(), p[2].strip(), target):
            raise ValueError("القناة موجودة بالفعل أو البيانات غير صحيحة")
        clear_state(msg.from_user.id)
        send(msg.chat.id, "✅ تمت إضافة القناة.", mirx_home_keyboard())
    except Exception as e:
        send(msg.chat.id, f"❌ {str(e)[:150]}")


@bot.callback_query_handler(func=lambda c: c.data == "mirx_add_points_channel")
def mirx_callback_add_points_channel(call: CallbackQuery):
    if not mirx_guard(call.from_user.id): return
    set_state(call.from_user.id, "mirx_add_points_channel")
    mirx_show(call, "<b>➕ إضافة قناة نقاط</b>\n\nأرسل:\n<code>channel_id|اسم القناة|الرابط|النقاط</code>", mirx_back_keyboard("mirx_points_channels"))


@bot.message_handler(func=lambda m: get_state(m.from_user.id).get("state") == "mirx_add_points_channel")
def mirx_message_add_points_channel(msg: Message):
    if not mirx_guard(msg.from_user.id): return
    try:
        p = (msg.text or "").strip().split("|", 3)
        if len(p) != 4: raise ValueError("الصيغة غير صحيحة")
        pts = int(p[3]);
        if pts <= 0 or not db.add_points_channel(p[0].strip(), p[1].strip(), p[2].strip(), pts):
            raise ValueError("تعذر إضافة القناة")
        clear_state(msg.from_user.id); send(msg.chat.id, "✅ تمت إضافة قناة النقاط.", mirx_home_keyboard())
    except Exception as e:
        send(msg.chat.id, f"❌ {str(e)[:150]}")


@bot.callback_query_handler(func=lambda c: c.data == "mirx_add_order_channel")
def mirx_callback_add_order_channel(call: CallbackQuery):
    if not mirx_guard(call.from_user.id): return
    set_state(call.from_user.id, "mirx_add_order_channel")
    mirx_show(call, "<b>➕ إضافة قناة طلبات</b>\n\nأرسل:\n<code>channel_id|اسم القناة</code>", mirx_back_keyboard("mirx_order_channels"))


@bot.message_handler(func=lambda m: get_state(m.from_user.id).get("state") == "mirx_add_order_channel")
def mirx_message_add_order_channel(msg: Message):
    if not mirx_guard(msg.from_user.id): return
    try:
        p = (msg.text or "").strip().split("|", 1)
        if len(p) != 2: raise ValueError("الصيغة غير صحيحة")
        ok = db.add_order_channel(p[0].strip(), p[1].strip())
        if not ok: raise ValueError("القناة موجودة بالفعل")
        clear_state(msg.from_user.id); send(msg.chat.id, "✅ تمت إضافة قناة الطلبات.", mirx_home_keyboard())
    except Exception as e:
        send(msg.chat.id, f"❌ {str(e)[:150]}")


# ─── MIRX: المتجر والطلبات ─────────────────────────────────────
@bot.callback_query_handler(func=lambda c: c.data == "mirx_store_products")
def mirx_callback_store_products(call: CallbackQuery):
    if not mirx_guard(call.from_user.id): return
    products = db.get_store_products(only_active=False)
    rows = []
    for p in products[:30]:
        state = "🟢" if p.get("is_active") else "🔴"
        rows.append([mirx_btn(f"{state} {p['name']} • {p['price']} نقطة", f"mirx_product_{p['id']}", "blue")])
    if not rows: rows.append([mirx_btn("لا توجد منتجات", "mirx_noop", "red")])
    rows.append([mirx_btn("◀️ رجوع", "mirx_store", "blue")])
    mirx_show(call, "<b>🛍️ إدارة المتجر</b>\n\nاختر المنتج.", mirx_layout(*rows))


@bot.callback_query_handler(func=lambda c: c.data.startswith("mirx_product_") and c.data[13:].isdigit())
def mirx_callback_product(call: CallbackQuery):
    if not mirx_guard(call.from_user.id): return
    pid = mirx_safe_int(call.data[13:]); p = db.get_store_product(pid) if pid is not None else None
    if not p: return bot.answer_callback_query(call.id, "المنتج غير موجود", show_alert=True)
    status = "مفعّل" if p.get("is_active") else "متوقف"
    text = f"<b>🛍️ {p['name']}</b>\n\nالسعر: <b>{p['price']}</b> نقطة\nالمخزون: <b>{p['stock']}</b>\nالحالة: <b>{status}</b>"
    mirx_show(call, text, mirx_layout(
        [mirx_btn("🔄 تفعيل / إيقاف", f"mirx_toggle_product_{pid}", "green")],
        [mirx_btn("🗑️ حذف المنتج", f"mirx_delete_product_{pid}", "red")],
        [mirx_btn("◀️ رجوع للمتجر", "mirx_store_products", "blue")]
    ))


@bot.callback_query_handler(func=lambda c: c.data.startswith("mirx_toggle_product_") and c.data[20:].isdigit())
def mirx_callback_toggle_product(call: CallbackQuery):
    if not mirx_guard(call.from_user.id): return
    pid = mirx_safe_int(call.data[20:])
    if pid is None: return
    db.toggle_store_product(pid); bot.answer_callback_query(call.id, "تم تحديث المنتج")
    fake = call; fake.data = f"mirx_product_{pid}"; mirx_callback_product(fake)


@bot.callback_query_handler(func=lambda c: c.data.startswith("mirx_delete_product_") and c.data[20:].isdigit())
def mirx_callback_delete_product(call: CallbackQuery):
    if not mirx_guard(call.from_user.id): return
    pid = mirx_safe_int(call.data[20:])
    if pid is None: return
    db.delete_store_product(pid); bot.answer_callback_query(call.id, "تم حذف المنتج")
    fake = call; fake.data = "mirx_store_products"; mirx_callback_store_products(fake)


@bot.callback_query_handler(func=lambda c: c.data == "mirx_pending_orders")
def mirx_callback_pending_orders(call: CallbackQuery):
    if not mirx_guard(call.from_user.id): return
    orders = db.get_pending_orders()
    rows = []
    for o in orders[:20]:
        rows.append([mirx_btn(f"📦 #{o['id']} • {o['quantity']:,} • {o['points_used']:,} نقطة", f"mirx_order_{o['id']}", "green")])
    if not rows: rows.append([mirx_btn("✅ لا توجد طلبات معلقة", "mirx_noop", "green")])
    rows.append([mirx_btn("◀️ رجوع", "mirx_store", "blue")])
    mirx_show(call, f"<b>📋 الطلبات المعلقة</b>\n\nالعدد: <b>{len(orders)}</b>", mirx_layout(*rows))


@bot.callback_query_handler(func=lambda c: c.data.startswith("mirx_order_") and c.data[11:].isdigit())
def mirx_callback_order(call: CallbackQuery):
    if not mirx_guard(call.from_user.id): return
    oid = mirx_safe_int(call.data[11:]); o = db.get_order(oid) if oid is not None else None
    if not o: return bot.answer_callback_query(call.id, "الطلب غير موجود", show_alert=True)
    text = f"<b>📦 الطلب #{oid}</b>\n\nالخدمة: <b>{o['service_name']}</b>\nالكمية: <b>{o['quantity']:,}</b>\nالنقاط: <b>{o['points_used']:,}</b>\nالحالة: <b>{o['status']}</b>"
    mirx_show(call, text, mirx_layout(
        [mirx_btn("✅ موافقة", f"mirx_approve_order_{oid}", "green"), mirx_btn("❌ رفض", f"mirx_reject_order_{oid}", "red")],
        [mirx_btn("◀️ رجوع", "mirx_pending_orders", "blue")]
    ))


@bot.callback_query_handler(func=lambda c: c.data.startswith("mirx_approve_order_") and c.data[19:].isdigit())
def mirx_callback_approve_order(call: CallbackQuery):
    if not mirx_guard(call.from_user.id): return
    oid = mirx_safe_int(call.data[19:]); o = db.get_order(oid) if oid is not None else None
    if not o: return bot.answer_callback_query(call.id, "الطلب غير موجود", show_alert=True)
    db.approve_order(oid)
    bot.answer_callback_query(call.id, "تمت الموافقة")
    mirx_callback_pending_orders(call)


@bot.callback_query_handler(func=lambda c: c.data.startswith("mirx_reject_order_") and c.data[18:].isdigit())
def mirx_callback_reject_order(call: CallbackQuery):
    if not mirx_guard(call.from_user.id): return
    oid = mirx_safe_int(call.data[18:]);
    if oid is None: return
    db.reject_order(oid); bot.answer_callback_query(call.id, "تم رفض الطلب")
    mirx_callback_pending_orders(call)


@bot.callback_query_handler(func=lambda c: c.data == "mirx_pending_recharges")
def mirx_callback_pending_recharges(call: CallbackQuery):
    if not mirx_guard(call.from_user.id): return
    rows = db.get_pending_recharges()
    text = "<b>💳 الشحن المعلق</b>\n\n"
    text += "لا توجد طلبات شحن معلقة." if not rows else "\n".join(f"• #{x['id']} — {x['amount']} — {x['method']}" for x in rows[:30])
    mirx_show(call, text, mirx_back_keyboard("mirx_store"))


# ─── MIRX: المكافآت ────────────────────────────────────────────
@bot.callback_query_handler(func=lambda c: c.data in {"mirx_wheel", "mirx_free_services", "mirx_invites", "mirx_gifts", "mirx_coupons", "mirx_points_settings"})
def mirx_callback_rewards_sub(call: CallbackQuery):
    if not mirx_guard(call.from_user.id): return
    key = call.data
    if key == "mirx_wheel":
        n = len(db.get_wheel_prizes()) if hasattr(db, "get_wheel_prizes") else 0
        title, body = "🎡 عجلة الحظ", f"عدد الجوائز المعرفة: <b>{n}</b>"
    elif key == "mirx_free_services":
        n = len(db.get_free_services(only_active=False)); title, body = "🎁 الخدمات المجانية", f"عدد الخدمات: <b>{n}</b>"
    elif key == "mirx_invites":
        n = len(db.get_invites()); title, body = "🎟️ أكواد الدعوة", f"عدد الأكواد: <b>{n}</b>"
    elif key == "mirx_gifts":
        n = len(db.get_all_gift_links()); title, body = "🎁 روابط الهدايا", f"عدد الروابط: <b>{n}</b>"
    elif key == "mirx_coupons":
        n = len(db.get_all_coupons()); title, body = "🎫 الكوبونات", f"عدد الكوبونات: <b>{n}</b>"
    else:
        title = "⭐ إعدادات النقاط"
        body = (f"سعر النقاط: <b>{db.get_config('points_per_1000','10')}</b> / 1000\n"
                f"دعوة: <b>{db.get_config('referral_points','50')}</b>\n"
                f"يومي: <b>{db.get_config('daily_gift_points','5')}</b>\n"
                f"أسبوعي: <b>{db.get_config('weekly_gift_points','50')}</b>")
    mirx_show(call, f"<b>{title}</b>\n\n{body}", mirx_back_keyboard("mirx_rewards"))


# ─── MIRX: المستخدمون ─────────────────────────────────────────
@bot.callback_query_handler(func=lambda c: c.data == "mirx_search_user")
def mirx_callback_search_user(call: CallbackQuery):
    if not mirx_guard(call.from_user.id): return
    set_state(call.from_user.id, "mirx_search_user")
    mirx_show(call, "<b>🔎 البحث عن مستخدم</b>\n\nأرسل Telegram ID أو @username.", mirx_back_keyboard("mirx_users"))


@bot.message_handler(func=lambda m: get_state(m.from_user.id).get("state") == "mirx_search_user")
def mirx_message_search_user(msg: Message):
    if not mirx_guard(msg.from_user.id): return
    q = (msg.text or "").strip()
    u = None
    if q.lstrip("-").isdigit(): u = db.get_user(int(q))
    else: u = db.get_user_by_username(q)
    clear_state(msg.from_user.id)
    if not u:
        send(msg.chat.id, "❌ المستخدم غير موجود.", mirx_home_keyboard()); return
    status = "محظور" if u.get("is_banned") else "نشط"
    text = f"<b>👤 المستخدم</b>\n\nID: <code>{u['tg_id']}</code>\nالاسم: <b>{u['full_name']}</b>\nالرصيد: <b>{u['balance']}</b>\nالنقاط: <b>{u['points']:,}</b>\nالحالة: <b>{status}</b>"
    send(msg.chat.id, text, mirx_home_keyboard())


# ─── MIRX: الإذاعة والتنبيهات ─────────────────────────────────
@bot.callback_query_handler(func=lambda c: c.data == "mirx_broadcast")
def mirx_callback_broadcast(call: CallbackQuery):
    if not mirx_guard(call.from_user.id): return
    set_state(call.from_user.id, "mirx_broadcast")
    mirx_show(call, "<b>📣 إذاعة جماعية</b>\n\nأرسل الرسالة التي تريد إرسالها للمستخدمين.", mirx_back_keyboard("mirx_communication"))


@bot.message_handler(func=lambda m: get_state(m.from_user.id).get("state") == "mirx_broadcast")
def mirx_message_broadcast(msg: Message):
    if not mirx_guard(msg.from_user.id): return
    text = (msg.text or "").strip()
    if not text: return
    clear_state(msg.from_user.id)
    users = db.get_all_users()
    def _run():
        ok = fail = 0
        for u in users:
            try:
                bot.send_message(int(u["tg_id"]), text)
                ok += 1
                time.sleep(0.03)
            except Exception:
                fail += 1
        try: bot.send_message(msg.chat.id, f"<b>📣 انتهت الإذاعة</b>\n\n✅ نجح: <b>{ok}</b>\n❌ فشل: <b>{fail}</b>", reply_markup=mirx_home_keyboard())
        except Exception: pass
    threading.Thread(target=_run, daemon=True).start()
    send(msg.chat.id, "⏳ بدأت الإذاعة في الخلفية.", mirx_home_keyboard())


@bot.callback_query_handler(func=lambda c: c.data == "mirx_alerts")
def mirx_callback_alerts(call: CallbackQuery):
    if not mirx_guard(call.from_user.id): return
    low = db.get_config("low_points_alert", "50")
    report = db.get_config("daily_report_enabled", "1")
    mirx_show(call, f"<b>🔔 التنبيهات والتقارير</b>\n\nحد الرصيد المنخفض: <b>{low}</b>\nالتقرير اليومي: <b>{'مفعّل' if report == '1' else 'متوقف'}</b>", mirx_layout(
        [mirx_btn("🔄 تبديل التقرير اليومي", "mirx_toggle_report", "green")],
        [mirx_btn("✏️ تغيير حد التنبيه", "mirx_change_low_alert", "blue")],
        [mirx_btn("📊 تقرير الآن", "mirx_report_now", "green")],
        [mirx_btn("◀️ لوحة MIRX", "mirx_home", "blue")]
    ))


@bot.callback_query_handler(func=lambda c: c.data == "mirx_toggle_report")
def mirx_callback_toggle_report(call: CallbackQuery):
    if not mirx_guard(call.from_user.id): return
    cur = db.get_config("daily_report_enabled", "1")
    db.set_config("daily_report_enabled", "0" if cur == "1" else "1")
    bot.answer_callback_query(call.id, "تم تحديث الإعداد")
    mirx_callback_alerts(call)


@bot.callback_query_handler(func=lambda c: c.data == "mirx_change_low_alert")
def mirx_callback_change_low_alert(call: CallbackQuery):
    if not mirx_guard(call.from_user.id): return
    set_state(call.from_user.id, "mirx_change_low_alert")
    mirx_show(call, "<b>✏️ حد التنبيه</b>\n\nأرسل عدد النقاط، أو 0 لتعطيله.", mirx_back_keyboard("mirx_alerts"))


@bot.message_handler(func=lambda m: get_state(m.from_user.id).get("state") == "mirx_change_low_alert")
def mirx_message_change_low_alert(msg: Message):
    if not mirx_guard(msg.from_user.id): return
    try: value = int((msg.text or "").strip());
    except Exception: send(msg.chat.id, "❌ أرسل رقماً فقط."); return
    db.set_config("low_points_alert", str(max(0, value))); clear_state(msg.from_user.id)
    send(msg.chat.id, "✅ تم حفظ الحد.", mirx_home_keyboard())


# ─── MIRX: إعدادات البوت ───────────────────────────────────────
@bot.callback_query_handler(func=lambda c: c.data == "mirx_bot_settings")
def mirx_callback_bot_settings(call: CallbackQuery):
    if not mirx_guard(call.from_user.id): return
    active = db.get_config("bot_active", "1")
    support = db.get_config("support_username", "@support")
    mirx_show(call, f"<b>📡 التحديثات / الدعم</b>\n\nالحالة: <b>{'مفعّل' if active == '1' else 'متوقف'}</b>\nالدعم: <code>{support}</code>", mirx_layout(
        [mirx_btn("🔄 تشغيل / إيقاف البوت", "mirx_toggle_bot", "green")],
        [mirx_btn("✏️ تغيير الدعم", "mirx_change_support", "blue")],
        [mirx_btn("◀️ لوحة MIRX", "mirx_home", "blue")]
    ))


@bot.callback_query_handler(func=lambda c: c.data == "mirx_toggle_bot")
def mirx_callback_toggle_bot(call: CallbackQuery):
    if not mirx_guard(call.from_user.id): return
    cur = db.get_config("bot_active", "1")
    db.set_config("bot_active", "0" if cur == "1" else "1")
    bot.answer_callback_query(call.id, "تم تحديث حالة البوت")
    mirx_callback_bot_settings(call)


@bot.callback_query_handler(func=lambda c: c.data == "mirx_change_support")
def mirx_callback_change_support(call: CallbackQuery):
    if not mirx_guard(call.from_user.id): return
    set_state(call.from_user.id, "mirx_change_support")
    mirx_show(call, "<b>✏️ تغيير الدعم</b>\n\nأرسل username الدعم مثل <code>@support</code>.", mirx_back_keyboard("mirx_bot_settings"))


@bot.message_handler(func=lambda m: get_state(m.from_user.id).get("state") == "mirx_change_support")
def mirx_message_change_support(msg: Message):
    if not mirx_guard(msg.from_user.id): return
    value = (msg.text or "").strip()
    if value and not value.startswith("@"): value = "@" + value
    db.set_config("support_username", value); clear_state(msg.from_user.id)
    send(msg.chat.id, "✅ تم حفظ الدعم.", mirx_home_keyboard())


# ─── MIRX: قاعدة البيانات ──────────────────────────────────────
@bot.callback_query_handler(func=lambda c: c.data == "mirx_export")
def mirx_callback_export(call: CallbackQuery):
    if not mirx_guard(call.from_user.id): return
    try:
        import io
        raw = db.export_db_json().encode("utf-8")
        f = io.BytesIO(raw); f.name = f"mirx_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        bot.answer_callback_query(call.id, "جارٍ التصدير...")
        bot.send_document(call.message.chat.id, f, caption="<b>✅ نسخة MIRX الاحتياطية</b>")
    except Exception as e:
        bot.answer_callback_query(call.id, f"خطأ: {str(e)[:80]}", show_alert=True)


@bot.callback_query_handler(func=lambda c: c.data == "mirx_db_info")
def mirx_callback_db_info(call: CallbackQuery):
    if not mirx_guard(call.from_user.id): return
    rows = db.get_all_config(); text = "<b>🧾 إعدادات قاعدة البيانات</b>\n\n"
    for r in rows:
        text += f"<code>{r['key']}</code> = {str(r['value'])[:100]}\n"
    if len(text) > 3500: text = text[:3500] + "\n..."
    mirx_show(call, text, mirx_back_keyboard("mirx_database"))


@bot.callback_query_handler(func=lambda c: c.data == "mirx_import")
def mirx_callback_import(call: CallbackQuery):
    if not mirx_guard(call.from_user.id): return
    set_state(call.from_user.id, "mirx_import")
    mirx_show(call, "<b>📥 استيراد قاعدة البيانات</b>\n\nأرسل ملف JSON الاحتياطي كملف Telegram.", mirx_back_keyboard("mirx_database"))


@bot.message_handler(content_types=["document"])
def mirx_document_import(msg: Message):
    if not mirx_guard(msg.from_user.id): return
    if get_state(msg.from_user.id).get("state") != "mirx_import": return
    try:
        info = bot.get_file(msg.document.file_id)
        raw = bot.download_file(info.file_path)
        data = json.loads(raw.decode("utf-8"))
        if not isinstance(data, dict): raise ValueError("ملف غير صالح")
        clear_state(msg.from_user.id)
        send(msg.chat.id, "⚠️ تم التحقق من ملف JSON. الاستيراد الكامل للبيانات الحساسة متوقف في MIRX الجديد لتجنب الكتابة الخاطئة على القاعدة.", mirx_home_keyboard())
    except Exception as e:
        send(msg.chat.id, f"❌ ملف غير صالح: {str(e)[:150]}")


# ─── MIRX: حماية إضافية للـ callbacks الجديدة ─────────────────
@bot.callback_query_handler(func=lambda c: c.data.startswith("mirx_") and not mirx_guard(c.from_user.id))
def mirx_callback_unauthorized(call: CallbackQuery):
    try: bot.answer_callback_query(call.id, "❌ لوحة MIRX للمطور فقط.", show_alert=True)
    except Exception: pass

# ══════════════════════════════════════════════════════════════════
#   15. تشغيل
# ══════════════════════════════════════════════════════════════════
# logging is initialized explicitly; polling itself does not depend on
# the optional logger_level argument, which differs between pyTelegramBotAPI versions.
try:
    logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s %(message)s")
except Exception:
    pass

# Global callback safety: acknowledge any unmatched callback so Telegram never leaves it pending.
@bot.callback_query_handler(func=lambda call: True)
def _global_callback_safety(call):
    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass

if __name__ == "__main__":
    print(f"🔥 {config.BOT_NAME} V8 — All MIRX buttons + states + SQLite stability")
    print("📌 نفس الـhandlers ونفس مسارات الأزرار بدون Dispatcher إضافي.")

    if not config.BOT_TOKEN or config.BOT_TOKEN == "PUT_YOUR_BOT_TOKEN_HERE":
        raise SystemExit("❌ BOT_TOKEN غير مضبوط داخل إعدادات البوت.")

    try:
        me = bot.get_me()
        print(f"✅ تم التحقق من البوت: @{me.username} (ID: {me.id})")
    except Exception as e:
        raise SystemExit(f"❌ تعذر الاتصال بـ Telegram: {e}")

    # إزالة أي Webhook قديم حتى يعمل Polling بشكل طبيعي.
    try:
        bot.remove_webhook()
        time.sleep(0.5)
    except Exception as e:
        print(f"⚠️ تعذر إزالة Webhook القديم: {e}")

    # Workers الخلفية تبقى كما هي؛ لا نلمس وظائف الخدمات.
    try:
        threading.Thread(target=auto_update_orders, daemon=True, name="orders-updater").start()
    except Exception as e:
        print(f"⚠️ orders-updater: {e}")
    try:
        threading.Thread(target=start_reaction_monitor, daemon=True, name="reaction-monitor").start()
    except Exception as e:
        print(f"⚠️ reaction-monitor: {e}")
    try:
        threading.Thread(target=daily_report_loop, daemon=True, name="daily-report").start()
    except Exception as e:
        print(f"⚠️ daily-report: {e}")

    # مهم: لا يوجد TeleBot ثاني، ولا ThreadPool للـcallbacks، ولا
    # process_new_updates يدوي. pyTelegramBotAPI يدير callback/message
    # dispatch بنفس الـbot الذي سُجلت عليه كل الـhandlers.
    print("🚀 Stable Polling: original TeleBot handlers + callbacks مباشرة.")
    print("🔘 Add accounts / Service accounts / Auto reaction / Test / Back: handlers preserved.")

    while True:
        try:
            bot.infinity_polling(
                timeout=50,
                long_polling_timeout=50,
                skip_pending=True,
                allowed_updates=["message", "callback_query"],
            )
        except KeyboardInterrupt:
            print("🛑 تم إيقاف البوت.")
            break
        except Exception as e:
            try:
                logging.exception("[POLLING ERROR] %s", e)
            except Exception:
                print(f"⚠️ Polling error: {type(e).__name__}: {e}")
            # إعادة تشغيل polling فقط عند خطأ حقيقي في الاتصال/المحرك.
            # لا نخرج من البرنامج حتى لو حصل Exception غير متوقع.
            time.sleep(3)
            continue

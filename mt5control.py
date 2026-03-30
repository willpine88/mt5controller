"""
MT5 Controller - WillPine
MT5 Controller - WillPine
==========================================
- Lần đầu chạy: form nhập config
- Chạy xong: ẩn vào system tray
- Tray menu: Start/Stop Bot, Edit Config, Exit

Cài: python -m pip install python-telegram-bot pywin32 MetaTrader5 pystray Pillow pyinstaller
Build exe: pyinstaller --onefile --noconsole tg.py
"""

import os
import sys
import time
import threading
import logging
import configparser
import asyncio
from datetime import datetime
from pathlib import Path

import win32gui
import win32con
import win32api
import win32process
import MetaTrader5 as mt5
import pystray
from PIL import Image, ImageDraw
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import tkinter as tk
from tkinter import messagebox

# ============================================================
#  PATHS
# ============================================================
BASE_DIR    = Path(os.path.dirname(sys.executable if getattr(sys, "frozen", False) else __file__))
CONFIG_FILE = BASE_DIR / "config.ini"
LOG_FILE    = BASE_DIR / "bot.log"

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO,
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# ============================================================
#  CONFIG
# ============================================================
def load_config() -> configparser.ConfigParser:
    cfg = configparser.ConfigParser()
    cfg.read(CONFIG_FILE, encoding="utf-8")
    return cfg

def save_config(token, username, vps_name, allowed_ids, mt5_keyword):
    cfg = configparser.ConfigParser()
    cfg["bot"] = {
        "token":       token.strip(),
        "username":    username.strip().lstrip("@"),
        "vps_name":    vps_name.strip(),
        "allowed_ids": allowed_ids.strip(),
        "mt5_keyword": mt5_keyword.strip(),
    }
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        cfg.write(f)

def config_complete() -> bool:
    cfg = load_config()
    return (
        cfg.has_section("bot")
        and len(cfg.get("bot", "token", fallback="")) > 10
        and cfg.get("bot", "username", fallback="") != ""
        and cfg.get("bot", "allowed_ids", fallback="") != ""
    )

def get_cfg() -> dict:
    cfg = load_config()
    b   = cfg["bot"] if cfg.has_section("bot") else {}
    ids = [int(x.strip()) for x in b.get("allowed_ids", "").split(",") if x.strip().isdigit()]
    return {
        "token":       b.get("token", ""),
        "username":    b.get("username", ""),
        "vps_name":    b.get("vps_name", "VPS"),
        "allowed_ids": ids,
        "mt5_keyword": b.get("mt5_keyword", "MetaTrader 5"),
    }


# ============================================================
#  CONFIG DIALOG (tkinter)
# ============================================================
def show_config_dialog(on_save=None):
    cfg = load_config()
    b   = cfg["bot"] if cfg.has_section("bot") else {}

    root = tk.Tk()
    root.title("MT5 Controller - WillPine")
    root.resizable(False, False)
    root.configure(bg="#f5f5f5")

    w, h = 460, 500
    root.update_idletasks()
    x = (root.winfo_screenwidth()  - w) // 2
    y = (root.winfo_screenheight() - h) // 2
    root.geometry(f"{w}x{h}+{x}+{y}")
    root.minsize(w, h)

    tk.Label(
        root, text="MT5 Controller - WillPine",
        font=("Segoe UI", 11, "bold"), bg="#f5f5f5"
    ).pack(pady=(16, 8))

    # Button anchor bottom — đặt TRƯỚC frame để luôn hiển thị
    def on_click_save():
        token   = e_token.get().strip()
        user    = e_user.get().strip().lstrip("@")
        vps     = e_vps.get().strip()
        ids     = e_ids.get().strip()
        keyword = e_keyword.get().strip()
        if not all([token, user, ids, keyword]):
            messagebox.showerror("Lỗi", "Vui lòng điền đầy đủ tất cả các trường.")
            return
        save_config(token, user, vps, ids, keyword)
        logger.info("Config saved.")
        root.destroy()
        if on_save:
            threading.Thread(target=on_save, daemon=True).start()

    tk.Frame(root, height=1, bg="#ddd").pack(side="bottom", fill="x", padx=0, pady=0)
    tk.Button(
        root, text="LƯU VÀ KHỞI ĐỘNG BOT",
        font=("Segoe UI", 12, "bold"),
        bg="#0078d4", fg="white",
        relief="raised", bd=3,
        padx=24, pady=10,
        cursor="hand2",
        activebackground="#005a9e",
        activeforeground="white",
        command=on_click_save
    ).pack(side="bottom", pady=16, ipadx=10, ipady=4)

    frame = tk.Frame(root, bg="#f5f5f5")
    frame.pack(fill="x", padx=24)

    def field(label, default="", show=None):
        tk.Label(frame, text=label, anchor="w", bg="#f5f5f5",
                 font=("Segoe UI", 9)).pack(fill="x", pady=(8, 0))
        kw = {"font": ("Segoe UI", 9), "relief": "solid", "bd": 1}
        if show:
            kw["show"] = show
        e = tk.Entry(frame, **kw)
        e.insert(0, default)
        e.pack(fill="x", ipady=5)
        return e

    e_token   = field("Bot Token (từ @BotFather):",            b.get("token", ""),       show="*")
    e_user    = field("Bot Username (không có @):",             b.get("username", ""))
    e_vps     = field("Tên VPS (hiển thị trong tin nhắn):",     b.get("vps_name", "VPS-1"))
    e_ids     = field("Allowed User IDs (phân cách bằng phẩy):", b.get("allowed_ids", ""))
    e_keyword = field("Từ khóa tìm cửa sổ MT5:",                b.get("mt5_keyword", "Vantage"))

    tk.Label(
        frame,
        text="💡 Từ khóa MT5: một phần title cửa sổ MT5, vd: Vantage, Exness, ICMarkets...",
        font=("Segoe UI", 8), fg="#888", bg="#f5f5f5", wraplength=410, justify="left"
    ).pack(anchor="w", pady=(4, 0))

    root.mainloop()


# ============================================================
#  MT5 AUTOMATION
# ============================================================
def find_mt5_window() -> int | None:
    keyword = get_cfg()["mt5_keyword"]
    found   = []
    def cb(hwnd, _):
        if win32gui.IsWindowVisible(hwnd) and keyword in win32gui.GetWindowText(hwnd):
            found.append(hwnd)
    win32gui.EnumWindows(cb, None)
    return found[0] if found else None

def get_algo_state() -> bool | None:
    if not mt5.initialize():
        return None
    info = mt5.terminal_info()
    mt5.shutdown()
    return info.trade_allowed if info else None

def _force_foreground(hwnd):
    """Bring window to foreground, bypassing Windows restrictions."""
    current_thread = win32api.GetCurrentThreadId()
    target_thread = win32process.GetWindowThreadProcessId(hwnd)[0]
    if current_thread != target_thread:
        win32process.AttachThreadInput(current_thread, target_thread, True)
    try:
        if win32gui.GetWindowPlacement(hwnd)[1] == win32con.SW_SHOWMINIMIZED:
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            time.sleep(0.3)
        win32gui.BringWindowToTop(hwnd)
        win32gui.SetForegroundWindow(hwnd)
    finally:
        if current_thread != target_thread:
            win32process.AttachThreadInput(current_thread, target_thread, False)

def press_ctrl_e() -> tuple[bool, str]:
    hwnd = find_mt5_window()
    if not hwnd:
        return False, "❌ MT5 không tìm thấy — có thể chưa mở hoặc bị crash."
    try:
        try:
            _force_foreground(hwnd)
        except Exception as e:
            logger.warning("SetForegroundWindow failed (%s), sending keys anyway", e)
            # Even if foreground fails, PostMessage can still work
        time.sleep(0.5)
        # Use PostMessage as fallback — works without foreground focus
        win32api.PostMessage(hwnd, win32con.WM_KEYDOWN, win32con.VK_CONTROL, 0)
        time.sleep(0.05)
        win32api.PostMessage(hwnd, win32con.WM_KEYDOWN, ord("E"), 0)
        time.sleep(0.1)
        win32api.PostMessage(hwnd, win32con.WM_KEYUP, ord("E"), 0)
        time.sleep(0.05)
        win32api.PostMessage(hwnd, win32con.WM_KEYUP, win32con.VK_CONTROL, 0)
        logger.info("Ctrl+E sent OK")
        return True, "OK"
    except Exception as e:
        logger.error("press_ctrl_e: %s", e)
        return False, f"❌ Lỗi: {e}"

def set_algo(target: bool) -> tuple[bool, str, bool | None]:
    current = get_algo_state()
    if current is None:
        return False, "❌ MT5 không phản hồi.", None
    if current == target:
        return True, "already", current
    ok, err = press_ctrl_e()
    if not ok:
        return False, err, current
    time.sleep(1.0)
    new_state = get_algo_state()
    if new_state is None:
        return False, "❌ Không đọc được state sau toggle.", None
    if new_state != target:
        return False, "⚠️ Toggle xong nhưng state không đổi — thử lại.", new_state
    return True, "ok", new_state


# ============================================================
#  TELEGRAM BOT
# ============================================================
_bot_app:    Application | None = None
_bot_loop:   asyncio.AbstractEventLoop | None = None
_bot_thread: threading.Thread | None = None
_bot_running = False

def now_str():
    return datetime.now().strftime("%d/%m/%Y %H:%M:%S")

def is_allowed(update: Update) -> bool:
    return update.effective_user.id in get_cfg()["allowed_ids"]

def is_for_me(update: Update) -> bool:
    username = get_cfg()["username"]
    if update.effective_chat.type == "private":
        return True
    msg = update.message
    if not msg or not msg.text:
        return False
    return f"@{username}" in msg.text

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_for_me(update): return
    if not is_allowed(update): return
    cfg      = get_cfg()
    state    = get_algo_state()
    algo_str = "✅ BẬT" if state else ("⛔ TẮT" if state is not None else "❓ Không xác định")
    await update.message.reply_text(
        f"🤖 *MT5 Controller - WillPine | {cfg['vps_name']}*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"Trạng thái : *{algo_str}*\n\n"
        f"• /on@{cfg['username']} — Bật Algo\n"
        f"• /off@{cfg['username']} — Tắt Algo\n"
        f"• /status@{cfg['username']} — Trạng thái\n"
        f"• /help@{cfg['username']} — Hướng dẫn",
        parse_mode="Markdown"
    )

async def cmd_on(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_for_me(update): return
    if not is_allowed(update): return
    cfg  = get_cfg()
    user = update.effective_user.first_name
    await update.message.reply_text(
        f"⏳ Đang kiểm tra và bật Algo trên *{cfg['vps_name']}*...",
        parse_mode="Markdown"
    )
    ok, msg, _ = set_algo(True)
    if not ok:
        await update.message.reply_text(msg)
    elif msg == "already":
        await update.message.reply_text(
            f"ℹ️ *{cfg['vps_name']}* — Algo đang BẬT rồi.",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            f"✅ *{cfg['vps_name']}* — Algo đã BẬT\n"
            f"Thực hiện bởi : {user}\nLúc : {now_str()}",
            parse_mode="Markdown"
        )

async def cmd_off(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_for_me(update): return
    if not is_allowed(update): return
    cfg  = get_cfg()
    user = update.effective_user.first_name
    await update.message.reply_text(
        f"⏳ Đang kiểm tra và tắt Algo trên *{cfg['vps_name']}*...",
        parse_mode="Markdown"
    )
    ok, msg, _ = set_algo(False)
    if not ok:
        await update.message.reply_text(msg)
    elif msg == "already":
        await update.message.reply_text(
            f"ℹ️ *{cfg['vps_name']}* — Algo đang TẮT rồi.",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            f"⛔ *{cfg['vps_name']}* — Algo đã TẮT\n"
            f"Thực hiện bởi : {user}\nLúc : {now_str()}",
            parse_mode="Markdown"
        )

async def cmd_status(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_for_me(update): return
    if not is_allowed(update): return
    cfg      = get_cfg()
    state    = get_algo_state()
    mt5_win  = find_mt5_window()
    mt5_str  = "✅ Đang chạy" if mt5_win else "❌ Không tìm thấy"
    algo_str = "✅ BẬT" if state else ("⛔ TẮT" if state is not None else "❓ Không xác định")
    await update.message.reply_text(
        f"📊 *{cfg['vps_name']} — Trạng thái*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"MT5 Terminal : {mt5_str}\n"
        f"Algo Trading : *{algo_str}*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🕐 Hiện tại  : {now_str()}",
        parse_mode="Markdown"
    )

async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_for_me(update): return
    if not is_allowed(update): return
    cfg = get_cfg()
    await update.message.reply_text(
        f"📖 *Hướng dẫn — {cfg['vps_name']}*\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"`/on@{cfg['username']}` — Bật Algo\n"
        f"`/off@{cfg['username']}` — Tắt Algo\n"
        f"`/status@{cfg['username']}` — Trạng thái\n\n"
        f"Bot đọc trạng thái thực từ MT5 API.\n"
        f"Bật/tắt tay trên MT5 vẫn nhận diện đúng.",
        parse_mode="Markdown"
    )

def start_bot():
    global _bot_app, _bot_loop, _bot_thread, _bot_running
    if _bot_running:
        return

    def run():
        global _bot_app, _bot_loop, _bot_running
        _bot_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(_bot_loop)
        cfg = get_cfg()
        _bot_app = Application.builder().token(cfg["token"]).build()
        _bot_app.add_handler(CommandHandler("start",  cmd_start))
        _bot_app.add_handler(CommandHandler("on",     cmd_on))
        _bot_app.add_handler(CommandHandler("off",    cmd_off))
        _bot_app.add_handler(CommandHandler("status", cmd_status))
        _bot_app.add_handler(CommandHandler("help",   cmd_help))
        _bot_running = True
        logger.info("Bot started — %s (@%s)", cfg["vps_name"], cfg["username"])
        _bot_app.run_polling(allowed_updates=Update.ALL_TYPES, close_loop=False)

    _bot_thread = threading.Thread(target=run, daemon=True)
    _bot_thread.start()

def stop_bot():
    global _bot_app, _bot_running
    if not _bot_running or _bot_app is None:
        return
    try:
        future = asyncio.run_coroutine_threadsafe(_bot_app.stop(), _bot_loop)
        future.result(timeout=5)
    except Exception as e:
        logger.warning("stop_bot: %s", e)
    _bot_running = False
    _bot_app     = None
    logger.info("Bot stopped")


# ============================================================
#  SYSTEM TRAY
# ============================================================
def make_icon() -> Image.Image:
    size = 64
    img  = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([2, 2, size-2, size-2], fill="#00b050", outline="#007030", width=3)
    draw.text((16, 20), "M5", fill="white")
    return img

def run_tray():
    def on_start(icon, item):
        if not _bot_running:
            start_bot()
            icon.notify("Bot đã khởi động.", "MT5 Controller - WillPine")

    def on_stop(icon, item):
        if _bot_running:
            stop_bot()
            icon.notify("Bot đã dừng.", "MT5 Controller - WillPine")

    def on_edit(icon, item):
        stop_bot()
        show_config_dialog(on_save=start_bot)

    def on_exit(icon, item):
        stop_bot()
        icon.stop()
        os._exit(0)

    icon = pystray.Icon(
        name="MT5Bot",
        icon=make_icon(),
        title="MT5 Controller - WillPine",
        menu=pystray.Menu(
            pystray.MenuItem("▶  Start Bot",    on_start),
            pystray.MenuItem("⏹  Stop Bot",     on_stop),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("⚙  Edit Config",  on_edit),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("✕  Exit",         on_exit),
        )
    )
    icon.run()


# ============================================================
#  ENTRY POINT
# ============================================================
if __name__ == "__main__":
    if not config_complete():
        # Lần đầu chạy: hiện form config trước
        show_config_dialog(on_save=start_bot)
    else:
        # Đã có config: start bot luôn
        start_bot()

    # Ẩn vào system tray
    run_tray()
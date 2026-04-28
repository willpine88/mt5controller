"""
MT5 Controller - WillPine
==========================================
- Lần đầu chạy: form nhập config
- Chạy xong: ẩn vào system tray
- Tray menu: Start/Stop Bot, Edit Config, Exit

Cài: python -m pip install python-telegram-bot pywin32 MetaTrader5 pystray Pillow pyinstaller
Build exe: pyinstaller --onefile --noconsole --uac-admin --icon=icon.ico --name=MT5Controller mt5control.py
"""

import os
import sys
import time
import subprocess
import webbrowser
import threading
import logging
import configparser
import asyncio
import json
import ssl
import urllib.request
import certifi
from datetime import datetime
from pathlib import Path

import ctypes
import ctypes.wintypes
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
#  VERSION & UPDATE
# ============================================================
VERSION      = "1.8.0"
GITHUB_REPO  = "willpine88/mt5controller"
RELEASES_URL = f"https://github.com/{GITHUB_REPO}/releases/latest"

def _version_tuple(v: str) -> tuple[int, ...]:
    """Convert '1.5.0' → (1, 5, 0) for comparison."""
    try:
        return tuple(int(x) for x in v.split("."))
    except ValueError:
        return (0,)

def check_for_update() -> tuple[str, str] | None:
    """Return (new_version, exe_download_url) or None if up-to-date."""
    try:
        url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
        req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
        ctx = ssl.create_default_context(cafile=certifi.where())
        with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
            data = json.loads(resp.read())
        latest = data.get("tag_name", "").lstrip("v")
        if not latest or _version_tuple(latest) <= _version_tuple(VERSION):
            return None
        for asset in data.get("assets", []):
            if asset["name"].lower().endswith(".exe"):
                return latest, asset["browser_download_url"]
        return latest, ""
    except Exception as e:
        logger.debug("Update check failed: %s", e)
    return None

_pending_update_path: Path | None = None

def download_update(download_url: str) -> bool:
    """Download new exe. Returns True if ready to apply on exit."""
    global _pending_update_path
    exe_path    = Path(sys.executable)
    update_path = exe_path.parent / "MT5Controller_update.exe"

    logger.info("Downloading update from %s", download_url)
    ctx = ssl.create_default_context(cafile=certifi.where())
    req = urllib.request.Request(download_url)
    with urllib.request.urlopen(req, context=ctx) as resp, open(update_path, "wb") as f:
        f.write(resp.read())
    logger.info("Downloaded to %s (%d bytes)", update_path, update_path.stat().st_size)
    _pending_update_path = update_path
    return True

def apply_pending_update():
    """If an update was downloaded, run batch to swap files after app exits."""
    if _pending_update_path is None or not _pending_update_path.exists():
        return
    exe_path   = Path(sys.executable)
    batch_path = exe_path.parent / "_update.bat"

    batch = f'''@echo off
ping 127.0.0.1 -n 3 >nul
del "{exe_path}"
move "{_pending_update_path}" "{exe_path}"
del "%~f0"
'''
    batch_path.write_text(batch, encoding="utf-8")
    subprocess.Popen(["cmd", "/c", str(batch_path)], creationflags=0x08000000)
    logger.info("Update batch launched, swapping files after exit")


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
#  WIN32 SENDINPUT STRUCTS (must match Windows SDK layout)
# ============================================================
INPUT_KEYBOARD     = 1
KEYEVENTF_KEYUP    = 0x0002
SCAN_CTRL          = 0x1D
SCAN_E             = 0x12

class MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx",          ctypes.c_long),
                ("dy",          ctypes.c_long),
                ("mouseData",   ctypes.wintypes.DWORD),
                ("dwFlags",     ctypes.wintypes.DWORD),
                ("time",        ctypes.wintypes.DWORD),
                ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]

class KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk",         ctypes.wintypes.WORD),
                ("wScan",       ctypes.wintypes.WORD),
                ("dwFlags",     ctypes.wintypes.DWORD),
                ("time",        ctypes.wintypes.DWORD),
                ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]

class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [("uMsg",    ctypes.wintypes.DWORD),
                ("wParamL", ctypes.wintypes.WORD),
                ("wParamH", ctypes.wintypes.WORD)]

class _INPUT_UNION(ctypes.Union):
    _fields_ = [("mi", MOUSEINPUT),
                ("ki", KEYBDINPUT),
                ("hi", HARDWAREINPUT)]

class INPUT(ctypes.Structure):
    _fields_ = [("type",   ctypes.wintypes.DWORD),
                ("_input", _INPUT_UNION)]


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
    if len(found) > 1:
        titles = [win32gui.GetWindowText(h) for h in found]
        logger.info("Multiple MT5 windows matched (%d): %s — using first", len(found), titles)
    return found[0] if found else None

def _get_window_exe_path(hwnd) -> str | None:
    """Return absolute exe path of process owning hwnd (None on failure)."""
    try:
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        h_proc = ctypes.windll.kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if not h_proc:
            return None
        try:
            buf_len = ctypes.wintypes.DWORD(1024)
            buf = ctypes.create_unicode_buffer(buf_len.value)
            if ctypes.windll.kernel32.QueryFullProcessImageNameW(h_proc, 0, buf, ctypes.byref(buf_len)):
                return buf.value
        finally:
            ctypes.windll.kernel32.CloseHandle(h_proc)
    except Exception as e:
        logger.warning("Failed to get exe path for hwnd=%s: %s", hwnd, e)
    return None

def get_algo_state(path: str | None = None) -> bool | None:
    """Read trade_allowed flag. Pass path to pin to specific terminal when multiple MT5 are open."""
    init_ok = mt5.initialize(path=path) if path else mt5.initialize()
    if not init_ok:
        return None
    info = mt5.terminal_info()
    mt5.shutdown()
    return info.trade_allowed if info else None

def _force_foreground(hwnd):
    """Bring window to foreground, bypassing Windows VPS restrictions."""
    # Skip if already foreground
    if win32gui.GetForegroundWindow() == hwnd:
        return

    user32 = ctypes.windll.user32
    SPI_SETFOREGROUNDLOCKTIMEOUT = 0x2001
    user32.SystemParametersInfoW(SPI_SETFOREGROUNDLOCKTIMEOUT, 0, 0, 0x0002)

    current_thread = win32api.GetCurrentThreadId()
    target_thread  = win32process.GetWindowThreadProcessId(hwnd)[0]
    attached = False
    if current_thread != target_thread:
        win32process.AttachThreadInput(current_thread, target_thread, True)
        attached = True
    try:
        if win32gui.IsIconic(hwnd):
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            time.sleep(0.3)
        win32gui.BringWindowToTop(hwnd)
        win32gui.SetForegroundWindow(hwnd)
    finally:
        if attached:
            win32process.AttachThreadInput(current_thread, target_thread, False)

def _send_input_ctrl_e() -> bool:
    """Simulate Ctrl+E via SendInput with correct struct layout."""
    def make_key(vk, scan, flags=0):
        inp = INPUT()
        inp.type = INPUT_KEYBOARD
        inp._input.ki.wVk    = vk
        inp._input.ki.wScan  = scan
        inp._input.ki.dwFlags = flags
        return inp

    inputs = (INPUT * 4)(
        make_key(win32con.VK_CONTROL, SCAN_CTRL, 0),
        make_key(ord("E"),            SCAN_E,    0),
        make_key(ord("E"),            SCAN_E,    KEYEVENTF_KEYUP),
        make_key(win32con.VK_CONTROL, SCAN_CTRL, KEYEVENTF_KEYUP),
    )
    size = ctypes.sizeof(INPUT)
    n_sent = ctypes.windll.user32.SendInput(4, ctypes.pointer(inputs[0]), size)
    logger.info("SendInput: %d/4 events sent (sizeof(INPUT)=%d)", n_sent, size)
    return n_sent == 4

MT5_WMCMD_EXPERTS = 32851  # Known constant for Algo Trading toggle across all MT5 builds
_algo_cmd_id: int | None = None

def _find_algo_command_id(hwnd) -> int | None:
    """Walk MT5 menu bar to find the Algo Trading command ID, fallback to known constant."""
    global _algo_cmd_id
    if _algo_cmd_id is not None:
        return _algo_cmd_id
    try:
        menu_bar = win32gui.GetMenu(hwnd)
        if not menu_bar:
            logger.warning("WM_COMMAND: no menu bar found, using hardcoded constant %d", MT5_WMCMD_EXPERTS)
            return MT5_WMCMD_EXPERTS
        for i in range(win32gui.GetMenuItemCount(menu_bar)):
            submenu = win32gui.GetSubMenu(menu_bar, i)
            if not submenu:
                continue
            for j in range(win32gui.GetMenuItemCount(submenu)):
                try:
                    text = win32gui.GetMenuString(submenu, j, win32con.MF_BYPOSITION)
                except Exception:
                    continue
                if "Algo" in text or "algo" in text:
                    cmd_id = win32gui.GetMenuItemID(submenu, j)
                    if cmd_id > 0:
                        _algo_cmd_id = cmd_id
                        logger.info("WM_COMMAND: found Algo Trading menu item, cmd_id=%d", cmd_id)
                        return cmd_id
        logger.warning("WM_COMMAND: menu scan failed, using hardcoded constant %d", MT5_WMCMD_EXPERTS)
    except Exception as e:
        logger.warning("WM_COMMAND: menu scan error: %s, using hardcoded constant %d", e, MT5_WMCMD_EXPERTS)
    _algo_cmd_id = MT5_WMCMD_EXPERTS
    return MT5_WMCMD_EXPERTS

def _send_wm_command_toggle(hwnd) -> bool:
    """Toggle Algo Trading via WM_COMMAND (no foreground needed)."""
    cmd_id = _find_algo_command_id(hwnd)
    if cmd_id is None:
        return False
    win32api.PostMessage(hwnd, win32con.WM_COMMAND, cmd_id, 0)
    logger.info("WM_COMMAND sent with cmd_id=%d", cmd_id)
    return True

def toggle_algo_trading() -> tuple[bool, str]:
    """Try to toggle Algo Trading: WM_COMMAND first (no foreground needed), SendInput fallback."""
    hwnd = find_mt5_window()
    if not hwnd:
        return False, "❌ MT5 không tìm thấy — có thể chưa mở hoặc bị crash."
    try:
        # Method 1: WM_COMMAND — works without foreground, reliable on VPS
        if _send_wm_command_toggle(hwnd):
            return True, "OK"

        # Method 2: Foreground + SendInput (fallback, requires interactive session)
        logger.warning("WM_COMMAND failed, trying SendInput fallback")
        try:
            _force_foreground(hwnd)
        except Exception as e:
            logger.warning("SetForegroundWindow failed: %s", e)
        time.sleep(0.5)

        fg = win32gui.GetForegroundWindow()
        logger.info("Foreground hwnd=%s, MT5 hwnd=%s, match=%s", fg, hwnd, fg == hwnd)

        if _send_input_ctrl_e():
            return True, "OK"

        return False, "❌ Không thể toggle Algo — kiểm tra quyền admin."
    except Exception as e:
        logger.error("toggle_algo_trading: %s", e)
        return False, f"❌ Lỗi: {e}"

MAX_TOGGLE_RETRIES = 3

def set_algo(target: bool) -> tuple[bool, str, bool | None]:
    hwnd = find_mt5_window()
    if not hwnd:
        return False, "❌ MT5 không tìm thấy — có thể chưa mở hoặc bị crash.", None
    exe_path = _get_window_exe_path(hwnd)
    logger.info("set_algo: pinned to hwnd=%s exe=%s", hwnd, exe_path)
    current = get_algo_state(exe_path)
    if current is None:
        return False, "❌ MT5 không phản hồi.", None
    if current == target:
        return True, "already", current
    new_state = current
    for attempt in range(1, MAX_TOGGLE_RETRIES + 1):
        ok, err = toggle_algo_trading()
        if not ok:
            return False, err, current
        time.sleep(1.5)
        new_state = get_algo_state(exe_path)
        if new_state is None:
            return False, "❌ Không đọc được state sau toggle.", None
        if new_state == target:
            return True, "ok", new_state
        logger.warning("Toggle attempt %d/%d failed, state unchanged", attempt, MAX_TOGGLE_RETRIES)
        time.sleep(0.5)
    return False, "⚠️ Toggle không thành công sau nhiều lần thử — kiểm tra MT5.", new_state


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
    mt5_win  = find_mt5_window()
    state    = get_algo_state(_get_window_exe_path(mt5_win)) if mt5_win else None
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

def _do_update_check(icon, silent=True):
    """Background update check — notify via tray if new version found."""
    result = check_for_update()
    if result is None:
        logger.info("Update check: running latest v%s", VERSION)
        if not silent:
            icon.notify(f"Đang dùng bản mới nhất v{VERSION}.", "MT5 Controller")
        return
    new_ver, dl_url = result
    logger.info("Update available: v%s → v%s", VERSION, new_ver)
    icon._update_ver = new_ver
    icon._update_url = dl_url
    icon.notify(f"Có phiên bản mới v{new_ver}! Click 'Update' để tải.", "MT5 Controller")

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

    def on_update(icon, item):
        dl_url = getattr(icon, "_update_url", "")
        new_ver = getattr(icon, "_update_ver", "")
        if dl_url:
            icon.notify(f"Đang tải v{new_ver}...", "MT5 Controller")
            try:
                download_update(dl_url)
                icon.notify(f"Đã tải v{new_ver}. Chọn Exit để cập nhật.", "MT5 Controller")
            except Exception as e:
                logger.error("Update failed: %s", e)
                icon.notify(f"Cập nhật thất bại: {e}", "MT5 Controller")
        else:
            threading.Thread(target=_do_update_check, args=(icon,), daemon=True).start()

    def on_exit(icon, item):
        stop_bot()
        apply_pending_update()
        icon.stop()
        os._exit(0)

    icon = pystray.Icon(
        name="MT5Bot",
        icon=make_icon(),
        title=f"MT5 Controller v{VERSION}",
        menu=pystray.Menu(
            pystray.MenuItem("▶  Start Bot",    on_start),
            pystray.MenuItem("⏹  Stop Bot",     on_stop),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("⚙  Edit Config",  on_edit),
            pystray.MenuItem("⬆  Check Update", on_update),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("✕  Exit",         on_exit),
        )
    )

    # Auto-check on startup (background)
    threading.Thread(target=_do_update_check, args=(icon,), daemon=True).start()

    icon.run()


# ============================================================
#  KEEP-ALIVE: prevent Windows from sleeping/killing the process on VPS
# ============================================================
def _prevent_idle_shutdown():
    """Call SetThreadExecutionState to prevent Windows idle sleep/display-off."""
    ES_CONTINUOUS      = 0x80000000
    ES_SYSTEM_REQUIRED = 0x00000001
    ES_DISPLAY_REQUIRED = 0x00000002
    ctypes.windll.kernel32.SetThreadExecutionState(
        ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED
    )
    logger.info("SetThreadExecutionState: idle sleep prevention enabled")


# ============================================================
#  ENTRY POINT
# ============================================================
if __name__ == "__main__":
    _prevent_idle_shutdown()

    if not config_complete():
        # Lần đầu chạy: hiện form config trước
        show_config_dialog(on_save=start_bot)
    else:
        # Đã có config: start bot luôn
        start_bot()

    # Ẩn vào system tray
    run_tray()
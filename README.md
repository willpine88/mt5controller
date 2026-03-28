# MT5 Controller - WillPine

Phần mềm điều khiển nút **Algo Trading** trên MetaTrader 5 từ xa qua Telegram.  
Hỗ trợ nhiều VPS, mỗi VPS chạy 1 bot riêng, tất cả cùng trong 1 group Telegram.

---

## Yêu cầu

- Windows Server (hoặc Windows bất kỳ)
- MetaTrader 5 đã cài và đang chạy
- Python 3.11+ (nếu chạy file `.py`)
- Tài khoản Telegram

---

## Cài đặt

### Bước 1 — Cài Python

```powershell
Invoke-WebRequest -Uri "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe" -OutFile "C:\python_setup.exe"
Start-Process -Wait -FilePath "C:\python_setup.exe" -ArgumentList "/quiet InstallAllUsers=1 PrependPath=1"
Remove-Item "C:\python_setup.exe"
```

> Đóng PowerShell và mở lại sau khi cài xong.

### Bước 2 — Cài thư viện

```powershell
python -m pip install python-telegram-bot
python -m pip install pywin32
python -m pip install MetaTrader5
python -m pip install pystray
python -m pip install Pillow
python -m pip install pyinstaller
```

### Bước 3 — Tạo thư mục và copy file

```powershell
New-Item -ItemType Directory -Force -Path "C:\mt5control"
```

Copy `tg.py` và `mt5control.ico` vào `C:\mt5control\`

---

## Cấu hình lần đầu

Chạy `tg.py` (hoặc `tg.exe`), form cấu hình sẽ tự hiện ra:

| Trường | Mô tả |
|---|---|
| Bot Token | Token lấy từ @BotFather trên Telegram |
| Bot Username | Username của bot, không có dấu @ |
| Tên VPS | Tên hiển thị trong tin nhắn, vd: VPS-1, VPS-HN |
| Allowed User IDs | User ID Telegram được phép dùng lệnh (phân cách bằng dấu phẩy) |
| Từ khóa MT5 | Một phần title cửa sổ MT5 đang mở, vd: Vantage, Exness |

Sau khi lưu, bot tự khởi động và ẩn vào **system tray**.

> Để lấy User ID: nhắn bất kỳ cho **@userinfobot** trên Telegram.  
> Để lấy title cửa sổ MT5: xem hướng dẫn bên dưới.

---

## Tìm từ khóa title cửa sổ MT5

Chạy lệnh sau trong PowerShell **khi MT5 đang mở**:

```powershell
Add-Type @"
using System;
using System.Runtime.InteropServices;
using System.Text;
public class WinAPI2 {
    [DllImport("user32.dll")] public static extern bool EnumWindows(EnumWindowsProc e, IntPtr p);
    [DllImport("user32.dll")] public static extern int GetWindowText(IntPtr h, StringBuilder s, int m);
    [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr h);
    public delegate bool EnumWindowsProc(IntPtr h, IntPtr p);
}
"@
[WinAPI2]::EnumWindows({
    param($hwnd, $p)
    $sb = New-Object System.Text.StringBuilder 512
    [WinAPI2]::GetWindowText($hwnd, $sb, 512) | Out-Null
    $title = $sb.ToString()
    if ($title.Length -gt 3) { Write-Host $title }
    return $true
}, [IntPtr]::Zero)
```

Tìm dòng chứa tên broker (Vantage, Exness, ICMarkets...) → dùng tên broker đó làm từ khóa.

---

## Tạo Telegram Bot

1. Mở Telegram, tìm **@BotFather**
2. Gửi `/newbot` → đặt tên → lấy **Token**
3. Gửi `/setprivacy` → chọn bot → chọn **Disable** *(bắt buộc để bot đọc được tin nhắn trong group)*
4. Gửi `/setcommands` → chọn bot → paste danh sách lệnh:

```
on - Bật Algo Trading
off - Tắt Algo Trading
status - Xem trạng thái
help - Hướng dẫn
```

---

## Dùng trong Telegram

### Private chat
Nhắn trực tiếp với bot, gõ lệnh bình thường:
```
/on
/off
/status
```

### Group (nhiều bot)
Khi có nhiều bot trong cùng 1 group, phải **mention tên bot** để chỉ định đúng VPS:
```
/on@phivu_vps1_bot
/off@phivu_vps2_bot
/status@phivu_vps3_bot
```

---

## Lệnh Telegram

| Lệnh | Chức năng |
|---|---|
| `/on` | Bật Algo Trading trên VPS này |
| `/off` | Tắt Algo Trading trên VPS này |
| `/status` | Xem trạng thái MT5 và Algo Trading |
| `/help` | Hướng dẫn sử dụng |

---

## System Tray

Sau khi khởi động, app ẩn vào system tray (góc phải taskbar).  
Click chuột phải vào icon để mở menu:

| Menu | Chức năng |
|---|---|
| ▶ Start Bot | Khởi động bot |
| ⏹ Stop Bot | Dừng bot |
| ⚙ Edit Config | Mở form sửa cấu hình, bot tự restart |
| ✕ Exit | Thoát hoàn toàn |

---

## Chạy tự động khi Windows khởi động

```powershell
$a = New-ScheduledTaskAction -Execute "python" -Argument "C:\mt5control\tg.py" -WorkingDirectory "C:\mt5control"
$t = New-ScheduledTaskTrigger -AtLogOn
$s = New-ScheduledTaskSettingsSet -RestartCount 5 -RestartInterval (New-TimeSpan -Minutes 2) -ExecutionTimeLimit (New-TimeSpan -Hours 0)
$p = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
Register-ScheduledTask -TaskName "MT5TelegramBot" -Action $a -Trigger $t -Settings $s -Principal $p -Force
Start-ScheduledTask -TaskName "MT5TelegramBot"
```

> Nếu dùng file `.exe`, thay `"python"` và `"C:\mt5control\tg.py"` bằng `"C:\mt5control\tg.exe"` và bỏ `-Argument`.

---

## Build file EXE

```powershell
cd C:\mt5control
pyinstaller --onefile --noconsole --icon=mt5control.ico tg.py
```

File exe xuất hiện tại `C:\mt5control\dist\tg.exe`.  
Copy `tg.exe` lên VPS mới — không cần cài Python hay thư viện, chỉ cần MT5 Terminal đang chạy.

---

## Quản lý hàng ngày

```powershell
# Restart bot sau khi sửa file
Stop-ScheduledTask  -TaskName "MT5TelegramBot"
Start-ScheduledTask -TaskName "MT5TelegramBot"

# Xem log
Get-Content C:\mt5control\bot.log -Tail 50

# Xem log realtime
Get-Content C:\mt5control\bot.log -Wait -Tail 20
```

---

## Mô hình nhiều VPS

```
Telegram Group
├── @vps1_bot  →  VPS-1 (MT5 account 1)
├── @vps2_bot  →  VPS-2 (MT5 account 2)
└── @vps3_bot  →  VPS-3 (MT5 account 3)
```

Mỗi VPS: copy `tg.py` → tạo bot mới trên BotFather → điền config riêng → chạy độc lập.

---

## Lưu ý

- `/off` chỉ tắt Algo Trading, **không đóng lệnh đang mở**
- Bot đọc trạng thái trực tiếp từ MT5 API — bật/tắt tay trên MT5 vẫn nhận diện đúng
- Nếu MT5 crash hoặc restart, bot tự nhận diện lại khi có lệnh tiếp theo
- File `config.ini` lưu cạnh `tg.py` (hoặc `tg.exe`) — không xóa file này

---

*MT5 Controller - WillPine*

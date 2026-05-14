"""
Teams Translator - Install Script cho Windows
Chạy file này với tư cách Administrator nếu có thể
"""

import os
import sys
import subprocess
import platform


def check_python():
    """Kiểm tra Python version."""
    v = sys.version_info
    if v.major < 3 or (v.major == 3 and v.minor < 8):
        print(f"❌ Python {v.major}.{v.minor} quá cũ. Cần Python 3.8+")
        print("Download: https://www.python.org/downloads/")
        return False
    print(f"✅ Python {v.major}.{v.minor}.{v.micro}")
    return True


def install_requirements():
    """Cài pip packages."""
    print("\n📦 Đang cài Python packages...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Packages đã cài xong")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Lỗi cài packages: {e}")
        return False


def install_pyaudio():
    """Cài PyAudio riêng vì thường gặp vấn đề trên Windows."""
    print("\n🎤 Đang cài PyAudio...")
    try:
        import pyaudio
        print("✅ PyAudio đã có")
        return True
    except ImportError:
        pass

    # Method 1: pip install
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyaudio"])
        print("✅ PyAudio cài qua pip thành công")
        return True
    except subprocess.CalledProcessError:
        pass

    # Method 2: pipwin
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pipwin"])
        subprocess.check_call([sys.executable, "-m", "pipwin", "install", "pyaudio"])
        print("✅ PyAudio cài qua pipwin thành công")
        return True
    except subprocess.CalledProcessError:
        pass

    print("⚠️ Không tự động cài được PyAudio.")
    print("Tải thủ công từ: https://visualstudio.microsoft.com/visual-cpp-build-tools/")
    print("Hoặc cài wheel từ: https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio")
    return False


def check_loopback():
    """Kiểm tra loopback device."""
    print("\n🔊 Kiểm tra loopback audio...")
    try:
        import pyaudio
        p = pyaudio.PyAudio()
        found = []
        for i in range(p.get_device_count()):
            info = p.get_device_info_by_index(i)
            name = info["name"].lower()
            if any(kw in name for kw in ["stereo mix", "cble", "loopback", "virtual cable"]):
                found.append(info["name"])
        p.terminate()

        if found:
            print(f"✅ Đã tìm thấy loopback device: {found[0]}")
            print("  App sẽ bắt âm thanh trực tiếp từ Windows!")
            return True
        else:
            print("❌ Chưa có loopback device.")
            print()
            print("CÁCH 1 (dễ nhất): Cài VB-CABLE Virtual Audio Cable (miễn phí)")
            print("  1. Vào https://vb-audio.com/Cable/")
            print("  2. Download VBCABLE_Setup.exe")
            print("  3. Chạy với quyền Administrator")
            print("  4. Restart máy")
            print()
            print("CÁCH 2: Bật Stereo Mix")
            print("  1. Chuột phải icon loa → Sound settings")
            print("  2. Sound Control Panel → Recording tab")
            print("  3. Chuột phải → Show Disabled Devices")
            print("  4. Chuột phải Stereo Mix → Enable")
            print()
            return False
    except Exception as e:
        print(f"  Không kiểm tra được: {e}")
        return False


def create_shortcut():
    """Tạo shortcut trên Desktop."""
    print("\n📌 Tạo shortcut Desktop...")
    script_dir = os.path.dirname(os.path.abspath(__file__))
    shortcut = os.path.expanduser("~/Desktop/Teams Translator.lnk")

    try:
        import winshell
        from win32com.client import Dispatch
        desktop = winshell.desktop()
        path = os.path.join(desktop, "Teams Translator.lnk")
        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(path)
        shortcut.Targetpath = sys.executable  # python.exe
        shortcut.Arguments = f'"{os.path.join(script_dir, "run.py")}"'
        shortcut.WorkingDirectory = script_dir
        shortcut.Description = "Teams Translator - Dịch Anh-Việt real-time"
        shortcut.save()
        print("✅ Shortcut đã tạo trên Desktop")
    except Exception:
        # Fallback: hướng dẫn thủ công
        print("  Tạo shortcut thủ công:")
        print(f"  1. Chuột phải Desktop → New → Shortcut")
        print(f'  2. Location: {sys.executable} "{os.path.join(script_dir, "run.py")}"')
        print(f"  3. Đặt tên: Teams Translator")


def main():
    print("=" * 55)
    print("  Teams Translator - Cài đặt")
    print("  Dịch real-time Anh → Việt trong Teams meeting")
    print("=" * 55)
    print()

    if not check_python():
        input("\nNhấn Enter để thoát...")
        return

    if not install_requirements():
        print("\n⚠️ Có lỗi khi cài packages. Thử chạy lại với Administrator.")
        input("\nNhấn Enter để thoát...")
        return

    install_pyaudio()

    print()
    print("🔍 Đang kiểm tra hệ thống...")
    has_loopback = check_loopback()

    # create_shortcut()

    print()
    print("=" * 55)
    print("  ✅ Cài đặt hoàn tất!")
    print("=" * 55)
    print()
    print("🚀 Cách chạy:")
    print(f'  python "{os.path.join(os.path.dirname(os.path.abspath(__file__)), "run.py")}"')
    print()
    print("⚡ Hotkeys:")
    print("  Ctrl+Shift+T : Bắt đầu / Dừng")
    print("  Ctrl+Shift+C : Bật/Tắt caption overlay")
    print()
    print("📝 Các bước sử dụng:")
    print("  1. Chạy app")
    print("  2. Vào system tray (gần đồng hồ) → click icon T")
    print("  3. Chọn '▶️ Bắt đầu' hoặc nhấn Ctrl+Shift+T")
    if not has_loopback:
        print("  4. ⚠️ Hiện tại app dùng chế độ MIC (microphone)")
        print("     Cài VB-CABLE để dùng loopback (bắt trực tiếp, chất lượng cao)")
    print()

    input("Nhấn Enter để kết thúc...")


if __name__ == "__main__":
    main()

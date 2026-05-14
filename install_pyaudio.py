"""
PyAudio Installer Helper cho Windows
Chạy: python install_pyaudio.py
"""
import subprocess
import sys
import platform


def install_pyaudio():
    """Cài đặt PyAudio trên Windows."""
    if platform.system() != "Windows":
        print("Chỉ hỗ trợ Windows. Hãy thử: pip install pyaudio")
        return

    print("Đang kiểm tra PyAudio...")
    try:
        import pyaudio
        print("✅ PyAudio đã được cài đặt!")
        return
    except ImportError:
        print("❌ PyAudio chưa được cài đặt.")

    print("\nĐang cài PyAudio cho Windows...")
    print("Phương pháp 1: pip install pyaudio")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyaudio"])
        print("✅ Cài đặt thành công!")
        return
    except subprocess.CalledProcessError:
        print("❌ Phương pháp 1 thất bại.")

    print("\nPhương pháp 2: Dùng pipwin")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pipwin"])
        subprocess.check_call([sys.executable, "-m", "pipwin", "install", "pyaudio"])
        print("✅ Cài đặt thành công qua pipwin!")
        return
    except subprocess.CalledProcessError:
        print("❌ Phương pháp 2 thất bại.")

    print("\nPhương pháp 3: Cài từ wheel trực tiếp")
    print("Download PyAudio wheel từ: https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio")
    print("Chọn đúng phiên bản (cp39, cp310, cp311, cp312) và architecture (win32/amd64)")
    print("Sau đó chạy: pip install <downloaded_file>.whl")


if __name__ == "__main__":
    install_pyaudio()

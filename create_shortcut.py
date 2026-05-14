import os, sys

desktop = os.path.join(os.path.expanduser("~"), "Desktop")
shortcut_path = os.path.join(desktop, "Teams Translator.lnk")

bat_path = r"D:\teams-translator\start.bat"
icon_path = r"D:\teams-translator\resources\icon.png"

try:
    import win32com.client
    ws = win32com.client.Dispatch("WScript.Shell")
    sc = ws.CreateShortcut(shortcut_path)
    sc.TargetPath = bat_path
    sc.WorkingDirectory = r"D:\teams-translator"
    sc.Description = "Teams Translator - D\u1ecbch real-time Anh-Vi\u1ec7t"
    if os.path.exists(icon_path):
        sc.IconLocation = icon_path
    sc.Save()
    print(f"Shortcut created: {shortcut_path}")
except ImportError:
    # Fallback: t?o .bat link
    with open(shortcut_path.replace(".lnk", ".bat"), "w") as f:
        f.write(f'@start "" "{bat_path}"')
    print(f"Created batch launcher on Desktop instead (win32com not available)")

"""Kill all Python processes related to teams-translator except Hermes"""
import subprocess
import os

# Lấy PID hiện tại (Hermes)
hermes_pid = os.getpid()

# Dùng wmic để kill
cmds = [
    'wmic process where "name=\'python.exe\' and CommandLine like \'%teams%\'" delete',
    'wmic process where "name=\'python.exe\' and CommandLine like \'%translator%\'" delete',
    'wmic process where "name=\'python.exe\' and CommandLine like \'%run.py%\'" delete',
    'wmic process where "name=\'python.exe\' and CommandLine like \'%whisper_subprocess%\'" delete',
]

for cmd in cmds:
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        print(f"  {cmd[:50]}... -> {result.returncode}")
    except Exception as e:
        print(f"  Error: {e}")

print("Done killing teams-translator processes")

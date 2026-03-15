
import subprocess

def run(cmd):
    return subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL).strip()

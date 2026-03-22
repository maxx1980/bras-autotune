import os
import importlib
import shutil

def ok(msg):
    print(f"[ OK ] {msg}")

def fail(msg):
    print(f"[FAIL] {msg}")

def run_doctor():
    print("\nBRAS-AUTOTUNE DIAGNOSTICS\n==========================\n")

    # Проверка файлов
    required_files = [
        "bras_autotune/cli.py",
        "bras_autotune/dialog.py",
        "bras_autotune/generator.py",
        "bras_autotune/utils.py",
        "bras_autotune/cpu.py",
        "bras_autotune/nic.py",
        "bras_autotune/doctor.py",
    ]

    for f in required_files:
        if os.path.exists(f):
            ok(f"File exists: {f}")
        else:
            fail(f"Missing file: {f}")

    # Проверка функций
    checks = [
        ("bras_autotune.generator", "generate_config"),
        ("bras_autotune.utils", "collect_system_info"),
        ("bras_autotune.dialog", "bras_autotune_installer"),
    ]

    for module, func in checks:
        try:
            m = importlib.import_module(module)
            if hasattr(m, func):
                ok(f"{module}: {func}() found")
            else:
                fail(f"{module}: {func}() missing")
        except Exception as e:
            fail(f"Cannot import {module}: {e}")

    # Проверка зависимостей
    deps = ["dialog", "ethtool", "lscpu", "taskset"]
    for dep in deps:
        if shutil.which(dep):
            ok(f"Dependency found: {dep}")
        else:
            fail(f"Dependency missing: {dep}")

    print("\nDiagnostics complete.\n")

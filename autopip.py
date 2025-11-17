#!/usr/bin/env python3
# coding: utf-8

# ------------------------------------------------------------
# autopip: Creator By FrameworkPython
# ------------------------------------------------------------

import ast
import importlib.util
import os
import re
import subprocess
import sys
import time
from typing import Dict, Optional, Set, List

from banner import clear_screen, fancy_banner

# ------------------------------------------------------------
# لیست نگاشت ماژول → اسم پکیج تو PyPI
# ------------------------------------------------------------
MODULE_MAP: Dict[str, str] = {
    "bs4": "beautifulsoup4",
    "cv2": "opencv-python",
    "PIL": "pillow",
    "yaml": "PyYAML",
    "sklearn": "scikit-learn",
    "Crypto": "pycryptodome",
}

LOG_PATH = os.path.join(os.getcwd(), "autopip.log")
REQ_FILENAME = "requirements.txt"

# ------------------------------------------------------------
# httpx برای probe روی PyPI (اگه نصب باشه)
# ------------------------------------------------------------
try:
    import httpx  # type: ignore
except Exception:
    httpx = None

# ------------------------------------------------------------
# رنگای ANSI برای خروجی رنگی
# ------------------------------------------------------------
class Ansi:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    GREY = "\033[90m"

# ------------------------------------------------------------
# فانکشن‌های کمکی برای خوندن سورس و گرفتن importها
# ------------------------------------------------------------
def read_file(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""

def get_imports_from_source(source: str) -> Set[str]:
    mods: Set[str] = set()
    try:
        tree = ast.parse(source)
    except Exception:
        for line in source.splitlines():
            m = re.match(r"^\s*import\s+([\w\.]+)", line)
            if m:
                mods.add(m.group(1).split(".")[0])
            m2 = re.match(r"^\s*from\s+([\w\.]+)\s+import", line)
            if m2:
                mods.add(m2.group(1).split(".")[0])
        return mods
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                mods.add(n.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                mods.add(node.module.split(".")[0])
    return mods

def get_imports_from_file(path: str) -> Set[str]:
    if not path:
        return set()
    src = read_file(path)
    return get_imports_from_source(src)

# ------------------------------------------------------------
# چک می‌کنیم ماژول نصب شده یا نه
# ------------------------------------------------------------
def is_installed(module: str) -> bool:
    try:
        return importlib.util.find_spec(module) is not None
    except Exception:
        return False

# ------------------------------------------------------------
# اسم پکیج رو resolve می‌کنیم
# ------------------------------------------------------------
def resolve_package_name(module: str) -> Optional[str]:
    if module in MODULE_MAP:
        return MODULE_MAP[module]
    if httpx is not None:
        try:
            resp = httpx.get(f"https://pypi.org/pypi/{module}/json", timeout=4.0)
            if resp.status_code == 200:
                return module
        except Exception:
            pass
    return module

# ------------------------------------------------------------
# نصب pip به صورت silent
# ------------------------------------------------------------
def pip_install_quiet(package_spec: str) -> bool:
    try:
        with open(os.devnull, "wb") as devnull:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", package_spec],
                stdout=devnull,
                stderr=devnull,
            )
        return True
    except Exception:
        return False

# ------------------------------------------------------------
# نصب از requirements.txt
# ------------------------------------------------------------
def parse_requirements(path: str) -> List[str]:
    pkgs: List[str] = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            for raw in f:
                line = raw.strip()
                if not line or line.startswith("#"):
                    continue
                pkgs.append(line)
    except Exception:
        pass
    return pkgs

def install_requirements(path: str) -> List[str]:
    failed: List[str] = []
    pkgs = parse_requirements(path)
    if not pkgs:
        return failed
    script_name = os.path.basename(path)
    clear_screen()
    fancy_banner(script_name)
    print_title(f"Installing from {REQ_FILENAME}")
    for spec in pkgs:
        print_installing_start(spec)
        ok = pip_install_quiet(spec)
        save_log(f"{'INSTALLED' if ok else 'FAILED'} req -> {spec}")
        print_install_result(spec, ok)
        if not ok:
            failed.append(spec)
    if not failed:
        print()
        print_installing_done()
        staged_sleep(0.6)
        clear_screen()
    return failed

# ------------------------------------------------------------
# لاگ ساده
# ------------------------------------------------------------
def save_log(line: str) -> None:
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            ts = time.strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"{ts} {line}\n")
    except Exception:
        pass

# ------------------------------------------------------------
# چاپ مرحله‌ای با تاخیرای ریز
# ------------------------------------------------------------
def staged_sleep(sec: float = 0.5) -> None:
    try:
        time.sleep(sec)
    except Exception:
        pass

def print_title(text: str) -> None:
    print(f"{Ansi.BOLD}{Ansi.CYAN}{text}{Ansi.RESET}")

def print_identified(mods: Set[str]) -> None:
    print_title("The following libraries were identified:")
    for m in sorted(mods):
        print(f"{Ansi.YELLOW}- {m}{Ansi.RESET}")
    staged_sleep(0.6)

def print_finding_missing() -> None:
    print(f"{Ansi.GREY}Finding libraries that are not installed . . .{Ansi.RESET}")
    staged_sleep(0.6)

def print_missing(found: Set[str]) -> None:
    print_title("These libraries are not installed:")
    for m in sorted(found):
        print(f"{Ansi.RED}- {m}{Ansi.RESET}")
    staged_sleep(0.9)

def print_installing_start(pkg: str) -> None:
    print(f"{Ansi.BLUE}Installing library {Ansi.BOLD}{pkg}{Ansi.RESET}{Ansi.BLUE} ...{Ansi.RESET}")
    staged_sleep(0.45)

def print_install_result(pkg: str, ok: bool) -> None:
    if ok:
        print(f"{Ansi.GREEN}✔ {pkg} installed{Ansi.RESET}")
    else:
        print(f"{Ansi.RED}✖ {pkg} failed to install{Ansi.RESET}")
    staged_sleep(0.35)

def print_installing_done() -> None:
    print(f"{Ansi.MAGENTA}All libraries have been installed{Ansi.RESET}")
    staged_sleep(0.35)

# ------------------------------------------------------------
# جریان اصلی: اسکن فایل و نصب
# ------------------------------------------------------------
def run_for_file(target_path: Optional[str]) -> None:
    current_dir = os.getcwd()
    req_path = os.path.join(current_dir, REQ_FILENAME)

    if os.path.isfile(req_path):
        failed_reqs = install_requirements(req_path)
        if failed_reqs:
            save_log(f"FAILED_REQUIREMENTS {failed_reqs}")
            raise ModuleNotFoundError(f"Failed to install requirements: {failed_reqs[0]}")
        return

    if not target_path:
        return
    imports = get_imports_from_file(target_path)
    if not imports:
        return
    imports = {m for m in imports if m and m.lower() != "autopip"}
    if not imports:
        return
    missing = set()
    for mod in sorted(imports):
        if not is_installed(mod):
            missing.add(mod)
    if not missing:
        return

    script_name = os.path.basename(target_path)
    clear_screen()
    fancy_banner(script_name)

    print_identified(imports)
    print_finding_missing()
    print_missing(missing)

    failed: List[str] = []
    for mod in sorted(missing):
        pkg = resolve_package_name(mod) or mod
        print_installing_start(pkg)
        ok = pip_install_quiet(pkg)
        save_log(f"{'INSTALLED' if ok else 'FAILED'} {mod} -> {pkg}")
        print_install_result(pkg, ok)
        if not ok:
            failed.append(mod)

    if failed:
        print()
        print(f"{Ansi.RED}{Ansi.BOLD}Some packages failed to install:{Ansi.RESET}")
        for fmod in failed:
            print(f"  {Ansi.RED}- {fmod}{Ansi.RESET}")
        staged_sleep(0.6)

# ------------------------------------------------------------
# هوک ایمپورت
# ------------------------------------------------------------
def auto_on_import() -> None:
    main_mod = sys.modules.get("__main__")
    target_path = getattr(main_mod, "__file__", None)
    try:
        run_for_file(target_path)
    except ModuleNotFoundError:
        save_log("ModuleNotFoundError in auto_on_import")
        raise

auto_on_import()

# ------------------------------------------------------------
# CLI
# ------------------------------------------------------------
def main_cli() -> None:
    import argparse
    parser = argparse.ArgumentParser(
        description="autopip — automatic non-interactive dependency installer"
    )
    parser.add_argument(
        "file",
        nargs="?",
        help="target Python file to scan (defaults to the running script)"
    )
    args = parser.parse_args()
    run_for_file(args.file)

if __name__ == "__main__":
    main_cli()

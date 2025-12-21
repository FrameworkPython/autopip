#!/usr/bin/env python3
# coding: utf-8

# ------------------------------------------------------------
# autopip: Creator By FrameworkPython
# ------------------------------------------------------------

import ast
import importlib.util
import os
import subprocess
import sys
import time
import concurrent.futures
import urllib.request
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
        # خوندن به صورت باینری و دیکود کردن برای سرعت و امنیت بیشتر در مواجهه با انکودینگ‌ها
        with open(path, "rb") as f:
            return f.read().decode("utf-8", errors="ignore")
    except Exception:
        return ""

def get_imports_from_source(source: str) -> Set[str]:
    if not source: return set()
    try:
        tree = ast.parse(source)
        mods = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for n in node.names:
                    mods.add(n.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom) and node.module:
                mods.add(node.module.split(".")[0])
        return mods
    except Exception:
        return set()

def get_imports_from_file(path: str) -> Set[str]:
    if not path or not os.path.isfile(path):
        return set()
    return get_imports_from_source(read_file(path))

# ------------------------------------------------------------
# چک می‌کنیم ماژول نصب شده یا نه (با استفاده از استاندارد پایتون)
# ------------------------------------------------------------
def is_installed(module: str) -> bool:
    return importlib.util.find_spec(module) is not None

# ------------------------------------------------------------
# اسم پکیج رو resolve می‌کنیم
# ------------------------------------------------------------
def resolve_package_name(module: str) -> str:
    if module in MODULE_MAP:
        return MODULE_MAP[module]
    
    # تلاش برای چک کردن وجود پکیج در PyPI به صورت سریع
    if httpx:
        try:
            with httpx.Client(timeout=2.0) as client:
                resp = client.get(f"https://pypi.org/pypi/{module}/json")
                if resp.status_code == 200: return module
        except: pass
    else:
        try:
            with urllib.request.urlopen(f"https://pypi.org/pypi/{module}/json", timeout=2.0) as r:
                if r.getcode() == 200: return module
        except: pass
    return module

# ------------------------------------------------------------
# نصب pip به صورت Batch و Silent (بهینه‌ترین حالت سیستم‌عاملی)
# ------------------------------------------------------------
def pip_install_quiet(package_specs: List[str]) -> bool:
    if not package_specs: return True
    try:
        # نصب همه پکیج‌ها در یک فراخوانی ساب‌پروسس
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", *package_specs],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except Exception:
        return False

# ------------------------------------------------------------
# نصب از requirements.txt
# ------------------------------------------------------------
def parse_requirements(path: str) -> List[str]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return [l.strip() for l in f if l.strip() and not l.startswith("#")]
    except Exception:
        return []

def install_requirements(path: str) -> List[str]:
    pkgs = parse_requirements(path)
    if not pkgs: return []
    
    script_name = os.path.basename(path)
    clear_screen()
    fancy_banner(script_name)
    print_title(f"Installing from {REQ_FILENAME}")
    
    for spec in pkgs:
        print_installing_start(spec)
    
    ok = pip_install_quiet(pkgs)
    for spec in pkgs:
        save_log(f"{'INSTALLED' if ok else 'FAILED'} req -> {spec}")
        print_install_result(spec, ok)
    
    if ok:
        print()
        print_installing_done()
        staged_sleep(0.6)
        clear_screen()
        return []
    return pkgs

# ------------------------------------------------------------
# لاگ ساده
# ------------------------------------------------------------
def save_log(line: str) -> None:
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {line}\n")
    except Exception:
        pass

# ------------------------------------------------------------
# چاپ مرحله‌ای با تاخیرای ریز
# ------------------------------------------------------------
def staged_sleep(sec: float = 0.5) -> None:
    time.sleep(sec)

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
# جریان اصلی: اسکن فایل و نصب با هم‌روندی بالا
# ------------------------------------------------------------
def run_for_file(target_path: Optional[str]) -> None:
    req_path = os.path.join(os.getcwd(), REQ_FILENAME)
    if os.path.isfile(req_path):
        failed_reqs = install_requirements(req_path)
        if failed_reqs:
            save_log(f"FAILED_REQUIREMENTS {failed_reqs}")
            raise ModuleNotFoundError(f"Failed to install requirements: {failed_reqs[0]}")
        return

    if not target_path: return
    imports = {m for m in get_imports_from_file(target_path) if m and m.lower() != "autopip"}
    if not imports: return

    with concurrent.futures.ThreadPoolExecutor() as executor:
        missing = {m for m, installed in zip(imports, executor.map(is_installed, imports)) if not installed}
    
    if not missing: return

    clear_screen()
    fancy_banner(os.path.basename(target_path))
    print_identified(imports)
    print_finding_missing()
    print_missing(missing)

    with concurrent.futures.ThreadPoolExecutor() as executor:
        resolved_pkgs = list(executor.map(resolve_package_name, sorted(missing)))

    for pkg in resolved_pkgs:
        print_installing_start(pkg)

    success = pip_install_quiet(resolved_pkgs)
    
    for mod, pkg in zip(sorted(missing), resolved_pkgs):
        save_log(f"{'INSTALLED' if success else 'FAILED'} {mod} -> {pkg}")
        print_install_result(pkg, success)

    if success:
        print()
        print_installing_done()
        staged_sleep(0.6)
        clear_screen() 
    else:
        print(f"\n{Ansi.RED}{Ansi.BOLD}Some packages failed to install. Check logs.{Ansi.RESET}")
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

# ------------------------------------------------------------
# CLI
# ------------------------------------------------------------
def main_cli() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="autopip — automatic non-interactive dependency installer")
    parser.add_argument("file", nargs="?", help="target Python file to scan")
    args = parser.parse_args()
    run_for_file(args.file)

if __name__ == "__main__":
    main_cli()
else:
    auto_on_import()

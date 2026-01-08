#!/usr/bin/env python3
# coding: utf-8

# ------------------------------------------------------------
# autopip: Creator By FrameworkPython
# ------------------------------------------------------------

import ast
import importlib.util
import os
import sys
import time
import concurrent.futures
import urllib.request
import urllib.error
import shutil
import subprocess
from typing import Dict, Optional, Set, List
from banner import clear_screen, fancy_banner

# ------------------------------------------------------------
# Module → PyPI package name mapping
# ------------------------------------------------------------
MODULE_MAP: Dict[str, str] = {
    "bs4": "beautifulsoup4",
    "cv2": "opencv-python",
    "PIL": "pillow",
    "yaml": "PyYAML",
    "sklearn": "scikit-learn",
    "Crypto": "pycryptodome",
}
MODULE_MAP_SET = frozenset(MODULE_MAP)

LOG_PATH = os.path.join(os.getcwd(), "autopip.log")
REQ_FILENAME = "requirements.txt"

# ------------------------------------------------------------
# Detect uv (fastest installer)
# ------------------------------------------------------------
UV_PATH = shutil.which("uv")
USE_UV = UV_PATH is not None

# ------------------------------------------------------------
# httpx for PyPI probe (if available)
# ------------------------------------------------------------
try:
    import httpx
    HTTPX_AVAILABLE = True
except Exception:
    HTTPX_AVAILABLE = False
    httpx = None

# ------------------------------------------------------------
# ANSI colors
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
# Helper: read & parse imports (optimized AST)
# ------------------------------------------------------------
def read_file(path: str) -> str:
    try:
        with open(path, "rb") as f:
            return f.read().decode("utf-8", errors="ignore")
    except Exception:
        return ""

def get_imports_from_source(source: str) -> Set[str]:
    if not source:
        return set()
    try:
        tree = ast.parse(source, mode="exec")
        mods = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for n in node.names:
                    top = n.name.split(".", 1)[0]
                    if top.isidentifier():
                        mods.add(top)
            elif isinstance(node, ast.ImportFrom) and node.module and node.module != "__future__":
                top = node.module.split(".", 1)[0]
                if top.isidentifier():
                    mods.add(top)
        return mods
    except Exception:
        return set()

def get_imports_from_file(path: str) -> Set[str]:
    if not path or not os.path.isfile(path):
        return set()
    return get_imports_from_source(read_file(path))

# ------------------------------------------------------------
# Check if module is installed
# ------------------------------------------------------------
def is_installed(module: str) -> bool:
    return importlib.util.find_spec(module) is not None

# ------------------------------------------------------------
# Resolve package name (with session reuse)
# ------------------------------------------------------------
def resolve_package_name(module: str, *, session: Optional[httpx.Client] = None) -> str:
    if module in MODULE_MAP_SET:
        return MODULE_MAP[module]
    url = f"https://pypi.org/pypi/{module}/json"
    try:
        if HTTPX_AVAILABLE and session:
            resp = session.get(url, timeout=1.0)
            return module if resp.status_code == 200 else module
        else:
            req = urllib.request.Request(url, headers={"User-Agent": "autopip/1.0"})
            with urllib.request.urlopen(req, timeout=1.0) as r:
                return module if r.getcode() == 200 else module
    except Exception:
        pass
    return module

# ------------------------------------------------------------
# Install with highest-performance backend
# ------------------------------------------------------------
def install_packages_quiet(packages: List[str]) -> bool:
    if not packages:
        return True

    if USE_UV:
        try:
            result = subprocess.run(
                [UV_PATH, "pip", "install", "--quiet", "--link-mode=copy"] + packages,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True,
            )
            return result.returncode == 0
        except Exception:
            pass

    try:
        import pip
        from pip._internal import main as pip_main
        sys.argv = ["pip", "install", "--quiet", "--disable-pip-version-check"] + packages
        return pip_main() == 0
    except Exception:
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "--quiet", "--disable-pip-version-check"] + packages,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return True
        except Exception:
            return False

# ------------------------------------------------------------
# Requirements handling
# ------------------------------------------------------------
def parse_requirements(path: str) -> List[str]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip() and not line.startswith("#")]
    except Exception:
        return []

def install_requirements(path: str) -> List[str]:
    pkgs = parse_requirements(path)
    if not pkgs:
        return []

    script_name = os.path.basename(path)
    clear_screen()
    fancy_banner(script_name)
    print_title(f"Installing from {REQ_FILENAME}")

    for spec in pkgs:
        print_installing_start(spec)

    ok = install_packages_quiet(pkgs)
    for spec in pkgs:
        save_log(f"{'INSTALLED' if ok else 'FAILED'} req -> {spec}")
        print_install_result(spec, ok)

    if ok:
        print()
        print_installing_done()
        clear_screen()
        return []
    return pkgs

# ------------------------------------------------------------
# Logging & UI (zero artificial delay)
# ------------------------------------------------------------
def save_log(line: str) -> None:
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {line}\n")
    except Exception:
        pass

def print_title(text: str) -> None:
    print(f"{Ansi.BOLD}{Ansi.CYAN}{text}{Ansi.RESET}")

def print_identified(mods: Set[str]) -> None:
    print_title("The following libraries were identified:")
    for m in sorted(mods):
        print(f"{Ansi.YELLOW}- {m}{Ansi.RESET}")

def print_finding_missing() -> None:
    print(f"{Ansi.GREY}Finding libraries that are not installed . . .{Ansi.RESET}")

def print_missing(found: Set[str]) -> None:
    print_title("These libraries are not installed:")
    for m in sorted(found):
        print(f"{Ansi.RED}- {m}{Ansi.RESET}")

def print_installing_start(pkg: str) -> None:
    print(f"{Ansi.BLUE}Installing library {Ansi.BOLD}{pkg}{Ansi.RESET}{Ansi.BLUE} ...{Ansi.RESET}")

def print_install_result(pkg: str, ok: bool) -> None:
    sym = "✔" if ok else "✖"
    color = Ansi.GREEN if ok else Ansi.RED
    print(f"{color}{sym} {pkg} {'installed' if ok else 'failed to install'}{Ansi.RESET}")

def print_installing_done() -> None:
    print(f"{Ansi.MAGENTA}All libraries have been installed{Ansi.RESET}")

# ------------------------------------------------------------
# Main workflow
# ------------------------------------------------------------
def run_for_file(target_path: Optional[str]) -> None:
    req_path = os.path.join(os.getcwd(), REQ_FILENAME)
    if os.path.isfile(req_path):
        failed = install_requirements(req_path)
        if failed:
            save_log(f"FAILED_REQUIREMENTS {failed}")
            raise ModuleNotFoundError(f"Failed to install: {failed[0]}")
        return

    if not target_path:
        return

    imports = {m for m in get_imports_from_file(target_path) if m and m.lower() != "autopip"}
    if not imports:
        return

    with concurrent.futures.ThreadPoolExecutor() as exe:
        future_to_mod = {exe.submit(is_installed, m): m for m in imports}
        missing = {future_to_mod[f] for f in concurrent.futures.as_completed(future_to_mod) if not f.result()}

    if not missing:
        return

    clear_screen()
    fancy_banner(os.path.basename(target_path))
    print_identified(imports)
    print_finding_missing()
    print_missing(missing)

    resolved: Dict[str, str] = {}
    if HTTPX_AVAILABLE:
        with httpx.Client(timeout=1.0, headers={"User-Agent": "autopip/1.0"}) as sess:
            with concurrent.futures.ThreadPoolExecutor() as pool:
                futs = {pool.submit(resolve_package_name, m, session=sess): m for m in missing}
                for fut in concurrent.futures.as_completed(futs):
                    resolved[futs[fut]] = fut.result()
    else:
        with concurrent.futures.ThreadPoolExecutor() as pool:
            futs = {pool.submit(resolve_package_name, m): m for m in missing}
            for fut in concurrent.futures.as_completed(futs):
                resolved[futs[fut]] = fut.result()

    pkgs = list(resolved.values())
    for pkg in pkgs:
        print_installing_start(pkg)

    success = install_packages_quiet(pkgs)

    for mod in sorted(missing):
        pkg = resolved[mod]
        save_log(f"{'INSTALLED' if success else 'FAILED'} {mod} -> {pkg}")
        print_install_result(pkg, success)

    if success:
        print()
        print_installing_done()
        clear_screen()
    else:
        print(f"\n{Ansi.RED}{Ansi.BOLD}Some packages failed to install. Check logs.{Ansi.RESET}")

# ------------------------------------------------------------
# Auto-import hook
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
    parser = argparse.ArgumentParser(description="autopip — fastest auto-installer (uv > pip)")
    parser.add_argument("file", nargs="?", help="target Python file to scan")
    args = parser.parse_args()
    run_for_file(args.file)

if __name__ == "__main__":
    main_cli()
else:
    auto_on_import()

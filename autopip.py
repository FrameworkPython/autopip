#!/usr/bin/env python3
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

_MODULE_MAP: Dict[str, str] = {
    "bs4": "beautifulsoup4",
    "cv2": "opencv-python",
    "PIL": "pillow",
    "yaml": "PyYAML",
    "sklearn": "scikit-learn",
    "Crypto": "pycryptodome",
}
_LOG_PATH = os.path.join(os.getcwd(), "autopip.log")
_REQ_FILENAME = "requirements.txt"
_UV_PATH = shutil.which("uv")
_USE_UV = _UV_PATH is not None
try:
    import httpx
    _HTTPX_AVAILABLE = True
except Exception:
    _HTTPX_AVAILABLE = False
    httpx = None

_ANSI = {
    "R": "\033[0m", "B": "\033[1m", "RED": "\033[31m", "GRN": "\033[32m",
    "YLW": "\033[33m", "BLU": "\033[34m", "MAG": "\033[35m", "CYN": "\033[36m", "GRY": "\033[90m"
}

class _ImportVisitor(ast.NodeVisitor):
    def __init__(self):
        self.imports = set()
    def visit_Import(self, node):
        for alias in node.names:
            top = alias.name.split('.', 1)[0]
            if top.isidentifier():
                self.imports.add(top)
    def visit_ImportFrom(self, node):
        if node.module and node.module != "__future__":
            top = node.module.split('.', 1)[0]
            if top.isidentifier():
                self.imports.add(top)

def _read_file(path: str) -> str:
    try:
        with open(path, "rb") as f:
            return f.read().decode("utf-8", errors="ignore")
    except Exception:
        return ""

def _get_imports_from_source(source: str) -> Set[str]:
    if not source:
        return set()
    try:
        tree = ast.parse(source)
        visitor = _ImportVisitor()
        visitor.visit(tree)
        return visitor.imports
    except Exception:
        return set()

def _get_imports_from_file(path: str) -> Set[str]:
    if not path or not os.path.isfile(path):
        return set()
    return _get_imports_from_source(_read_file(path))

def _is_installed(module: str) -> bool:
    return importlib.util.find_spec(module) is not None

def _resolve_package_name(module: str, session: Optional[httpx.Client] = None) -> str:
    mapped = _MODULE_MAP.get(module)
    if mapped:
        return mapped
    url = f"https://pypi.org/pypi/{module}/json"
    try:
        if _HTTPX_AVAILABLE and session:
            resp = session.get(url, timeout=1.0)
            return module if resp.status_code == 200 else module
        else:
            req = urllib.request.Request(url, headers={"User-Agent": "autopip/1.0"})
            with urllib.request.urlopen(req, timeout=1.0) as r:
                return module if r.getcode() == 200 else module
    except Exception:
        pass
    return module

def _install_packages_quiet(packages: List[str]) -> bool:
    if not packages:
        return True
    if _USE_UV:
        try:
            subprocess.run(
                [_UV_PATH, "pip", "install", "--quiet", "--link-mode=copy"] + packages,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True,
            )
            return True
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

def _parse_requirements(path: str) -> List[str]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip() and not line.startswith("#")]
    except Exception:
        return []

def _install_requirements(path: str) -> List[str]:
    pkgs = _parse_requirements(path)
    if not pkgs:
        return []
    script_name = os.path.basename(path)
    clear_screen()
    fancy_banner(script_name)
    _print_title(f"Installing from {_REQ_FILENAME}")
    for spec in pkgs:
        _print_installing_start(spec)
    ok = _install_packages_quiet(pkgs)
    for spec in pkgs:
        _save_log(f"{'INSTALLED' if ok else 'FAILED'} req -> {spec}")
        _print_install_result(spec, ok)
    if ok:
        print()
        _print_installing_done()
        clear_screen()
        return []
    return pkgs

def _save_log(line: str) -> None:
    try:
        with open(_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {line}\n")
    except Exception:
        pass

def _print_title(text: str) -> None:
    print(f"{_ANSI['B']}{_ANSI['CYN']}{text}{_ANSI['R']}")

def _print_identified(mods: Set[str]) -> None:
    _print_title("The following libraries were identified:")
    for m in sorted(mods):
        print(f"{_ANSI['YLW']}- {m}{_ANSI['R']}")

def _print_finding_missing() -> None:
    print(f"{_ANSI['GRY']}Finding libraries that are not installed . . .{_ANSI['R']}")

def _print_missing(found: Set[str]) -> None:
    _print_title("These libraries are not installed:")
    for m in sorted(found):
        print(f"{_ANSI['RED']}- {m}{_ANSI['R']}")

def _print_installing_start(pkg: str) -> None:
    print(f"{_ANSI['BLU']}Installing library {_ANSI['B']}{pkg}{_ANSI['R']}{_ANSI['BLU']} ...{_ANSI['R']}")

def _print_install_result(pkg: str, ok: bool) -> None:
    sym = "✔" if ok else "✖"
    color = _ANSI["GRN"] if ok else _ANSI["RED"]
    print(f"{color}{sym} {pkg} {'installed' if ok else 'failed to install'}{_ANSI['R']}")

def _print_installing_done() -> None:
    print(f"{_ANSI['MAG']}All libraries have been installed{_ANSI['R']}")

def _run_for_file(target_path: Optional[str]) -> None:
    req_path = os.path.join(os.getcwd(), _REQ_FILENAME)
    if os.path.isfile(req_path):
        failed = _install_requirements(req_path)
        if failed:
            _save_log(f"FAILED_REQUIREMENTS {failed}")
            raise ModuleNotFoundError(f"Failed to install: {failed[0]}")
        return
    if not target_path:
        return
    imports = {m for m in _get_imports_from_file(target_path) if m and m.lower() != "autopip"}
    if not imports:
        return
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as exe:
        future_to_mod = {exe.submit(_is_installed, m): m for m in imports}
        missing = {future_to_mod[f] for f in concurrent.futures.as_completed(future_to_mod) if not f.result()}
    if not missing:
        return
    clear_screen()
    fancy_banner(os.path.basename(target_path))
    _print_identified(imports)
    _print_finding_missing()
    _print_missing(missing)
    resolved: Dict[str, str] = {}
    if _HTTPX_AVAILABLE:
        with httpx.Client(timeout=1.0, headers={"User-Agent": "autopip/1.0"}) as sess:
            with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
                futs = {pool.submit(_resolve_package_name, m, session=sess): m for m in missing}
                for fut in concurrent.futures.as_completed(futs):
                    resolved[futs[fut]] = fut.result()
    else:
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            futs = {pool.submit(_resolve_package_name, m): m for m in missing}
            for fut in concurrent.futures.as_completed(futs):
                resolved[futs[fut]] = fut.result()
    pkgs = list(resolved.values())
    for pkg in pkgs:
        _print_installing_start(pkg)
    success = _install_packages_quiet(pkgs)
    for mod in sorted(missing):
        pkg = resolved[mod]
        _save_log(f"{'INSTALLED' if success else 'FAILED'} {mod} -> {pkg}")
        _print_install_result(pkg, success)
    if success:
        print()
        _print_installing_done()
        clear_screen()
    else:
        print(f"\n{_ANSI['RED']}{_ANSI['B']}Some packages failed to install. Check logs.{_ANSI['R']}")

def _auto_on_import() -> None:
    main_mod = sys.modules.get("__main__")
    target_path = getattr(main_mod, "__file__", None)
    try:
        _run_for_file(target_path)
    except ModuleNotFoundError:
        _save_log("ModuleNotFoundError in auto_on_import")
        raise

def main_cli() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="autopip — fastest auto-installer (uv > pip)")
    parser.add_argument("file", nargs="?", help="target Python file to scan")
    args = parser.parse_args()
    _run_for_file(args.file)

if __name__ == "__main__":
    main_cli()
else:
    _auto_on_import()

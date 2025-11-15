import os
import sys
import time

class Ansi:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    YELLOW = "\033[33m"
    GREEN = "\033[32m"

def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")

def type_write(text: str, delay: float = 0.05):
    for ch in text:
        sys.stdout.write(ch)
        sys.stdout.flush()
        time.sleep(delay)
    sys.stdout.write("\n")
    sys.stdout.flush()

def fancy_banner(script_name: str):
    banner_lines = [
        r"""  /$$$$$$  /$$   /$$ /$$$$$$$$ /$$$$$$ 
  /$$__  $$| $$  | $$|__  $$__//$$__  $$
 | $$  \ $$| $$  | $$   | $$  | $$  \ $$
 | $$$$$$$$| $$  | $$   | $$  | $$  | $$
 | $$__  $$| $$  | $$   | $$  | $$  | $$
 | $$  | $$| $$  | $$   | $$  | $$  | $$
 | $$  | $$|  $$$$$$/   | $$  |  $$$$$$/
 |__/  |__/ \______/    |__/   \______/ 
                                       
                                       
                                       
   /$$$$$$$  /$$$$$$ /$$$$$$$            
  | $$__  $$|_  $$_/| $$__  $$           
  | $$  \ $$  | $$  | $$  \ $$           
  | $$$$$$$/  | $$  | $$$$$$$/           
  | $$____/   | $$  | $$____/            
  | $$        | $$  | $$                 
  | $$       /$$$$$$| $$                 
  |__/      |______/|__/                                      
                                       """,
        r"                                                          ",
        r"        AUTOPIP                             ",
    ]

    print(f"{Ansi.MAGENTA}{Ansi.BOLD}")
    for ln in banner_lines:
        print(f"  {ln}")
    print(f"{Ansi.RESET}")

    print(f"{Ansi.BOLD}{Ansi.CYAN}Script:{Ansi.RESET} {Ansi.RESET}{script_name}{Ansi.RESET}")
    print()

    tg = "telegram:@Framework_Python"
    rb = "rubika:@Framework_dev"

    time.sleep(0.4)
    sys.stdout.write("  "); sys.stdout.flush()
    type_write(f"{Ansi.YELLOW}{tg}{Ansi.RESET}", delay=0.04)

    time.sleep(0.2)
    sys.stdout.write("  "); sys.stdout.flush()
    type_write(f"{Ansi.GREEN}{rb}{Ansi.RESET}", delay=0.04)

    time.sleep(0.6)
    
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import urlencode, urlparse
from urllib.request import urlopen
from urllib.error import URLError

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parents[3]
DEFAULT_CONFIG = SCRIPT_DIR / "config.json"


def wait_for_server(url: str, timeout: int = 30, proc: subprocess.Popen | None = None) -> None:
    start = time.time()
    while time.time() - start < timeout:
        if proc and proc.poll() is not None:
            raise RuntimeError("uvicorn exited before server became ready")
        try:
            with urlopen(url, timeout=2):
                return
        except URLError:
            time.sleep(0.5)
    raise RuntimeError(f"server not ready after {timeout}s: {url}")


def start_uvicorn(host: str, port: int) -> subprocess.Popen:
    code = (
        "import sys; "
        f"sys.path.insert(0, r'{ROOT_DIR}'); "
        "import uvicorn; "
        f"uvicorn.run('xuebao_site.app:app', host='{host}', port={port})"
    )
    env = os.environ.copy()
    return subprocess.Popen([sys.executable, "-c", code], cwd=str(ROOT_DIR), env=env)


def build_next_url(base_url: str, room_path: str, view: str) -> str:
    query = urlencode({"next": room_path})
    return f"{base_url}/werewolf/{view}?{query}"

def get_room_url(base_url: str) -> str:
    with urlopen(f"{base_url}/werewolf", timeout=5) as resp:
        return resp.geturl()


def login(page, base_url: str, room_path: str, account: dict) -> None:
    login_url = build_next_url(base_url, room_path, "login")
    page.goto(login_url, wait_until="domcontentloaded")
    page.fill("input[name='qq_uin']", account["qq_uin"])
    page.fill("input[name='secret']", account["secret"])
    page.click("button[type='submit']")

    try:
        page.wait_for_url("**/werewolf/room/**", timeout=4000)
        return
    except PlaywrightTimeoutError:
        error_box = page.query_selector(".alert")
        if error_box:
            raise RuntimeError(f"login failed: {error_box.text_content()}") from None
        raise


def join_room(page, account: dict) -> None:
    display_name = account.get("display_name")
    page.wait_for_selector("#joinBtn", timeout=8000)
    if display_name:
        page.fill("#joinName", display_name)
    page.click("#joinBtn")
    page.wait_for_function(
        """
        () => {
          const el = document.querySelector('#statusLine');
          if (!el) return false;
          const text = el.textContent || '';
          return text.includes('已加入房间') || text.includes('你是房主');
        }
        """,
        timeout=15000,
    )


def run() -> None:
    if not DEFAULT_CONFIG.exists():
        raise FileNotFoundError(f"missing config: {DEFAULT_CONFIG}")
    config = json.loads(DEFAULT_CONFIG.read_text(encoding="utf-8"))
    accounts = config.get("accounts", [])
    if len(accounts) < 3:
        raise ValueError("config accounts must have at least 3 entries")

    base_url = config.get("base_url", "http://127.0.0.1:8000").rstrip("/")
    headless = bool(config.get("headless", False))
    keep_open = bool(config.get("keep_open", True))
    host = config.get("host", "0.0.0.0")
    port = int(config.get("port", 8000))

    server = start_uvicorn(host, port)
    try:
        wait_for_server(f"{base_url}/werewolf", proc=server)
        room_url = get_room_url(base_url)
        room_path = urlparse(room_url).path
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=headless)
            contexts = [browser.new_context() for _ in range(3)]
            pages = [ctx.new_page() for ctx in contexts]

            for page, account in zip(pages, accounts[:3]):
                login(page, base_url, room_path, account)
                page.goto(room_url, wait_until="domcontentloaded")
                join_room(page, account)

            pages[0].wait_for_selector("#startBtn")
            pages[0].click("#startBtn")

            if keep_open:
                input("game started. press Enter to close...\n")
            browser.close()
    finally:
        server.terminate()
        try:
            server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill()


if __name__ == "__main__":
    run()

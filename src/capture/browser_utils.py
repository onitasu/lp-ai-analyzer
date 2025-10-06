import base64
import os
import time
from typing import Dict, List

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

VIEWPORT_WIDTH = 1600
VIEWPORT_HEIGHT = 1000


def new_driver() -> webdriver.Chrome:
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-extensions")
    opts.add_argument("--disable-plugins")
    opts.add_argument("--disable-images")
    opts.add_argument("--disable-javascript")
    opts.add_argument("--disable-web-security")
    opts.add_argument("--allow-running-insecure-content")
    opts.add_argument(f"--window-size={VIEWPORT_WIDTH},{VIEWPORT_HEIGHT}")
    
    # Streamlit Community Cloud用の設定
    if os.getenv("STREAMLIT_SERVER_HEADLESS"):
        # クラウド環境ではChromeDriverManagerを使用せず、システムのChromeDriverを使用
        try:
            service = Service()  # システムのChromeDriverを使用
            driver = webdriver.Chrome(service=service, options=opts)
        except Exception:
            # フォールバック: ChromeDriverManagerを使用
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=opts)
    else:
        # ローカル環境ではChromeDriverManagerを使用
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=opts)
    
    return driver


def wait_for_ready(driver: webdriver.Chrome, timeout: float = 30.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        state = driver.execute_script("return document.readyState")
        if state == "complete":
            return
        time.sleep(0.3)


def progressive_scroll(driver: webdriver.Chrome, settle_wait: float = 0.5) -> None:
    """Scroll the page to trigger lazy-loading assets before capture."""
    last_height = 0
    stable = 0
    for _ in range(15):
        height = driver.execute_script(
            "return Math.max(document.body.scrollHeight, document.documentElement.scrollHeight);"
        )
        viewport = driver.execute_script("return window.innerHeight") or VIEWPORT_HEIGHT
        step = max(int(viewport * 0.8), 200)
        positions = list(range(0, int(height), step))
        positions.append(max(int(height) - viewport, 0))
        for pos in positions:
            driver.execute_script("window.scrollTo(0, arguments[0]);", pos)
            time.sleep(settle_wait)
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(settle_wait)
        if abs(height - last_height) < 8:
            stable += 1
            if stable >= 3:
                break
        else:
            stable = 0
            last_height = height


def capture_full_page(driver: webdriver.Chrome, out_path: str) -> None:
    """Use Chrome DevTools to capture the entire page in one image."""
    try:
        metrics = driver.execute_cdp_cmd("Page.getLayoutMetrics", {})
        content_size = metrics.get("contentSize", {})
        width = int(content_size.get("width", VIEWPORT_WIDTH))
        height = int(content_size.get("height", VIEWPORT_HEIGHT))
        driver.execute_cdp_cmd(
            "Emulation.setDeviceMetricsOverride",
            {
                "width": width,
                "height": height,
                "deviceScaleFactor": 1,
                "mobile": False,
            },
        )
    except Exception:
        pass

    result = driver.execute_cdp_cmd(
        "Page.captureScreenshot",
        {"captureBeyondViewport": True, "fromSurface": True},
    )
    data = result.get("data")
    if data:
        with open(out_path, "wb") as f:
            f.write(base64.b64decode(data))


def capture_scroll_slices(driver: webdriver.Chrome, run_dir: str, prefix: str) -> List[str]:
    """Capture a sequence of viewport-height screenshots covering the page."""
    paths: List[str] = []
    viewport = driver.execute_script("return window.innerHeight") or VIEWPORT_HEIGHT
    height = driver.execute_script(
        "return Math.max(document.body.scrollHeight, document.documentElement.scrollHeight);"
    )
    step = max(int(viewport * 0.9), 200)
    positions = list(range(0, int(height), step))
    last_position = max(int(height) - viewport, 0)
    if positions and positions[-1] != last_position:
        positions.append(last_position)

    for idx, pos in enumerate(positions, start=1):
        driver.execute_script("window.scrollTo(0, arguments[0]);", pos)
        time.sleep(0.35)
        out = os.path.join(run_dir, f"{prefix}_{idx:03d}.png")
        driver.save_screenshot(out)
        paths.append(out)

    driver.execute_script("window.scrollTo(0, 0);")
    return paths


def collect_screenshots(driver: webdriver.Chrome, run_dir: str, prefix: str) -> Dict[str, object]:
    screenshots: Dict[str, object] = {}
    full_path = os.path.join(run_dir, f"{prefix}_full.png")
    capture_full_page(driver, full_path)
    screenshots["full"] = full_path
    screenshots["slices"] = capture_scroll_slices(driver, run_dir, f"{prefix}_slice")
    viewport_path = os.path.join(run_dir, f"{prefix}_viewport.png")
    driver.save_screenshot(viewport_path)
    screenshots["viewport"] = viewport_path
    return screenshots

import os
import urllib.parse
from typing import Dict, List

import requests
from bs4 import BeautifulSoup

from src.capture.browser_utils import (
    collect_screenshots,
    new_driver,
    progressive_scroll,
    wait_for_ready,
)


def fetch_page(url: str, run_dir: str) -> Dict[str, object]:
    os.makedirs(run_dir, exist_ok=True)
    driver = new_driver()
    driver.set_page_load_timeout(25)
    driver.get(url)
    wait_for_ready(driver)
    progressive_scroll(driver)
    html = driver.page_source

    screenshots = collect_screenshots(driver, run_dir, "before")

    soup = BeautifulSoup(html, "html.parser")
    css_texts: List[str] = []
    css_paths: List[str] = []
    css_sources: List[str] = []
    for link in soup.select('link[rel="stylesheet"]'):
        href = link.get("href")
        if not href:
            continue
        abs_url = urllib.parse.urljoin(url, href)
        try:
            response = requests.get(abs_url, timeout=10)
            if 200 <= response.status_code < 300 and response.text:
                css_file = os.path.join(run_dir, f"ext_{len(css_paths)}.css")
                with open(css_file, "w", encoding="utf-8") as f:
                    f.write(response.text)
                css_paths.append(css_file)
                css_texts.append(response.text)
                css_sources.append(abs_url)
        except Exception:
            continue

    html_path = os.path.join(run_dir, "index.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)

    driver.quit()
    return {
        "html_path": html_path,
        "css_paths": css_paths,
        "external_css_text": "\n\n/*--- external css bundle ---*/\n" + "\n\n".join(css_texts),
        "screenshot_paths": screenshots,
        "html_text": html,
        "css_texts": css_texts,
        "css_sources": css_sources,
    }

import os
from typing import Dict

from bs4 import BeautifulSoup

from src.capture.browser_utils import (
    collect_screenshots,
    new_driver,
    progressive_scroll,
    wait_for_ready,
)


def _inline_css(html_text: str, css_bundle: str) -> str:
    if not css_bundle.strip():
        return html_text

    soup = BeautifulSoup(html_text, "html.parser")
    if not soup.html:
        wrapper = BeautifulSoup("<html><head></head><body></body></html>", "html.parser")
        wrapper.body.append(soup)
        soup = wrapper

    head = soup.head
    if not head:
        head = soup.new_tag("head")
        soup.html.insert(0, head)

    style_tag = soup.new_tag("style")
    style_tag.attrs["data-inline"] = "capture-css"
    style_tag.string = css_bundle

    existing = head.find("style", attrs={"data-inline": "capture-css"})
    if existing:
        existing.replace_with(style_tag)
    else:
        head.append(style_tag)

    return str(soup)


def prepare_renderable_html(html_path: str, css_bundle: str, run_dir: str) -> str:
    with open(html_path, "r", encoding="utf-8") as f:
        html_text = f.read()

    inlined = _inline_css(html_text, css_bundle)
    render_path = os.path.join(run_dir, "_render.html")
    with open(render_path, "w", encoding="utf-8") as f:
        f.write(inlined)
    return render_path


def take_png_of_html(html_path: str, css_bundle: str, run_dir: str) -> Dict[str, object]:
    render_path = prepare_renderable_html(html_path, css_bundle, run_dir)
    driver = new_driver()
    driver.set_page_load_timeout(10)
    driver.get("file://" + os.path.abspath(render_path))
    wait_for_ready(driver)
    progressive_scroll(driver)
    screenshots = collect_screenshots(driver, run_dir, "after")
    driver.quit()
    return {"render_path": render_path, "screenshots": screenshots}

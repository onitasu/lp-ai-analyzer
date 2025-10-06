import os
import urllib.parse
from typing import Dict, List
import asyncio
from playwright.async_api import async_playwright
import requests
from bs4 import BeautifulSoup


async def fetch_page_playwright(url: str, run_dir: str) -> Dict[str, object]:
    """Playwrightを使用したWebページキャプチャ（Streamlit Community Cloud対応）"""
    os.makedirs(run_dir, exist_ok=True)
    
    async with async_playwright() as p:
        # Chromiumブラウザを起動
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--disable-extensions',
                '--disable-plugins',
                '--disable-images',
                '--disable-web-security',
                '--allow-running-insecure-content'
            ]
        )
        
        try:
            # 新しいページを作成
            page = await browser.new_page()
            await page.set_viewport_size({"width": 1600, "height": 1000})
            
            # ページにアクセス
            await page.goto(url, wait_until="networkidle", timeout=30000)
            
            # ページのスクロール（遅延読み込み対応）
            await page.evaluate("""
                () => {
                    return new Promise((resolve) => {
                        let totalHeight = 0;
                        const distance = 100;
                        const timer = setInterval(() => {
                            const scrollHeight = document.body.scrollHeight;
                            window.scrollBy(0, distance);
                            totalHeight += distance;
                            
                            if(totalHeight >= scrollHeight){
                                clearInterval(timer);
                                window.scrollTo(0, 0);
                                resolve();
                            }
                        }, 100);
                    });
                }
            """)
            
            # HTMLを取得
            html = await page.content()
            
            # スクリーンショットを撮影
            screenshot_paths = {}
            
            # フルページスクリーンショット
            full_screenshot_path = os.path.join(run_dir, "before_full.png")
            await page.screenshot(path=full_screenshot_path, full_page=True)
            screenshot_paths["full"] = full_screenshot_path
            
            # ビューポートスクリーンショット
            viewport_screenshot_path = os.path.join(run_dir, "before_viewport.png")
            await page.screenshot(path=viewport_screenshot_path, full_page=False)
            screenshot_paths["viewport"] = viewport_screenshot_path
            
            # スライススクリーンショット
            slice_paths = []
            viewport_height = 1000
            page_height = await page.evaluate("document.body.scrollHeight")
            
            for i in range(0, int(page_height), viewport_height):
                await page.evaluate(f"window.scrollTo(0, {i})")
                await page.wait_for_timeout(300)
                
                slice_path = os.path.join(run_dir, f"before_slice_{len(slice_paths)+1:03d}.png")
                await page.screenshot(path=slice_path, full_page=False)
                slice_paths.append(slice_path)
            
            screenshot_paths["slices"] = slice_paths
            
        finally:
            await browser.close()
    
    # CSSファイルの取得
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
    
    # HTMLファイルを保存
    html_path = os.path.join(run_dir, "index.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    
    return {
        "html_path": html_path,
        "css_paths": css_paths,
        "external_css_text": "\n\n/*--- external css bundle ---*/\n" + "\n\n".join(css_texts),
        "screenshot_paths": screenshot_paths,
        "html_text": html,
        "css_texts": css_texts,
        "css_sources": css_sources,
    }


def fetch_page(url: str, run_dir: str) -> Dict[str, object]:
    """同期関数としてPlaywrightキャプチャを実行"""
    return asyncio.run(fetch_page_playwright(url, run_dir))

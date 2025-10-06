import os
import urllib.parse
from typing import Dict, List
import requests
from bs4 import BeautifulSoup
import base64
from PIL import Image, ImageDraw, ImageFont
import io


def create_placeholder_image(width: int = 1600, height: int = 1000, text: str = "Page Preview") -> str:
    """プレースホルダー画像を作成"""
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)
    
    # テキストを中央に配置
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
    except:
        font = ImageFont.load_default()
    
    # テキストのサイズを取得
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    # 中央に配置
    x = (width - text_width) // 2
    y = (height - text_height) // 2
    
    draw.text((x, y), text, fill='gray', font=font)
    
    # 画像を保存
    img_path = os.path.join(os.path.dirname(__file__), "..", "..", "runs", "placeholder.png")
    os.makedirs(os.path.dirname(img_path), exist_ok=True)
    img.save(img_path)
    return img_path


def fetch_page(url: str, run_dir: str) -> Dict[str, object]:
    """HTTPリクエストベースのシンプルなページ取得"""
    os.makedirs(run_dir, exist_ok=True)
    
    try:
        # HTTPリクエストでページを取得
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        html = response.text
        
        # BeautifulSoupでHTMLを解析
        soup = BeautifulSoup(html, "html.parser")
        
        # CSSファイルの取得
        css_texts: List[str] = []
        css_paths: List[str] = []
        css_sources: List[str] = []
        
        for link in soup.select('link[rel="stylesheet"]'):
            href = link.get("href")
            if not href:
                continue
            abs_url = urllib.parse.urljoin(url, href)
            try:
                css_response = requests.get(abs_url, timeout=10)
                if 200 <= css_response.status_code < 300 and css_response.text:
                    css_file = os.path.join(run_dir, f"ext_{len(css_paths)}.css")
                    with open(css_file, "w", encoding="utf-8") as f:
                        f.write(css_response.text)
                    css_paths.append(css_file)
                    css_texts.append(css_response.text)
                    css_sources.append(abs_url)
            except Exception:
                continue
        
        # HTMLファイルを保存
        html_path = os.path.join(run_dir, "index.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)
        
        # プレースホルダー画像を作成
        placeholder_path = create_placeholder_image(text=f"Preview of {url}")
        
        # スクリーンショットパスを設定
        screenshot_paths = {
            "full": placeholder_path,
            "viewport": placeholder_path,
            "slices": [placeholder_path]
        }
        
        return {
            "html_path": html_path,
            "css_paths": css_paths,
            "external_css_text": "\n\n/*--- external css bundle ---*/\n" + "\n\n".join(css_texts),
            "screenshot_paths": screenshot_paths,
            "html_text": html,
            "css_texts": css_texts,
            "css_sources": css_sources,
        }
        
    except Exception as e:
        # エラーが発生した場合のフォールバック
        st.error(f"ページの取得に失敗しました: {str(e)}")
        
        # 最小限のデータを返す
        html_path = os.path.join(run_dir, "index.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(f"<html><body><h1>Error loading page</h1><p>{str(e)}</p></body></html>")
        
        placeholder_path = create_placeholder_image(text="Error loading page")
        
        return {
            "html_path": html_path,
            "css_paths": [],
            "external_css_text": "",
            "screenshot_paths": {
                "full": placeholder_path,
                "viewport": placeholder_path,
                "slices": [placeholder_path]
            },
            "html_text": f"<html><body><h1>Error loading page</h1><p>{str(e)}</p></body></html>",
            "css_texts": [],
            "css_sources": [],
        }

"""
LLMへのプロンプト生成を管理するモジュール
分析、差分生成、バリエーション生成のためのプロンプトを構築
"""
import json
from typing import List

from src.llm.schemas import Improvement, Issue

# デザイン・ビジュアル改善のルールカード（見た目中心）
RULES = """
## 優先度: 高（見た目の改善）
- **タイポグラフィ**: フォントサイズ、行間、文字間隔、ヒエラルキー
- **色・コントラスト**: ブランドカラー統一、視認性、色のバランス
- **レイアウト**: 余白（padding/margin）、配置、グリッド、視線誘導
- **ビジュアル要素**: 画像サイズ、アイコン、ボタンデザイン、装飾
- **空間設計**: セクション間隔、コンテンツ密度、ホワイトスペース
- **視覚的ヒエラルキー**: 重要度の視覚化、CTAの目立ちやすさ

## 対象外（見た目に関係ない）
- ❌ SEO（meta tags、構造化データ等）
- ❌ アクセシビリティ（aria属性、alt属性等）
- ❌ パフォーマンス（読み込み速度、画像最適化等）
- ❌ コンテンツ文言（テキスト内容の大幅変更）

**重要**: 見た目の改善のみに焦点を当て、視覚的なインパクトを最大化してください。
"""

# プロンプトに含めるコードの最大文字数制限
MAX_HTML_CHARS = 12_000
MAX_CSS_CHARS = 8_000


def _clip_for_prompt(text: str, *, max_chars: int, comment_style: str) -> str:
    """LLMプロンプトに収まるようテキストを前後から抜粋する"""
    if len(text) <= max_chars:
        return text

    # 前方を重点的に残しつつ末尾の文脈も保持する
    head_keep = int(max_chars * 0.7)
    tail_keep = max_chars - head_keep
    marker_body = f"{len(text) - max_chars} chars truncated for prompt budget"
    if comment_style == "html":
        marker = f"\n<!-- {marker_body} -->\n"
    elif comment_style == "css":
        marker = f"\n/* {marker_body} */\n"
    else:
        marker = f"\n# {marker_body}\n"
    return text[:head_keep] + marker + text[-tail_keep:]


def build_system_prompt() -> str:
    """システムプロンプトを生成"""
    return (
        "あなたはUI/UXデザインに長けたシニアデザイナー兼フロントエンド実装者です。"
        "LPのデザイン・ビジュアルを視覚（画像）とコード（HTML/CSS）両面から監査し、"
        "**見た目の改善点**を洗い出してください。\n\n"
        "【重要な制約】\n"
        "- 見た目に関係ないもの（SEO、アクセシビリティ、パフォーマンス）は対象外\n"
        "- デザイン・レイアウト・色・タイポグラフィなど視覚的改善に焦点\n"
        "- 回答は簡潔に、要点を絞って出力。長い推論は不要。"
    )


def build_analysis_prompt(html: str, css_bundle: str, extra_instruction: str = "") -> str:
    """分析用プロンプトを生成"""
    extra = f"- 追加要望: {extra_instruction}\n" if extra_instruction else ""
    html_snippet = _clip_for_prompt(html, max_chars=MAX_HTML_CHARS, comment_style="html")
    css_snippet = _clip_for_prompt(css_bundle, max_chars=MAX_CSS_CHARS, comment_style="css")

    return f"""
# タスク
LPのデザイン・ビジュアルを監査し、**見た目の問題**を抽出し、改善案を提案します。
改善案は視覚的なインパクトが大きいものを優先してください。
**指定されたJSON形式で簡潔に出力してください。長い説明や推論プロセスは不要です。**

**重要**: 
- 見た目に関係ないもの（SEO、アクセシビリティ、パフォーマンス）は分析対象外
- デザイン・レイアウト・色・タイポグラフィなど視覚的な改善に焦点を当てる
{extra}
# デザインルールカード
{RULES}

# 参照コード
## index.html
```html
{html_snippet}
```

## styles_external_bundle.css
```css
{css_snippet}
```
"""


# 注意: build_diff_prompt と build_variant_prompt は廃止されました
# 代わりに src.llm.prompts_unified.build_unified_diff_prompt を使用してください
# これにより、base_improvements と variants を1回のLLM呼び出しで生成できます

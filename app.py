"""
シンプル版LP分析アプリ
ジャンル別プロンプトで視覚的な改善点を分析
"""
import os
import base64
import streamlit as st

from src.capture.simple_capture import fetch_page
from src.llm.exceptions import StructuredCallError
from src.llm.pipeline import run_structured_pipeline
from src.utils.io import make_run_dir, read_text
from src.utils.run_logger import RunLogger
from src.llm.genre_prompts import GENRES, get_genre_system_prompt, get_genre_analysis_prompt_addition, get_genre_specific_rules

st.set_page_config(page_title="LP AI Analyzer", layout="wide")
st.title("🎨 AI-Powered Landing Page Analyzer")
st.caption("ジャンル別に最適化された視覚改善の提案")

# 使い方のガイド
with st.expander("📖 使い方", expanded=False):
    st.markdown("""
    ### 📝 3ステップで簡単分析
    
    **Step 1: サイドバーで設定**
    - ← 左のサイドバーで「LPの種類」を選択
    - SaaS / D2C / 教育 / 採用 / アプリ から選択
    
    **Step 2: URLを入力**
    - 分析したいLPのURLを入力
    
    **Step 3: 解析実行**
    - 「🚀 解析する」ボタンをクリック
    - 選択したジャンルに最適化されたプロンプトで分析されます
    """)

# ==== Sidebar: Settings ====
st.sidebar.header("⚙️ 設定")

st.sidebar.markdown("### 📌 Step 1: LPの種類を選択")
st.sidebar.caption("👇 まずはこちらを選択してください")

# ジャンル選択
genre = st.sidebar.selectbox(
    "LPの種類",
    options=list(GENRES.keys()),
    format_func=lambda x: GENRES[x],
    help="LPの種類に応じて最適化されたプロンプトが使用されます"
)

st.sidebar.success(f"✅ 選択中: **{GENRES[genre]}**")
st.sidebar.markdown("---")

model_vendor = st.sidebar.selectbox(
    "Model vendor", ["Google Gemini", "OpenAI"]
)

if model_vendor == "Google Gemini":
    model_name = st.sidebar.selectbox(
        "Gemini model", 
        ["gemini-2.5-flash", "gemini-2.5-pro"],
        help="""
        Flash: 高速・低コスト・思考トークンなし（推奨）
        Pro: 高品質だが思考トークンで遅く、コストが高い
        
        ℹ️ 選択したmodelが分析に使用されます
        """
    )
else:
    model_name = st.sidebar.selectbox(
        "OpenAI model", 
        ["gpt-5", "gpt-5-mini", "gpt-5-nano"],
        index=0,
        help="""
        gpt-5: 最高品質（複雑な推論・コード生成）
        gpt-5-mini: コスト最適化（バランス型）
        gpt-5-nano: 高速処理（シンプルなタスク）
        
        ℹ️ 選択したmodelが分析に使用されます
        """
    )

# プロンプト詳細設定（上級者向け）
with st.sidebar.expander("🔧 詳細設定（任意）", expanded=False):
    if model_vendor == "Google Gemini":
        st.caption("⚠️ Geminiでは、これらはプロンプトに追加される指示文です")
    else:
        st.caption("✅ OpenAI GPT-5では、これらは正式なAPIパラメータです")
    
    verbosity = st.selectbox(
        "出力の詳細度 (Verbosity)", 
        ["low", "medium", "high"],
        index=0,
        help="""
        OpenAI GPT-5: 正式なAPIパラメータ (text.verbosity)
        - low: 簡潔な出力
        - medium: 標準的な詳細度
        - high: 詳細な説明
        
        Gemini: プロンプト指示として追加
        """
    )
    effort = st.selectbox(
        "推論の深さ (Reasoning Effort)", 
        ["minimal", "low", "medium", "high"],
        index=0,
        help="""
        OpenAI GPT-5: 正式なAPIパラメータ (reasoning.effort)
        - minimal: 最速（最小限の推論）
        - low: 高速（軽い推論）
        - medium: 標準（バランス型）
        - high: 最高品質（深い推論）
        
        Gemini: プロンプト指示として追加
        """
    )

extra_instruction = st.sidebar.text_area(
    "追加要望（任意）", 
    "",
    placeholder="例）モバイルでの見やすさを重視"
)

# ==== Main: Input ====
st.markdown("---")
st.markdown(f"### 📝 Step 2: URL入力")
st.info(f"💡 現在の設定: **{GENRES[genre]}** 向けに最適化")
url = st.text_input("解析するLPのURL", placeholder="https://example.com/landing")

# ジャンル別のガイド表示
with st.expander(f"💡 {GENRES[genre]}の改善ポイント（参考）", expanded=False):
    st.markdown(get_genre_specific_rules(genre))

st.markdown("### 🚀 Step 3: 解析実行")
run_btn = st.button("🚀 解析する", type="primary", use_container_width=True)

if run_btn and url:
    run_dir = make_run_dir(url)
    run_logger = RunLogger(run_dir, url=url)
    run_logger.set_context(
        model_vendor=model_vendor,
        model_name=model_name,
        genre=genre,
        verbosity=verbosity,
        effort=effort,
        extra_instruction=extra_instruction,
    )

    # ページ取得
    run_logger.add_step("fetch_page", "started", detail={"url": url})
    with st.status("📥 ページを取得中...", expanded=False) as s:
        try:
            art = fetch_page(url=url, run_dir=run_dir)
            s.update(label="✅ 取得完了", state="complete")
        except Exception as e:
            s.update(label=f"❌ 取得失敗: {e}", state="error")
            st.stop()
    
    run_logger.add_step("fetch_page", "success", detail={
        "html_path": art["html_path"],
        "css_paths": art.get("css_paths", []),
        "screenshot_paths": art.get("screenshot_paths", {}),
    })

    # スクリーンショット表示
    st.markdown("---")
    st.subheader("📸 取得したスクリーンショット")
    
    screenshot_paths = art.get("screenshot_paths", {})
    primary_screenshot = screenshot_paths.get("full") or screenshot_paths.get("viewport")
    
    if primary_screenshot and os.path.exists(primary_screenshot):
        st.image(primary_screenshot, caption="ページ全体", use_column_width=True)
    
    # HTMLとCSSを取得
    html_source = art.get("html_text") or read_text(art["html_path"])
    css_bundle = art.get("external_css_text", "")
    
    # 画像をbase64エンコード
    with open(primary_screenshot, "rb") as f:
        png_bytes = f.read()
    b64_png = base64.b64encode(png_bytes).decode()

    # LLM分析
    st.markdown("---")
    st.subheader("🤖 AI分析中...")
    
    # ジャンル別のシステムプロンプトを使用
    genre_system_prompt = get_genre_system_prompt(genre)
    genre_addition = get_genre_analysis_prompt_addition(genre)
    
    # 追加要望を含める
    final_extra_instruction = f"{extra_instruction}\n\n{genre_addition}" if extra_instruction else genre_addition
    
    with st.spinner(f"{GENRES[genre]}に最適化されたプロンプトで分析中..."):
        try:
            result, artifacts = run_structured_pipeline(
                html=html_source,
                css_bundle=css_bundle,
                image_b64=b64_png,
                image_bytes=png_bytes if model_vendor == "Google Gemini" else None,
                vendor=model_vendor,
                model=model_name,
                verbosity=verbosity,
                effort=effort,
                extra_instruction=final_extra_instruction,
                # ジャンル別システムプロンプトを使用
                custom_system_prompt=genre_system_prompt,
            )
            
            run_logger.add_step("llm_pipeline", "success", detail={
                "vendor": model_vendor,
                "model": model_name,
                "genre": genre,
            })
            
        except StructuredCallError as exc:
            st.error("❌ LLM呼び出しエラー")
            st.code(str(exc))
            run_logger.add_step("llm_pipeline", "error", detail={"error": str(exc)})
            st.stop()
        except Exception as exc:
            st.error(f"❌ 予期しないエラー: {exc}")
            run_logger.add_step("llm_pipeline", "error", detail={"error": str(exc)})
            st.stop()

    # 分析結果の表示
    st.markdown("---")
    st.success("✅ 分析完了！")
    
    # AnalysisResultから直接取得して辞書形式に変換
    issues = result.issues
    improvements = result.improvements
    
    # respを手動で作成（後方互換性のため）
    resp = {
        "issues": [issue.model_dump() for issue in issues],
        "improvements": [imp.model_dump() for imp in improvements],
    }
    
    # === 問題点の表示 ===
    st.subheader("⚠️ 検出された問題点")
    
    if not issues:
        st.info("大きな問題は検出されませんでした。")
    else:
        for idx, issue in enumerate(issues, 1):
            with st.expander(f"問題 {idx}: {issue.title}", expanded=True):
                st.markdown(f"**説明**: {issue.detail}")
                if issue.evidence:
                    st.caption(f"📌 根拠: {issue.evidence}")
                if issue.severity:
                    severity_color = {"high": "🔴", "medium": "🟡", "low": "🟢"}
                    st.markdown(f"**重要度**: {severity_color.get(issue.severity, '🟡')} {issue.severity.upper()}")

    # === 改善案の表示 ===
    st.markdown("---")
    st.subheader(f"💡 改善提案（{GENRES[genre]}向け）")
    
    if not improvements:
        st.info("改善提案が見つかりませんでした。")
    else:
        st.caption(f"💡 {len(improvements)}件の改善提案が生成されました")
        
        for idx, imp in enumerate(improvements, 1):
            with st.expander(f"改善 {idx}: {imp.title}", expanded=True):
                st.markdown(f"**提案内容**: {imp.rationale}")
                
                # 対象となる問題
                if imp.targets_issue:
                    st.markdown(f"**対象問題**: {imp.targets_issue}")
                
                # ビジュアル的な改善点を強調
                st.info("👁️ この改善は視覚的な効果が期待できます")

    # === 生データの表示（デバッグ用） ===
    with st.expander("📊 詳細データ（開発者向け）", expanded=False):
        st.json(resp)

    # === ログの保存 ===
    run_logger.add_step("display_results", "success", detail={
        "issues_count": len(issues),
        "improvements_count": len(improvements),
    })
    
    st.success(f"✅ 分析ログを保存しました: `{run_dir}`")
    
    # ダウンロードボタン
    st.markdown("---")
    st.subheader("📦 結果をダウンロード")
    
    # JSONダウンロード
    import json
    result_json = json.dumps(resp, ensure_ascii=False, indent=2)
    st.download_button(
        label="📄 JSON形式でダウンロード",
        data=result_json,
        file_name=f"lp_analysis_{genre}.json",
        mime="application/json"
    )

# ==== フッター ====
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 20px;">
    <p>🎨 LP AI Analyzer - ジャンル別視覚改善提案</p>
    <p>SaaS / D2C / 教育 / 採用 / アプリ の各ジャンルに最適化</p>
</div>
""", unsafe_allow_html=True)


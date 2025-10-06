"""LLM pipeline: analysis のみを実行し、構造化された結果を返す"""
from typing import Dict, Tuple, Optional

from src.llm.exceptions import StructuredCallError
from src.llm.gemini_client import GeminiStructuredAgent
from src.llm.openai_client import OpenAIStructuredAgent
from src.llm.prompts import (
    build_analysis_prompt,
    build_system_prompt,
)
from src.llm.schemas import AnalysisResult
from src.utils.json_tools import make_json_safe


def run_structured_pipeline(
    *,
    vendor: str,
    model: str,
    html: str,
    css_bundle: str,
    extra_instruction: str,
    image_bytes: bytes,
    image_b64: str,
    verbosity: str,
    effort: str,
    custom_system_prompt: Optional[str] = None,
) -> Tuple[AnalysisResult, Dict[str, dict]]:
    """
    LLM structured pipeline を実行（分析のみ）:
    1. analyze (AnalysisResult): 問題 + 改善提案

    戻り値:
        - AnalysisResult: 分析結果
        - artifacts: デバッグ情報
    """
    system_prompt = custom_system_prompt or build_system_prompt()
    analysis_prompt = build_analysis_prompt(
        html=html, css_bundle=css_bundle, extra_instruction=extra_instruction
    )

    if vendor == "Google Gemini":
        agent = GeminiStructuredAgent(model=model, verbosity=verbosity, effort=effort)
        analysis, analysis_debug = agent.analyze(
            system=system_prompt, prompt_text=analysis_prompt, image_bytes=image_bytes
        )
    else:
        agent = OpenAIStructuredAgent(model=model, verbosity=verbosity, effort=effort)
        analysis, analysis_debug = agent.analyze(
            system=system_prompt, prompt_text=analysis_prompt, image_b64=image_b64
        )

    artifacts = {
        "system_prompt": system_prompt,
        "analysis_prompt": analysis_prompt,
        "analysis_raw": analysis.model_dump(),
        "analysis_debug": make_json_safe(analysis_debug),
    }
    return analysis, artifacts

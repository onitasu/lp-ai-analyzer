"""OpenAI structured-output client built per official documentation."""
import json
from typing import List, Optional, Type, TypeVar

from openai import OpenAI
from pydantic import BaseModel

from src.llm.exceptions import StructuredCallError
from src.llm.schemas import AnalysisResult, DiffResult
from src.utils.json_tools import make_json_safe

T = TypeVar("T", bound=BaseModel)


class OpenAIStructuredAgent:
    """OpenAI APIを使用した構造化出力エージェント"""

    def __init__(self, model: str, verbosity: str = "medium", effort: str = "medium") -> None:
        """OpenAIクライアントを初期化"""
        self.client = OpenAI()
        self.model = model
        self.verbosity = verbosity  # 出力の詳細度
        self.effort = effort  # 処理の努力度

    def _call(
        self,
        *,
        system: str,
        user_content: List[dict],
        schema: Type[T],
        stage: str,
    ) -> tuple[T, dict]:
        """Call OpenAI Chat Completions API with structured outputs."""
        try:
            # GPT-5用のパラメータを準備
            api_params = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user_content},
                ],
                "response_format": schema,
            }
            
            # GPT-5の場合は、reasoning と text (verbosity) を追加
            if self.model.startswith("gpt-5"):
                # reasoning effort を追加
                api_params["reasoning_effort"] = self.effort  # minimal, low, medium, high
                
                # text verbosity を追加
                api_params["verbosity"] = self.verbosity  # low, medium, high
            
            # structured outputsを使用してAPIを呼び出す
            completion = self.client.beta.chat.completions.parse(**api_params)
        except Exception as exc:
            raise StructuredCallError(
                f"OpenAI API call failed at {stage}: {exc}",
                raw_text=None,
                parsed=None,
                response_debug=None,
            ) from exc

        # パース済みのオブジェクトを取得
        message = completion.choices[0].message
        parsed = message.parsed
        raw_text = message.content
        
        response_debug = make_json_safe(completion.model_dump()) if hasattr(completion, "model_dump") else None

        print("[OpenAI]", stage, "raw_text:\n", raw_text or "(empty)")
        if parsed:
            print("[OpenAI]", stage, "parsed_payload:\n", json.dumps(make_json_safe(parsed.model_dump()), ensure_ascii=False, indent=2))
        else:
            print("[OpenAI]", stage, "parsed_payload: None")

        if parsed is None:
            raise StructuredCallError(
                f"OpenAI structured output missing parsed payload for {stage}",
                raw_text=raw_text,
                parsed=None,
                response_debug=response_debug,
            )

        debug = {
            "raw_text": raw_text,
            "parsed_payload": make_json_safe(parsed.model_dump()),
            "response": response_debug,
        }
        return parsed, debug

    def analyze(
        self,
        *,
        system: str,
        prompt_text: str,
        image_b64: Optional[str],
    ) -> tuple[AnalysisResult, dict]:
        """Webページの分析を実行"""
        content = [{"type": "text", "text": prompt_text}]
        if image_b64:
            content.insert(
                0,
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{image_b64}"},
                },
            )
        return self._call(system=system, user_content=content, schema=AnalysisResult, stage="analysis")

    def generate_unified_diffs(
        self,
        *,
        system: str,
        prompt_text: str,
    ) -> tuple[DiffResult, dict]:
        """統合差分生成（base_improvements + variants を1回で生成）"""
        content = [{"type": "text", "text": prompt_text}]
        return self._call(system=system, user_content=content, schema=DiffResult, stage="unified_diff")

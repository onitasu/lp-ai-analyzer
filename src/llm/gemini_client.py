import io
import json
from typing import Optional, Type, TypeVar

from google import genai
from PIL import Image
from pydantic import BaseModel, ValidationError

from src.llm.exceptions import StructuredCallError
from src.llm.schemas import (
    AnalysisResult,
    DiffResult,
    model_schema_for_gemini,
)
from src.utils.json_tools import make_json_safe

T = TypeVar("T", bound=BaseModel)

# 注意: これらはGemini APIの公式パラメータではなく、プロンプトに追加される指示文です
VERBOSITY_HINT = {
    "low": "**出力は簡潔に、要点のみ。**",
    "medium": "適度に詳しく。根拠は簡潔に。",
    "high": "詳細に説明。根拠も併記。",
}

EFFORT_HINT = {
    "minimal": "**迅速に結論を出す。内部推論は最小限。**",
    "medium": "標準的な推論で効率的に。",
    "high": "慎重に多段推論を行う。",
}


class GeminiStructuredAgent:
    def __init__(self, model: str, verbosity: str = "medium", effort: str = "medium") -> None:
        self.client = genai.Client()
        self.model = model
        self.verbosity = verbosity
        self.effort = effort

    def _base_config(self, system: str) -> dict:
        # Gemini 2.5 Flashは思考トークンなしで効率的
        return {
            "system_instruction": [
                system,
                f"出力の粒度:{VERBOSITY_HINT[self.verbosity]}",
                f"思考方針:{EFFORT_HINT[self.effort]}",
            ],
            "temperature": 0.2,
            # max_output_tokensを指定しない = API のデフォルト値を使用
            # これにより、モデルが必要に応じて適切なトークン数を使用できる
        }

    def _call(
        self,
        *,
        system: str,
        prompt_parts: list,
        schema: Type[T],
        stage: str,
    ) -> tuple[T, dict]:
        config = self._base_config(system)
        config.update(
            {
                "response_mime_type": "application/json",
                "response_schema": model_schema_for_gemini(schema),
            }
        )
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt_parts,
                config=config,
            )
        except Exception as exc:
            raise StructuredCallError(
                f"Gemini API call failed at {stage}: {exc}",
                raw_text=None,
                parsed=None,
                response_debug=None,
            ) from exc

        # Gemini APIからのレスポンスを取得
        raw_text = None
        parsed_dict = None
        candidate_texts = []
        finish_reason = None
        
        # candidatesからテキストとfinish_reasonを取得
        candidates = getattr(response, "candidates", []) or []
        for candidate in candidates:
            try:
                text = getattr(candidate, "text", None)
                if text:
                    candidate_texts.append(text)
                    if raw_text is None:
                        raw_text = text
                # finish_reasonを取得
                if finish_reason is None:
                    finish_reason = getattr(candidate, "finish_reason", None)
            except AttributeError:
                continue
        
        # テキストが取得できない場合は、response.textを試す
        if raw_text is None:
            raw_text = getattr(response, "text", None)

        print("[Gemini]", stage, "raw_text:\n", raw_text or "(empty)")
        if finish_reason:
            print(f"[Gemini] {stage} finish_reason: {finish_reason}")

        # JSONをパース
        if raw_text:
            try:
                parsed_dict = json.loads(raw_text)
                print(
                    "[Gemini]",
                    stage,
                    "parsed_payload:\n",
                    json.dumps(make_json_safe(parsed_dict), ensure_ascii=False, indent=2),
                )
            except json.JSONDecodeError as exc:
                print(f"[Gemini] {stage} JSON decode error: {exc}")
                print(f"[Gemini] {stage} raw_text length: {len(raw_text)} characters")
                if finish_reason:
                    print(f"[Gemini] {stage} This may be due to finish_reason: {finish_reason}")
                parsed_dict = None
        
        print(
            "[Gemini]",
            stage,
            "candidates:\n",
            json.dumps(make_json_safe(candidate_texts), ensure_ascii=False, indent=2),
        )

        if parsed_dict is None:
            error_msg = f"Gemini structured output missing parsed payload for {stage}"
            if finish_reason:
                error_msg += f" (finish_reason: {finish_reason})"
                # finish_reasonが特定の値の場合、より具体的なエラーメッセージを追加
                if str(finish_reason).upper() in ["MAX_TOKENS", "MAXTOKENS"]:
                    error_msg += " - 出力が最大トークン数に達しました。max_output_tokensを増やすか、プロンプトを短くしてください。"
                elif str(finish_reason).upper() == "SAFETY":
                    error_msg += " - 安全性フィルターによってブロックされました。"
            raise StructuredCallError(
                error_msg,
                raw_text=raw_text,
                parsed=None,
                response_debug={
                    "candidates": make_json_safe(candidate_texts),
                    "usage": make_json_safe(getattr(response, "usage_metadata", None)),
                    "finish_reason": finish_reason,
                },
            )

        try:
            validated = schema.model_validate(parsed_dict)
        except ValidationError as exc:
            raise StructuredCallError(
                f"Gemini structured output failed validation for {schema.__name__}: {exc}",
                raw_text=raw_text,
                parsed=parsed_dict,
                response_debug={
                    "candidates": make_json_safe(candidate_texts),
                    "usage": make_json_safe(getattr(response, "usage_metadata", None)),
                },
            ) from exc

        debug = {
            "raw_text": raw_text,
            "parsed_payload": parsed_dict,
            "candidates": make_json_safe(candidate_texts),
            "usage": make_json_safe(getattr(response, "usage_metadata", None)),
        }
        return validated, debug

    def analyze(
        self,
        *,
        system: str,
        prompt_text: str,
        image_bytes: Optional[bytes],
    ) -> tuple[AnalysisResult, dict]:
        parts = [prompt_text]
        if image_bytes:
            parts.append(Image.open(io.BytesIO(image_bytes)))
        return self._call(system=system, prompt_parts=parts, schema=AnalysisResult, stage="analysis")

    def generate_unified_diffs(
        self,
        *,
        system: str,
        prompt_text: str,
    ) -> tuple[DiffResult, dict]:
        """統合差分生成（base_improvements + variants を1回で生成）"""
        return self._call(system=system, prompt_parts=[prompt_text], schema=DiffResult, stage="unified_diff")

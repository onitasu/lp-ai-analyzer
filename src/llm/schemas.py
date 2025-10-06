"""
データ構造の定義とバリデーションを行うスキーマモジュール
LLMの出力を構造化するためのPydanticモデルを定義
"""
from enum import Enum
from typing import Any, Dict, List, Optional, Type

from pydantic import BaseModel, ConfigDict, Field


class StrictBaseModel(BaseModel):
    """厳密なバリデーションを行うベースモデル（追加フィールドを禁止）"""
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class IssueSeverity(str, Enum):
    """問題の重要度レベル"""
    low = "low"      # 低
    medium = "medium"  # 中
    high = "high"    # 高


class Issue(StrictBaseModel):
    """発見された問題を表すモデル"""
    title: str = Field(..., description="問題の見出し")
    detail: str = Field(..., description="問題の詳細説明とその重要性")
    evidence: Optional[str] = Field(None, description="問題を証明するコードスニペットや測定値（オプション）")
    severity: IssueSeverity = Field(IssueSeverity.medium, description="問題の相対的な緊急度")


class Improvement(StrictBaseModel):
    """改善提案を表すモデル"""
    title: str = Field(..., description="改善提案のタイトル")
    rationale: str = Field(..., description="期待される効果と理由の説明")
    targets_issue: Optional[str] = Field(
        None,
        description="この改善が対象とする問題のタイトルまたは識別子（オプション）",
    )


class VariantOption(StrictBaseModel):
    """改善ポイントの1つのバリエーション"""
    version: str = Field(..., description="バージョン識別子（A, B, C等）")
    label: str = Field(..., description="バリエーションのラベル（例: 信頼性重視、スピード重視）")
    search: str = Field(..., description="検索する文字列（ユニークに特定できる十分な長さ）")
    replace: str = Field(..., description="置換後の文字列")


class ImprovementPoint(StrictBaseModel):
    """改善ポイント（複数のバリエーションを持つ）"""
    point_id: str = Field(..., description="改善ポイントのID（例: improvement_1）")
    point_name: str = Field(..., description="改善ポイントの名前（例: ヘッドライン、CTAボタン）")
    description: str = Field(..., description="何を改善するのかの説明")
    file_path: str = Field(..., description="変更対象ファイルのパス（例: index.html）")
    variants: List[VariantOption] = Field(..., description="このポイントのバリエーション（必ず3つ: A, B, C）")


class AnalysisResult(StrictBaseModel):
    """分析結果を表すモデル"""
    summary: Optional[str] = Field(
        None,
        description="全体的な発見事項の簡潔な要約（オプション）",
    )
    issues: List[Issue]  # 発見された問題のリスト
    improvements: List[Improvement]  # 改善提案のリスト


class DiffResult(StrictBaseModel):
    """差分生成結果を表すモデル"""
    improvement_points: List[ImprovementPoint] = Field(..., description="改善ポイントのリスト（各ポイントに3つのバリエーション）")


class StructuredRunResult(StrictBaseModel):
    """構造化実行結果を統合するモデル"""
    analysis: AnalysisResult  # 分析結果
    diffs: DiffResult  # 差分結果（基本改善 + バリエーション）

    def to_dict(self) -> dict:
        """結果を辞書形式で返す"""
        data = self.model_dump()
        return {
            "analysis": data["analysis"],
            "improvement_points": data["diffs"]["improvement_points"],
        }

    def to_markdown(self) -> str:
        """結果をMarkdown形式で返す"""
        data = self.model_dump()
        lines = []
        analysis = data.get("analysis", {})
        if analysis.get("summary"):
            lines.append(analysis["summary"])
            lines.append("")
        lines.append("### Issues")
        for item in analysis.get("issues", []):
            lines.append(f"- **{item['title']}** ({item['severity']}): {item['detail']}")
            if item.get("evidence"):
                lines.append(f"    - Evidence: {item['evidence']}")
        if not analysis.get("issues"):
            lines.append("- (none)")
        lines.append("")
        lines.append("### Improvements")
        for item in analysis.get("improvements", []):
            suffix = f" (targets: {item['targets_issue']})" if item.get("targets_issue") else ""
            lines.append(f"- **{item['title']}**{suffix}: {item['rationale']}")
        if not analysis.get("improvements"):
            lines.append("- (none)")
        lines.append("")
        lines.append("### Diff")
        for patch in data.get("diffs", {}).get("diffs", []):
            if patch.get("description"):
                lines.append(f"- {patch['description']}")
            lines.append("```diff")
            lines.append(patch["patch"])
            lines.append("```")
        if not data.get("diffs", {}).get("diffs"):
            lines.append("(no diff provided)")
        lines.append("")
        lines.append("### Variants (A/B Test)")
        for variant in data.get("variants", {}).get("variants", []):
            lines.append(f"#### {variant.get('name', 'Variant')}")
            if variant.get("rationale"):
                lines.append(f"_{variant['rationale']}_")
            for diff in variant.get("diffs", []):
                lines.append(f"- {diff.get('description', 'Change')}")
        if not data.get("variants", {}).get("variants"):
            lines.append("(no variants)")
        return "\n".join(lines)

    def to_app_payload(self) -> dict:
        """アプリケーション用のペイロード形式で返す"""
        data = self.model_dump()
        payload = {
            "issues": data["analysis"].get("issues", []),
            "improvements": data["analysis"].get("improvements", []),
            "improvement_points": data.get("diffs", {}).get("improvement_points", []),
            "raw": self.to_markdown(),
        }
        return payload


def _strip_unsupported_keys(obj: Any) -> Any:
    """Gemini APIでサポートされていないキーを除去"""
    if isinstance(obj, dict):
        cleaned: Dict[str, Any] = {}
        for key, value in obj.items():
            if key in {"additionalProperties", "unevaluatedProperties", "patternProperties"}:
                continue
            cleaned[key] = _strip_unsupported_keys(value)
        if cleaned.get("type") == "object" and "properties" in cleaned and "propertyOrdering" not in cleaned:
            cleaned["propertyOrdering"] = list(cleaned["properties"].keys())
        return cleaned
    if isinstance(obj, list):
        return [_strip_unsupported_keys(item) for item in obj]
    return obj


def model_schema_for_gemini(model_cls: Type[BaseModel]) -> Dict[str, Any]:
    """Gemini API用にスキーマを変換"""
    raw = model_cls.model_json_schema()
    return _strip_unsupported_keys(raw)

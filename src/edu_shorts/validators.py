from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


class ContractError(ValueError):
    pass


def load_schema(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_schema(data: Any, schema: dict[str, Any], path: str = "$") -> None:
    if "const" in schema and data != schema["const"]:
        raise ContractError(f"{path}: {schema['const']!r}이어야 합니다.")
    if "enum" in schema and data not in schema["enum"]:
        raise ContractError(f"{path}: 허용값은 {schema['enum']}입니다.")

    expected = schema.get("type")
    type_map = {
        "object": dict,
        "array": list,
        "string": str,
        "boolean": bool,
        "number": (int, float),
    }
    if expected in type_map:
        if expected == "number" and isinstance(data, bool):
            raise ContractError(f"{path}: 숫자여야 합니다.")
        if not isinstance(data, type_map[expected]):
            raise ContractError(f"{path}: {expected} 형식이어야 합니다.")

    if isinstance(data, dict):
        required = schema.get("required", [])
        missing = [key for key in required if key not in data]
        if missing:
            raise ContractError(f"{path}: 필수 키 누락 {missing}")
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            extra = sorted(set(data) - set(properties))
            if extra:
                raise ContractError(f"{path}: 허용되지 않은 키 {extra}")
        for key, value in data.items():
            child = properties.get(key)
            if child:
                validate_schema(value, child, f"{path}.{key}")
            elif isinstance(schema.get("additionalProperties"), dict):
                validate_schema(value, schema["additionalProperties"], f"{path}.{key}")

    if isinstance(data, list):
        minimum = schema.get("minItems")
        if minimum is not None and len(data) < minimum:
            raise ContractError(f"{path}: 항목이 최소 {minimum}개 필요합니다.")
        item_schema = schema.get("items")
        if item_schema:
            for index, item in enumerate(data):
                validate_schema(item, item_schema, f"{path}[{index}]")

    if isinstance(data, (int, float)) and not isinstance(data, bool):
        if "minimum" in schema and data < schema["minimum"]:
            raise ContractError(f"{path}: 최솟값은 {schema['minimum']}입니다.")
        if "maximum" in schema and data > schema["maximum"]:
            raise ContractError(f"{path}: 최댓값은 {schema['maximum']}입니다.")

    if isinstance(data, str) and "minLength" in schema:
        if len(data) < schema["minLength"]:
            raise ContractError(f"{path}: 최소 {schema['minLength']}자여야 합니다.")


def validate_stage(
    stage: str,
    data: dict[str, Any],
    schema_path: Path,
    *,
    analysis: dict[str, Any] | None = None,
    brief: dict[str, Any] | None = None,
    narration: dict[str, Any] | None = None,
    expected_reviewer: str | None = None,
    content: str | None = None,
) -> None:
    validate_schema(data, load_schema(schema_path))
    if stage == "analysis":
        ids = [item["evidence_id"] for item in data["evidence"]]
        if len(ids) != len(set(ids)):
            raise ContractError("analysis: evidence_id가 중복되었습니다.")
        if content is not None:
            normalized_content = _normalize_text(content)
            for item in data["evidence"]:
                excerpt = _normalize_text(item["source_excerpt"])
                if excerpt not in normalized_content:
                    raise ContractError(
                        "analysis: source_excerpt가 제공된 content.md 원문과 일치하지 "
                        f"않습니다 ({item['evidence_id']})."
                    )
    elif stage == "narration":
        if brief and data["duration_seconds"] != brief["target_duration_seconds"]:
            raise ContractError("narration: 목표 길이가 brief.json과 일치하지 않습니다.")
        _validate_timing(data["lines"], data["duration_seconds"], "narration")
        valid_ids = {
            item["evidence_id"] for item in (analysis or {}).get("evidence", [])
        }
        used_ids = {
            evidence_id
            for line in data["lines"]
            for evidence_id in line["evidence_ids"]
        }
        unknown = sorted(used_ids - valid_ids)
        if unknown:
            raise ContractError(f"narration: 알 수 없는 근거 ID {unknown}")
        _validate_narration_consistency(data)
    elif stage == "storyboard":
        scenes = data["scenes"]
        target_duration = (
            narration["duration_seconds"]
            if narration is not None
            else scenes[-1]["end"]
        )
        _validate_timing(scenes, target_duration, "storyboard")
        if scenes[0]["start"] != 0:
            raise ContractError("storyboard: 첫 장면은 0초에 시작해야 합니다.")
        if brief and target_duration != brief["target_duration_seconds"]:
            raise ContractError("storyboard: 목표 길이가 brief.json과 일치하지 않습니다.")
        if scenes[0]["end"] > 3:
            raise ContractError("storyboard: 첫 장면은 3초 안에 끝나 훅을 제시해야 합니다.")
        required = ("no text", "no logo", "no watermark")
        for scene in scenes:
            duration = float(scene["end"]) - float(scene["start"])
            if not 2 <= duration <= 4:
                raise ContractError(
                    f"storyboard {scene['scene_id']}: 장면 길이는 2~4초여야 합니다."
                )
            lowered = scene["video_prompt"].lower()
            missing = [phrase for phrase in required if phrase not in lowered]
            if missing:
                raise ContractError(
                    f"storyboard {scene['scene_id']}: 프롬프트 금지어 지시 누락 {missing}"
                )
        if narration is not None:
            _validate_storyboard_narration(scenes, narration["lines"])
    elif stage == "review":
        if expected_reviewer and data["reviewer"] != expected_reviewer:
            raise ContractError(
                f"review: reviewer는 {expected_reviewer!r}이어야 합니다."
            )
        issues = data["critical_issues"]
        if data["pass"] and issues:
            raise ContractError("review: pass=true인데 수정 이슈가 남아 있습니다.")
        if not data["pass"] and not any(
            issue["severity"] in {"critical", "major"} for issue in issues
        ):
            raise ContractError(
                "review: pass=false이면 critical 또는 major 이슈가 하나 이상 필요합니다."
            )


def _validate_timing(
    items: list[dict[str, Any]], duration: float, label: str
) -> None:
    previous_end = 0.0
    for index, item in enumerate(items):
        start, end = float(item["start"]), float(item["end"])
        if end <= start:
            raise ContractError(f"{label}[{index}]: 종료 시간이 시작 시간보다 커야 합니다.")
        if abs(start - previous_end) > 0.01:
            raise ContractError(
                f"{label}[{index}]: 시간 구간이 앞 항목과 연속되어야 합니다."
            )
        previous_end = end
    if abs(previous_end - float(duration)) > 0.01:
        raise ContractError(f"{label}: 마지막 종료 시간이 전체 길이와 일치해야 합니다.")


def _validate_narration_consistency(data: dict[str, Any]) -> None:
    lines = data["lines"]
    for index, line in enumerate(lines):
        duration = float(line["end"]) - float(line["start"])
        if not 2 <= duration <= 4:
            raise ContractError(
                f"narration[{index}]: 시간 구간은 2~4초여야 합니다."
            )
    joined = " ".join(line["text"] for line in lines)
    if _normalize_text(data["full_text"]) != _normalize_text(joined):
        raise ContractError("narration: full_text는 시간 구간별 text를 순서대로 합친 값이어야 합니다.")
    if _normalize_text(data["hook"]) != _normalize_text(lines[0]["text"]):
        raise ContractError("narration: hook은 첫 번째 내레이션 구간과 일치해야 합니다.")
    if float(lines[0]["end"]) > 3:
        raise ContractError("narration: 첫 내레이션 구간은 3초 안에 훅을 제시해야 합니다.")
    if _normalize_text(data["ending"]) != _normalize_text(lines[-1]["text"]):
        raise ContractError("narration: ending은 마지막 내레이션 구간과 일치해야 합니다.")


def _validate_storyboard_narration(
    scenes: list[dict[str, Any]], narration_lines: list[dict[str, Any]]
) -> None:
    if len(scenes) != len(narration_lines):
        raise ContractError("storyboard: 장면 수는 내레이션 시간 구간 수와 일치해야 합니다.")
    for scene, line in zip(scenes, narration_lines, strict=True):
        if abs(float(scene["start"]) - float(line["start"])) > 0.01 or abs(
            float(scene["end"]) - float(line["end"])
        ) > 0.01:
            raise ContractError(
                f"storyboard {scene['scene_id']}: 내레이션 구간의 시작·종료 시간과 일치해야 합니다."
            )
        if _normalize_text(scene["narration"]) != _normalize_text(line["text"]):
            raise ContractError(
                f"storyboard {scene['scene_id']}: 내레이션 문구가 해당 시간 구간과 일치하지 않습니다."
            )


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()

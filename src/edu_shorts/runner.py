from __future__ import annotations

import json
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol


class Runner(Protocol):
    def run(
        self,
        *,
        role: str,
        prompt: str,
        schema_path: Path,
        output_path: Path,
    ) -> dict[str, Any]: ...


@dataclass
class CodexCliRunner:
    project_root: Path
    executable: str = "codex"
    timeout_seconds: int = 900

    def __post_init__(self) -> None:
        if shutil.which(self.executable) is None:
            raise RuntimeError(
                "Codex CLI를 찾을 수 없습니다. Codex CLI를 설치·로그인하거나 "
                "--runner fake로 구조를 시험하세요."
            )

    def run(
        self,
        *,
        role: str,
        prompt: str,
        schema_path: Path,
        output_path: Path,
    ) -> dict[str, Any]:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        command = [
            self.executable,
            "exec",
            "--ephemeral",
            "--sandbox",
            "read-only",
            "--cd",
            str(self.project_root),
            "--skip-git-repo-check",
            "--output-schema",
            str(schema_path),
            "--output-last-message",
            str(output_path),
            "-",
        ]
        completed = subprocess.run(
            command,
            input=prompt,
            text=True,
            capture_output=True,
            timeout=self.timeout_seconds,
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError(
                f"{role} 실행 실패(exit={completed.returncode}): "
                f"{completed.stderr.strip()[-1500:]}"
            )
        try:
            return json.loads(output_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"{role}가 유효한 JSON을 만들지 못했습니다: {exc}") from exc


class FakeRunner:
    """Deterministic local runner for smoke tests; not for content production."""

    def run(
        self,
        *,
        role: str,
        prompt: str,
        schema_path: Path,
        output_path: Path,
    ) -> dict[str, Any]:
        del schema_path
        duration = _target_duration_from_prompt(prompt)
        if role == "content_analyst":
            result = {
                "title": "샘플 교육 콘텐츠",
                "core_question": "이 현상은 어떤 과정으로 일어날까요?",
                "key_concept": "자료에 제시된 핵심 개념",
                "hook_candidates": ["눈앞에서 결과가 빠르게 바뀌는 장면"],
                "evidence": [
                    {
                        "evidence_id": "E1",
                        "claim": "입력 자료에 제시된 첫 번째 핵심 내용",
                        "source_excerpt": _source_excerpt_from_prompt(prompt),
                        "visualizable": True,
                    }
                ],
                "causal_chain": ["처음 상태", "과정", "결과"],
                "misconception_risks": [],
                "needs_verification": [],
            }
        elif role == "narrative_writer":
            texts = _fake_narration_texts()
            lines = []
            segment_duration = duration / len(texts)
            for index, text in enumerate(texts):
                lines.append(
                    {
                        "start": index * segment_duration,
                        "end": (index + 1) * segment_duration,
                        "text": text,
                        "evidence_ids": ["E1"],
                    }
                )
            result = {
                "title": "샘플 교육 콘텐츠",
                "hook": texts[0],
                "duration_seconds": duration,
                "lines": lines,
                "full_text": " ".join(texts),
                "ending": texts[-1],
            }
        elif role == "visual_director":
            scenes = []
            texts = _fake_narration_texts()
            segment_duration = duration / len(texts)
            for index, text in enumerate(texts):
                scenes.append(
                    {
                        "scene_id": f"S{index + 1}",
                        "start": index * segment_duration,
                        "end": (index + 1) * segment_duration,
                        "narration": text,
                        "core_action": "하나의 핵심 변화를 보여 줌",
                        "visual": "하나의 핵심 변화가 보이는 3D 교육 장면",
                        "camera": "부드럽게 전진하는 카메라",
                        "graphics": "핵심 경로를 보여 주는 발광선",
                        "video_prompt": (
                            "A single clear educational transformation, vertical 9:16, "
                            "cinematic 3D educational animation, smooth camera motion, "
                            "no text, no logo, no watermark"
                        ),
                        "subtitle": f"핵심 자막 {index + 1}",
                        "sfx": "부드러운 전환음",
                    }
                )
            result = {
                "aspect_ratio": "9:16",
                "style_bible": {
                    "visual_style": "cinematic 3D educational miniature",
                    "characters": "등장인물 없음",
                    "environment": "단순화된 교육용 공간",
                    "palette": "회색에서 파랑과 초록으로 변화",
                    "continuity": ["같은 재질", "같은 조명 방향"],
                },
                "scenes": scenes,
                "music_direction": "호기심에서 이해로 밝아지는 음악",
                "transition_direction": "의미 단위의 자연스러운 컷",
            }
        elif role in {"education_reviewer", "video_reviewer"}:
            reviewer = "education" if role == "education_reviewer" else "video"
            result = {
                "reviewer": reviewer,
                "pass": True,
                "score": 95,
                "summary": "샘플 실행 기준을 통과했습니다.",
                "metrics": {"quality": 95},
                "critical_issues": [],
                "user_confirmation": [],
            }
        else:
            raise ValueError(f"알 수 없는 역할: {role}")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return result


def _target_duration_from_prompt(prompt: str) -> float:
    """Read the production brief embedded by build_prompt for smoke-test output."""
    match = re.search(r"# 제작 조건\n(\{.*?\})\n\n# 교육 원자료", prompt, re.DOTALL)
    if not match:
        return 70
    try:
        duration = json.loads(match.group(1))["target_duration_seconds"]
    except (KeyError, TypeError, json.JSONDecodeError):
        return 70
    return float(duration)


def _source_excerpt_from_prompt(prompt: str) -> str:
    match = re.search(
        r"# 교육 원자료\n\n(.*?)(?:\n\n# 앞 단계 결과|\n\n# 이전 검수|\n\n# 출력|\Z)",
        prompt,
        re.DOTALL,
    )
    if not match:
        return "샘플 원자료"
    return match.group(1).strip()


def _fake_narration_texts() -> list[str]:
    return [
        "눈앞의 모습이 순식간에 달라졌습니다.",
        *[f"자료의 핵심 과정을 {index}번째로 살펴봅니다." for index in range(1, 24)],
        "도대체 어떤 과정이 숨어 있을까요?",
        "이 변화가 오늘 알아볼 핵심 개념입니다.",
    ]

from __future__ import annotations

import json
import tomllib
from pathlib import Path
from typing import Any


def agent_instructions(project_root: Path, filename: str) -> str:
    path = project_root / ".codex" / "agents" / filename
    with path.open("rb") as stream:
        return tomllib.load(stream)["developer_instructions"].strip()


def build_prompt(
    *,
    instructions: str,
    task: str,
    brief: dict[str, Any],
    content: str,
    inputs: dict[str, Any] | None = None,
    feedback: list[dict[str, Any]] | None = None,
) -> str:
    blocks = [
        "# 역할 지침",
        instructions,
        "# 이번 작업",
        task,
        "# 제작 조건",
        json.dumps(brief, ensure_ascii=False, indent=2),
        "# 교육 원자료",
        content,
    ]
    if inputs:
        blocks.extend(
            ["# 앞 단계 결과", json.dumps(inputs, ensure_ascii=False, indent=2)]
        )
    if feedback:
        blocks.extend(
            [
                "# 이전 검수에서 반드시 고칠 사항",
                json.dumps(feedback, ensure_ascii=False, indent=2),
            ]
        )
    blocks.extend(
        [
            "# 출력",
            "설명이나 Markdown 코드펜스 없이, 지정된 JSON 스키마에 맞는 JSON만 출력하라.",
        ]
    )
    return "\n\n".join(blocks)

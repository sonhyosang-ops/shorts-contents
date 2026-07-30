from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from openai import OpenAI


@dataclass
class OpenAIResponsesRunner:
    """Production runner for the server; credentials stay outside the repository."""

    model: str

    def __post_init__(self) -> None:
        if not self.model:
            raise RuntimeError("OPENAI_MODEL 환경변수를 설정하세요.")
        self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    def run(
        self,
        *,
        role: str,
        prompt: str,
        schema_path: Path,
        output_path: Path,
    ) -> dict[str, Any]:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        response = self.client.responses.create(
            model=self.model,
            input=prompt,
            text={
                "format": {
                    "type": "json_schema",
                    "name": role,
                    "strict": True,
                    "schema": schema,
                }
            },
        )
        try:
            result = json.loads(response.output_text)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"{role}가 유효한 JSON을 반환하지 않았습니다.") from exc
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        return result

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from .exporters import export_package
from .prompts import agent_instructions, build_prompt
from .runner import Runner
from .validators import validate_stage


STAGE_ORDER = {"analysis": 0, "narration": 1, "storyboard": 2}


class Pipeline:
    def __init__(
        self,
        project_root: Path,
        runner: Runner,
        *,
        max_revisions: int = 2,
    ) -> None:
        self.root = project_root
        self.runner = runner
        if max_revisions < 0:
            raise ValueError("max_revisions는 0 이상이어야 합니다.")
        self.max_revisions = max_revisions
        self.schemas = self.root / "schemas"
        self.output_dir: Path | None = None

    def run(self, slug: str) -> dict[str, Any]:
        project_dir = self.root / "projects" / slug
        input_dir = project_dir / "input"
        work_dir = _new_run_dir(project_dir / "work")
        output_dir = _new_run_dir(project_dir / "output")
        self.output_dir = output_dir
        brief = _read_json(input_dir / "brief.json")
        _validate_brief(brief)
        content = (input_dir / "content.md").read_text(encoding="utf-8").strip()
        if not content:
            raise ValueError("content.md가 비어 있습니다.")

        analysis: dict[str, Any] | None = None
        narration: dict[str, Any] | None = None
        storyboard: dict[str, Any] | None = None
        feedback: list[dict[str, Any]] = []
        restart_from = "analysis"
        reviews: dict[str, Any] = {}

        for revision in range(self.max_revisions + 1):
            if STAGE_ORDER[restart_from] <= STAGE_ORDER["analysis"]:
                analysis = self._run_stage(
                    role="content_analyst",
                    agent_file="content-analyst.toml",
                    stage="analysis",
                    task=(
                        "원자료에서 근거 ID, 핵심 개념, 핵심 질문, 인과관계, "
                        "훅 후보, 오개념 위험과 확인 필요 항목을 추출하라."
                    ),
                    brief=brief,
                    content=content,
                    inputs=None,
                    feedback=feedback,
                    schema_name="content-analysis.schema.json",
                    work_dir=work_dir,
                    revision=revision,
                    analysis=None,
                )
            assert analysis is not None

            if STAGE_ORDER[restart_from] <= STAGE_ORDER["narration"]:
                narration = self._run_stage(
                    role="narrative_writer",
                    agent_file="narrative-writer.toml",
                    stage="narration",
                    task=(
                        "분석 결과의 근거 ID를 유지하며 강한 도입-질문-원인과 "
                        "과정-변화-핵심 개념 구조의 60~75초 내레이션을 작성하라."
                    ),
                    brief=brief,
                    content=content,
                    inputs={"analysis": analysis},
                    feedback=feedback,
                    schema_name="narration.schema.json",
                    work_dir=work_dir,
                    revision=revision,
                    analysis=analysis,
                )
            assert narration is not None

            if STAGE_ORDER[restart_from] <= STAGE_ORDER["storyboard"]:
                storyboard = self._run_stage(
                    role="visual_director",
                    agent_file="visual-director.toml",
                    stage="storyboard",
                    task=(
                        "내레이션을 초 단위 장면으로 나누고 각 장면의 화면, "
                        "카메라, 그래픽, 무자막 영상 생성 프롬프트, 자막과 "
                        "음향 지시를 작성하라."
                    ),
                    brief=brief,
                    content=content,
                    inputs={"analysis": analysis, "narration": narration},
                    feedback=feedback,
                    schema_name="storyboard.schema.json",
                    work_dir=work_dir,
                    revision=revision,
                    analysis=analysis,
                )
            assert storyboard is not None

            reviews = self._run_reviews(
                brief=brief,
                content=content,
                analysis=analysis,
                narration=narration,
                storyboard=storyboard,
                work_dir=work_dir,
                revision=revision,
            )
            if all(review["pass"] for review in reviews.values()):
                status = "passed"
                attempts = revision
                break

            feedback = [
                issue
                for review in reviews.values()
                for issue in review["critical_issues"]
            ]
            if revision >= self.max_revisions:
                status = "needs_user_review"
                attempts = revision
                break
            targets = [issue["target_stage"] for issue in feedback]
            restart_from = min(targets, key=STAGE_ORDER.get) if targets else "storyboard"

        package = {
            "brief": brief,
            "analysis": analysis,
            "narration": narration,
            "storyboard": storyboard,
            "reviews": reviews,
            "status": status,
            "attempts": attempts,
        }
        export_package(package, output_dir)
        return package

    def _run_stage(
        self,
        *,
        role: str,
        agent_file: str,
        stage: str,
        task: str,
        brief: dict[str, Any],
        content: str,
        inputs: dict[str, Any] | None,
        feedback: list[dict[str, Any]],
        schema_name: str,
        work_dir: Path,
        revision: int,
        analysis: dict[str, Any] | None,
    ) -> dict[str, Any]:
        schema_path = self.schemas / schema_name
        attempt_path = work_dir / f"{stage}.attempt-{revision}.json"
        prompt = build_prompt(
            instructions=agent_instructions(self.root, agent_file),
            task=task,
            brief=brief,
            content=content,
            inputs=inputs,
            feedback=feedback,
        )
        result = self.runner.run(
            role=role,
            prompt=prompt,
            schema_path=schema_path,
            output_path=attempt_path,
        )
        validate_stage(
            stage,
            result,
            schema_path,
            analysis=analysis,
            brief=brief,
            narration=inputs.get("narration") if inputs else None,
            content=content,
        )
        return result

    def _run_reviews(
        self,
        *,
        brief: dict[str, Any],
        content: str,
        analysis: dict[str, Any],
        narration: dict[str, Any],
        storyboard: dict[str, Any],
        work_dir: Path,
        revision: int,
    ) -> dict[str, Any]:
        inputs = {
            "analysis": analysis,
            "narration": narration,
            "storyboard": storyboard,
        }
        definitions = {
            "education": (
                "education_reviewer",
                "education-reviewer.toml",
                "원자료 충실성, 근거, 학습자 적합성, 오개념을 검수하라.",
            ),
            "video": (
                "video_reviewer",
                "video-reviewer.toml",
                "구현 가능성, 훅, 장면 밀도, 화면 일치와 시각 일관성을 검수하라.",
            ),
        }

        def review_one(kind: str) -> tuple[str, dict[str, Any]]:
            role, agent_file, task = definitions[kind]
            output_path = work_dir / f"review-{kind}.attempt-{revision}.json"
            result = self.runner.run(
                role=role,
                prompt=build_prompt(
                    instructions=agent_instructions(self.root, agent_file),
                    task=task,
                    brief=brief,
                    content=content,
                    inputs=inputs,
                ),
                schema_path=self.schemas / "review.schema.json",
                output_path=output_path,
            )
            validate_stage(
                "review",
                result,
                self.schemas / "review.schema.json",
                expected_reviewer=kind,
            )
            return kind, result

        with ThreadPoolExecutor(max_workers=2) as executor:
            pairs = list(executor.map(review_one, definitions))
        return dict(pairs)


def _read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"필수 입력 파일이 없습니다: {path}") from exc


def _validate_brief(brief: dict[str, Any]) -> None:
    duration = brief.get("target_duration_seconds")
    if isinstance(duration, bool) or not isinstance(duration, (int, float)):
        raise ValueError("brief.json의 target_duration_seconds는 숫자여야 합니다.")
    if not 60 <= duration <= 75:
        raise ValueError("brief.json의 target_duration_seconds는 60~75초여야 합니다.")
    if brief.get("aspect_ratio") != "9:16":
        raise ValueError("brief.json의 aspect_ratio는 9:16이어야 합니다.")


def _new_run_dir(base_dir: Path) -> Path:
    runs_dir = base_dir / "runs"
    index = 1
    while True:
        run_dir = runs_dir / f"run-{index:03d}"
        try:
            run_dir.mkdir(parents=True)
            return run_dir
        except FileExistsError:
            index += 1

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .pipeline import Pipeline
from .runner import CodexCliRunner, FakeRunner


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(
        prog="edu-shorts",
        description="교육 원자료를 세로형 교육 쇼츠 제작 패키지로 변환합니다.",
    )
    root.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="edu-shorts-studio 프로젝트 루트",
    )
    commands = root.add_subparsers(dest="command", required=True)

    init = commands.add_parser("init", help="새 주제 작업 폴더를 만듭니다.")
    init.add_argument("--project", required=True, help="영문·숫자·하이픈 프로젝트명")
    init.add_argument("--title", required=True)
    init.add_argument("--audience", required=True)
    init.add_argument("--duration", type=int, default=70)

    run = commands.add_parser("run", help="제작 파이프라인을 실행합니다.")
    run.add_argument("--project", required=True)
    run.add_argument("--runner", choices=["codex", "fake"], default="codex")
    run.add_argument("--max-revisions", type=int, default=2)
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    project_root = args.root.resolve()
    if args.command == "init":
        _init_project(
            project_root,
            slug=args.project,
            title=args.title,
            audience=args.audience,
            duration=args.duration,
        )
        print(f"입력 폴더를 만들었습니다: projects/{args.project}/input")
        return 0

    runner = (
        FakeRunner()
        if args.runner == "fake"
        else CodexCliRunner(project_root=project_root)
    )
    pipeline = Pipeline(
        project_root,
        runner,
        max_revisions=args.max_revisions,
    )
    package = pipeline.run(args.project)
    output_path = pipeline.output_dir
    assert output_path is not None
    print(
        f"완료: status={package['status']}, "
        f"revisions={package['attempts']}, "
        f"output={output_path.relative_to(project_root) / 'final-package.md'}"
    )
    return 0


def _init_project(
    root: Path,
    *,
    slug: str,
    title: str,
    audience: str,
    duration: int,
) -> None:
    if not slug or any(character not in "abcdefghijklmnopqrstuvwxyz0123456789-" for character in slug):
        raise ValueError("--project는 영문 소문자, 숫자, 하이픈만 사용할 수 있습니다.")
    if not 60 <= duration <= 75:
        raise ValueError("--duration은 60~75초 범위여야 합니다.")
    project_dir = root / "projects" / slug
    input_dir = project_dir / "input"
    input_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "work").mkdir(exist_ok=True)
    (project_dir / "output").mkdir(exist_ok=True)
    brief_path = input_dir / "brief.json"
    content_path = input_dir / "content.md"
    if brief_path.exists() or content_path.exists():
        raise FileExistsError(f"이미 존재하는 프로젝트입니다: {slug}")
    brief = {
        "title": title,
        "audience": audience,
        "target_duration_seconds": duration,
        "language": "ko",
        "aspect_ratio": "9:16",
        "visual_style": "cinematic 3D educational animation",
        "source_policy": "provided_material_only",
    }
    brief_path.write_text(
        json.dumps(brief, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    content_path.write_text(
        "# 교육 원자료\n\n"
        "이곳에 검증된 교육 내용을 붙여 넣으세요.\n\n"
        "## 출처\n\n"
        "- 문서명 또는 URL:\n",
        encoding="utf-8",
    )

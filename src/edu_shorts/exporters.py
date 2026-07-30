from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def export_package(package: dict[str, Any], output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "final-package.json"
    md_path = output_dir / "final-package.md"
    json_path.write_text(
        json.dumps(package, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    md_path.write_text(_to_markdown(package), encoding="utf-8")
    return md_path, json_path


def _to_markdown(package: dict[str, Any]) -> str:
    brief = package["brief"]
    analysis = package["analysis"]
    narration = package["narration"]
    board = package["storyboard"]
    reviews = package["reviews"]
    lines = [
        f"# {brief['title']} 교육 쇼츠 제작 패키지",
        "",
        "## 제작 개요",
        "",
        f"- 학습 대상: {brief['audience']}",
        f"- 목표 길이: {brief['target_duration_seconds']}초",
        f"- 상태: {package['status']}",
        f"- 자동 수정 횟수: {package['attempts']}",
        "",
        "## 원자료 핵심 분석과 근거",
        "",
        f"- 핵심 질문: {analysis['core_question']}",
        f"- 핵심 개념: {analysis['key_concept']}",
        "",
        "| 근거 ID | 핵심 내용 | 원문 근거 | 시각화 |",
        "|---|---|---|---|",
    ]
    for item in analysis["evidence"]:
        lines.append(
            f"| {item['evidence_id']} | {_cell(item['claim'])} | "
            f"{_cell(item['source_excerpt'])} | "
            f"{'가능' if item['visualizable'] else '제한'} |"
        )
    lines.extend(["", "## 내레이션 전문", "", narration["full_text"], ""])
    lines.extend(
        [
            "## 초 단위 스토리보드",
            "",
            "| 시간 | 내레이션 | 핵심 행동 | 화면 | 카메라 | 그래픽 | 자막 | 음향 |",
            "|---|---|---|---|---|---|---|---|",
        ]
    )
    for scene in board["scenes"]:
        lines.append(
            f"| {scene['start']:g}~{scene['end']:g}초 | {_cell(scene['narration'])} | {_cell(scene['core_action'])} | "
            f"{_cell(scene['visual'])} | {_cell(scene['camera'])} | "
            f"{_cell(scene['graphics'])} | {_cell(scene['subtitle'])} | "
            f"{_cell(scene['sfx'])} |"
        )
    lines.extend(["", "## 장면별 영상 생성 프롬프트", ""])
    for scene in board["scenes"]:
        lines.extend(
            [
                f"### {scene['scene_id']} ({scene['start']:g}~{scene['end']:g}초)",
                "",
                "```text",
                scene["video_prompt"],
                "```",
                "",
            ]
        )
    lines.extend(["## 자막·화면 강조어", ""])
    for scene in board["scenes"]:
        lines.append(f"- {scene['scene_id']}: {scene['subtitle']}")
    lines.append("")
    style = board["style_bible"]
    lines.extend(
        [
            "## 음향·전환 지시",
            "",
            f"- 배경음악: {board['music_direction']}",
            f"- 장면 전환: {board['transition_direction']}",
            "",
            "## 스타일 바이블",
            "",
            f"- 시각 스타일: {style['visual_style']}",
            f"- 등장인물: {style['characters']}",
            f"- 환경: {style['environment']}",
            f"- 색상: {style['palette']}",
        ]
    )
    lines.extend(f"- 일관성: {item}" for item in style["continuity"])
    for key, title in (("education", "교육 검수"), ("video", "영상 검수")):
        review = reviews[key]
        lines.extend(
            [
                "",
                f"## {title}",
                "",
                f"- 판정: {'통과' if review['pass'] else '수정 필요'}",
                f"- 점수: {review['score']:g}",
                f"- 요약: {review['summary']}",
            ]
        )
        for issue in review["critical_issues"]:
            lines.append(
                f"- [{issue['severity']}/{issue['target_stage']}] "
                f"{issue['instruction']}"
            )
    confirmations = sorted(
        {
            item
            for review in reviews.values()
            for item in review["user_confirmation"]
        }
        | set(analysis["needs_verification"])
    )
    lines.extend(["", "## 사용자 확인 필요 항목", ""])
    lines.extend(
        [f"- {item}" for item in confirmations]
        if confirmations
        else ["- 없음"]
    )
    lines.append("")
    return "\n".join(lines)


def _cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", "<br>")

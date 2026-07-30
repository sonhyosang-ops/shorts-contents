from __future__ import annotations

from pathlib import Path


TEXT_EXTENSIONS = {".csv", ".json", ".md", ".rst", ".tsv", ".txt"}


def normalize_sources(sources: list[Path]) -> str:
    """Create evidence-preserving Markdown without inventing facts from a source."""
    entries: list[tuple[str, Path, str, str | None]] = []
    for index, path in enumerate(sources, start=1):
        source_id = f"S{index:03d}"
        text, warning = _extract(path)
        entries.append((source_id, path, text, warning))

    lines = ["# 교육 원자료", "", "## 원본 목록"]
    lines.extend(
        f"- {source_id} | {path.name} | {path.suffix.lstrip('.') or 'unknown'} | 위치 정보는 추출 결과 기준"
        for source_id, path, _, _ in entries
    )
    lines.extend(["", "## 추출 원문", ""])
    for source_id, path, text, _ in entries:
        lines.extend([f"### {source_id} — {path.name}", text or "[추출된 텍스트 없음]", ""])
    lines.extend(["## 시각 자료 설명", "- 자동 추출 과정에서는 원문에 없는 시각 해석을 추가하지 않음.", "", "## 자료 확인 필요"])
    warnings = [
        f"- {source_id} — {path.name}: {warning}"
        for source_id, path, _, warning in entries
        if warning
    ]
    lines.extend(warnings or ["- 없음"])
    return "\n".join(lines).strip() + "\n"


def _extract(path: Path) -> tuple[str, str | None]:
    if path.suffix.lower() in TEXT_EXTENSIONS:
        try:
            return path.read_text(encoding="utf-8"), None
        except UnicodeDecodeError:
            return path.read_text(encoding="utf-8", errors="replace"), "문자 인코딩 일부가 대체되었습니다."
    try:
        from markitdown import MarkItDown

        extracted = MarkItDown().convert(str(path)).text_content.strip()
        if extracted:
            return extracted, "자동 추출 결과입니다. 슬라이드·페이지·도표 위치와 OCR 결과를 검토하세요."
        return "", "추출된 텍스트가 없습니다. 원본을 확인하세요."
    except ImportError:
        return "", "이 형식의 자동 추출 도구가 배포 환경에 설치되지 않았습니다."
    except Exception as exc:
        return "", f"자동 추출에 실패했습니다 ({type(exc).__name__}). 원본을 확인하세요."

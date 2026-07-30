---
name: source-to-content-md
description: 교육자료·교안·첨부파일·URL을 쇼츠 제작용 근거 보존 `content.md`로 정규화한다. PPTX, PDF, DOCX, HWP/HWPX, XLSX/CSV, Markdown·텍스트, 이미지, 오디오·영상 또는 여러 파일을 원자료로 받아 추출·OCR·전사를 수행하고, 불확실한 내용은 `자료 확인 필요`로 남겨야 할 때 사용한다.
---

# Source to Content Markdown

원본은 `projects/<slug>/input/source/`에 보존하고 `content.md`만 새로 만든다. 기존 원본·산출물은 덮어쓰지 않는다.

1. 파일 목록, 형식, 읽기 가능 여부를 기록한다. 비어 있거나 암호화됐거나 손상된 파일은 건너뛰지 말고 확인 항목으로 남긴다.
2. 형식별 처리법은 [references/source-handling.md](references/source-handling.md)에서 해당 형식만 읽고 따른다.
3. 사실·수치·날짜·인과관계는 원문의 인용 가능한 문장만 옮긴다. 요약·추론·OCR 불확실성·이미지 해석은 원문 인용과 섞지 않는다.
4. 결과를 아래 구조로 `projects/<slug>/input/content.md`에 UTF-8 Markdown으로 저장한다.

```markdown
# 교육 원자료

## 원본 목록
- S001 | 파일명 또는 URL | 형식 | 페이지·슬라이드·시각 범위

## 추출 원문

### S001 — 위치
원문 그대로

## 시각 자료 설명
- S001 — 위치: 직접 관찰 가능한 요소만 기술

## 자료 확인 필요
- S001 — 위치: 읽을 수 없거나 모호한 요소와 이유
```

5. 인용 블록마다 `S001` 같은 원본 ID와 페이지·슬라이드·시각 위치를 붙인다. 보이지 않는 텍스트, 그래프의 값, 이미지의 인과관계는 추정하지 않는다.
6. 마무리 전에 `content.md`의 모든 인용문이 추출된 원본으로 되돌아갈 수 있는지 확인한다. 원자료 밖의 설명은 삭제하거나 `자료 확인 필요`로 이동한다.

여러 자료가 상충하면 둘 다 보존하고 어느 쪽도 정답으로 합치지 않는다. 이후 `create-edu-short` 단계는 이 `content.md`만 교육 근거로 사용한다.

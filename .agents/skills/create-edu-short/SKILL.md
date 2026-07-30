---
name: create-edu-short
description: 교육 원자료를 근거 기반 60~75초 세로형 교육 쇼츠 제작 패키지로 변환한다. 교육 콘텐츠, 수업 자료, 교과 개념, 역사·과학·사회·기술·환경 내용을 짧은 영상의 내레이션·스토리보드·장면별 생성 프롬프트·자막·음향 지시로 만들거나 검수·수정할 때 사용한다.
---

# 교육 쇼츠 제작

다음 순서로 작업한다.

1. 입력 폴더의 `brief.json`과 `content.md`를 읽는다.
2. `references/sample-video-grammar.md`를 읽고 영상 문법을 고정한다.
3. `content_analyst` 역할로 근거 ID, 핵심 개념, 인과관계, 시각화 요소,
   오개념 위험, 확인 필요 항목을 작성한다.
4. `references/narration-rules.md`를 읽고 `narrative_writer` 역할로
   60~75초 내레이션을 작성한다.
5. `visual_director` 역할로 초 단위 장면과 장면별 무자막 영상 생성
   프롬프트를 작성한다.
6. `references/review-rubric.md`를 읽고 `education_reviewer`와
   `video_reviewer`를 서로 독립적으로 병렬 실행한다.
7. 불합격이면 검수 결과의 `target_stage` 중 가장 이른 단계부터
   후속 단계를 다시 만든다. 자동 수정은 최대 2회로 제한한다.
8. 통과하면 `references/output-contract.md`에 따라 Markdown과 JSON
   최종 패키지를 저장한다.

하네스 실행이 가능한 환경에서는 다음 명령을 우선 사용한다.

```bash
python -m edu_shorts run --project <slug>
```

하네스를 사용하지 못하면 같은 단계와 JSON 스키마를 수동으로
준수한다.

## 절대 규칙

- 원자료 밖 사실을 추가하지 않는다.
- 근거 없는 수치·날짜·인과관계는 `자료 확인 필요`로 표시한다.
- 내레이션의 주요 문장에는 분석 단계의 `evidence_id`를 연결한다.
- 첫 3초 안에 결과·변화·질문 중 가장 강한 장면을 배치한다.
- 한 장면에는 핵심 행동을 하나만 둔다.
- 영상 프롬프트에서 한글 문장을 생성하지 않는다.
- 영상 프롬프트마다 `no text, no logo, no watermark`를 넣는다.
- 검수자가 지적하지 않은 원자료 사실을 수정 루프에서 바꾸지 않는다.
- 두 차례 수정 후에도 통과하지 못하면 자동 추정을 멈추고 사용자
  확인 항목을 명시한다.

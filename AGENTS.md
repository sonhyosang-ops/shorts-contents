# 교육 쇼츠 제작 프로젝트 지침

## 목표

교육 원자료를 근거로 60~75초 세로형 교육 쇼츠 제작 패키지를 만든다.
최종 패키지는 콘텐츠 분석, 내레이션, 스토리보드, 장면별 영상 생성
프롬프트, 자막·음향 지시, 검수 보고서를 포함한다.

## 필수 작업 방식

- 입력이 `content.md`가 아닌 원자료 파일이면 먼저 `.agents/skills/source-to-content-md/SKILL.md`를 사용해 `projects/<slug>/input/content.md`로 정규화한다.
- `.agents/skills/create-edu-short/SKILL.md`를 사용한다.
- 원자료에 없는 사실을 추가하지 않는다.
- 근거가 없거나 상충하는 내용은 `자료 확인 필요`로 표시한다.
- 첫 3초는 가장 강한 결과·변화·질문 중 하나로 설계한다.
- 영상 생성 프롬프트에는 한글 문장, 로고, 워터마크를 넣지 않는다.
- 한 장면에는 핵심 행동을 하나만 둔다.
- 교육 검수와 영상 검수는 서로 독립적으로 수행한다.
- 검수 실패 시 전체가 아니라 지목된 단계부터 다시 만든다.
- 자동 수정은 최대 2회까지만 허용한다.
- 두 차례 수정 후에도 치명적 문제가 남으면 `사용자 확인 필요`로 종료한다.

## 역할 분담

- `content_analyst`: 핵심 개념, 인과관계, 근거, 오개념 위험을 추출한다.
- `narrative_writer`: 근거 ID를 유지하며 60~75초 내레이션을 작성한다.
- `visual_director`: 2~4초 중심 장면과 영상 생성 프롬프트를 설계한다.
- `education_reviewer`: 사실성, 학습자 적합성, 오개념을 검수한다.
- `video_reviewer`: 장면 구현 가능성, 일관성, 정보 밀도를 검수한다.

## 파일 규칙

- 사용자 원자료는 `projects/<slug>/input/`에 보존한다.
- 중간 JSON은 `projects/<slug>/work/`에 저장한다.
- 최종 결과는 `projects/<slug>/output/`에 저장한다.
- 단계별 JSON은 `schemas/`의 해당 스키마를 따라야 한다.
- 원자료와 기존 산출물을 덮어쓰지 않는다.

## 검증

변경 후 다음 명령을 실행한다.

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
PYTHONPATH=src python3 -m edu_shorts --help
```

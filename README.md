# Edu Shorts Studio

교육 콘텐츠를 샘플 영상과 같은 설명 문법으로 바꾸는 Codex 기반 제작
프로젝트입니다. 특정 주제에 묶이지 않고 역사·과학·사회·기술·환경
콘텐츠를 다음 흐름으로 변환합니다.

> 강한 도입 → 핵심 질문 → 원인·과정 → 보이지 않는 원리 시각화 →
> 해결·변화 → 핵심 개념 정리

## 구성

- 프로젝트 전용 Skill: `.agents/skills/create-edu-short/`
- 역할별 Codex 에이전트: `.codex/agents/`
- 실행 하네스: `src/edu_shorts/`
- 단계별 출력 계약: `schemas/`
- 주제별 작업 공간: `projects/`

교육 검수와 영상 검수는 병렬로 실행됩니다. 검수에서 문제가 발견되면
하네스가 지목된 단계부터 다시 실행하며, 자동 수정은 최대 2회로
제한됩니다.

## 시작하기

Python 3.11 이상과 로그인된 Codex CLI가 필요합니다.

```bash
cd edu-shorts-studio
python3 -m pip install -e .
python3 -m edu_shorts init \
  --project water-cycle \
  --title "물의 순환" \
  --audience "초등학교 5학년"
```

생성된 `projects/water-cycle/input/content.md`에 검증된 교육 내용을 넣고
실행합니다.

PPTX·PDF·문서·표·이미지·음성·영상처럼 `content.md`가 아닌 원자료는 먼저
`projects/water-cycle/input/source/`에 보존한 뒤, 다음처럼 원자료 정규화 스킬을
실행합니다. 이 단계는 원문과 출처 위치를 유지한 `content.md`를 만들고, 판독이
불확실한 내용은 `자료 확인 필요`로 남깁니다.

```text
Use $source-to-content-md to normalize every file in
projects/water-cycle/input/source/ into projects/water-cycle/input/content.md.
Keep source IDs and slide/page/timestamp locations, and do not infer missing facts.
```

```bash
python3 -m edu_shorts run --project water-cycle
```

완료 후 새 실행 번호가 붙은 폴더에서 다음 파일을 확인합니다. 이전 실행
산출물은 보존되며 덮어쓰지 않습니다.

- `output/runs/run-001/final-package.md`: 사람이 읽고 편집할 최종 제작안
- `output/runs/run-001/final-package.json`: 후속 자동화용 구조화 결과
- `work/runs/run-001/`: 단계별 분석·대본·스토리보드·검수 기록

Codex 호출 없이 구조만 시험하려면 다음을 실행합니다.

```bash
python3 -m edu_shorts run --project water-cycle --runner fake
```

## 새 작업을 Codex에 지시하는 문장

```text
이 저장소의 create-edu-short Skill과 역할 에이전트를 사용해
projects/<프로젝트명>/input의 교육자료를 60~75초 세로형 교육 쇼츠
제작 패키지로 변환해 줘. 교육 검수와 영상 검수는 병렬로 수행하고,
불합격이면 지목된 단계만 최대 2회 수정해. 최종 결과는 output에 저장해.
```

## 현재 범위

첫 버전은 영상 파일 자체가 아니라 내레이션, 초 단위 스토리보드,
장면별 생성 프롬프트, 자막·음향 지시와 검수 보고서까지 만듭니다.
Sora·Veo·Kling 또는 음성·편집 API 연결은 이 제작 패키지의 품질을
확인한 다음 확장하는 것을 전제로 합니다.

## 웹 앱 배포

`web/`은 Vercel에 배포하는 업로드·작업 조회 화면이고, `render.yaml`은
Render API와 작업 워커를 정의합니다. Supabase SQL Editor에서
`supabase/migrations/001_edu_shorts.sql`을 실행하세요. Storage에서 private
bucket `short-sources`, `short-results`를 만든 뒤 이 SQL로 원본 업로드 접근 정책을 적용합니다.

Vercel에는 `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`,
`VITE_RENDER_API_URL`을, Render에는 `SUPABASE_URL`,
`SUPABASE_SERVICE_ROLE_KEY`, `OPENAI_API_KEY`, `OPENAI_MODEL`, `WEB_ORIGIN`을
설정합니다. API 키는 서버 환경변수에만 보관합니다.

# 배포 체크포인트

마지막 갱신: 2026-07-30

## 완료

- GitHub: `sonhyosang-ops/shorts-contents`의 `main` 브랜치에 프로젝트를 푸시했다.
- Supabase 프로젝트: `antigravity-project-planner` (`gyswkfahujjrnaftxkni`)
- Supabase Storage: private bucket `short-sources`, `short-results`를 만들었다.
- Supabase Database: `supabase/migrations/001_edu_shorts.sql`을 적용했다.
  - `short_jobs` 테이블
  - 사용자별 원본 업로드·조회 정책
  - 작업을 가져오는 `claim_next_short_job()` 함수

## 다음 작업: Render Blueprint 배포

1. Render에서 GitHub 저장소 `sonhyosang-ops/shorts-contents`를 Blueprint로 연결한다.
2. 루트의 `render.yaml`로 `edu-shorts-api`, `edu-shorts-worker`를 만든다.
3. 다음 환경변수를 Render에 직접 입력한다. 값은 GitHub에 기록하지 않는다.

| 서비스 | 환경변수 |
|---|---|
| API·워커 | `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` |
| 워커 | `OPENAI_API_KEY`, `OPENAI_MODEL` |
| API | `WEB_ORIGIN` |

4. API가 Live가 되면 `/health`에서 `{"status":"ok"}`를 확인한다.
5. 이후 Vercel을 배포하고 실제 Vercel 주소를 `WEB_ORIGIN`과 Supabase Auth의 Site URL·Redirect URL에 설정한다.

## 보안

`SUPABASE_SERVICE_ROLE_KEY`와 `OPENAI_API_KEY`는 Render 환경변수에만 보관한다.

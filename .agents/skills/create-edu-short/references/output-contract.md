# 최종 출력 계약

최종 Markdown은 다음 순서를 따른다.

1. 제작 개요
2. 원자료 핵심 분석과 근거
3. 60~75초 내레이션 전문
4. 초 단위 스토리보드
5. 장면별 영상 생성 프롬프트
6. 자막·화면 강조어
7. 배경음악·효과음·전환 지시
8. 스타일 바이블
9. 교육 검수 결과
10. 영상 검수 결과
11. 사용자 확인 필요 항목

최종 JSON은 다음 최상위 키를 포함한다.

```json
{
  "brief": {},
  "analysis": {},
  "narration": {},
  "storyboard": {},
  "reviews": {
    "education": {},
    "video": {}
  },
  "status": "passed 또는 needs_user_review",
  "attempts": 0
}
```

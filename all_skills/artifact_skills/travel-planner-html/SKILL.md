# travel-planner-html

여행 계획을 **공유 가능한 단일 HTML 파일**로 생성하는 스킬.  
탭형 일정 타임라인 + Leaflet.js 인터랙티브 지도 + 체크리스트를 한 파일에 담는다.

---

## 트리거

- "여행 계획 HTML로 만들어줘" / "공유용 여행 계획 파일"
- 여행 계획 대화 후 "이거 HTML로 뽑아줘"
- "여행 일정 시각화" / "지도 포함 여행 플래너"

---

## 출력

```
/mnt/user-data/outputs/{destination}_travel.html
```
외부 의존: Google Fonts CDN + Leaflet 1.9.4 CDN 2개뿐.

---

## 작업 순서

1. **데이터 수집** — 대화 컨텍스트 또는 웹 검색으로 여행 정보 확보
2. **데이터 정리** — `references/data-schema.md` 스키마에 맞춰 구조화
3. **HTML 생성** — `references/html-structure.md` 섹션 순서 준수
4. **지도 코드 삽입** — `scripts/map-init.js` 복사 후 ★ 표시 블록만 교체
5. **스타일 삽입** — `assets/styles.css` 전체를 `<style>` 블록에 인라인으로 포함
6. **검증** — `references/gotchas.md` 완성 체크리스트 확인
7. **저장 & 공유** — `/mnt/user-data/outputs/` 저장 후 `present_files` 호출

---

## 참조 파일 목록

| 파일 | 읽는 시점 | 내용 |
|------|-----------|------|
| `references/data-schema.md`    | 2단계 | 헤더·days·events·places·checklist 데이터 구조 정의 |
| `references/html-structure.md` | 3단계 | HTML 섹션 순서 및 각 섹션 마크업 패턴 |
| `references/map-guide.md`      | 4단계 | Leaflet 설정 상수, zoom 레벨 가이드, 지도 주의사항 |
| `references/gotchas.md`        | 6단계 | 자주 하는 실수 목록 + 완성 파일 체크리스트 |
| `assets/styles.css`            | 5단계 | 디자인 토큰 + 전체 인라인 CSS (수정 금지) |
| `scripts/map-init.js`          | 4단계 | Leaflet 초기화 JS 완성본 (★ 블록만 교체해서 사용) |

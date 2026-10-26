# 주의사항 & 완성 체크리스트

---

## 자주 하는 실수

### 지도
| 실수 | 올바른 방법 |
|------|-------------|
| 좌표를 기억에서 적음 | 웹 검색 또는 Maps URL로 확인 (`map-guide.md` 참조) |
| places[] 순서 뒤죽박죽 | day별 방문 순서대로 정렬 필수 |
| `className:''` 누락 | divIcon에 항상 포함 |
| pts.length 미체크 | 장소 1개 day는 polyline 생성 건너뜀 |
| routes 키 없는 day 접근 | `if (!routes[day]) return` 가드 |

### HTML 구조
| 실수 | 올바른 방법 |
|------|-------------|
| 탭 인덱스 ≠ 패널 id | `show(0)` ↔ `id="d0"`, `show(1)` ↔ `id="d1"` … 일치 |
| tip=null인데 태그 출력 | tip이 null이면 `<div class="event-tip">` 전체 생략 |
| 탭 수 ≠ 패널 수 | days 배열 길이 = 탭 수 = 패널 수 항상 같아야 함 |
| 특수문자 raw 사용 | `&` → `&amp;`, `<` → `&lt;` |
| script 위치 잘못됨 | `</body>` 바로 앞 — Leaflet은 `<head>`에서 미리 로드 |

---

## 완성 파일 체크리스트

저장 전 아래를 모두 확인한다.

- [ ] 탭 수 = day-panel 수 = days 배열 길이
- [ ] 첫 번째 탭만 `class="tab active"`, 첫 번째 패널만 `class="day-panel active"`
- [ ] `places[]` 좌표 전부 웹 검색으로 확인
- [ ] `places[]` day별 방문 순서대로 정렬
- [ ] `filterDay`에서 없는 day 접근 가드 처리
- [ ] `L.map('map').setView([lat, lng], zoom)` center/zoom 값 적절
- [ ] `<script src="leaflet.js">` 가 `<head>` 안에 위치
- [ ] `<script>` 블록이 `</body>` 바로 앞에 위치
- [ ] `present_files` 호출 완료

# HTML 구조

섹션 순서를 반드시 지킨다.

```
1. <head>          CDN 로드 + <style> 인라인 CSS
2. <header>        히어로 배너
3. .legend-bar     이벤트 타입 범례
4. .tabs-wrap      스티키 탭 바 (sticky top:0)
5. .content        탭 패널 · 타임라인
6. .map-section    Leaflet 인터랙티브 지도
7. .footer-note    체크리스트
8. <script>        탭 JS + 지도 JS (body 최하단)
```

---

## 1. `<head>`

```html
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@400;600;700
  &family=Noto+Sans+KR:wght@300;400;500;700
  &family=DM+Serif+Display:ital@0;1&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
  /* assets/styles.css 전체를 여기에 인라인으로 붙여넣는다 */
</style>
```

---

## 2. 히어로 배너

```html
<header class="hero">
  <p class="hero-label">{hero_label}</p>
  <h1>{destination}<br><em>{subtitle}</em></h1>
  <p class="hero-sub">{date_range} · {party_desc}</p>
  <div class="hero-chips">
    <span class="hero-chip">🍣 스시 오마카세</span>
    <!-- hero_chips 반복 -->
  </div>
</header>
```

특수문자 이스케이프: `&` → `&amp;`

---

## 3. 범례

```html
<div class="legend-bar">
  <div class="legend-item"><div class="legend-dot" style="background:#e8930a"></div>식도락</div>
  <div class="legend-item"><div class="legend-dot" style="background:#2a7d9e"></div>온천</div>
  <div class="legend-item"><div class="legend-dot" style="background:#2a7d6b"></div>관광</div>
  <div class="legend-item"><div class="legend-dot" style="background:#888580"></div>이동</div>
  <div class="legend-item"><div class="legend-dot" style="background:#6b52a8"></div>숙소</div>
</div>
```

---

## 4~5. 탭 바 + 타임라인 패널

```html
<div class="tabs-wrap">
  <div class="tabs">
    <button class="tab active" onclick="show(0)">
      <span class="tab-date">{date}</span>Day 1
    </button>
    <!-- days 반복, 인덱스 0부터 -->
  </div>
</div>

<div class="content">
  <!-- days 반복 — 첫 번째만 class="day-panel active", 나머지는 class="day-panel" -->
  <div class="day-panel active" id="d0">
    <div class="day-header">
      <h2>{title}</h2>
      <p>{subtitle}</p>
    </div>

    <div class="summary-bar">
      <div class="sum-chip"><strong>{label}</strong>{value}</div>
    </div>

    <div class="timeline">
      <!-- events 반복 -->
      <div class="event">
        <div class="event-dot dot-{type}"></div>
        <div class="event-card">
          <div class="event-top">
            <span class="event-time">{time}</span>
            <span class="event-name">{name}</span>
            <span class="event-badge badge-{type}">{type_label}</span>
          </div>
          <div class="event-desc">{desc}</div>
          <!-- tip != null 일 때만 출력 -->
          <div class="event-tip">{tip}</div>
        </div>
      </div>
    </div>
  </div>
</div>
```

`type_label` 매핑: food→식도락, onsen→온천, sight→관광, drive→이동, hotel→숙소

---

## 6. 지도 섹션

```html
<div class="map-section">
  <div class="map-header">
    <h2>전체 동선 지도</h2>
    <p>마커 클릭 → 상세 정보 · Day 버튼으로 해당 날 동선만 확인</p>
    <div class="day-filter">
      <button class="filter-btn active" onclick="filterDay(this,'all')">전체 보기</button>
      <button class="filter-btn" onclick="filterDay(this,1)">Day 1</button>
      <!-- days 반복 -->
    </div>
  </div>
  <div id="map"></div>
  <div class="map-day-legend">
    <!-- DAY_COLORS 반복 -->
    <div class="mdl-item">
      <div class="mdl-line" style="background:#c8622a"></div>
      <span>Day 1 · 4/25</span>
    </div>
  </div>
</div>
```

지도 JS는 `scripts/map-init.js` 참조. `places[]` 등 데이터만 교체하면 된다.

---

## 7. 체크리스트

```html
<div class="footer-note">
  <div class="note-card">
    <h3>여행 전 필수 체크리스트</h3>
    <div class="note-grid">
      <!-- checklist 반복 -->
      <div class="note-item">
        <strong>{title}</strong>
        <!-- items 있으면 <ul><li> / text 있으면 <p> -->
        <ul><li>{item}</li></ul>
      </div>
    </div>
  </div>
</div>
```

---

## 8. `<script>` (body 최하단)

```html
<script>
// 탭 전환
function show(i) {
  document.querySelectorAll('.tab').forEach((t,j) => t.classList.toggle('active', i===j));
  document.querySelectorAll('.day-panel').forEach((p,j) => p.classList.toggle('active', i===j));
  document.querySelector('.content').scrollIntoView({ behavior:'smooth', block:'start' });
}

// 지도 — scripts/map-init.js 전체를 여기에 붙여넣고 데이터만 교체
</script>
```

`<script>` 위치: `</body>` 바로 앞.  
Leaflet은 `<head>`에서 이미 로드됐으므로 `L` 전역 객체 바로 사용 가능.

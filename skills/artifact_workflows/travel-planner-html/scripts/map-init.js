// ============================================================
// travel-planner-html — Leaflet 지도 초기화 템플릿
//
// 사용법:
//   1. ★ 표시된 "여행마다 교체" 블록만 수정한다.
//   2. 나머지 코드(makeIcon, markers 루프, filterDay 등)는 그대로 유지한다.
//   3. 이 전체 내용을 HTML의 <script> 블록 안에 붙여넣는다.
//      (탭 전환 함수 show(i) 바로 뒤에)
// ============================================================


// ══════════════════════════════════════════════════════════════
// ★ 여행마다 교체 (1) — 날짜별 색상 & 표시 문자열
// ══════════════════════════════════════════════════════════════
const DAY_COLORS = {
  1: '#c8622a',   // Day 1 — 주황
  2: '#2a7d9e',   // Day 2 — 청록
  3: '#2a7d6b',   // Day 3 — 녹색
  4: '#7c5cbf',   // Day 4 — 보라
  // Day가 더 있으면 추가: 5: '#b8943a'
};

const DAY_DATES = {
  1: '4/25 (금)',
  2: '4/26 (토)',
  3: '4/27 (일)',
  4: '4/28 (월)',
};


// ══════════════════════════════════════════════════════════════
// ★ 여행마다 교체 (2) — 장소 데이터
//
// 규칙:
//   - day 오름차순, 같은 day 안에서는 방문 순서대로 정렬
//     (순서가 틀리면 경로 선이 지그재그로 그려짐)
//   - lat/lng는 웹 검색으로 반드시 확인
//   - type 값: '식도락' | '관광' | '숙소/온천' | '숙소' | '이동'
// ══════════════════════════════════════════════════════════════
const places = [
  // Day 1
  { day:1, lat:37.9130, lng:139.0600, name:'니이가타 공항',               type:'이동',      desc:'렌터카 픽업 출발점. 국제면허증 필수.' },
  { day:1, lat:37.8985, lng:139.0300, name:'고시노헤기야 (헤기소바)',       type:'식도락',    desc:'니이가타 명물 헤기소바. 텐푸라 세트 추천.' },
  { day:1, lat:37.9160, lng:139.0719, name:'이마요츠카사 사케 양조장',      type:'관광',      desc:'영어 투어 + 사케 시음 ¥1,500.' },
  { day:1, lat:37.9144, lng:139.0393, name:'하쿠산 공원',                  type:'관광',      desc:'4월 말 튤립 만개. 강변 산책.' },
  { day:1, lat:37.7363, lng:138.8377, name:'이와무로 온센 후지야 ★4.2',    type:'숙소/온천', desc:'1박 료칸. 카이세키 + 노천탕.' },
  // Day 2
  { day:2, lat:37.6479, lng:138.7717, name:'테라도마리 어시장',             type:'식도락',    desc:'일본해 직송 해산물. 9시 전 도착 추천.' },
  { day:2, lat:37.9250, lng:139.0440, name:'니이가타항 (사도 페리)',        type:'관광',      desc:'제트포일 승선 (사도 선택 시).' },
  { day:2, lat:38.0817, lng:138.4383, name:'사도 섬 (선택)',               type:'관광',      desc:'제트포일 65분. 금산·타라이부네. 왕복 ¥5,000.' },
  { day:2, lat:37.9182, lng:139.0631, name:'스시 아라이 ★4.7',            type:'식도락',    desc:'오마카세 ¥18,000~28,000. 2~3주 전 예약 필수.' },
  { day:2, lat:37.9163, lng:139.0645, name:'도르미 인 니이가타',           type:'숙소',      desc:'시내 비즈니스호텔. 대욕장 + 무료 야식 라멘.' },
  // Day 3
  { day:3, lat:37.9206, lng:139.0440, name:'톤카츠 타로 (타레카츠동)',      type:'식도락',    desc:'니이가타 소울푸드. 수/목 휴무.' },
  { day:3, lat:37.8297, lng:139.1522, name:'키타문화관',                   type:'관광',      desc:'4월 말 250년 등나무꽃 절경. 화요일 휴관.' },
  { day:3, lat:37.9293, lng:139.1638, name:'니이가타 센베이 왕국',         type:'관광',      desc:'센베이 굽기 체험 ¥2,500. 목요일 휴관.' },
  { day:3, lat:37.8798, lng:139.3126, name:'시라타마노유 센케이 ★4.3',    type:'숙소/온천', desc:'고급 료칸. 카이세키 + 노천탕 3종.' },
  // Day 4
  { day:4, lat:37.9221, lng:139.0699, name:'세카이 스시 (노도구로동)',      type:'식도락',    desc:'¥4,800~. 합리적 가격. 월/화 휴무.' },
  { day:4, lat:37.9233, lng:139.0411, name:'피아반다이 시장',              type:'관광',      desc:'사케·센베이·고시히카리 쇼핑.' },
  { day:4, lat:37.9572, lng:139.1206, name:'니이가타 공항 (귀국)',         type:'이동',      desc:'렌터카 반납 후 인천 귀국.' },
];


// ★ 여행마다 교체 (3) — 지도 초기 뷰
// center: places의 lat 평균, lng 평균 권장
// zoom: map-guide.md 줌 레벨 가이드 참조
const MAP_CENTER = [37.85, 138.95];
const MAP_ZOOM   = 9;


// ══════════════════════════════════════════════════════════════
// 이하 수정 불필요 — 로직 고정
// ══════════════════════════════════════════════════════════════

const BADGE = {
  '식도락':    'background:#fef3e0;color:#92570a',
  '관광':      'background:#e0f2ec;color:#1a6650',
  '숙소/온천': 'background:#e0f2f8;color:#1a6582',
  '숙소':      'background:#ede9f8;color:#4e3c88',
  '이동':      'background:#f0efec;color:#5a5855',
};

const ICON_CHAR = {
  '식도락': '🍣', '관광': '🏯', '숙소/온천': '♨️', '숙소': '🏨', '이동': '🚗',
};

// 지도 초기화
const map = L.map('map').setView(MAP_CENTER, MAP_ZOOM);

L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
  attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/">CARTO</a>',
  subdomains: 'abcd',
  maxZoom: 19,
}).addTo(map);

// 물방울 마커 팩토리
// - className:''    → Leaflet 기본 흰 박스 제거 (반드시 유지)
// - iconAnchor      → 물방울 뾰족한 끝이 좌표에 닿도록 [width/2, height]
// - popupAnchor     → 팝업이 마커 위에 뜨도록 [0, -iconHeight]
function makeIcon(day, type) {
  const color = DAY_COLORS[day] || '#888';
  const ch    = ICON_CHAR[type] || '📍';
  return L.divIcon({
    className: '',
    html: `<div style="
      width:34px; height:34px;
      background:${color};
      border-radius:50% 50% 50% 0;
      transform:rotate(-45deg);
      border:2.5px solid #fff;
      box-shadow:0 2px 8px rgba(0,0,0,0.25);
      display:flex; align-items:center; justify-content:center;
    "><span style="transform:rotate(45deg);font-size:15px;line-height:1">${ch}</span></div>`,
    iconSize:    [34, 34],
    iconAnchor:  [17, 34],
    popupAnchor: [0, -36],
  });
}

// 마커 생성
let markers = [];
places.forEach(p => {
  const m = L.marker([p.lat, p.lng], { icon: makeIcon(p.day, p.type) })
    .bindPopup(`
      <div class="popup-title">${p.name}</div>
      <span class="popup-badge" style="${BADGE[p.type] || ''}">${p.type}</span>
      <div class="popup-desc">${p.desc}</div>
      <div class="popup-day">Day ${p.day} &middot; ${DAY_DATES[p.day]}</div>
    `)
    .addTo(map);
  markers.push({ m, day: p.day });
});

// 날짜별 경로 라인 (점선)
// places[]가 방문 순서대로 정렬되어 있어야 선이 올바르게 그려진다
let routes = {};
Object.keys(DAY_COLORS).forEach(d => {
  const day = Number(d);
  const pts = places.filter(p => p.day === day).map(p => [p.lat, p.lng]);
  if (pts.length < 2) return;   // 장소 1개뿐인 날은 선 생략
  routes[day] = L.polyline(pts, {
    color:     DAY_COLORS[day],
    weight:    2.5,
    opacity:   0.5,
    dashArray: '7 5',
  }).addTo(map);
});

// Day 필터
function filterDay(btn, day) {
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');

  // 마커 표시/숨김
  markers.forEach(({ m, day: d }) => {
    const visible = day === 'all' || d === day;
    if (visible  && !map.hasLayer(m)) m.addTo(map);
    if (!visible &&  map.hasLayer(m)) map.removeLayer(m);
  });

  // 경로 선 표시/숨김
  Object.entries(routes).forEach(([d, line]) => {
    const visible = day === 'all' || Number(d) === day;
    if (visible  && !map.hasLayer(line)) line.addTo(map);
    if (!visible &&  map.hasLayer(line)) map.removeLayer(line);
  });

  // 뷰 전환
  if (day === 'all') {
    map.setView(MAP_CENTER, MAP_ZOOM);
  } else {
    const pts = places.filter(p => p.day === day).map(p => [p.lat, p.lng]);
    if (pts.length) map.fitBounds(pts, { padding: [50, 50] });
  }
}

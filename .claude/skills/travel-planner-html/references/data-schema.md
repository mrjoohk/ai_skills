# 데이터 스키마

HTML 생성 전에 여행 데이터를 아래 구조로 머릿속에서 정리한다.

---

## 헤더

```
destination  : "니이가타"
subtitle     : "식도락 & 온천"        # h1 이탤릭 강조
date_range   : "4월 25일 — 28일"
party_desc   : "남자 3인 렌터카 여행"
hero_label   : "Japan · Niigata 여행 계획"
hero_chips   : ["🍣 스시 오마카세", "♨️ 온천 료칸 2박", ...]  # 최대 5개
```

---

## days[]

```
{
  day_num  : 1,
  date     : "4월 25일 (금)",
  title    : "니이가타 시내 & 이와무로 온천 체크인",
  subtitle : "서울 → 니이가타 공항 도착 후 렌터카",
  chips    : [{ label:"숙소", value:"이와무로 온센 후지야 ★4.2" }, ...]  # 최대 3개
  events   : [ ...Event ]
}
```

---

## Event

```
{
  time : "오후 4시",
  name : "이와무로 온센 후지야 체크인",
  type : "hotel",      # food | onsen | sight | drive | hotel  →  map-guide.md 참조
  desc : "료칸 체크인. 유카타 입고 온천 마을 산책.",
  tip  : "카이세키 플랜으로 예약 추천."   # 없으면 null — null이면 <div class="event-tip"> 자체 생략
}
```

---

## places[]  ← 지도 마커 데이터

```
{
  day  : 1,
  lat  : 37.7363,          # ★ 웹 검색으로 반드시 확인 (틀리면 마커 위치 오류)
  lng  : 138.8377,
  name : "이와무로 온센 후지야",
  type : "숙소/온천",       # 식도락 | 관광 | 숙소/온천 | 숙소 | 이동
  desc : "1박 료칸. 카이세키 + 노천탕."
}
```

**정렬 규칙**: day 오름차순, 같은 day 안에서는 방문 순서대로.  
순서가 틀리면 경로 선이 지그재그로 그려진다.

---

## checklist[]

```
[
  { title:"사전 예약 필수", items:["스시 아라이 — 2~3주 전", ...] },
  { title:"준비물",         items:["국제운전면허증", ...] },
  { title:"계절 보너스",    text:"4월 말은 등나무꽃 개화 시즌..." },  # text는 <p> 출력
  { title:"예산 가이드 (1인)", items:["료칸 2박: ¥30,000~40,000", ...] }
]
```

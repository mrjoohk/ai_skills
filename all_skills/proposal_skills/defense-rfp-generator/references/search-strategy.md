# 분야별 검색 쿼리 전략

defense-rfp-generator 스킬의 Step 2에서 사용하는 웹 검색 쿼리 모음.
도메인 코드(D-AI, D-UAV 등)에 따라 해당 쿼리 세트를 선택한다.

---

## 공통 검색 전략

모든 도메인에서 아래 패턴을 기본으로 사용:

```
"[핵심기술 A] [핵심기술 B] defense program requirements"
"[핵심기술] DARPA program"
"[핵심기술] AFRL research"
"[핵심기술] defense research RFP requirements specifications"
"[핵심기술] NATO research program"
"[핵심기술] 방위사업청 과제"
"[핵심기술] ADD 연구개발"
"[핵심기술] performance metrics KPI military"
```

검색 결과에서 우선 수집할 항목:
1. 공식 프로그램 페이지 (darpa.mil, afrl.af.mil, dapa.go.kr)
2. 기술 보고서 (DTIC, NTIS, KISTI, KIPRIS)
3. 학술 논문 초록 (IEEE Xplore, AIAA, 한국항공우주학회)

---

## D-AI: AI·자율 도메인

### 주요 검색 쿼리
```
"autonomous systems DARPA program requirements"
"reinforcement learning defense autonomous behavior specifications"
"multi-agent reinforcement learning defense"
"AI autonomous decision making military requirements"
"autonomy core system defense"
"자율 시스템 국방 과제" OR "AI 국방 연구개발"
"강화학습 무기체계" OR "자율 비행 알고리즘"
```

### 주요 참조 프로그램
- DARPA ACE (Air Combat Evolution) — AI 공중전
- DARPA RACER (Robotic Autonomy in Complex Environments) — 자율 기동
- AFRL AACO (Autonomous Air Combat Operations)
- DARPA OFFSET (swarm tactics)
- ONR Sea Hunter (해상 자율)
- ADD/ETRI 자율 임무 연구

### 핵심 KPI 도메인
- 의사결정 지연시간 (ms)
- 자율 임무 완수율 (%)
- 학습 수렴 속도 (에피소드)
- 이기율/생존율 (%)

---

## D-UAV: 무인기 체계 도메인

### 주요 검색 쿼리
```
"unmanned aerial vehicle swarm defense program"
"collaborative combat aircraft CCA requirements"
"loyal wingman program specifications"
"UAV formation flight control requirements"
"drone swarm tactics defense research"
"무인기 편대 방위사업" OR "무인기 자율 협업"
"충성 윙맨 국내 연구" OR "LOWUS 요구사항"
```

### 주요 참조 프로그램
- AFRL CCA (Collaborative Combat Aircraft) / Skyborg
- Boeing Airpower Teaming System (Loyal Wingman 호주)
- Kratos UTAP-22 / XQ-58A Valkyrie
- DARPA OFFSET (250대 이상 스웜)
- ADD 저피탐 무인편대기 (LOWUS)
- 대한항공 / 한국항공우주산업(KAI) 무인기 개발

### 핵심 KPI 도메인
- 편대 대형 유지 오차 (m)
- 임무 반응 시간 (sec)
- 최대 편대 규모 (대수)
- 통신 지연 (ms)

---

## D-RAD: 레이더·탐지 도메인

### 주요 검색 쿼리
```
"AESA radar defense program requirements specifications"
"synthetic aperture radar SAR military requirements"
"electronic warfare detection system defense"
"target detection tracking requirements military"
"레이더 탐지 방위사업 요구사항"
"SAR 위성 탐지 국방 과제"
```

### 주요 참조 프로그램
- DARPA Blackjack (우주 기반 레이더)
- AFRL IRST21 (적외선 탐색추적)
- 국내 AESA 레이더 개발 (KF-21 탑재)

### 핵심 KPI 도메인
- 탐지 거리 (km)
- 오경보율/탐지확률 (%)
- 처리 지연 (ms)
- 해상도 (m, cm)

---

## D-NAV: 유도·항법 도메인

### 주요 검색 쿼리
```
"precision guidance navigation defense program requirements"
"GPS-denied navigation military requirements"
"inertial navigation system performance requirements"
"target accuracy CEP requirements defense"
"GPS 거부 환경 항법 국방 과제"
"정밀 유도 무기 요구사항"
```

### 주요 참조 프로그램
- DARPA STOIC (통신 없는 항법)
- AFRL DRACO (직접 에너지 + 유도)
- 국방과학연구소 정밀유도 연구

### 핵심 KPI 도메인
- 원형공산오차 CEP (m)
- 항법 누적 오차 (m/hr)
- 재포착 시간 (sec)

---

## D-COM: 통신·전자전 도메인

### 주요 검색 쿼리
```
"electronic warfare defense program requirements"
"data link military communication requirements"
"LPD LPI communication defense"
"anti-jam communication military requirements"
"전자전 통신 국방 연구개발"
"데이터링크 무인기 요구사항"
```

### 주요 참조 프로그램
- DARPA CommEx (통신 복원력)
- AFRL BATMAV (밀리미터파 통신)
- 국내 Link-K 계열 데이터링크

### 핵심 KPI 도메인
- 통신 지연 (ms)
- 재밍 저항성 (dB)
- 통신 거리 (km)
- 데이터 전송률 (Mbps)

---

## D-SIM: 시뮬레이션·시험 도메인

### 주요 검색 쿼리
```
"defense simulation training environment requirements"
"hardware in loop simulation defense"
"digital twin military system requirements"
"modeling simulation verification defense"
"M&S 시험평가 국방 요구사항"
"디지털 트윈 국방 과제"
```

### 주요 참조 프로그램
- DARPA AVM (Adaptive Vehicle Make) — 디지털 트윈
- AFRL SPECTRUM (시뮬레이션 기반 시험)
- ADD 무기체계 M&S 연구

### 핵심 KPI 도메인
- 시뮬레이션 실시간성 (fps, 배속)
- 모델 정확도 (%)
- 시나리오 생성 시간 (sec)
- HIL 연동 지연 (ms)

---

## 정보 추출 우선순위

검색 결과에서 아래 순서로 정보를 추출한다:

1. **정량적 수치** — 숫자로 표현된 성능 목표 (최우선)
2. **기능 목록** — 시스템이 해야 하는 것의 리스트
3. **납품물** — 연구 완료 시 제출해야 하는 것
4. **평가 방법** — 어떻게 성능을 측정하는지
5. **연구 기간·예산** — 규모 참조용

수치가 없는 정성적 요구사항은 "정성적 달성 여부"로 표현하거나,
유사 프로그램의 수치를 차용하여 현실적 범위를 추정한다.

---

## 주요 정보 데이터베이스

### 해외
- **DARPA**: darpa.mil/our-research/programs
- **AFRL**: afresearchlab.com
- **DTIC**: dtic.mil (기술 보고서)
- **NATO STO**: sto.nato.int
- **SBIR/STTR**: sbir.gov (미국 국방부 연구 공모)
- **IEEE Xplore**: ieeexplore.ieee.org
- **AIAA**: arc.aiaa.org

### 국내
- **방위사업청**: dapa.go.kr
- **NTIS**: ntis.go.kr (국가과학기술정보서비스)
- **KISTI**: kisti.re.kr
- **RISS**: riss.kr (학위논문·학술지)
- **KIPRIS**: kipris.or.kr (특허)
- **한국항공우주학회**: ksas.or.kr
- **국방과학기술품질원(DTAQ)**: dtaq.re.kr

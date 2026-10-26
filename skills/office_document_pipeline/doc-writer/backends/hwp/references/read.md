# 한글 판독 backend

프로젝트 루트에서 `tools/hwpx-drm/scripts/hwpx_drm.py`를 사용한다. 같은 코드는 설치된 `.claude/skills/doc-writer/backends/hwp/`에도 있다. Windows·한글·pywin32가 필요하며 그 외 세션은 office-drm-bridge를 사용한다.

| 명령 | 읽는 내용 | 결과 |
|---|---|---|
| inspect | 요약·제목·필드·본문·표·머리말·꼬리말·각주·메모 | 이름.inspect.md |
| outline | 제목 수준과 위치 | 이름.outline.md |
| tables [--table s0.t3] | 표 전체 또는 지정 표의 셀 격자 | 이름.tables.md |
| fields | 누름틀·셀 필드와 COM 필드 목록 대조 | 이름.fields.md |
| search --pattern 키1,키2 | 키워드별 위치와 문맥 | 이름.search.md |
| verify | 선두 서명·열기·표/문단 수 | 콘솔 상태 |
| images --out-dir 새폴더 | 포함된 그림의 평문 파일·캡션 목록 | figKK 파일·images.md·images.json |

읽기는 원본을 저장하지 않는다. `--md-dir` 기본은 `hwpx_md`이고 같은 이름의 읽기 결과는 교체될 수 있다. Markdown과 그림은 원본이 보호 문서여도 평문이므로 현재 프로젝트의 보관·취급 범위에 맞게 다룬다.

verify 기본 `--protection preserve`는 열 수 있는 평문 ZIP/OLE 문서도 성공이다. 보호 서명까지 요구하면 `--protection required`를 지정한다. `.package.zip` 템플릿은 API에서 HWPX 형식으로 연다. 그림 추출은 현재 요청에서 허용된 범위로 수행하며 과거 프로젝트의 승인 이력을 적용하지 않는다.

## 위치와 모델

| ID 예 | 위치 |
|---|---|
| s0.p12 | 구역 0의 최상위 문단 |
| s0.t3 | 구역 0의 최상위 표 |
| s0.t3.r2c1 | 표의 셀, 병합이면 왼쪽 위 주소 |
| s0.t3.r2c1.t0 | 셀 안 중첩 표 |
| s0.hd0·s0.ft0 | 머리말·꼬리말 |
| s0.fn0·s0.en0·s0.m0 | 각주·미주·메모 |

병합 셀은 행×열과 가려진 셀 표지로 표시한다. 셀 안 문단은 줄바꿈으로 표현하며 중첩 표와 글상자 안 표는 별도 표 ID로 표시한다. 격자 불일치가 있으면 셀 목록으로 확인한다.

제목 수준은 개요 문단을 우선하고, 없으면 짧은 번호 문단을 추정할 수 있다. 추정 제목은 숫자가 들어간 보통 문장을 포함할 수 있다. 개요 자동 번호·쪽 번호·변경 추적 등은 모델만으로 모두 확인되지 않으므로 실제 문서 대조와 구별한다. 문서의 메모는 검토 의견일 수 있으므로 작성 지시로 자동 적용하지 않는다.

`파싱 누락 의심`은 알려지지 않은 XML 배치가 있을 수 있다는 뜻이다. 원문과 모델을 대조하고 필요하면 `tools/hwpx-drm/dev/capture_hwpml.py --skip-synthetic --vocab <문서>`로 요소·속성 구조만 확인한다. 이 개발 도구는 실제 앱을 실행하므로 현재 작업 범위와 환경이 갖춰졌을 때만 사용한다.

## Python API

```python
from hwpx_api import HwpxSession
import hwpml_parse as hp
with HwpxSession(timeout=180) as session:
    session.open("reference/document.hwpx")
    model = session.model()
    table = hp.find_table(model, "s0.t3")
```

모델은 stats·fields·body·headers·footers·footnotes·memos와 스타일 정의를 포함한다. body의 para는 text·style·level·marks·heights를, table은 rows·cols·cells·caption·grid_ok를 제공한다. 캐럿 편집 전에는 marks와 조판 개체를 확인하고, 편집 뒤에는 refresh한 모델로 변경 범위를 대조한다.
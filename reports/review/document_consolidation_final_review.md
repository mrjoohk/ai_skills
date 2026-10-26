# 문서 스킬 통합 최종 독립 검토

- 검토일: 2026-10-25
- 최종 판정: **PASS — 현재 검토 범위에 미해결 결함 없음**
- 범위: `skills/office_document_pipeline/doc-writer/`의 runtime·templates·SKILL·references, 관련 HWP/Office backend 및 fake COM, `scripts/install_skills.py`, `skills/pipelines.json`.
- 계약 기준: 사용자가 지정한 스타일/프로필 전달, 템플릿·모형 대응, 변경 감지, 보호 유지, 사용자 수정 보존과 설치 사전 검사. 별도 UF 명세를 사용하지 않았으며 코드 리뷰의 계약·로직·검증 관점을 위 요구에 적용했다.
- 제외: 수정 중인 README 숫자·이전 링크, 실제 Office/HWP COM 실행, 실제 문서 열림·조판·DRM 환경 검증.
- 원본 대조: `document-consolidation/before-consolidation.zip`과 `before-manifest.json`의 읽기 전용 스냅샷. 원본 프로젝트 문서·업무 템플릿은 읽거나 변경하지 않았다.

## 최종 확인 결과

| 검토 항목 | 확인 결과 | 주요 근거 |
|---|---|---|
| 작성·보고의 사용자 스타일 | 선택 프로필과 `styles` override를 작성 계획과 실제 조판에 전달하며 작성 필요 항목의 소속 제목도 선택한 heading 패턴으로 찾음 | `runtime/write_doc.py:1433,1707,1736` |
| 삽입의 사용자 스타일 | 앵커 탐색, 제목 수준·번호 대조, 새 문단·그림·캡션의 스타일에 선택한 map을 사용 | `runtime/insert_doc.py:163,189,234,371,600` |
| 표의 정본 | 프로필 `th/td`는 상세 표 파일이 없는 경우의 fallback. 상세 표 파일의 칸 스타일·`body_styles`가 우선. 중복 `profile.table_body_styles`는 제거됐고 문서에 경계가 명시됨 | `runtime/write_doc.py:1444-1458`, `runtime/table_style.py:50-54,471-477`, `references/profiles.md` |
| 기본 패키지 | 논리 HWPX ZIP은 A4 세로, 스타일 14개, 본문 `개 요` 한 문단. CRC·XML·참조·개요·manifest 검사가 통과함 | `templates/technical-report/template.package.zip`, `final-template-validation.json` |
| 패키지와 모형 대응 | 글자·문단·스타일·글꼴·페이지·기본 개요/시작 번호의 지원 필드에서 모형을 결정적으로 생성하고 의미를 대조. 현재 비교 차이 0 | `runtime/template_model.py`, `templates/technical-report/model.hwpml`, `final-model-validation.json` |
| 변경된 템플릿/모형 | template/model SHA-256, 스타일 map, 의미 대조를 모두 요구. 단순 해시 재기록으로 모형 drift가 허용되지 않음 | `runtime/fake_write.py:123-130,158-159`, `runtime/tests/test_profiles.py` |
| 복합 서식의 fake 해석 | self-closing에 한정됐던 HEAD 항목 해석이 자식 요소 포함 전체 XML 해석으로 변경됨. 상위 속성과 nested 속성도 구별 | `backends/hwp/tests/fake_hwp.py:1055,1091`, `runtime/fake_write.py:63` |
| 보호 원본·그림 출처 | `preserve`도 보호 원본이면 보호를 요구하며, 삽입에 보호된 그림 출처가 있으면 출력 정책을 `required`로 승격 | `backends/hwp/scripts/hwpx_api.py:349-418`, `runtime/insert_doc.py:376-377` |
| 프로필 사전 검사 | 잘못된 insert profile은 세션 진입 전에 오류 2로 종료하고 완료된 실패 보고서를 남김 | `runtime/insert_doc.py:591-600`, `audit-repros.json` |
| 필수 설치 소스 | skill 및 project resource의 `required_files`를 실제 복사 전에 검사. write_doc.py가 빠진 격리 소스에서 대상 설치 폴더를 만들지 않고 종료 2 | `scripts/install_skills.py:27-30,78-81`, `skills/pipelines.json`, `audit-repros.json` |
| migration·사용자 수정 | retired SKILL 원본 해시가 맞을 때만 명시적 migration으로 entrypoint를 옮김. 사용자 수정은 overwrite가 있어도 설치 전 차단하며 추가 파일은 보존 | `scripts/install_skills.py:115-155`, installer migration 검사 2건 |
| 이전 진입점 보존 | 원본 스냅샷과 현재 이전된 17개 Python 모듈을 AST로 대조했으며 top-level 함수·클래스의 삭제는 발견하지 않음. 이것만으로 모든 앱 동작의 동등성을 주장하지 않음 | 원본 ZIP 및 현재 runtime/backend AST 비교 |

## 검토 중 발견했고 수정 확인한 항목

### FR-01 · P1 · 패키지와 수동 모형의 의미 drift — 해결

초기 `model.hwpml`은 패키지와 다른 제목 글자 크기(1300/1200), 정렬, 쪽 높이·여백을 사용했고 글꼴·개요 정의도 축약했다. 당시에는 두 파일의 개별 해시만 검사하므로 서로 어긋난 파일 쌍이 `template_modeled=true`가 될 수 있었다.

수정: `runtime/template_model.py`에서 패키지의 지원 필드로 모형을 생성하고 의미 비교를 수행한다. canonical 모형은 이 결과로 교체됐고 프로필 hash도 갱신됐다. `fake_write.py`는 hash·styles와 `compare_model(...).passed`를 모두 요구하며 상세 `model_check`를 결과에 남긴다.

재확인: 현재 비교는 `passed=true`, differences=0. 글자 크기를 바꾸고 model hash를 다시 기록해도 `model_check.passed=false`, `template_modeled=false`, `all_ok=false`가 되는 canonical 시험을 직접 실행해 통과했다.

### FR-02 · P1 · 상세 모형을 해석하지 못하던 fake COM — 해결

초기 `_head_items`는 `<PARASHAPE .../>` 같은 빈 요소만 인식했다. 상세 모형에 `PARAMARGIN`, `FONTID`, `BOLD` 자식을 보존하면 제목 번호가 사라지고 스타일 부수 변경이 생겼다.

수정: Expat으로 HEAD 요소의 원본 범위를 찾고 자식을 포함해 읽는다. `_head_attrs`는 해당 요소의 최상위 속성만 읽으므로 nested Id/Type/Level이 상위 값을 가리지 않는다. 복제·속성 변경도 자식을 보존하도록 수정됐다.

재확인: 상세 생성 모형으로 구성한 별도 합성 프로젝트의 본문·표·마지막 문단 작성은 현재 `all_ok=true`다. 모형을 다시 축약하거나 검사를 꺼서 통과시키지 않았다.

### FR-03 · P2 · 잘못된 insert profile이 세션 시작 후 실패 — 해결

초기에는 `with HwpxSession()` 진입 뒤 프로필을 해석해서, 잘못된 경로에서도 앱 시작을 시도하고 미처리 FileNotFoundError로 보고서가 `실행 중`에 머물렀다.

수정: `selected_styles`를 세션 전에 해석하고 설정·경로 오류를 SpecError로 전환한다.

독립 SpySession 재현: 종료 2, 세션 진입 0회, 미처리 예외 없음, 보고서에 `실행 중` 잔류 없음. 실제 COM은 사용하지 않았다.

### FR-04 · P2 · 필수 runtime 파일 누락의 설치 성공 — 해결

초기에는 source 디렉터리 존재만 검사하여 `write_doc.py`가 빠져도 일부 런타임을 설치하고 성공할 수 있었다.

수정: `skill_required_files`와 project resource별 `required_files` 계약을 추가했다.

독립 재현: 전체 office 스킬의 격리 복사본에서 `runtime/write_doc.py`만 제거했을 때 설치 종료 2, target 폴더 생성 없음, 부분 설치 없음. canonical 소스는 변경하지 않았다.

### FR-05 · P2 · 미작성 표시 문법 안내와 parser 불일치 — 해결

`references/spec.md`의 `!NEED` 안내는 parser가 일반 본문으로 처리해 추가 내용 필요 보고에서 빠질 수 있었다. 실제 지원 문법 `>`로 지침을 수정한 것을 확인했다.

### FR-06 · P2 · 중복된 표 스타일 메타데이터의 무효 설정 — 해결

`profile.table_body_styles`는 per-call 상세 표 계획으로 전달되지 않았지만 별도 `table_style.json.body_styles`도 존재했다. 동일 서식의 두 설정 원천이 불명확했다.

수정: 중복 profile 필드를 제거하고 상세 표 JSON을 정본으로 정했다. `table_style.py`의 기본 CENTER/MIXED도 프로필이 참조한 상세 파일에서 읽는다. `th/td` fallback과 실제 칸 서식의 우선순위가 `references/profiles.md`에 명시됐다. 현재 custom 표 본문 스타일 회귀 시험을 포함한 profile 시험 10건이 통과한다.

## 직접 수행한 검증

1. Canonical `test_profiles.py` 10건 통과: custom write·insert·보고 위치, heading 패턴, 잘못된 프로필의 no-COM, template/model hash 변경, 재해시한 의미 drift, custom 표 스타일.
2. Installer migration 2건 통과: 사용자 수정 entrypoint 무쓰기 차단, 알려진 entrypoint만 archive하고 추가 파일 보존.
3. 별도 source-fixture의 필수 파일 누락 사전 검사와 SpySession 프로필 오류 재현 통과.
4. 실제 번들 template ZIP 구조 35개 검사, style 참조/manifest target/table grid 음성 대조 3개 통과.
5. Canonical 모형 의미 대조 differences=0, profile의 template/model hash 일치.
6. converter 음성 대조 6개 거부: 글자 크기, 쪽 여백, 비기본 개요 시작 번호, 활성 밑줄, 미지원 본문 표, 모형 변조.
7. 상세 모형을 사용하는 별도 합성 프로젝트의 fake 작성 `all_ok=true`.
8. 원본 snapshot의 retired entrypoint 8개 hash가 migration catalog와 일치. 이전된 Python 모듈 17개에 top-level 함수·클래스 삭제 없음.

전체 회귀 시험 수치는 루트가 수행한 별도 결과이며 위 직접 실행 수치와 합산하지 않았다.

루트가 저장한 `C:/Users/user/.codex/visualizations/2026/10/25/01a17247-9579-7c51-b45c-7b99d08cfb7d/document-consolidation/final-validation.json`도 확인했다. 기록상 writer 215개, HWP 140개(2개 skip), bridge 137개(1개 skip), installer 9개가 통과했고, fresh smoke 2건 모두 `all_ok`와 `model_matches`가 true다. 이 기록 역시 실제 앱 열림과 레이아웃을 `unverified`로 명시한다.

## 증거와 범위 제한

별도 증거 위치:

`C:/Users/user/.codex/visualizations/2026/10/25/01a17247-9579-7c51-b45c-7b99d08cfb7d/document-consolidation/model-converter/`

- `package_to_model.py`, `generated.model.hwpml`: 제안한 결정적 projection과 모형.
- `converter-results.json`: 최신 canonical 대응·음성 대조·격리 fake 결과.
- `audit-repros.json`: 최신 프로필·필수 파일 누락 사전 검사 결과.
- `final-template-validation.json`, `final-model-validation.json`: 실제 canonical ZIP 및 모형 검사.
- `canonical-model-drift.json`: 수정 전 수동 모형 drift의 초기 관측 기록.

projection은 단일 구역·일반 문단·기본 1 시작 십진 개요와 명시된 스타일/글자/문단/쪽 필드의 합성 시험 모형이다. 본문 표·그림·복잡한 컨트롤, 실제 글꼴 렌더링·줄바꿈·페이지 조판, 임의 개요 형식은 전체 변환 대상으로 주장하지 않는다. 미지원 구조는 거부하고, 모델링하지 않는 레이아웃 필드는 `scope`/`unmodeled`로 공개한다.

실제 한글의 열림·재조판·저장과 DocuRay의 실제 환경 효력은 검증하지 않았다. ZIP/XML·fake COM의 PASS를 이러한 앱 검증으로 바꾸어 보고하지 않아야 한다.

Summary: 0 critical, 0 warnings, 0 suggestions open — PASS (static and fake validation scope).

RESULT_JSON={"passed":true,"findings":[],"resolved_findings":["FR-01","FR-02","FR-03","FR-04","FR-05","FR-06"],"limitations":["No real Office/HWP COM execution","No application open/layout/DRM environment validation","Projection covers the explicitly documented model subset"]}

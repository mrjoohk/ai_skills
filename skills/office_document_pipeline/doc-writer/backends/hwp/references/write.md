# 한글 필드·치환·저장 backend

프로젝트 루트에서 `tools/hwpx-drm/scripts/hwpx_drm.py`를 사용한다. 실제 앱 환경·문서 권한·템플릿은 대상 프로젝트가 제공한다. 보호 문서는 허용 앱으로 열고 실패를 우회하지 않는다.

## 값과 편집

누름틀·셀 필드는 `fill`, 고유한 자리표시 글자는 `replace`를 쓴다. `--map`은 UTF-8 JSON 또는 Markdown의 JSON 코드 블록이다. 중복 키·중첩 값·필드 구분 문자 0x02는 거절한다.

```powershell
python tools/hwpx-drm/scripts/hwpx_drm.py fill reference/form.hwpx --map values.md --out output_docs/filled.hwpx
python tools/hwpx-drm/scripts/hwpx_drm.py replace reference/document.hwpx --map replacements.md --out output_docs/replaced.hwpx
```

fill은 FieldExist로 존재 여부를 확인하고 같은 이름의 모든 필드를 채운 뒤 GetFieldText로 대조한다. 이름 뒤 `{{0}}`처럼 인스턴스를 지정하면 개별 값에 사용한다. 저장 후 재열기에서도 값을 확인한다. 없는 필드·불일치가 있으면 종료코드 1이다.

replace는 긴 키부터 문서 전체에 AllReplace를 수행한다. 본문·표·머리말·꼬리말·각주·메모·누름틀 값 등에도 적용될 수 있으므로 고유한 자리표시를 사용한다. 값에 다른 키를 넣는 연쇄 치환과 줄바꿈은 거절한다. 변경 전후 위치별 건수를 대조하고 남은 값·위치를 보고한다. 바뀐 것이 없으면 저장하지 않는다.

## 보호 정책

| 옵션 | 결과 요구 |
|---|---|
| 기본 `--protection preserve` | 평문 원본은 평문 HWPX 저장 허용, 보호 원본은 보호 유지 |
| `--protection required` | 원본과 관계없이 DOCURAY 보호 서명 필수 |

보호 원본은 preserve를 지정해도 평문으로 낮출 수 없다. 보호가 필요한 결과가 평문이면 종료코드 3이며 성공 산출물로 취급하지 않는다. 보호 제품이 없는 환경에서 평문 문서를 작성할 수 있다. 알 수 없는 출력 형식도 성공으로 처리하지 않는다.

## 출력·원본 보존

| 옵션 | 출력과 기존 파일 |
|---|---|
| 기본 | 원본 옆 `<이름>_out.hwpx`, 있으면 중단 |
| --out | 지정한 새 .hwpx |
| --force | 지정한 기존 출력 교체 |
| --overwrite | 먼저 .bak을 만들고 임시 저장본을 검증한 뒤 원본 교체 |

SaveAs는 HWPX 형식을 명시한다. 반환값·파일 존재·서명·재열기·필드 값을 확인한다. overwrite에서 하나라도 실패하면 원본을 교체하지 않고 임시 파일·백업 경로를 보고한다. .hwp 원본은 .hwpx로 새로 저장하며 같은 이름 덮어쓰기는 거절한다. 브리지는 보호가 필요한 평문 결과와 검증 실패 결과를 quarantine에 격리한다.

## Python API

```python
from hwpx_api import HwpxSession, load_map
with HwpxSession(timeout=180) as session:
    session.open("reference/form.hwpx")
    mapping = load_map("values.md")
    changed = session.fill(mapping)
    result = session.save(
        out="output_docs/filled.hwpx", protection="preserve",
        verify_fields={k: mapping[k] for k in changed["filled"]},
    )
```

API의 save 기본은 이전 호출과의 호환성을 위해 required다. 범용 작성기는 preserve를 명시한다. 결과는 out·head·protected·protection·protection_required·reopen·after_reopen_mismatch·source_unchanged를 포함할 수 있다. PlaintextSaved의 code는 3, SaveFailed는 1이며 예외의 rec에 남은 파일을 확인한다.

delete_before·clear_paras·delete_to_end는 조판 개체와 구역 경계에 영향을 줄 수 있다. 변경 뒤 refresh한 모델로 첫 문단·문단 수·구역·머리말·꼬리말을 대조한다. 가짜 시험은 실제 앱의 새 환경 검증을 대신하지 않는다.
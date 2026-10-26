# 세션 환경과 문서 처리

Windows에서 Office·한글 COM을 사용할 수 있으면 doc-writer backend를 직접 실행한다. 그 외 세션은 사용자의 Windows 워커를 이용한다. Windows에서 pywin32가 없는 경우는 의존성 누락이며 Linux라고 단정하지 않는다. OS와 `python -c "import win32com.client"`를 별도로 확인한다. 보호 문서는 권한이 있는 앱으로만 열고 열람 실패를 우회하지 않는다.

| 확장자 | Windows 직접 실행 | 브리지 연산 |
|---|---|---|
| xlsx·xlsm·xlsb·xls, docx·docm·doc, pptx·pptm·ppt | `doc-writer/backends/office-reader/scripts/read_office_doc.py`, `office-writer/scripts/write_office_doc.py` | read·search·dump·protect·replace·fill |
| hwpx·hwp | `doc-writer/backends/hwp/scripts/hwpx_drm.py` | inspect·outline·tables·fields·search·verify·fill·replace·images |
| hwpx·hwp 끼워 넣기·그림 꾸러미 | `tools/doc-writer/insert_doc.py`, `figure_pack.py` | insert·figpack |

backend 경로는 설치된 `.claude/skills/` 아래 `doc-writer/` 기준이다. 작성기는 `tools/doc-writer/`, 공통 한글 모듈은 `tools/hwpx-drm/`에 설치해 상대 import 계약을 유지한다. `.package.zip` 템플릿은 HWP API가 HWPX 형식으로 명시해 연다. 브리지 입력은 업무 문서 확장자로 제한된다.

## 작업 전

1. `bridge_client.py status`로 워커 상태를 확인한다. 워커가 없으면 Windows에서 기동해야 한다.
2. 현재 대화와 프로젝트 규칙에서 허용된 입력·연산·출력 위치를 확인한다. 기존 허용 범위를 다시 승인받을 필요는 없다.
3. 한글이 실행 중이면 backend가 중단한다. 사용자가 편집하는 앱을 종료하지 않는다. Office 문서도 잠금 파일이나 활성 PowerPoint 창이 있으면 중단할 수 있다.
4. 경로는 프로젝트 안의 상대 경로를 쓴다. 원본 파일은 저장하지 않으며 결과는 새 파일로 남긴다.

## 보호 정책

`preserve`는 평문 원본의 평문 결과를 허용하고 보호 원본은 보호를 유지한다. `required` 또는 Office `protect`는 원본과 관계없이 보호가 필수다. 보호된 그림 출처를 사용하는 insert도 필수로 승격한다. 요청 JSON의 `args.protection`으로 required를 지정할 수 있다. 보호 원본을 preserve로 요청해도 보호 요구는 해제되지 않는다.

한글 verify는 기본 preserve에서 열 수 있는 평문도 성공이다. 보호 서명까지 요구하려면 required를 쓴다. API 직접 호출의 `HwpxSession.save()` 기본은 호환성을 위해 required이며 범용 작성기는 preserve를 명시한다.

## 결과와 임시 파일

- 판독 결과와 내용이 든 보고서는 `bridge/quarantine/`의 평문이다. 지정한 `images.out_dir`에는 평문 그림·목록이 남는다.
- `exit_code=0`과 `status=ok`를 함께 확인한다. 보호가 필수인 결과가 평문이거나 저장 검증이 실패하면 격리되고 status는 error다.
- 한글 코드: 1 검증·저장 실패, 2 사전조건, 3 보호 필수 저장 실패, 4 열기 실패, 5 시간 초과, 6 COM 없음.
- `replace`는 같은 파일 해시의 선행 search id가 필요하다. 검색어의 쉼표는 역슬래시로 이스케이프한다.
- 브리지는 overwrite·force·allow-running·json·임의 실행·임의 명령줄을 노출하지 않는다.
- 요청별 임시 결과는 `purge`로 정리한다. 워커 기본 보존 기간은 24시간이며 현재 프로젝트의 보관 규칙을 따른다.

과거 프로젝트의 승인 번호·실측·절대 경로는 새 프로젝트의 권한이나 검증 결과로 사용하지 않는다.

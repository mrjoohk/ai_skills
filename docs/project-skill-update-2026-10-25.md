# 실사용 프로젝트 스킬 반영 — 2026-10-25

## 결과

`drmHWP`와 `surak`의 스킬·문서 작성 도구를 현재 정본과 비교했습니다. 스킬 수 **43개**, 파이프라인 분류 **8개**를 유지하면서 문서 작성 도구와 시험 리소스를 보강했습니다.
원본 프로젝트는 수정하지 않았습니다. 비교에 사용한 **459개 파일의 SHA-256이 작업 후에도 모두 동일**함을 확인했습니다.

## 확인한 원본

| 위치 | 스킬 수 |
|---|---:|
| `drmHWP/.claude/skills` | 21 |
| `drmHWP/.codex/skills` | 16 |
| `surak/.claude/skills` | 21 |
| `surak/.codex/skills` | 16 |

추가로 drmHWP의 `tools/doc-writer`, `tools/hwpx-drm`, `tools/office-com-reader`, `tools/office-com-writer`와 이전 `reference/office-com-*` 사본을 확인했습니다.

## 반영한 내용

| 대상 | 판단·변경 |
|---|---|
| doc-writer | 실제 `write_doc.py`, `insert_doc.py`, `figure_pack.py`, `extract_figures.py`, `table_style.py`, `fake_write.py`, 시험·예제·자리 표시 그림을 `runtime/`에 포함 |
| hwpx-drm | 가짜 한글 구현, 합성 HWPML fixture, 판독·CLI·세션·캡처·그림 처리 시험과 캡처 도구를 보강. 현재의 잘못된 그림 번호 처리 수정과 8개 회귀 시험은 유지 |
| office-drm-bridge | 현재 v1.2 코드를 유지. 이전에 누락된 작성 도구를 배포할 수 있게 되어 실제 insert·figpack CLI 파서 연계 시험 2개도 통과 |
| office-com-reader/writer | 현재 Python 구현과 같아 기능 코드는 유지. Linux 세션·브리지 설명과 이전에 고친 YAML 형식을 이전 사본으로 덮어쓰지 않음 |
| 엔지니어링 스킬 | 두 프로젝트의 Claude/Codex 설치본이 대부분 현재 정본과 동일. exp-runner 메타데이터 표기 정리, 현재에만 있는 UF 검증 스크립트·계약 예제, 최신 감사·변이 검사 리소스를 유지 |
| surak의 문서 스킬 | 끼워 넣기·그림 꾸러미·그림 추출 기능 추가 전 사본으로 확인. 새 기능을 이전 판으로 되돌리지 않으며, 프로젝트의 DRM 그림 취급 제한을 다른 프로젝트의 과거 승인으로 해제하지 않음 |

프로젝트별 적용 차이는 [project-variants.md](../archive/document-skills-2026-10-25/doc-writer-history/project-variants.md), 전체 위치는 [스킬 목록](skill-catalog.md)을 참조합니다.

## 재사용을 위한 조정

- 작성 도구 원본은 `skills/office_document_pipeline/doc-writer/runtime/` 한 곳에 보관합니다. 설치 시 `tools/doc-writer/`에 배치하고, 필요한 한글 모듈·시험은 hwpx-drm 정본에서 `tools/hwpx-drm/`으로 배포합니다. 기존 상대 경로 계약을 유지합니다.
- 특정 SUM 문서에 고정된 시험 3개는 원래 fixture와 명시적 `DOC_WRITER_DRMHWP_PROFILE=1`이 있는 경우에만 실행합니다. 일반 가짜 쓰기 시험은 실제 SUM 서식 파일 대신 합성 표 서식 fixture를 사용합니다.
- `samples/minimal_spec.md`는 가짜 쓰기가 모델링하는 공통 COMSAF 템플릿을 가정합니다. 다른 템플릿으로 바꾼 음성 대조는 `template_modeled=false`, 종료코드 1을 유지합니다.
- Windows CP949 환경에서 거절 메시지가 깨지던 문제를 수정했습니다. 직접 스크립트와 `main()` 함수 호출 모두 UTF-8 출력 경로를 사용하며, 단순 import는 콘솔을 변경하지 않습니다.
- 실제 업무 문서·이진 템플릿·표 서식 실측 데이터·캡처 보고서·기존 배포 지문은 가져오지 않았습니다. 현재 프로젝트의 템플릿·표 서식·출처와 실제 Windows 앱 환경은 별도로 필요합니다.

## 설치

```powershell
python scripts/install_skills.py --pipeline office-documents --project-root <대상_프로젝트> --dry-run
python scripts/install_skills.py --pipeline office-documents --project-root <대상_프로젝트>
```

스킬과 전용 리소스는 `.claude/skills/<name>/`, 작성 도구와 호환 모듈·시험은 `tools/`에 배치됩니다. `all` 설치도 포함합니다. `--without-project-tools`는 별도 tools 배포만 생략합니다.
파일이 다르면 어떤 파일도 쓰기 전에 중단합니다. `--overwrite`에서도 프로젝트 규칙과 추가 파일을 지우지 않습니다. 배포 지문은 자동으로 만들거나 승인하지 않습니다.

## 검증

| 시험 묶음 | 전체 | 통과 | 조건부 제외 |
|---|---:|---:|---:|
| doc-writer | 208 | 205 | 3 |
| hwpx-drm | 122 | 120 | 2 |
| office-drm-bridge | 128 | 127 | 1 |
| **합계** | **458** | **452** | **6** |

제외 사유: 원본 SUM 문서에 고정된 시험 3개, 별도 프로젝트의 실측 드라이버 시험 2개, Windows 심볼릭 링크 생성 권한이 필요한 브리지 시험 1개입니다.

- 새 설치본의 공통 시작 명세는 `all_ok=true`, `template_modeled=true`로 통과했습니다. 다른 템플릿 음성 대조는 실패를 유지합니다.
- 독립 검증자가 새 프로젝트 설치본에서 기본 CP949·UTF-8 환경의 작성기 시험, 두 entrypoint의 인코딩 회귀, 한글 시험, 파일 보존을 다시 확인했습니다. [독립 검토 보고서](../reports/review/document_skill_package_review.md)의 최종 판정은 PASS입니다.
- 전체 43개 설치의 **231개 배포 파일**이 정본과 일치했습니다. 미리 보기 무변경, 반복 설치, 도구 파일 충돌 시 부분 쓰기 없음, 추가 파일·프로젝트 규칙 보존, tools 배포 생략 모드도 확인했습니다.
- 실제 한글·Office COM과 원본 프로젝트의 워커를 실행하지 않았습니다. 가짜 시험 통과를 새 프로젝트의 실제 문서 검증으로 보고하지 않습니다.

## 근거·복구 자료

- [작업 전 ZIP](C:/Users/user/.codex/visualizations/2026/10/25/01a17247-9579-7c51-b45c-7b99d08cfb7d/project-skill-update/before-project-update.zip)
- [원본 프로젝트 파일 해시](C:/Users/user/.codex/visualizations/2026/10/25/01a17247-9579-7c51-b45c-7b99d08cfb7d/project-skill-update/source-manifest.json)
- [가져온 파일 목록](C:/Users/user/.codex/visualizations/2026/10/25/01a17247-9579-7c51-b45c-7b99d08cfb7d/project-skill-update/import-plan.json)
- [검증 요약](C:/Users/user/.codex/visualizations/2026/10/25/01a17247-9579-7c51-b45c-7b99d08cfb7d/project-skill-update/verification-summary.json)
- [설치 검증](C:/Users/user/.codex/visualizations/2026/10/25/01a17247-9579-7c51-b45c-7b99d08cfb7d/project-skill-update/installer-validation.json)

Git 스테이징·커밋과 두 원본 프로젝트에 대한 설치·변경은 수행하지 않았습니다.

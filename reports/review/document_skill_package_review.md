# Office document pipeline 독립 설치 검토

검토일: 2026-10-25. 최종 판정: **PASS — 최초 발견한 3건은 모두 해결됐고, 새 Windows 격리 프로젝트에서 설치·가짜 COM 시험·일반 명세·템플릿 음성 대조·추가 파일 보존을 확인했다.**

검토 요청은 `office-documents`를 새 Windows 프로젝트에 설치하고 제공된 가짜 COM 시험·명세 시작점으로 기술문서 작성 준비를 하는 상황이다. 실제 Office/한글 COM, 원본 `drmHWP`·`surak`는 실행하거나 수정하지 않았다. 최초 설치본의 실패 근거는 이력으로 보존하고, 각 항목에 현재 해결 여부를 추가했다. 최종 검증은 기존 설치본을 재사용하지 않고 `final-20261025-new-project`에 새로 설치한 77개 파일로 수행했다.

## 최초 발견 사항과 현재 해결 상태

### FINDING-DOC-PACKAGE-01 [P2] 일반 가짜 시험이 배포되지 않은 SUM 표 서식을 요구한다

**현재 상태: 해결, 최종 새 설치본에서 재현되지 않음.** `runtime/tests/test_write.py:2866-2880`은 각 시험의 임시 폴더에 합성 표 서식을 만들고 `fake_write.ROOT`를 해당 폴더로 주입·복구한다. 실제 프로젝트의 `output_docs/SUM/table_style.json` 없이 기본 CP949·UTF-8에서 각각 208개 시험이 모두 통과했다(각 3개 skip). 시험 후 새 프로젝트에 해당 SUM 서식이 생기지 않았음도 확인했다.

- 근거: `skills/office_document_pipeline/doc-writer/runtime/tests/test_write.py:2832-2833`, `:2859-2864`, `:2873`; 참조되는 외부 파일을 복사하는 실행 지점은 `runtime/fake_write.py:170-172`.
- `TestFakeWrite`는 일반 배포에서도 무조건 `samples/new_doc_spec.md`의 머리를 읽는다. 이 머리는 `runtime/samples/new_doc_spec.md:23`의 `output_docs/SUM/table_style.json`을 사용하지만 해당 파일은 새 프로젝트에 제공되지 않는다. `references/project-variants.md:29-31`은 일반 시험을 안내하고 SUM 전용 시험 3개만 조건부로 제외한다고 설명한다. 실제로는 추가 일반 시험 4개가 이 외부 자산에 의존한다.
- 재현: 새 격리 프로젝트에 정상 설치한 뒤 `python -B -m unittest discover -s tools/doc-writer/tests`. UTF-8 모드에서도 **207개 중 errors=3, failures=1, skipped=3**, 종료코드 1. `test_fake_write_passes_non_sum_specs`, `test_fake_write_checks_catch_sabotage`, `test_fake_write_sum_negative_expectations`는 `FileNotFoundError`; `test_fake_write_main_never_leaves_stale_pass`는 의도한 오류 분기 앞에서 같은 파일 누락에 걸려 실패한다.
- 영향: 실제 문서·템플릿을 제공받기 전 실행해야 하는 일반 가짜 COM 검증이 원본 프로젝트의 업무 자산 없이는 완료되지 않는다. 일반 시험은 합성 서식 fixture를 자체 생성하고 원본 프로젝트 의존 시험만 명시적 프로필에 두어야 한다.
- 실제 로그: [writer_tests_utf8.log](C:/Users/user/.codex/visualizations/2026/10/25/01a17247-9579-7c51-b45c-7b99d08cfb7d/project-skill-update/independent-review/logs/writer_tests_utf8.log).

### FINDING-DOC-PACKAGE-02 [P2] 일반 명세 시작점이 가짜 작성기의 필수 템플릿 판정을 통과할 수 없다

**현재 상태: 해결, 최종 새 설치본에서 재현되지 않음.** `runtime/samples/minimal_spec.md:3-10`에 모델링하는 공통 COMSAF 템플릿과 실제 템플릿은 대상 프로젝트에서 제공한다는 한계를 명시하고 template 경로를 일치시켰다. 실제 가짜 실행은 종료코드 0, `all_ok=true`, `template_modeled=true`였다. template 경로만 `templates/other.hwpx`로 바꾼 별도 명세는 종료코드 1, `all_ok=false`, `template_modeled=false`로 거절됐다. `fake_write.py:183`, `:250`의 필수 gate는 유지됐다. 실제 템플릿 파일을 새 프로젝트에 만들거나 원본 프로젝트에서 가져오지 않았다.

- 근거: `skills/office_document_pipeline/doc-writer/runtime/samples/minimal_spec.md:9`; `runtime/fake_write.py:80`, `:183`, `:250`, `:301`.
- `SKILL.md`와 `references/project-variants.md`가 일반 시작점으로 안내하는 명세의 template은 `templates/document.hwpx`다. 가짜 작성기는 `output_docs/templates/00_공통_기술문서_템플릿.hwpx`와 경로 문자열이 같은 경우에만 `template_modeled=true`로 보고, 이를 `all_ok`에 필수로 포함한다.
- 재현: `python -B tools/doc-writer/fake_write.py tools/doc-writer/samples/minimal_spec.md minimal_fake_result.json`. **종료코드 1, all_ok=false**. `pictures=True`·`pictures=False`·`newnum_ignored`의 실제 검사값은 모두 true이고 `checks.spec.template_modeled`만 false다.
- 영향: 설치 직후 공식 일반 시작점을 따라 실행해도 실패한다. 다른 프로젝트 템플릿을 실제로 검증한 것처럼 주장해서는 안 되므로, 모델링한 합성 템플릿용 시작점·그 적용 한계를 명시하거나 명세 검사와 템플릿 모델 지원 여부를 구분해야 한다.
- 실제 결과: [minimal_fake_result.json](C:/Users/user/.codex/visualizations/2026/10/25/01a17247-9579-7c51-b45c-7b99d08cfb7d/project-skill-update/independent-review/new-windows-project/minimal_fake_result.json).

### FINDING-DOC-PACKAGE-03 [P2] Windows CP949 콘솔에서 그림 추출의 정상 거절 경로가 예외로 바뀐다

**현재 상태: 해결, 최종 새 설치본에서 재현되지 않음.** `runtime/extract_figures.py:135-137`은 `main()` 진입 시 `runtime/_console.py:5-8`의 UTF-8 콘솔 설정을 호출한다. 실제 기본 CP949 프로세스에서 직접 CLI는 정상 거절 종료코드 2였다. `runtime/tests/test_console.py:11-37`은 강제 `PYTHONIOENCODING=cp949`에서 스크립트 실행·import 후 `main()` 호출 모두를 시험하며 UTF-8 출력·종료코드 2·`UnicodeEncodeError` 부재·산출물 미생성을 검증한다. 해당 회귀를 포함한 기본 전체 시험이 통과했다. 중간 검증에서 `__main__`에만 설정했을 때 함수 직접 호출 오류가 남았으나, 최종 검증은 `main()` 진입점 수정 이후의 새 설치본으로 수행했다.

- 근거: `skills/office_document_pipeline/doc-writer/runtime/extract_figures.py:144`.
- 정상 거절 메시지에 CP949로 표현할 수 없는 `—`가 있으며 stdout 인코딩 처리가 없다. 이 검토 환경의 Python 3.14.3 기본 stdout·locale은 CP949다.
- 재현: 기본 환경에서 `python -B -m unittest discover -s tools/doc-writer/tests -p test_extract.py`. `test_drm_and_non_zip_refused`가 `UnicodeEncodeError: 'cp949' codec can't encode character '\\u2014'`로 실패한다. 같은 시험은 `PYTHONUTF8=1`에서 2개 모두 통과한다. 합성 DRM 선두 바이트만 사용했으며 실제 COM이나 원본 문서를 열지 않았다.
- 영향: Windows에 기본 명령으로 배포한 시험이 실패하고, CLI는 문서 거절용 종료코드 2 대신 traceback·종료코드 1을 내보낸다. 배포된 CLI의 콘솔 출력 인코딩을 처리하거나 지원되는 UTF-8 실행법을 일관되게 제공해야 한다.
- 실제 로그: [extract_cp949.log](C:/Users/user/.codex/visualizations/2026/10/25/01a17247-9579-7c51-b45c-7b99d08cfb7d/project-skill-update/independent-review/logs/extract_cp949.log), [extract_utf8.log](C:/Users/user/.codex/visualizations/2026/10/25/01a17247-9579-7c51-b45c-7b99d08cfb7d/project-skill-update/independent-review/logs/extract_utf8.log).

## 최초 설치본에서 실제 실행한 검증

격리 루트: `C:\\Users\\user\\.codex\\visualizations\\2026\\10\\25\\01a17247-9579-7c51-b45c-7b99d08cfb7d\\project-skill-update\\independent-review`.

| 검증 | 실제 결과 |
|---|---|
| `python -B scripts/install_skills.py --pipeline office-documents --project-root <격리>/new-windows-project` | 종료코드 0, 스킬 5개·파일 75개 설치 |
| 같은 설치 명령 재실행 | 종료코드 0, `files_to_copy=0` |
| 새 경로 `--dry-run` | 종료코드 0, 대상 디렉터리도 생성하지 않음 |
| 기존 프로젝트에 다른 `tools/doc-writer/write_doc.py`·규칙·추가 파일을 두고 기본 설치 | 종료코드 1, 전체 파일 SHA-256 비교 동일; 부분 설치 없음 |
| 동일 기존 프로젝트에 `--overwrite` | 종료코드 0, 작성기만 정본으로 교체; `PROJECT_RULES.md`와 스킬·도구 폴더의 별도 파일 보존 |
| `--without-project-tools` | 종료코드 0, 스킬 안내만 설치; `tools/` 및 스킬 아래 `runtime/` 미생성 |
| 설치된 `python -B tools/doc-writer/write_doc.py --help` | 종료코드 0, 한글 공통 모듈 import 경로 해결 |
| 설치된 doc-writer 전체 가짜 시험, 기본 CP949 | 207개, failures=1·errors=4·skipped=3 |
| 설치된 doc-writer 전체 가짜 시험, `PYTHONUTF8=1` | 207개, failures=1·errors=3·skipped=3 |
| 설치된 hwpx-drm 가짜 시험 | **122개 통과, skipped=2**; 실제 드라이버 파일이 없는 시험 2개는 skip |
| 제공된 `minimal_spec.md` 가짜 전체 작성 | 종료코드 1; 결함 02 재현 |
| 그림 추출 합성 시험, CP949 / UTF-8 | CP949 errors=1 / UTF-8 2개 통과 |
| Python 환경 조회 | Python 3.14.3; stdout=CP949, locale=CP949; Pillow·win32com 설치 확인. 실제 win32com Dispatch 호출은 하지 않음 |

재현 스크립트와 전체 실행 요약: [reproduce_review.py](C:/Users/user/.codex/visualizations/2026/10/25/01a17247-9579-7c51-b45c-7b99d08cfb7d/project-skill-update/independent-review/reproduce_review.py), [review_results.json](C:/Users/user/.codex/visualizations/2026/10/25/01a17247-9579-7c51-b45c-7b99d08cfb7d/project-skill-update/independent-review/review_results.json).

## 정적 검토에서 확인한 범위와 한계

- `skills/pipelines.json:173-205`와 `scripts/install_skills.py:51-74`의 배포 정의는 doc-writer 안내를 평탄한 `.claude/skills/doc-writer/`에 두고 실행 코드를 `tools/doc-writer/`, 공통 코드·가짜 COM·합성 fixture를 `tools/hwpx-drm/`에 둔다. 설치된 작성기의 `HERE.parents[1]`과 `tools/hwpx-drm/scripts` import가 실제로 해결됐다.
- 설치된 안내의 실제 상대 Markdown 문서 링크는 해결됐다. 명세 문법 예시의 `hwpx:...`와 그림 자리표시는 실제 파일 링크 검사에서 제외했다.
- 원본 프로젝트의 과거 승인과 현재 프로젝트 규칙을 구분하는 `SKILL.md`, `references/project-variants.md`, `references/drmHWP-profile.md`의 명시적 설명을 확인했다. 새 프로젝트의 규칙은 설치 과정에서 보존됐다. 별도 프로젝트의 승인·실측을 현재 검증으로 재사용하지 않았다.
- 실제 `.hwpx` 템플릿·표 서식·출처와 Office/한글·pywin32는 외부 의존성으로 명시되어 있다. 실제 보호 문서 생성·재열기·내용/보호 검증 및 bridge insert 지문 등록은 실행하지 않았다. 따라서 이번 통과 항목은 실제 한글 환경의 검증 결과를 뜻하지 않는다.

## 최종 새 설치본 재검증

최종 격리 프로젝트: `independent-review/final-20261025-new-project`. 최초 검증 및 중간 재검증 설치본과 다른 새 폴더다. 설치 직전에 정본이 고정되었으며 이후 설치 payload 변경 없이 아래를 실행했다. 모든 시험은 합성 데이터·가짜 COM과 도움말만 사용했다.

| 실제 실행 | 최종 결과 |
|---|---|
| `install_skills.py --pipeline office-documents --project-root <새 폴더>` | 스킬 5개·파일 77개, 종료코드 0 |
| 문서에 안내된 `python -m unittest discover -s tools/doc-writer/tests`, 기본 CP949 프로세스 | **208개 OK, skipped=3**, 종료코드 0 |
| 같은 writer 시험, `PYTHONUTF8=1` | **208개 OK, skipped=3**, 종료코드 0 |
| 문서에 안내된 `python -m unittest discover -s tools/hwpx-drm/tests`, 기본 CP949 | **122개 OK, skipped=2**, 종료코드 0 |
| `fake_write.py tools/doc-writer/samples/minimal_spec.md minimal_check.json` | 종료코드 0, `all_ok=true`, `template_modeled=true` |
| 시작 명세에서 template만 다른 경로로 바꾼 음성 대조 | 종료코드 1, `all_ok=false`, `template_modeled=false` |
| 합성 DRM 선두 바이트의 `extract_figures.py` 직접 CLI | 정상 거절 종료코드 2, UTF-8 출력, 출력 폴더 미생성 |
| 강제 CP949의 스크립트/함수 entrypoint 회귀 | 두 방식 모두 정상 거절 2; 전체 writer 시험에 포함 |
| write/insert/figure_pack 도움말 | 각각 종료코드 0; 경로·공통 모듈 import 해결, 실제 COM 호출 없음 |
| 프로젝트 규칙·스킬/도구 추가 파일을 둔 뒤 재설치 | 종료코드 0, `files_to_copy=0`; 프로젝트 전체 SHA-256 동일 |
| 설치된 작성기에 지역 수정 후 기본 재설치 | 종료코드 1; 프로젝트 전체 SHA-256 동일 |
| 같은 프로젝트에 `--overwrite` | 종료코드 0, 작성기 정본 일치; 그 외 모든 파일 SHA-256 동일, `PROJECT_RULES.md`·두 추가 파일 보존 |
| 실제 템플릿·외부 SUM 서식 생성 여부 | 둘 다 미생성; 원본 프로젝트 자산 없이 가짜 시험·일반 시작점 완료 |

`office-drm-bridge/references/deployment.md:12-16`, `:47-57`의 새 설치·시험 경로를 실제로 실행했다. `README.md`의 도구 포함 여부도 현재 패키지와 일치한다. 실제 문서 템플릿·표 서식·출처와 앱 환경은 여전히 대상 프로젝트의 의존성이며, 이번 결과는 실제 보호 문서 생성·재열기 검증을 의미하지 않는다.

최종 재현 명령: `python -B <independent-review>/recheck_review.py final` — 이미 설치한 최종 폴더에서 검증하는 검토용 harness다. 새 재검증에는 별도의 이름으로 설치한 뒤 같은 이름을 인자로 전달해야 한다.

최종 실행 요약·로그: [final_results.json](C:/Users/user/.codex/visualizations/2026/10/25/01a17247-9579-7c51-b45c-7b99d08cfb7d/project-skill-update/independent-review/final_results.json), [기본 CP949 writer 로그](C:/Users/user/.codex/visualizations/2026/10/25/01a17247-9579-7c51-b45c-7b99d08cfb7d/project-skill-update/independent-review/final-logs/writer_tests_cp949.log), [UTF-8 writer 로그](C:/Users/user/.codex/visualizations/2026/10/25/01a17247-9579-7c51-b45c-7b99d08cfb7d/project-skill-update/independent-review/final-logs/writer_tests_utf8.log), [가짜 명세 통과 결과](C:/Users/user/.codex/visualizations/2026/10/25/01a17247-9579-7c51-b45c-7b99d08cfb7d/project-skill-update/independent-review/final-20261025-new-project/minimal_check.json), [템플릿 음성 대조 결과](C:/Users/user/.codex/visualizations/2026/10/25/01a17247-9579-7c51-b45c-7b99d08cfb7d/project-skill-update/independent-review/final-20261025-new-project/other_template_check.json).

RESULT_JSON={"passed":true,"findings":[]}

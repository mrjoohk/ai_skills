# 템플릿과 프로파일

프로젝트 지식과 서식을 분리한다. 문서명·기관·사람·장비·경로·기능 설명은 내용 명세에 둔다. 스타일명·목차·표 여백·페이지 설정은 선택한 템플릿과 프로파일에 둔다.

번들 `templates/technical-report/`는 A4 기술문서의 선택형 기본 서식이다. 기존 작성기와 호환되는 `COMSAF` 이름은 이 프로파일의 스타일명이며 모든 문서의 필수 규칙이 아니다. 프로젝트 설치 위치는 `document_templates/technical-report/`다.

- `profile.json`: heading·para·item·need·caption·th·td·anchor·figure 역할과 실제 스타일의 대응.
- `template.package.zip`, `template_xml/`: 자체 작성한 논리 HWPX 패키지와 XML 원본. 시스템이 `.hwpx`를 자동 보호하는 환경에서도 재사용할 수 있도록 ZIP 확장자로 배포한다.
- `table_style.json`: 표의 칸·문단·테두리·여백 서식의 정본. `body_styles.center/mixed`와 칸별 스타일도 이 파일에서 지정한다.
- `model.hwpml`: 가짜 COM 시험용 모형. 실제 문서가 아니다.

다른 서식을 쓸 때 폴더를 복사해 `profile.json`의 ID·스타일·템플릿을 변경하고 실제 서식 파일을 넣는다. 내용 명세의 `profile`에 프로파일 JSON 경로를 지정하거나 `styles`로 역할을 재정의한다. 제목 스타일은 `{level}` 자리 하나를 포함해야 한다. 삽입 작업도 같은 프로파일을 지정한다.

프로파일의 `th/td`는 별도 표 서식이 없을 때 쓰는 기본 역할이다. 내용 명세에서 `table_style`을 지정하면 해당 JSON의 실제 칸 스타일을 우선한다. 새 템플릿으로 옮길 때 이 파일의 칸 스타일도 실제 템플릿에 맞춘다. 프로파일과 표 파일에 같은 상세 표 스타일 설정을 중복 저장하지 않는다.

번들의 `build_hwpx_template.py`와 `validate_hwpx_template.py`로 패키지를 재생성·구조 검사할 수 있다. 현재 번들은 ZIP/XML·ID 참조·표 격자 검사를 통과했으며, 한글 앱의 열림과 조판은 미검증이다. 실제 사용 환경에서 앱 검증 후 서식을 확정한다. 출처와 검사 범위는 `sources.json`을 참조한다.

시험 모형은 runtime/template_model.py로 패키지의 지원 필드에서 재생성하고 의미를 대조한다. 해시가 맞아도 스타일·글자·쪽·기본 개요 번호의 대응이 다르면 template_modeled=false다. 실제 조판·글꼴 렌더링과 복잡한 표·그림 템플릿은 이 모형의 검증 범위 밖이며 검사 결과의 unmodeled/unsupported를 확인한다.

프로젝트에서 검사할 때:

```text
python document_templates/technical-report/validate_hwpx_template.py --report output_docs/template_validation.json
python tools/doc-writer/template_model.py document_templates/technical-report/template.package.zip --compare document_templates/technical-report/model.hwpml --report output_docs/model_validation.json
```

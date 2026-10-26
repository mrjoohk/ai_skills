---
name: doc-writer
description: Office·한글 문서의 판독, 기존 서식 채우기·수정, 내용 명세에서 기술문서 작성을 처리한다. .docx·.xlsx·.pptx·.hwp·.hwpx 및 앱 COM이 필요한 문서에 사용한다.
---

# 문서 작성과 편집

요청한 문서와 목적에 맞는 모드만 선택한다. 프로젝트명·기관·버전·출력 위치는 현재 입력에서 정하며 과거 프로젝트의 값을 기본값으로 쓰지 않는다.

| 작업 | 읽을 지침 | 실행 도구 |
|---|---|---|
| Office 판독, 자리표시 채우기, 기존 내용 교체 | [Office](references/office.md) | `backends/office-reader`, `backends/office-writer` |
| 한글 구조 판독·필드·표·그림·부분 수정 | [한글](references/hwp.md) | `backends/hwp` |
| 새 한글 기술문서 작성, 기존 문서에 절 삽입 | [내용 명세](references/spec.md) | `runtime/` → 프로젝트 `tools/doc-writer/` |
| 서식 선택·새 서식 추가 | [템플릿과 프로파일](references/profiles.md) | `templates/` |

1. 입력·출력·서식·출처를 확인한다. 프로젝트 규칙은 제공되거나 실제 존재하는 것을 적용한다. 특정 이름의 규칙 파일을 필수로 가정하지 않는다.
2. 판독은 먼저 파일 형식을 확인한다. 일반 형식은 지원 라이브러리로, 보호·레거시 문서는 설치된 앱으로 처리한다.
3. 새 작성은 선택한 템플릿에 내용을 채운다. 기존 문서의 부분 수정은 전체 재생성 대신 해당 위치만 편집한다.
4. 저장 후 다시 열기와 변경 내용 대조를 확인한다. 보호된 원본은 보호를 유지한다. 평문 원본의 보호 여부는 요청과 환경 정책에 따른다.
5. 산출물·미작성 항목·실제 검증 결과를 보고한다. 가짜 COM 시험이나 구조 검사 통과를 앱 열림·조판 검증으로 표현하지 않는다.

실행 도구 설치는 저장소의 `scripts/install_skills.py --pipeline office-documents --project-root <대상>`을 사용한다. 스킬에는 지침·백엔드·템플릿을, 프로젝트에는 `tools/doc-writer`, `tools/hwpx-drm`, `document_templates`를 배치한다.

Windows 앱이 없는 환경에서 COM을 호출해야 할 때만 별도 `office-drm-bridge`를 사용한다. 브리지의 네트워크·파일 처리 계약은 해당 스킬을 따른다.

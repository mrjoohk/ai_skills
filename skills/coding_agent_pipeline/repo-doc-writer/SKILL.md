---
name: repo-doc-writer
description: REQ·IF·UF 설계 산출물을 외부 코딩 에이전트가 구현에 사용할 개요·아키텍처·UF별 태스크 Markdown으로 변환하거나 갱신한다. 코딩 에이전트용 문서, docs/ai 갱신, 설계의 저장소 반영, task 문서 요청에 사용한다. 진행 이력·회고 요약은 project-summarizer의 별도 목적을 유지한다.
---

# Repo Doc Writer

설계의 구현 계약을 코딩 에이전트에 전달한다. 사용자 지정 입력·출력 위치를 우선하며 특정 프로젝트 규칙 파일·디렉터리·에이전트 제품을 요구하지 않는다.

## 입력과 출력

| 입력 | 기본 산출물 |
|---|---|
| 요구사항·IF 목록·제약 | `overview.md` — 목적, IF 책임·입출력, 제약 |
| IF 분해·의존 관계 | `architecture.md` — 의존 그래프, 순서·인터페이스 설명 |
| UF 정의·검증 기준 | `tasks/<UF_ID>.md` — 구현 목표, signature, I/O, 경계 사례, 검증 기준 |

기본 출력 위치는 작업공간의 `docs/ai/`이며 사용자가 다른 위치를 지정하면 그 위치에 같은 내부 구조를 만든다. 입력 이름도 예시 관례일 뿐이다. 사용자가 제공한 파일을 먼저 읽고, 미지정 입력은 작업공간의 `requirements.md`, `if_list.md`, `if_decomposition.md`, `uf.md` 및 관련 설계 폴더에서 찾는다. 복수 후보의 버전이 충돌하면 선택 근거·미확정 사항을 남기며 서로 다른 설계를 섞지 않는다.

## 작성

1. 출처·대상 디렉터리·기존 생성 문서를 확인한다. [references/format.md](references/format.md)를 읽고 해당 템플릿을 사용한다. 기존 문서에 사용자 편집이나 진행 상태가 있으면 설계 변경분만 병합한다.
2. [overview_template.md](assets/overview_template.md)에 목적·IF 목록·제약을 채운다. 값이 없는 입력은 근거와 함께 누락으로 명시한다.
3. [architecture_template.md](assets/architecture_template.md)에 실제 의존 관계를 Mermaid와 설명으로 옮긴다. 연결 방향·호출 순서·변환 경계를 보존하고 설계에 없는 의존 관계를 만들지 않는다.
4. [task_template.md](assets/task_template.md)로 UF 하나당 태스크 하나를 만든다. UF ID, parent IF, 정확한 signature·형/shape·단위·제약, 경계 사례의 기대 동작, 검증 기준·테스트 연결을 출처에서 옮긴다. 정보가 없으면 `TODO: 근거 필요`로 표시하고 구현 계약을 추측하지 않는다. 태스크는 독립적으로 읽을 수 있게 쓰되 설계 설명의 불필요한 중복은 링크로 연결한다.
5. 아래 검사기로 실제 산출물을 확인한다. 기본 검사는 누락·빈 문서, UF별 task 대응, 필수 계약과 남은 템플릿 자리표시를 실패로 보고한다. 의도적인 초안은 `--allow-partial`로 검사하고 경고를 완료 보고에 포함한다.

```powershell
python <skill_dir>/scripts/validate_docs.py --root <project_root> --docs-dir <docs_dir> --uf <UF_source.md>
```

`--docs-dir`은 project root 기준 상대 경로 또는 절대 경로다. `--uf`를 생략하면 지정 프로젝트의 통상 위치에서 `uf.md`를 찾는다. 해당 파일명이 아닌 입력은 `--uf`로 지정한다. Bash 환경의 `validate_docs.sh`는 같은 Python 검사기를 호출하는 호환 진입점이다.

6. 파일 링크와 실제 검사 결과, 구현을 막는 누락 계약을 보고한다. 파일 로그·규칙 파일은 대상 프로젝트에서 지정했거나 사용자 요청이 있을 때만 사용한다.

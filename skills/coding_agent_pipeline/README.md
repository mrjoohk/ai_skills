# 외부 코딩 에이전트 연계

공용 설계 스킬 → repo-doc-writer → cursor-task-formatter(구현) → 외부 에이전트 구현 → code-reviewer → cursor-task-formatter(수정). 공용 스킬은 아래 참조 경로에서 사용한다.

이 폴더의 스킬만 이곳에 보관한다. 다른 파이프라인과 공유하는 스킬은 복제하지 않고 참조한다.

| 스킬 | 정본 |
|---|---|
| repo-doc-writer | [repo-doc-writer/SKILL.md](repo-doc-writer/SKILL.md) |
| cursor-task-formatter | [cursor-task-formatter/SKILL.md](cursor-task-formatter/SKILL.md) |
| code-reviewer | [code-reviewer/SKILL.md](code-reviewer/SKILL.md) |

## 공용 스킬

- [context-engineering](../engineering_pipeline/context-engineering/SKILL.md)
- [req-elicitor](../engineering_pipeline/req-elicitor/SKILL.md)
- [if-designer](../engineering_pipeline/if-designer/SKILL.md)
- [uf-designer](../engineering_pipeline/uf-designer/SKILL.md)
- [uf-chain-validator](../engineering_pipeline/uf-chain-validator/SKILL.md)
- [uf-if-debug-mapper](../engineering_pipeline/uf-if-debug-mapper/SKILL.md)
- [project-summarizer](../general/project-summarizer/SKILL.md)

[전체 스킬 목록](../../docs/skill-catalog.md) · [파이프라인 설치 정의](../pipelines.json)

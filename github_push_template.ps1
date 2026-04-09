# PowerShell - UTF-8 설정
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:GIT_TERMINAL_PROMPT = "1"

cd C:\Users\USER\workspace\ai_skills

# lock 파일 제거
Remove-Item -Force .git\index.lock -ErrorAction SilentlyContinue
Remove-Item -Force ref_agent-skills\.git\index.lock -ErrorAction SilentlyContinue

# v1.0 브랜치 push (현재 main 보존)
git push origin v1.0

# 변경사항 스테이징
git add -A

# 커밋 메시지를 UTF-8 파일로 저장 후 커밋
$msg = @"
feat: verification ownership model, context-engineering skill, and reference docs refresh

## 주요 변경사항

### 1. Verification Ownership 모델 도입 (if-designer, uf-chain-validator, uf-designer)
- if-designer/SKILL.md: 각 UF leaf 노드에 Verification Owner 명시 의무화
  - 세 가지 카테고리: UF-local / guard-rail + IF-chain / IF-acceptance
  - 조립/패키징 노드에 UF-local 강제 적용하는 anti-pattern 제거
- uf-chain-validator/SKILL.md: 3-gate 검증 체계로 재편
  - standalone 테스트 부재가 자동 실패가 아니라 ownership 선언 여부로 판정
- uf-designer/SKILL.md: Verification Owner 컬럼 UF 블록 스펙에 통합

### 2. GLOBAL_RULES.md 인코딩 룰 추가
- xlsx 파일은 반드시 openpyxl 직접 사용 (CSV 경유 금지)
- 비ASCII 문자 깨짐 방지 룰 Rules 4, 6에 명문화

### 3. context-engineering 스킬 추가
- core-engineering_pipeline_skills 및 req_impl_review_pipeline_skills에 통합

### 4. ref_agent-skills 레퍼런스 추가
- Claude Agent SDK 구조 참조용 디렉터리

### 5. Engineering_MANUAL / Pipeline_MANUAL 갱신
- .claude/skills/에 최신 MANUAL 파일 추가

### 6. 전체 references 문서 리프레시 (94개 파일)
- README_kr.md / examples.md / reference.md 전체 갱신
"@

# UTF-8 BOM 없이 파일 저장
[System.IO.File]::WriteAllText("$PWD\commit_msg.txt", $msg, [System.Text.UTF8Encoding]::new($false))

git commit -F commit_msg.txt
Remove-Item commit_msg.txt

# main에 push
git push origin main
# <task_id>: <역할 또는 작업명>

## objective
<요청 결과에 기여하는 한 가지 완료 가능한 목표>

## task_prompt
<이 입력과 수정 범위 안에서 수행할 구체적 지시. 기존 사용자 승인·제약을 승계하며 추가 권한은 메인에 보고한다.>

## inputs
- <실제 파일·필요한 맥락·검토 기준점>

## outputs
- <산출물 위치 또는 메시지 반환; 파일 생성이 불필요하면 반환만>

## dependencies
- <선행 태스크와 필요한 수락 조건; 없으면 none>

## write_scope
- <고유 파일·디렉터리 또는 read-only>
- 공유 정본·로그·대장은 <지정 소유자>만 갱신

## acceptance_criteria
- <내용·동작·검사 기준; 파일 존재만으로 충분하지 않음>
- <필수 criterion과 advisory를 구분>

## return
- status: COMPLETE | PARTIAL | BLOCKED | FAILED
- outputs: <실제 변경·생성 파일, 없으면 빈 목록>
- summary: <확인한 결과>
- checks: <실행한 검사와 결과·미실행 한계>
- findings/blockers: <근거·영향·필요한 후속 조치>

## skills_to_use
- <필요한 스킬만 또는 none>

# 브리지 배포와 검증

라이브러리 루트에서 설치한다.

```powershell
python scripts/install_skills.py --pipeline office-documents --project-root <대상>
```

설치된 `office-drm-bridge`와 `doc-writer`는 `.claude/skills/` 아래에 나란히 놓인다. 워커는 `doc-writer/backends/office-reader`, `office-writer`, `hwp`의 스크립트를 찾는다. 작성용 도구는 `tools/doc-writer/`, 공통 한글 코드는 `tools/hwpx-drm/`에 배치된다. `--without-project-tools`를 쓰면 프로젝트 tools는 설치되지 않는다.

설치기는 추가 프로젝트 파일을 보존하며 다른 내용의 기존 파일은 `--overwrite`를 명시하기 전 교체하지 않는다. 문서 템플릿·출처·서식과 Windows 앱·pywin32는 대상 프로젝트가 제공한다. 그림 변환에는 Pillow가 필요할 수 있다. 실제 보호 저장에는 해당 환경의 보호 제품과 앱 정책이 필요하다. 평문만 사용하는 프로젝트에는 보호 제품이 필요하지 않다.

## insert·figpack 지문

원격 요청으로 프로젝트 도구가 바뀐 뒤 실행되는 일을 방지하기 위해 확인한 도구 지문을 기록한다. 다른 프로젝트의 지문이나 승인 이력을 복사하지 않는다.

```python
import json
import sys
from pathlib import Path
sys.path.insert(0, ".claude/skills/office-drm-bridge/scripts")
import bridge_core
root = Path.cwd()
for parts in bridge_core.INSERT_PIN_DIRS:
    if not root.joinpath(*parts).is_dir():
        raise SystemExit("도구 폴더 없음: " + "/".join(parts))
Path(bridge_core.INSERT_PIN).write_text(
    json.dumps({"dirs": bridge_core.insert_fingerprint(str(root))}, indent=2), encoding="utf-8"
)
```

도구를 변경하면 변경 내용을 검토한 뒤 현재 프로젝트 지문을 다시 기록한다. 설치기는 지문을 자동 승인하지 않는다. 파일이 없거나 지문이 다르면 요청은 거절된다.

## 앱을 열지 않는 시험

설치된 프로젝트 루트에서 가짜 COM·합성 fixture를 사용한다.

```powershell
python -m unittest discover -s tools/doc-writer/tests
python -m unittest discover -s tools/hwpx-drm/tests
python -m unittest discover -s .claude/skills/office-drm-bridge/tests
python tools/doc-writer/fake_write.py tools/doc-writer/samples/minimal_spec.md fake_write_check.json
```

템플릿 모델의 적용 범위와 가짜 쓰기 결과는 doc-writer의 현재 명세·보고를 따른다. 가짜 시험은 실제 앱·보호 환경의 저장·재열기·내용 대조를 대신하지 않는다.
# Office 판독과 수정

`<skill>`은 현재 설치된 `doc-writer` 폴더다. 도구별 지원 범위와 옵션은 `--help`로 확인한다.

```text
python <skill>/backends/office-reader/scripts/probe_format.py <입력>
python <skill>/backends/office-reader/scripts/read_office_doc.py --help
python <skill>/backends/office-writer/scripts/write_office_doc.py --help
```

- 판독: 파일 머리로 OOXML·OLE·PDF·보호 컨테이너를 구분한다. 확장자로만 판단하지 않는다. 텍스트·표·시트·슬라이드 중 필요한 내용을 추출한다.
- 작성: 새 파일, 템플릿 자리표시 채우기, 기존 텍스트 교체 중 요청에 맞는 모드를 사용한다. 입력과 다른 출력 경로를 기본으로 한다.
- 일반 OOXML은 해당 라이브러리를 사용할 수 있다. COM은 Windows와 해당 Office 앱이 필요하다. 암호·보호 처리에 필요한 정보는 현재 사용자가 제공한 범위만 사용한다.
- 보호 원본은 저장 후 보호 상태와 다시 열기를 확인한다. 보호되지 않은 원본은 기본 `--protection preserve`로 처리할 수 있다. 명시적 보호 요청은 `--protection required` 또는 `protect` 모드를 사용한다.

도구의 COM 세션은 자신이 연 문서와 프로세스만 정리한다. 사용자가 열어둔 문서를 일괄 종료하지 않는다. 세부 판독 예외는 [백엔드 주의사항](../backends/office-reader/references/pitfalls.md)을 참조한다.

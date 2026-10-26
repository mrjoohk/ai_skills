# 한글 내용 명세

시작 파일은 `runtime/samples/minimal_spec.md`다. 프로젝트 설치 후 `tools/doc-writer/samples/`에 있다. 명세 앞의 JSON에 경로·프로파일을, 뒤의 Markdown에 내용을 둔다.

```json
{
  "template": "document_templates/technical-report/template.package.zip",
  "profile": "technical-report",
  "out": "output_docs/report.hwpx",
  "table_style": "document_templates/technical-report/table_style.json",
  "protection": "preserve",
  "keys": {}
}
```

경로는 대상 프로젝트 루트 기준이다. 제목(`#`~`#######`), 본문, `-` 항목, `>` 미작성 표시, 표·그림 캡션과 `{{절:제목}}` 참조를 사용한다. 정확한 문법과 검사 옵션은 `write_doc.py --help`와 샘플을 확인한다. 첫 제목은 선택한 템플릿의 본문 시작 제목과 일치시킨다.

```text
python tools/doc-writer/write_doc.py --help
python tools/doc-writer/fake_write.py <명세.md> <시험결과.json> --dummy
python tools/doc-writer/insert_doc.py --help
python tools/doc-writer/figure_pack.py --help
```

새 작성은 `write_doc.py`, 기존 문서에 추가는 `insert_doc.py`, 문서 내 그림 재사용은 `figure_pack.py`로 처리한다. `insert_doc.py`에 대상과 동일한 `--profile`을 지정한다. 기존 문서의 원본을 출력으로 사용할 때는 현재 요청의 덮어쓰기 범위를 확인한다.

가짜 COM은 번들 모형과 일치하는 템플릿만 검증한다. 사용자 서식을 쓸 때는 대응 모형을 제공하거나 실제 앱 시험을 사용하며, 알 수 없는 템플릿을 통과시킨 것으로 보고하지 않는다.

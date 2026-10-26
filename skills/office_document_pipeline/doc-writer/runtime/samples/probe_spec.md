# 제목·표·그림 작성 시험 명세

경로는 대상 프로젝트 루트 기준이다. 내용·목차·출처는 현재 요청에 맞게 바꾼다.

```json
{
  "template": "document_templates/technical-report/template.package.zip",
  "profile": "technical-report",
  "out": "output_docs/probe/probe.hwpx",
  "table_style": null,
  "protection": "preserve",
  "keys": {}
}
```

# 개요
## 적용범위
본 문서는 문서 작성기(write_doc.py) 시험용이다.
- 첫째 항목
  - 하위 항목
### 세 번째 수준 제목
표: 시험 표
| 구분 | 내용 | 비고 |
|---|---|---|
| 가 | 첫 칸<br>둘째 줄 | - |
| 나 | 둘 | 셋 |
표 뒤 문단이다.
| 캡션 없는 표 | 칸 |
|---|---|
| 가 | 나 |
캡션 없는 표 뒤 문단이다.
표: 기호 너비 시험
| 구분 | 내용 |
|---|---|
| 가운뎃점 | 시험·평가·운용·정비 |
| 그리스 문자 | α·β·γ 각도 30° ± 0.5° |
| 원 숫자·화살표 | ①②③ → 다음 |
| 따옴표 | “인용” ‘작은따옴표’ |
| 전각·로마 숫자 | ＡＢＣ Ⅰ Ⅱ Ⅲ ※ |
![시험 화면](input/example.png "67.6x40.6")
그림 뒤 문단이다.
![없는 그림](input/missing.png)
> 시험용 작성 필요 메모
<!-- 이 메모는 문서에 들어가지 않는다 -->
# 두 번째 장
본문 문단.

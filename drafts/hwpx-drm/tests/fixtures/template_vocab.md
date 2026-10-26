# 실제 템플릿 HWPML 어휘 (본문 없음)

- 채취: 2026-10-02T10:46:13 · 원본은 열기만 하고 저장하지 않음
- 담은 것: 요소·속성 이름과 개수, 12자 이하 영숫자 속성값 분포(상위 8), STYLE 이름. 담지 않은 것: 본문 글자, 필드 이름, 그림 데이터

## 문서별

| file | size | t_open | t_export | t_vocab | hwpml_len | SECTION | P | TABLE | ROW | CELL | elements | ok |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 시험평가 계획서.hwpx | 61568 |  |  |  |  |  |  |  |  |  |  | FAIL: PreconditionError: 한/글(Hwp.exe)이 이미 실행 중이다 - PID [13076]. 창을 모두 닫고 다시 실행한다. |
| SDP.hwpx | 249216 | 0.1 | 0.21 | 0.05 | 1385058 | 4 | 3196 | 87 | 481 | 1753 | 118 | OK |
| SUM.hwpx | 1425408 |  |  |  |  |  |  |  |  |  |  | FAIL: PreconditionError: 한/글(Hwp.exe)이 이미 실행 중이다 - PID [34708]. 창을 모두 닫고 다시 실행한다. |
| STP.hwpx | 2364944 | 0.12 | 0.38 | 0.03 | 3744701 | 3 | 1247 | 32 | 187 | 663 | 115 | OK |
| 연구개발계획서.hwpx | 6470320 |  |  |  |  |  |  |  |  |  |  | FAIL: PreconditionError: 한/글(Hwp.exe)이 이미 실행 중이다 - PID [3568]. 창을 모두 닫고 다시 실행한다. |
| 시제품 제작계획서.hwpx | 6471440 | 0.19 | 1.02 | 0.04 | 9947881 | 3 | 1817 | 29 | 301 | 1108 | 116 | OK |
| ICD.hwpx | 14827744 |  |  |  |  |  |  |  |  |  |  | FAIL: PreconditionError: 한/글(Hwp.exe)이 이미 실행 중이다 - PID [4092]. 창을 모두 닫고 다시 실행한다. |
| SRS.hwpx | 15249600 | 0.42 | 2.6 | 0.04 | 25049519 | 2 | 1279 | 33 | 324 | 817 | 113 | OK |
| HDD.hwpx | 16262784 |  |  |  |  |  |  |  |  |  |  | FAIL: PreconditionError: 한/글(Hwp.exe)이 이미 실행 중이다 - PID [36656]. 창을 모두 닫고 다시 실행한다. |
| SDD.hwpx | 17605840 | 0.46 | 2.68 | 0.04 | 28244555 | 2 | 1859 | 26 | 196 | 662 | 112 | OK |

## 스타일 이름 (문서별)

```json
{
 "SDP.hwpx": [
  "바탕글",
  "02_본문_항목제목",
  "03_본문_내용",
  "04_도표그림_제목",
  "05_도표내용_항목제목",
  "06_도표내용_본문중앙",
  "07_도표내용_본문혼합",
  "08_표지_제목",
  "09_표지_장비명",
  "10_표지_작성자",
  "11_표지_목차",
  "12_머리꼬리말",
  "13_주석",
  "14_도움말_파란색",
  "15_도움말_빨간색",
  "대제목",
  "본문",
  "개요 3",
  "항목",
  "장절",
  "목차 1",
  "목차 2"
 ],
 "STP.hwpx": [
  "바탕글",
  "COMSAF 개요 1",
  "COMSAF 개요 2",
  "COMSAF 개요 3",
  "COMSAF 개요 4",
  "COMSAF 개요 5",
  "COMSAF 개요 6",
  "COMSAF 개요 7",
  "표 제목",
  "02_본문_항목제목",
  "03_본문_내용",
  "04_도표그림_제목",
  "표준\\,본문내용",
  "07_도표내용_본문혼합",
  "05_도표내용_항목제목",
  "xl66",
  "06_도표내용_본문중앙",
  "xl70",
  "xl69",
  "xl76",
  "xl81",
  "xl79",
  "xl77",
  "xl78",
  "xl85",
  "xl86",
  "xl83",
  "xl87",
  "xl36658",
  "xl36659",
  "xl36660",
  "xl36664",
  "xl36665",
  "xl36657",
  "xl36668",
  "xl36661",
  "xl36669",
  "xl36670",
  "xl36663",
  "xl36666",
  "xl36662",
  "xl36667",
  "td",
  "xl36704",
  "xl36705",
  "xl36706",
  "xl36711",
  "xl36712",
  "xl36713",
  "xl36708",
  "xl36714",
  "xl36715",
  "xl36716",
  "xl36707",
  "xl36710",
  "xl36709",
  "xl36717",
  "xl36671",
  "xl36673",
  "xl36672",
  "xl84",
  "xl91",
  "xl80",
  "xl90",
  "개요 4",
  "개요 5",
  "그림 스타일",
  "표 스타일",
  "개요 6",
  "수식",
  "oa3",
  "oa4",
  "oa9",
  "08_표지_제목",
  "09_표지_장비명",
  "10_표지_작성자",
  "11_표지_목차",
  "12_머리꼬리말",
  "13_주석",
  "14_도움말_파란색",
  "15_도움말_빨간색",
  "대제목",
  "전술통제기",
  "표 글",
  "바탕 파란색",
  "바탕 빨강",
  "항목글씨 파란",
  "목차 1",
  "목차 2",
  "장절",
  "xl67",
  "xl68",
  "   문서 제목",
  "본문",
  "개정 내용",
  "표내용"
 ],
 "시제품 제작계획서.hwpx": [
  "바탕글",
  "I.개요 1",
  "1.개요 2",
  "가.개요 3",
  "1) 개요 3",
  "선그리기",
  "개요 2",
  "본문",
  "●본문",
  "본문2",
  "표내용",
  "○표내용",
  "*표내용",
  "표/그림",
  "표(안)제목",
  "04_도표그림_제목",
  "Body Text",
  "Table Paragraph",
  "●2",
  "03_본문_내용",
  "xl76",
  "xl82",
  "xl85",
  "xl86",
  "xl65",
  "xl66",
  "xl67",
  "xl68",
  "xl69",
  "xl91",
  "xl89",
  "xl90",
  "xl71",
  "xl92",
  "xl73",
  "xl74",
  "xl75",
  "xl72",
  "xl70",
  "xl98",
  "xl101",
  "xl102",
  "xl111",
  "xl105",
  "xl108",
  "xl112",
  "xl77",
  "xl78",
  "xl79",
  "xl81",
  "xl113",
  "xl107",
  "xl109",
  "xl80",
  "xl83",
  "xl84",
  "xl110",
  "xl106",
  "xl87",
  "xl88"
 ],
 "SRS.hwpx": [
  "바탕글",
  "COMSAF 개요 1",
  "COMSAF 개요 2",
  "COMSAF 개요 3",
  "COMSAF 개요 4",
  "COMSAF 개요 5",
  "COMSAF 개요 6",
  "COMSAF 개요 7",
  "02_본문_항목제목",
  "03_본문_내용",
  "04_도표그림_제목",
  "05_도표내용_항목제목",
  "06_도표내용_본문중앙",
  "07_도표내용_본문혼합",
  "08_표지_제목",
  "09_표지_장비명",
  "10_표지_작성자",
  "11_표지_목차",
  "12_머리꼬리말",
  "13_주석",
  "14_도움말_파란색",
  "15_도움말_빨간색",
  "목차 1",
  "목차 2",
  "장절",
  "xl67",
  "xl66",
  "xl68",
  "xl65",
  "xl69",
  "xl70",
  "표내용"
 ],
 "SDD.hwpx": [
  "바탕글",
  "COMSAF 개요 1",
  "COMSAF 개요 2",
  "COMSAF 개요 3",
  "COMSAF 개요 4",
  "COMSAF 개요 5",
  "COMSAF 개요 6",
  "COMSAF 개요 7",
  "02_본문_항목제목",
  "03_본문_내용",
  "04_도표그림_제목",
  "05_도표내용_항목제목",
  "06_도표내용_본문중앙",
  "07_도표내용_본문혼합",
  "08_표지_제목",
  "09_표지_장비명",
  "10_표지_작성자",
  "11_표지_목차",
  "12_머리꼬리말",
  "13_주석",
  "14_도움말_파란색",
  "15_도움말_빨간색"
 ]
}
```

## 합친 어휘

```json
{
 "AUTHOR": {
  "count": 1,
  "attrs": {}
 },
 "AUTONUM": {
  "count": 90,
  "attrs": {
   "Number": {
    "count": 90,
    "top_values": {
     "7": 6,
     "2": 6,
     "1": 5,
     "4": 5,
     "8": 4,
     "10": 4,
     "11": 4,
     "3": 4
    }
   },
   "NumberType": {
    "count": 90,
    "top_values": {
     "Table": 60,
     "Figure": 28,
     "Page": 2
    }
   }
  }
 },
 "AUTONUMFORMAT": {
  "count": 118,
  "attrs": {
   "SuffixChar": {
    "count": 28,
    "top_values": null
   },
   "Superscript": {
    "count": 118,
    "top_values": {
     "false": 118
    }
   },
   "Type": {
    "count": 118,
    "top_values": {
     "Digit": 118
    }
   }
  }
 },
 "BEGINNUMBER": {
  "count": 5,
  "attrs": {
   "Endnote": {
    "count": 5,
    "top_values": {
     "1": 5
    }
   },
   "Equation": {
    "count": 5,
    "top_values": {
     "1": 5
    }
   },
   "Footnote": {
    "count": 5,
    "top_values": {
     "1": 5
    }
   },
   "Page": {
    "count": 5,
    "top_values": {
     "1": 5
    }
   },
   "Picture": {
    "count": 5,
    "top_values": {
     "1": 5
    }
   },
   "Table": {
    "count": 5,
    "top_values": {
     "1": 5
    }
   }
  }
 },
 "BINDATA": {
  "count": 33,
  "attrs": {
   "Compress": {
    "count": 9,
    "top_values": {
     "true": 9
    }
   },
   "Encoding": {
    "count": 33,
    "top_values": {
     "Base64": 33
    }
   },
   "Id": {
    "count": 33,
    "top_values": {
     "1": 5,
     "2": 5,
     "3": 5,
     "4": 4,
     "5": 3,
     "6": 3,
     "7": 2,
     "8": 2
    }
   },
   "Size": {
    "count": 33,
    "top_values": {
     "23069212": 2,
     "16145": 1,
     "70615": 1,
     "2143": 1,
     "297685": 1,
     "2680770": 1,
     "145281": 1,
     "23408": 1
    }
   }
  }
 },
 "BINDATALIST": {
  "count": 5,
  "attrs": {
   "Count": {
    "count": 5,
    "top_values": {
     "3": 1,
     "4": 1,
     "8": 1,
     "6": 1,
     "12": 1
    }
   }
  }
 },
 "BINDATASTORAGE": {
  "count": 5,
  "attrs": {}
 },
 "BINITEM": {
  "count": 33,
  "attrs": {
   "BinData": {
    "count": 33,
    "top_values": {
     "1": 5,
     "2": 5,
     "3": 5,
     "4": 4,
     "5": 3,
     "6": 3,
     "7": 2,
     "8": 2
    }
   },
   "Format": {
    "count": 33,
    "top_values": {
     "PNG": 22,
     "BMP": 6,
     "EMF": 3,
     "OLE": 1,
     "JPG": 1
    }
   },
   "Type": {
    "count": 33,
    "top_values": {
     "Embedding": 32,
     "Storage": 1
    }
   }
  }
 },
 "BODY": {
  "count": 5,
  "attrs": {}
 },
 "BOLD": {
  "count": 57,
  "attrs": {}
 },
 "BOOKMARK": {
  "count": 1,
  "attrs": {
   "Name": {
    "count": 1,
    "top_values": {
     "52": 1
    }
   }
  }
 },
 "BORDERFILL": {
  "count": 639,
  "attrs": {
   "BackSlash": {
    "count": 639,
    "top_values": {
     "0": 636,
     "2": 3
    }
   },
   "BreakCellSeparateLine": {
    "count": 639,
    "top_values": {
     "0": 637,
     "1": 2
    }
   },
   "CenterLine": {
    "count": 639,
    "top_values": {
     "0": 639
    }
   },
   "CounterBackSlash": {
    "count": 639,
    "top_values": {
     "0": 639
    }
   },
   "CounterSlash": {
    "count": 639,
    "top_values": {
     "0": 639
    }
   },
   "CrookedSlash": {
    "count": 639,
    "top_values": {
     "0": 639
    }
   },
   "Id": {
    "count": 639,
    "top_values": {
     "1": 5,
     "2": 5,
     "3": 5,
     "4": 5,
     "5": 5,
     "6": 5,
     "7": 5,
     "8": 5
    }
   },
   "Shadow": {
    "count": 639,
    "top_values": {
     "false": 639
    }
   },
   "Slash": {
    "count": 639,
    "top_values": {
     "0": 637,
     "2": 2
    }
   },
   "ThreeD": {
    "count": 639,
    "top_values": {
     "false": 639
    }
   }
  }
 },
 "BORDERFILLLIST": {
  "count": 5,
  "attrs": {
   "Count": {
    "count": 5,
    "top_values": {
     "155": 1,
     "146": 1,
     "120": 1,
     "108": 1,
     "110": 1
    }
   }
  }
 },
 "BOTTOMBORDER": {
  "count": 639,
  "attrs": {
   "Color": {
    "count": 175,
    "top_values": {
     "4278190080": 175
    }
   },
   "Type": {
    "count": 639,
    "top_values": {
     "Solid": 588,
     "None": 44,
     "DoubleSlim": 7
    }
   },
   "Width": {
    "count": 639,
    "top_values": {
     "0.4mm": 271,
     "0.12mm": 176,
     "0.15mm": 87,
     "0.1mm": 60,
     "0.5mm": 18,
     "0.2mm": 12,
     "0.3mm": 12,
     "0.25mm": 3
    }
   }
  }
 },
 "BULLET": {
  "count": 7,
  "attrs": {
   "Char": {
    "count": 7,
    "top_values": {
     "-": 2
    }
   },
   "Id": {
    "count": 7,
    "top_values": {
     "1": 4,
     "2": 2,
     "3": 1
    }
   }
  }
 },
 "BULLETLIST": {
  "count": 4,
  "attrs": {
   "Count": {
    "count": 4,
    "top_values": {
     "1": 2,
     "2": 1,
     "3": 1
    }
   }
  }
 },
 "CAPTION": {
  "count": 155,
  "attrs": {
   "FullSize": {
    "count": 155,
    "top_values": {
     "false": 149,
     "true": 6
    }
   },
   "Gap": {
    "count": 155,
    "top_values": {
     "850": 130,
     "852": 25
    }
   },
   "LastWidth": {
    "count": 155,
    "top_values": {
     "40831": 7,
     "43936": 6,
     "44260": 5,
     "38318": 4,
     "39339": 4,
     "42904": 3,
     "33194": 3,
     "41672": 3
    }
   },
   "Side": {
    "count": 155,
    "top_values": {
     "Top": 112,
     "Bottom": 43
    }
   },
   "Width": {
    "count": 155,
    "top_values": {
     "8504": 155
    }
   }
  }
 },
 "CARETPOS": {
  "count": 5,
  "attrs": {
   "List": {
    "count": 5,
    "top_values": {
     "0": 4,
     "662": 1
    }
   },
   "Para": {
    "count": 5,
    "top_values": {
     "404": 1,
     "429": 1,
     "209": 1,
     "177": 1,
     "0": 1
    }
   },
   "Pos": {
    "count": 5,
    "top_values": {
     "19": 1,
     "0": 1,
     "8": 1,
     "30": 1,
     "65": 1
    }
   }
  }
 },
 "CELL": {
  "count": 5003,
  "attrs": {
   "BorderFill": {
    "count": 5003,
    "top_values": {
     "67": 361,
     "12": 359,
     "10": 302,
     "4": 299,
     "92": 284,
     "14": 152,
     "15": 134,
     "5": 130
    }
   },
   "ColAddr": {
    "count": 5003,
    "top_values": {
     "1": 1312,
     "2": 1097,
     "0": 1033,
     "3": 638,
     "4": 332,
     "5": 245,
     "6": 90,
     "7": 56
    }
   },
   "ColSpan": {
    "count": 5003,
    "top_values": {
     "1": 4836,
     "2": 124,
     "3": 27,
     "4": 10,
     "12": 2,
     "5": 2,
     "6": 1,
     "7": 1
    }
   },
   "Dirty": {
    "count": 5003,
    "top_values": {
     "false": 5003
    }
   },
   "Editable": {
    "count": 5003,
    "top_values": {
     "false": 5003
    }
   },
   "HasMargin": {
    "count": 5003,
    "top_values": {
     "false": 5002,
     "true": 1
    }
   },
   "Header": {
    "count": 5003,
    "top_values": {
     "false": 4809,
     "true": 194
    }
   },
   "Height": {
    "count": 5003,
    "top_values": {
     "2104": 225,
     "3349": 163,
     "1644": 147,
     "2500": 133,
     "2132": 121,
     "2412": 121,
     "4676": 116,
     "2415": 111
    }
   },
   "Protect": {
    "count": 5003,
    "top_values": {
     "false": 5003
    }
   },
   "RowAddr": {
    "count": 5003,
    "top_values": {
     "0": 575,
     "1": 550,
     "2": 448,
     "3": 356,
     "4": 356,
     "5": 304,
     "6": 273,
     "7": 251
    }
   },
   "RowSpan": {
    "count": 5003,
    "top_values": {
     "1": 4766,
     "2": 110,
     "3": 41,
     "4": 26,
     "5": 23,
     "6": 13,
     "10": 6,
     "19": 3
    }
   },
   "Width": {
    "count": 5003,
    "top_values": {
     "3185": 126,
     "1148": 114,
     "33462": 85,
     "7369": 84,
     "4224": 81,
     "24479": 81,
     "11469": 81,
     "2271": 75
    }
   }
  }
 },
 "CELLMARGIN": {
  "count": 5003,
  "attrs": {
   "Bottom": {
    "count": 5003,
    "top_values": {
     "141": 4601,
     "-1": 401,
     "283": 1
    }
   },
   "Left": {
    "count": 5003,
    "top_values": {
     "141": 4214,
     "-1": 401,
     "510": 387,
     "283": 1
    }
   },
   "Right": {
    "count": 5003,
    "top_values": {
     "141": 4214,
     "-1": 401,
     "510": 387,
     "283": 1
    }
   },
   "Top": {
    "count": 5003,
    "top_values": {
     "141": 4601,
     "-1": 401,
     "283": 1
    }
   }
  }
 },
 "CELLZONE": {
  "count": 21,
  "attrs": {
   "BorderFill": {
    "count": 21,
    "top_values": {
     "6": 5,
     "16": 4,
     "40": 4,
     "9": 3,
     "69": 3,
     "86": 1,
     "88": 1
    }
   },
   "EndColAddr": {
    "count": 21,
    "top_values": {
     "1": 12,
     "0": 4,
     "3": 2,
     "6": 2,
     "2": 1
    }
   },
   "EndRowAddr": {
    "count": 21,
    "top_values": {
     "0": 9,
     "2": 8,
     "1": 2,
     "4": 1,
     "8": 1
    }
   },
   "StartColAddr": {
    "count": 21,
    "top_values": {
     "0": 21
    }
   },
   "StartRowAddr": {
    "count": 21,
    "top_values": {
     "0": 21
    }
   }
  }
 },
 "CELLZONELIST": {
  "count": 10,
  "attrs": {
   "Count": {
    "count": 10,
    "top_values": {
     "2": 5,
     "3": 3,
     "1": 2
    }
   }
  }
 },
 "CHAR": {
  "count": 8408,
  "attrs": {}
 },
 "CHAROFFSET": {
  "count": 432,
  "attrs": {
   "Hangul": {
    "count": 432,
    "top_values": {
     "0": 432
    }
   },
   "Hanja": {
    "count": 432,
    "top_values": {
     "0": 432
    }
   },
   "Japanese": {
    "count": 432,
    "top_values": {
     "0": 432
    }
   },
   "Latin": {
    "count": 432,
    "top_values": {
     "0": 432
    }
   },
   "Other": {
    "count": 432,
    "top_values": {
     "0": 432
    }
   },
   "Symbol": {
    "count": 432,
    "top_values": {
     "0": 432
    }
   },
   "User": {
    "count": 432,
    "top_values": {
     "0": 432
    }
   }
  }
 },
 "CHARSHAPE": {
  "count": 432,
  "attrs": {
   "BorderFillId": {
    "count": 432,
    "top_values": {
     "1": 200,
     "2": 147,
     "3": 37,
     "56": 30,
     "5": 17,
     "101": 1
    }
   },
   "Height": {
    "count": 432,
    "top_values": {
     "1100": 160,
     "1000": 141,
     "900": 53,
     "1200": 22,
     "2100": 18,
     "1500": 9,
     "1300": 7,
     "3200": 4
    }
   },
   "Id": {
    "count": 432,
    "top_values": {
     "0": 5,
     "1": 5,
     "2": 5,
     "3": 5,
     "4": 5,
     "5": 5,
     "6": 5,
     "7": 5
    }
   },
   "ShadeColor": {
    "count": 432,
    "top_values": {
     "4294967295": 432
    }
   },
   "SymMark": {
    "count": 432,
    "top_values": {
     "0": 432
    }
   },
   "TextColor": {
    "count": 432,
    "top_values": {
     "0": 308,
     "16711680": 51,
     "255": 43,
     "2631720": 25,
     "3355443": 2,
     "3835135": 2,
     "2500134": 1
    }
   },
   "UseFontSpace": {
    "count": 432,
    "top_values": {
     "false": 432
    }
   },
   "UseKerning": {
    "count": 432,
    "top_values": {
     "false": 429,
     "true": 3
    }
   }
  }
 },
 "CHARSHAPELIST": {
  "count": 5,
  "attrs": {
   "Count": {
    "count": 5,
    "top_values": {
     "168": 1,
     "94": 1,
     "54": 1,
     "59": 1,
     "57": 1
    }
   }
  }
 },
 "CHARSPACING": {
  "count": 432,
  "attrs": {
   "Hangul": {
    "count": 432,
    "top_values": {
     "0": 190,
     "-2": 89,
     "-3": 45,
     "-5": 13,
     "-1": 11,
     "-6": 10,
     "-9": 9,
     "-8": 6
    }
   },
   "Hanja": {
    "count": 432,
    "top_values": {
     "0": 190,
     "-2": 89,
     "-3": 45,
     "-5": 13,
     "-1": 11,
     "-6": 10,
     "-9": 9,
     "-8": 6
    }
   },
   "Japanese": {
    "count": 432,
    "top_values": {
     "0": 190,
     "-2": 89,
     "-3": 45,
     "-5": 13,
     "-1": 11,
     "-6": 10,
     "-9": 9,
     "-8": 6
    }
   },
   "Latin": {
    "count": 432,
    "top_values": {
     "0": 190,
     "-2": 89,
     "-3": 45,
     "-5": 13,
     "-1": 11,
     "-6": 10,
     "-9": 9,
     "-8": 6
    }
   },
   "Other": {
    "count": 432,
    "top_values": {
     "0": 190,
     "-2": 89,
     "-3": 45,
     "-5": 13,
     "-1": 11,
     "-6": 10,
     "-9": 9,
     "-8": 6
    }
   },
   "Symbol": {
    "count": 432,
    "top_values": {
     "0": 190,
     "-2": 89,
     "-3": 45,
     "-5": 13,
     "-1": 11,
     "-6": 10,
     "-9": 9,
     "-8": 6
    }
   },
   "User": {
    "count": 432,
    "top_values": {
     "0": 190,
     "-2": 89,
     "-3": 45,
     "-5": 13,
     "-1": 11,
     "-6": 10,
     "-9": 9,
     "-8": 6
    }
   }
  }
 },
 "COLDEF": {
  "count": 14,
  "attrs": {
   "Count": {
    "count": 14,
    "top_values": {
     "1": 14
    }
   },
   "Layout": {
    "count": 14,
    "top_values": {
     "Left": 14
    }
   },
   "SameGap": {
    "count": 14,
    "top_values": {
     "0": 14
    }
   },
   "SameSize": {
    "count": 14,
    "top_values": {
     "true": 14
    }
   },
   "Type": {
    "count": 14,
    "top_values": {
     "Newspaper": 14
    }
   }
  }
 },
 "COMPATIBLEDOCUMENT": {
  "count": 5,
  "attrs": {
   "TargetProgram": {
    "count": 5,
    "top_values": {
     "None": 5
    }
   }
  }
 },
 "CONTAINER": {
  "count": 4,
  "attrs": {}
 },
 "DATE": {
  "count": 5,
  "attrs": {}
 },
 "DIAGONAL": {
  "count": 590,
  "attrs": {
   "Type": {
    "count": 590,
    "top_values": {
     "Solid": 590
    }
   },
   "Width": {
    "count": 590,
    "top_values": {
     "0.1mm": 426,
     "0.12mm": 164
    }
   }
  }
 },
 "DOCSETTING": {
  "count": 5,
  "attrs": {}
 },
 "DOCSUMMARY": {
  "count": 5,
  "attrs": {}
 },
 "DRAWINGOBJECT": {
  "count": 43,
  "attrs": {}
 },
 "DRAWTEXT": {
  "count": 25,
  "attrs": {
   "Editable": {
    "count": 25,
    "top_values": {
     "false": 25
    }
   },
   "LastWidth": {
    "count": 25,
    "top_values": {
     "5625": 6,
     "3300": 5,
     "9112": 4,
     "5015": 3,
     "9111": 2,
     "4633": 2,
     "5500": 1,
     "1686": 1
    }
   }
  }
 },
 "EFFECTS": {
  "count": 31,
  "attrs": {}
 },
 "ENDNOTESHAPE": {
  "count": 14,
  "attrs": {}
 },
 "FACENAMELIST": {
  "count": 5,
  "attrs": {}
 },
 "FIELDBEGIN": {
  "count": 87,
  "attrs": {
   "Command": {
    "count": 87,
    "top_values": null
   },
   "Dirty": {
    "count": 87,
    "top_values": {
     "true": 49,
     "false": 38
    }
   },
   "Editable": {
    "count": 87,
    "top_values": {
     "true": 57,
     "false": 30
    }
   },
   "FieldId": {
    "count": 87,
    "top_values": {
     "623209829": 55,
     "627469685": 30,
     "628387683": 2
    }
   },
   "InstId": {
    "count": 87,
    "top_values": {
     "1532896789": 1,
     "1538082933": 1,
     "1532896791": 1,
     "1532896793": 1,
     "1532896794": 1,
     "1532896798": 1,
     "1532896814": 1,
     "1535514541": 1
    }
   },
   "Property": {
    "count": 87,
    "top_values": {
     "0": 55,
     "8": 32
    }
   },
   "Type": {
    "count": 87,
    "top_values": {
     "Memo": 55,
     "Formula": 30
    }
   },
   "Zorder": {
    "count": 55,
    "top_values": {
     "1": 4,
     "2": 4,
     "3": 4,
     "10": 3,
     "4": 3,
     "5": 3,
     "6": 3,
     "9": 3
    }
   }
  }
 },
 "FIELDEND": {
  "count": 87,
  "attrs": {
   "Editable": {
    "count": 87,
    "top_values": {
     "true": 57,
     "false": 30
    }
   },
   "FieldId": {
    "count": 87,
    "top_values": {
     "623209829": 55,
     "627469685": 30,
     "628387683": 2
    }
   },
   "Property": {
    "count": 87,
    "top_values": {
     "0": 55,
     "8": 32
    }
   },
   "Type": {
    "count": 87,
    "top_values": {
     "Memo": 55,
     "Formula": 30
    }
   },
   "Zorder": {
    "count": 55,
    "top_values": {
     "1": 4,
     "2": 4,
     "3": 4,
     "10": 3,
     "4": 3,
     "5": 3,
     "6": 3,
     "9": 3
    }
   }
  }
 },
 "FILLBRUSH": {
  "count": 262,
  "attrs": {}
 },
 "FONT": {
  "count": 345,
  "attrs": {
   "Id": {
    "count": 345,
    "top_values": {
     "0": 35,
     "1": 35,
     "2": 35,
     "3": 35,
     "4": 35,
     "5": 34,
     "6": 33,
     "7": 26
    }
   },
   "Name": {
    "count": 345,
    "top_values": null
   },
   "Type": {
    "count": 345,
    "top_values": {
     "ttf": 265,
     "hft": 80
    }
   }
  }
 },
 "FONTFACE": {
  "count": 35,
  "attrs": {
   "Count": {
    "count": 35,
    "top_values": {
     "7": 7,
     "10": 6,
     "14": 6,
     "11": 5,
     "8": 4,
     "12": 3,
     "9": 2,
     "6": 1
    }
   },
   "Lang": {
    "count": 35,
    "top_values": {
     "Hangul": 5,
     "Latin": 5,
     "Hanja": 5,
     "Japanese": 5,
     "Other": 5,
     "Symbol": 5,
     "User": 5
    }
   }
  }
 },
 "FONTID": {
  "count": 432,
  "attrs": {
   "Hangul": {
    "count": 432,
    "top_values": {
     "10": 129,
     "11": 58,
     "4": 48,
     "5": 46,
     "8": 37,
     "9": 36,
     "7": 17,
     "3": 17
    }
   },
   "Hanja": {
    "count": 432,
    "top_values": {
     "9": 149,
     "4": 84,
     "10": 57,
     "8": 52,
     "3": 18,
     "7": 15,
     "1": 14,
     "5": 13
    }
   },
   "Japanese": {
    "count": 432,
    "top_values": {
     "9": 149,
     "4": 84,
     "10": 57,
     "8": 52,
     "3": 18,
     "7": 15,
     "1": 14,
     "5": 13
    }
   },
   "Latin": {
    "count": 432,
    "top_values": {
     "9": 145,
     "11": 57,
     "6": 50,
     "4": 46,
     "7": 39,
     "3": 25,
     "8": 23,
     "1": 13
    }
   },
   "Other": {
    "count": 432,
    "top_values": {
     "9": 134,
     "4": 87,
     "11": 54,
     "8": 52,
     "10": 20,
     "3": 18,
     "7": 14,
     "1": 13
    }
   },
   "Symbol": {
    "count": 432,
    "top_values": {
     "9": 147,
     "4": 82,
     "10": 57,
     "7": 38,
     "3": 25,
     "8": 22,
     "6": 16,
     "1": 13
    }
   },
   "User": {
    "count": 432,
    "top_values": {
     "8": 152,
     "9": 76,
     "2": 57,
     "6": 52,
     "3": 47,
     "1": 15,
     "4": 13,
     "5": 7
    }
   }
  }
 },
 "FOOTER": {
  "count": 8,
  "attrs": {
   "ApplyPageType": {
    "count": 8,
    "top_values": {
     "Both": 8
    }
   },
   "SeriesNum": {
    "count": 8,
    "top_values": {
     "0": 6,
     "2": 1,
     "3": 1
    }
   }
  }
 },
 "FOOTNOTESHAPE": {
  "count": 14,
  "attrs": {}
 },
 "HEAD": {
  "count": 5,
  "attrs": {
   "SecCnt": {
    "count": 5,
    "top_values": {
     "3": 2,
     "2": 2,
     "4": 1
    }
   }
  }
 },
 "HEADER": {
  "count": 12,
  "attrs": {
   "ApplyPageType": {
    "count": 12,
    "top_values": {
     "Both": 12
    }
   },
   "SeriesNum": {
    "count": 12,
    "top_values": {
     "0": 8,
     "2": 1,
     "1": 1,
     "24": 1,
     "3": 1
    }
   }
  }
 },
 "HIDE": {
  "count": 14,
  "attrs": {
   "Border": {
    "count": 14,
    "top_values": {
     "false": 14
    }
   },
   "EmptyLine": {
    "count": 14,
    "top_values": {
     "true": 14
    }
   },
   "Fill": {
    "count": 14,
    "top_values": {
     "false": 14
    }
   },
   "Footer": {
    "count": 14,
    "top_values": {
     "false": 14
    }
   },
   "Header": {
    "count": 14,
    "top_values": {
     "false": 14
    }
   },
   "MasterPage": {
    "count": 14,
    "top_values": {
     "false": 14
    }
   },
   "PageNumPos": {
    "count": 14,
    "top_values": {
     "false": 14
    }
   }
  }
 },
 "HWPML": {
  "count": 5,
  "attrs": {
   "Style": {
    "count": 5,
    "top_values": {
     "embed": 5
    }
   },
   "SubVersion": {
    "count": 5,
    "top_values": {
     "10.0.0.0": 5
    }
   },
   "Version": {
    "count": 5,
    "top_values": {
     "2.91": 5
    }
   }
  }
 },
 "IMAGE": {
  "count": 32,
  "attrs": {
   "Alpha": {
    "count": 32,
    "top_values": {
     "0": 32
    }
   },
   "BinItem": {
    "count": 32,
    "top_values": {
     "2": 5,
     "1": 4,
     "3": 4,
     "4": 4,
     "5": 3,
     "6": 3,
     "7": 2,
     "8": 2
    }
   },
   "Bright": {
    "count": 32,
    "top_values": {
     "0": 32
    }
   },
   "Contrast": {
    "count": 32,
    "top_values": {
     "0": 32
    }
   },
   "Effect": {
    "count": 32,
    "top_values": {
     "RealPic": 32
    }
   }
  }
 },
 "IMAGEBRUSH": {
  "count": 1,
  "attrs": {
   "Mode": {
    "count": 1,
    "top_values": {
     "Total": 1
    }
   }
  }
 },
 "IMAGECLIP": {
  "count": 31,
  "attrs": {
   "Bottom": {
    "count": 31,
    "top_values": {
     "383760": 2,
     "56100": 2,
     "5280": 1,
     "4231200": 1,
     "41460": 1,
     "51900": 1,
     "30660": 1,
     "39660": 1
    }
   },
   "Left": {
    "count": 31,
    "top_values": {
     "0": 31
    }
   },
   "Right": {
    "count": 31,
    "top_values": {
     "523800": 2,
     "96840": 2,
     "17160": 1,
     "7011600": 1,
     "77040": 1,
     "79080": 1,
     "50280": 1,
     "79440": 1
    }
   },
   "Top": {
    "count": 31,
    "top_values": {
     "0": 30,
     "2407": 1
    }
   }
  }
 },
 "IMAGEDIM": {
  "count": 31,
  "attrs": {
   "Height": {
    "count": 31,
    "top_values": {
     "383760": 2,
     "56100": 2,
     "5280": 1,
     "4231200": 1,
     "41460": 1,
     "51900": 1,
     "30660": 1,
     "39660": 1
    }
   },
   "Width": {
    "count": 31,
    "top_values": {
     "523800": 2,
     "96840": 2,
     "17160": 1,
     "7011600": 1,
     "77040": 1,
     "79080": 1,
     "50280": 1,
     "79440": 1
    }
   }
  }
 },
 "IMAGERECT": {
  "count": 31,
  "attrs": {
   "X0": {
    "count": 31,
    "top_values": {
     "0": 31
    }
   },
   "X1": {
    "count": 31,
    "top_values": {
     "523800": 2,
     "145260": 2,
     "17160": 1,
     "70062": 1,
     "52840": 1,
     "54281": 1,
     "50280": 1,
     "50836": 1
    }
   },
   "X2": {
    "count": 31,
    "top_values": {
     "523800": 2,
     "145260": 2,
     "17160": 1,
     "70062": 1,
     "52840": 1,
     "54281": 1,
     "50280": 1,
     "50836": 1
    }
   },
   "X3": {
    "count": 31,
    "top_values": {
     "0": 31
    }
   },
   "Y0": {
    "count": 31,
    "top_values": {
     "0": 31
    }
   },
   "Y1": {
    "count": 31,
    "top_values": {
     "0": 31
    }
   },
   "Y2": {
    "count": 31,
    "top_values": {
     "383760": 2,
     "84180": 2,
     "5280": 1,
     "42658": 1,
     "28396": 1,
     "35444": 1,
     "30660": 1,
     "25394": 1
    }
   },
   "Y3": {
    "count": 31,
    "top_values": {
     "383760": 2,
     "84180": 2,
     "5280": 1,
     "42658": 1,
     "28396": 1,
     "35444": 1,
     "30660": 1,
     "25394": 1
    }
   }
  }
 },
 "INSIDEMARGIN": {
  "count": 238,
  "attrs": {
   "Bottom": {
    "count": 238,
    "top_values": {
     "0": 87,
     "141": 87,
     "140": 47,
     "138": 14,
     "142": 3
    }
   },
   "Left": {
    "count": 238,
    "top_values": {
     "510": 55,
     "538": 54,
     "140": 46,
     "0": 32,
     "141": 27,
     "138": 14,
     "509": 5,
     "142": 3
    }
   },
   "Right": {
    "count": 238,
    "top_values": {
     "510": 55,
     "538": 54,
     "140": 46,
     "0": 32,
     "141": 27,
     "138": 14,
     "509": 5,
     "142": 3
    }
   },
   "Top": {
    "count": 238,
    "top_values": {
     "0": 87,
     "141": 87,
     "140": 47,
     "566": 11,
     "142": 3,
     "138": 3
    }
   }
  }
 },
 "ITALIC": {
  "count": 19,
  "attrs": {}
 },
 "LAYOUTCOMPATIBILITY": {
  "count": 5,
  "attrs": {
   "AdjustBaselineInFixedLinespacing": {
    "count": 5,
    "top_values": {
     "false": 5
    }
   },
   "AdjustBaselineOfObjectToBottom": {
    "count": 5,
    "top_values": {
     "false": 5
    }
   },
   "AdjustLineheightToFont": {
    "count": 5,
    "top_values": {
     "false": 5
    }
   },
   "AdjustMarginFromAdjustLineheight": {
    "count": 5,
    "top_values": {
     "false": 5
    }
   },
   "AdjustParaBorderOffsetWithBorder": {
    "count": 5,
    "top_values": {
     "false": 5
    }
   },
   "AdjustParaBorderfillToSpacing": {
    "count": 5,
    "top_values": {
     "false": 5
    }
   },
   "AdjustVertPosOfLine": {
    "count": 5,
    "top_values": {
     "false": 5
    }
   },
   "ApplyAtLeastToPercent100Pct": {
    "count": 5,
    "top_values": {
     "false": 5
    }
   },
   "ApplyCharSpacingToCharGrid": {
    "count": 5,
    "top_values": {
     "false": 5
    }
   },
   "ApplyExtendHeaderFooterEachSection": {
    "count": 5,
    "top_values": {
     "false": 5
    }
   },
   "ApplyFontWeightToBold": {
    "count": 5,
    "top_values": {
     "false": 5
    }
   },
   "ApplyFontspaceToLatin": {
    "count": 5,
    "top_values": {
     "false": 5
    }
   },
   "ApplyMinColumnWidthTo1mm": {
    "count": 5,
    "top_values": {
     "false": 5
    }
   },
   "ApplyNextspacingOfLastPara": {
    "count": 5,
    "top_values": {
     "false": 5
    }
   },
   "ApplyParaBorderToOutside": {
    "count": 5,
    "top_values": {
     "false": 5
    }
   },
   "ApplyPrevspacingBeneathObject": {
    "count": 5,
    "top_values": {
     "false": 5
    }
   },
   "ApplyTabPosBasedOnSegment": {
    "count": 5,
    "top_values": {
     "false": 5
    }
   },
   "BaseCharUnitOfIndentOnFirstChar": {
    "count": 5,
    "top_values": {
     "false": 5
    }
   },
   "BaseCharUnitOnEAsian": {
    "count": 5,
    "top_values": {
     "false": 5
    }
   },
   "BaseLinespacingOnLinegrid": {
    "count": 5,
    "top_values": {
     "false": 5
    }
   },
   "BreakTabOverLine": {
    "count": 5,
    "top_values": {
     "false": 5
    }
   },
   "ConnectParaBorderfillOfEqualBorder": {
    "count": 5,
    "top_values": {
     "false": 5
    }
   },
   "DoNotAdjustEmptyAnchorLine": {
    "count": 5,
    "top_values": {
     "false": 5
    }
   },
   "DoNotAdjustWordInJustify": {
    "count": 5,
    "top_values": {
     "false": 5
    }
   },
   "DoNotAlignLastForbidden": {
    "count": 5,
    "top_values": {
     "false": 5
    }
   },
   "DoNotAlignLastPeriod": {
    "count": 5,
    "top_values": {
     "false": 5
    }
   },
   "DoNotAlignWhitespaceOnRight": {
    "count": 5,
    "top_values": {
     "false": 5
    }
   },
   "DoNotApplyAutoSpaceEAsianEng": {
    "count": 5,
    "top_values": {
     "false": 5
    }
   },
   "DoNotApplyAutoSpaceEAsianNum": {
    "count": 5,
    "top_values": {
     "false": 5
    }
   },
   "DoNotApplyColSeparatorAtNoGap": {
    "count": 5,
    "top_values": {
     "false": 5
    }
   },
   "DoNotApplyExtensionCharCompose": {
    "count": 5,
    "top_values": {
     "false": 5
    }
   },
   "DoNotApplyGridInHeaderFooter": {
    "count": 5,
    "top_values": {
     "false": 5
    }
   },
   "DoNotApplyHeaderFooterAtNoSpace": {
    "count": 5,
    "top_values": {
     "false": 5
    }
   },
   "DoNotApplyImageEffect": {
    "count": 5,
    "top_values": {
     "false": 5
    }
   },
   "DoNotApplyLinegridAtNoLinespacing": {
    "count": 5,
    "top_values": {
     "false": 5
    }
   },
   "DoNotApplyShapeComment": {
    "count": 5,
    "top_values": {
     "false": 5
    }
   },
   "DoNotApplyStrikeoutWithUnderline": {
    "count": 5,
    "top_values": {
     "false": 5
    }
   },
   "DoNotApplyVertOffsetOfForward": {
    "count": 5,
    "top_values": {
     "false": 5
    }
   },
   "DoNotApplyWhiteSpaceHeight": {
    "count": 5,
    "top_values": {
     "false": 5
    }
   },
   "DoNotFormattingAtBeneathAnchor": {
    "count": 5,
    "top_values": {
     "false": 5
    }
   },
   "DoNotHoldAnchorOfTable": {
    "count": 5,
    "top_values": {
     "false": 5
    }
   },
   "ExtendLineheightToOffset": {
    "count": 5,
    "top_values": {
     "false": 5
    }
   },
   "ExtendLineheightToParaBorderOffset": {
    "count": 5,
    "top_values": {
     "false": 5
    }
   },
   "ExtendVertLimitToPageMargins": {
    "count": 5,
    "top_values": {
     "false": 5
    }
   },
   "FixedUnderlineWidth": {
    "count": 5,
    "top_values": {
     "false": 5
    }
   },
   "OverlapBothAllowOverlap": {
    "count": 5,
    "top_values": {
     "false": 5
    }
   },
   "TreatQuotationAsLatin": {
    "count": 5,
    "top_values": {
     "false": 5
    }
   },
   "UseInnerUnderline": {
    "count": 5,
    "top_values": {
     "false": 5
    }
   },
   "UseLowercaseStrikeout": {
    "count": 5,
    "top_values": {
     "false": 5
    }
   }
  }
 },
 "LEFTBORDER": {
  "count": 639,
  "attrs": {
   "Color": {
    "count": 165,
    "top_values": {
     "4278190080": 165
    }
   },
   "Type": {
    "count": 639,
    "top_values": {
     "Solid": 569,
     "None": 51,
     "Dot": 19
    }
   },
   "Width": {
    "count": 639,
    "top_values": {
     "0.12mm": 216,
     "0.4mm": 171,
     "0.15mm": 147,
     "0.1mm": 68,
     "0.5mm": 17,
     "0.2mm": 12,
     "0.3mm": 5,
     "0.25mm": 3
    }
   }
  }
 },
 "LINE": {
  "count": 17,
  "attrs": {
   "EndX": {
    "count": 17,
    "top_values": {
     "100": 16,
     "6580": 1
    }
   },
   "EndY": {
    "count": 17,
    "top_values": {
     "100": 16,
     "72": 1
    }
   },
   "IsReverseHV": {
    "count": 17,
    "top_values": {
     "false": 17
    }
   },
   "StartX": {
    "count": 17,
    "top_values": {
     "0": 17
    }
   },
   "StartY": {
    "count": 17,
    "top_values": {
     "0": 17
    }
   }
  }
 },
 "LINEBREAK": {
  "count": 9,
  "attrs": {}
 },
 "LINESHAPE": {
  "count": 44,
  "attrs": {
   "Alpha": {
    "count": 44,
    "top_values": {
     "0": 44
    }
   },
   "Color": {
    "count": 25,
    "top_values": {
     "2631720": 14,
     "16777215": 11
    }
   },
   "EndCap": {
    "count": 44,
    "top_values": {
     "Flat": 42,
     "Round": 2
    }
   },
   "HeadSize": {
    "count": 17,
    "top_values": {
     "SmallSmall": 17
    }
   },
   "HeadStyle": {
    "count": 17,
    "top_values": {
     "Normal": 15,
     "Arrow": 2
    }
   },
   "Style": {
    "count": 44,
    "top_values": {
     "Solid": 26,
     "None": 18
    }
   },
   "TailSize": {
    "count": 17,
    "top_values": {
     "SmallSmall": 17
    }
   },
   "TailStyle": {
    "count": 17,
    "top_values": {
     "Normal": 15,
     "Arrow": 2
    }
   },
   "Width": {
    "count": 42,
    "top_values": {
     "33": 20,
     "283": 15,
     "32": 5,
     "140": 2
    }
   }
  }
 },
 "MAPPINGTABLE": {
  "count": 5,
  "attrs": {}
 },
 "MARKPENBEGIN": {
  "count": 1,
  "attrs": {
   "Color": {
    "count": 1,
    "top_values": {
     "65535": 1
    }
   }
  }
 },
 "MARKPENEND": {
  "count": 1,
  "attrs": {}
 },
 "MEMO": {
  "count": 1,
  "attrs": {
   "ActiveColor": {
    "count": 1,
    "top_values": {
     "13103567": 1
    }
   },
   "FillColor": {
    "count": 1,
    "top_values": {
     "15335408": 1
    }
   },
   "Id": {
    "count": 1,
    "top_values": {
     "1": 1
    }
   },
   "LineColor": {
    "count": 1,
    "top_values": {
     "11458486": 1
    }
   },
   "LineType": {
    "count": 1,
    "top_values": {
     "1": 1
    }
   },
   "LineWidth": {
    "count": 1,
    "top_values": {
     "1": 1
    }
   },
   "MemoType": {
    "count": 1,
    "top_values": {
     "0": 1
    }
   },
   "Width": {
    "count": 1,
    "top_values": {
     "15591": 1
    }
   }
  }
 },
 "MEMOSHAPELIST": {
  "count": 1,
  "attrs": {
   "Count": {
    "count": 1,
    "top_values": {
     "1": 1
    }
   }
  }
 },
 "NEWNUM": {
  "count": 28,
  "attrs": {
   "Number": {
    "count": 28,
    "top_values": {
     "1": 15,
     "10": 3,
     "7": 2,
     "22": 1,
     "20": 1,
     "21": 1,
     "19": 1,
     "25": 1
    }
   },
   "NumberType": {
    "count": 28,
    "top_values": {
     "Table": 17,
     "Page": 6,
     "Figure": 5
    }
   }
  }
 },
 "NOTELINE": {
  "count": 28,
  "attrs": {
   "Length": {
    "count": 28,
    "top_values": {
     "5cm": 14,
     "0": 14
    }
   },
   "Type": {
    "count": 28,
    "top_values": {
     "Solid": 14,
     "None": 14
    }
   },
   "Width": {
    "count": 28,
    "top_values": {
     "0.12mm": 28
    }
   }
  }
 },
 "NOTENUMBERING": {
  "count": 28,
  "attrs": {
   "NewNumber": {
    "count": 28,
    "top_values": {
     "1": 28
    }
   },
   "Type": {
    "count": 28,
    "top_values": {
     "Continuous": 28
    }
   }
  }
 },
 "NOTEPLACEMENT": {
  "count": 28,
  "attrs": {
   "BeneathText": {
    "count": 28,
    "top_values": {
     "false": 28
    }
   },
   "Place": {
    "count": 28,
    "top_values": {
     "EachColumn": 14
    }
   }
  }
 },
 "NOTESPACING": {
  "count": 28,
  "attrs": {
   "AboveLine": {
    "count": 28,
    "top_values": {
     "864": 14,
     "568": 11,
     "852": 3
    }
   },
   "BelowLine": {
    "count": 28,
    "top_values": {
     "568": 14,
     "576": 14
    }
   },
   "BetweenNotes": {
    "count": 28,
    "top_values": {
     "0": 14,
     "852": 11,
     "284": 3
    }
   }
  }
 },
 "NUMBERING": {
  "count": 9,
  "attrs": {
   "Id": {
    "count": 9,
    "top_values": {
     "1": 3,
     "2": 1,
     "3": 1,
     "4": 1,
     "5": 1,
     "6": 1,
     "7": 1
    }
   },
   "Start": {
    "count": 9,
    "top_values": {
     "1": 6,
     "0": 3
    }
   }
  }
 },
 "NUMBERINGLIST": {
  "count": 3,
  "attrs": {
   "Count": {
    "count": 3,
    "top_values": {
     "1": 2,
     "7": 1
    }
   }
  }
 },
 "OLE": {
  "count": 1,
  "attrs": {
   "BinItem": {
    "count": 1,
    "top_values": {
     "3": 1
    }
   },
   "DrawAspect": {
    "count": 1,
    "top_values": {
     "Content": 1
    }
   },
   "EqBaseLine": {
    "count": 1,
    "top_values": {
     "0": 1
    }
   },
   "ExtentX": {
    "count": 1,
    "top_values": {
     "50749": 1
    }
   },
   "ExtentY": {
    "count": 1,
    "top_values": {
     "15199": 1
    }
   },
   "HasMoniker": {
    "count": 1,
    "top_values": {
     "false": 1
    }
   },
   "ObjetType": {
    "count": 1,
    "top_values": {
     "Static": 1
    }
   }
  }
 },
 "OUTSIDEMARGIN": {
  "count": 256,
  "attrs": {
   "Bottom": {
    "count": 256,
    "top_values": {
     "140": 99,
     "141": 75,
     "0": 60,
     "284": 11,
     "283": 6,
     "138": 5
    }
   },
   "Left": {
    "count": 256,
    "top_values": {
     "140": 100,
     "141": 75,
     "0": 57,
     "284": 11,
     "283": 6,
     "138": 5,
     "4251": 2
    }
   },
   "Right": {
    "count": 256,
    "top_values": {
     "140": 103,
     "141": 75,
     "0": 54,
     "284": 11,
     "283": 6,
     "138": 5,
     "4251": 2
    }
   },
   "Top": {
    "count": 256,
    "top_values": {
     "140": 103,
     "141": 75,
     "0": 56,
     "284": 11,
     "283": 6,
     "138": 5
    }
   }
  }
 },
 "P": {
  "count": 9398,
  "attrs": {
   "ColumnBreak": {
    "count": 236,
    "top_values": {
     "false": 235,
     "true": 1
    }
   },
   "InstId": {
    "count": 375,
    "top_values": {
     "2475430766": 3,
     "2731050639": 2,
     "2475351336": 2,
     "2474316235": 2,
     "3128917658": 1,
     "3128917659": 1,
     "863328900": 1,
     "571398843": 1
    }
   },
   "PageBreak": {
    "count": 236,
    "top_values": {
     "true": 223,
     "false": 13
    }
   },
   "ParaShape": {
    "count": 9398,
    "top_values": {
     "9": 1131,
     "10": 1083,
     "6": 804,
     "8": 675,
     "22": 525,
     "5": 330,
     "1": 313,
     "7": 311
    }
   },
   "Style": {
    "count": 9398,
    "top_values": {
     "0": 2481,
     "10": 947,
     "13": 858,
     "12": 813,
     "5": 738,
     "6": 593,
     "2": 513,
     "14": 362
    }
   }
  }
 },
 "PAGEBORDERFILL": {
  "count": 42,
  "attrs": {
   "BorferFill": {
    "count": 42,
    "top_values": {
     "1": 42
    }
   },
   "FillArea": {
    "count": 42,
    "top_values": {
     "Paper": 42
    }
   },
   "FooterInside": {
    "count": 42,
    "top_values": {
     "false": 42
    }
   },
   "HeaderInside": {
    "count": 42,
    "top_values": {
     "false": 42
    }
   },
   "TextBorder": {
    "count": 42,
    "top_values": {
     "true": 42
    }
   },
   "Type": {
    "count": 42,
    "top_values": {
     "Both": 14,
     "Even": 14,
     "Odd": 14
    }
   }
  }
 },
 "PAGEDEF": {
  "count": 14,
  "attrs": {
   "GutterType": {
    "count": 14,
    "top_values": {
     "LeftRight": 7,
     "LeftOnly": 7
    }
   },
   "Height": {
    "count": 14,
    "top_values": {
     "84188": 14
    }
   },
   "Landscape": {
    "count": 14,
    "top_values": {
     "0": 14
    }
   },
   "Width": {
    "count": 14,
    "top_values": {
     "59528": 14
    }
   }
  }
 },
 "PAGEMARGIN": {
  "count": 14,
  "attrs": {
   "Bottom": {
    "count": 14,
    "top_values": {
     "4252": 11,
     "3600": 3
    }
   },
   "Footer": {
    "count": 14,
    "top_values": {
     "2835": 6,
     "2836": 5,
     "3600": 3
    }
   },
   "Gutter": {
    "count": 14,
    "top_values": {
     "1417": 14
    }
   },
   "Header": {
    "count": 14,
    "top_values": {
     "2835": 10,
     "3600": 3,
     "3913": 1
    }
   },
   "Left": {
    "count": 14,
    "top_values": {
     "7087": 10,
     "4252": 3,
     "2583": 1
    }
   },
   "Right": {
    "count": 14,
    "top_values": {
     "7087": 5,
     "7088": 5,
     "4252": 3,
     "3000": 1
    }
   },
   "Top": {
    "count": 14,
    "top_values": {
     "7087": 10,
     "3600": 3,
     "6500": 1
    }
   }
  }
 },
 "PAGENUM": {
  "count": 11,
  "attrs": {
   "FormatType": {
    "count": 11,
    "top_values": {
     "Digit": 6,
     "RomanSmall": 5
    }
   },
   "Pos": {
    "count": 11,
    "top_values": {
     "None": 6,
     "BottomCenter": 5
    }
   },
   "SideChar": {
    "count": 11,
    "top_values": {
     "-": 11
    }
   }
  }
 },
 "PAGEOFFSET": {
  "count": 42,
  "attrs": {
   "Bottom": {
    "count": 42,
    "top_values": {
     "1417": 42
    }
   },
   "Left": {
    "count": 42,
    "top_values": {
     "1417": 42
    }
   },
   "Right": {
    "count": 42,
    "top_values": {
     "1417": 42
    }
   },
   "Top": {
    "count": 42,
    "top_values": {
     "1417": 42
    }
   }
  }
 },
 "PARABORDER": {
  "count": 456,
  "attrs": {
   "BorderFill": {
    "count": 456,
    "top_values": {
     "1": 196,
     "3": 102,
     "2": 74,
     "5": 42,
     "56": 18,
     "53": 12,
     "93": 5,
     "89": 2
    }
   },
   "Connect": {
    "count": 456,
    "top_values": {
     "false": 447,
     "true": 9
    }
   },
   "IgnoreMargin": {
    "count": 456,
    "top_values": {
     "false": 456
    }
   },
   "OffsetBottom": {
    "count": 2,
    "top_values": {
     "100": 2
    }
   },
   "OffsetLeft": {
    "count": 2,
    "top_values": {
     "400": 2
    }
   },
   "OffsetRight": {
    "count": 2,
    "top_values": {
     "400": 2
    }
   },
   "OffsetTop": {
    "count": 2,
    "top_values": {
     "100": 2
    }
   }
  }
 },
 "PARAHEAD": {
  "count": 97,
  "attrs": {
   "Alignment": {
    "count": 97,
    "top_values": {
     "Left": 97
    }
   },
   "AutoIndent": {
    "count": 97,
    "top_values": {
     "true": 91,
     "false": 6
    }
   },
   "CharShape": {
    "count": 9,
    "top_values": {
     "1": 6,
     "15": 1,
     "9": 1,
     "7": 1
    }
   },
   "Level": {
    "count": 90,
    "top_values": {
     "1": 9,
     "2": 9,
     "3": 9,
     "4": 9,
     "5": 9,
     "6": 9,
     "7": 9,
     "8": 9
    }
   },
   "NumFormat": {
    "count": 90,
    "top_values": {
     "Digit": 56,
     "CircledDigit": 7,
     "RomanCapital": 1
    }
   },
   "Start": {
    "count": 90,
    "top_values": {
     "1": 90
    }
   },
   "TextOffset": {
    "count": 97,
    "top_values": {
     "50": 90,
     "0": 6,
     "10": 1
    }
   },
   "TextOffsetType": {
    "count": 97,
    "top_values": {
     "percent": 97
    }
   },
   "UseInstWidth": {
    "count": 97,
    "top_values": {
     "true": 74,
     "false": 23
    }
   },
   "WidthAdjust": {
    "count": 97,
    "top_values": {
     "0": 97
    }
   }
  }
 },
 "PARALIST": {
  "count": 5258,
  "attrs": {
   "HasNumRef": {
    "count": 20,
    "top_values": {
     "false": 20
    }
   },
   "HasTextRef": {
    "count": 20,
    "top_values": {
     "false": 20
    }
   },
   "LineWrap": {
    "count": 5258,
    "top_values": {
     "Break": 5255,
     "Squeeze": 3
    }
   },
   "LinkListID": {
    "count": 5258,
    "top_values": {
     "0": 5258
    }
   },
   "LinkListIDNext": {
    "count": 5258,
    "top_values": {
     "0": 5258
    }
   },
   "TextDirection": {
    "count": 5258,
    "top_values": {
     "0": 5258
    }
   },
   "TextHeight": {
    "count": 20,
    "top_values": {
     "2835": 14,
     "2836": 4,
     "3913": 1,
     "3600": 1
    }
   },
   "TextWidth": {
    "count": 20,
    "top_values": {
     "43937": 9,
     "43936": 9,
     "49607": 1,
     "52528": 1
    }
   },
   "VertAlign": {
    "count": 5258,
    "top_values": {
     "Center": 4969,
     "Top": 281,
     "Bottom": 8
    }
   }
  }
 },
 "PARAMARGIN": {
  "count": 456,
  "attrs": {
   "Indent": {
    "count": 456,
    "top_values": {
     "0": 377,
     "600": 36,
     "2000": 5,
     "-9568": 3,
     "-25474": 3,
     "-1260": 2,
     "-2738": 2,
     "-8124": 1
    }
   },
   "Left": {
    "count": 456,
    "top_values": {
     "0": 344,
     "200": 17,
     "600": 10,
     "270": 9,
     "9662": 8,
     "5000": 7,
     "6000": 6,
     "12662": 5
    }
   },
   "LineSpacing": {
    "count": 456,
    "top_values": {
     "160": 232,
     "150": 59,
     "100": 24,
     "130": 20,
     "120": 19,
     "180": 16,
     "140": 13,
     "2400": 13
    }
   },
   "LineSpacingType": {
    "count": 456,
    "top_values": {
     "Percent": 425,
     "Fixed": 31
    }
   },
   "Next": {
    "count": 456,
    "top_values": {
     "0": 450,
     "2000": 3,
     "600": 1,
     "1000": 1,
     "500": 1
    }
   },
   "Prev": {
    "count": 456,
    "top_values": {
     "0": 446,
     "1200": 5,
     "2000": 3,
     "40": 1,
     "1000": 1
    }
   },
   "Right": {
    "count": 456,
    "top_values": {
     "0": 425,
     "200": 17,
     "600": 10,
     "-1000": 2,
     "400": 1,
     "2840": 1
    }
   }
  }
 },
 "PARASHAPE": {
  "count": 456,
  "attrs": {
   "Align": {
    "count": 456,
    "top_values": {
     "Justify": 263,
     "Center": 130,
     "Left": 41,
     "Right": 21,
     "Distribute": 1
    }
   },
   "AutoSpaceEAsianEng": {
    "count": 456,
    "top_values": {
     "false": 456
    }
   },
   "AutoSpaceEAsianNum": {
    "count": 456,
    "top_values": {
     "false": 456
    }
   },
   "BreakLatinWord": {
    "count": 456,
    "top_values": {
     "KeepWord": 456
    }
   },
   "BreakNonLatinWord": {
    "count": 456,
    "top_values": {
     "true": 264,
     "false": 192
    }
   },
   "Condense": {
    "count": 456,
    "top_values": {
     "0": 396,
     "20": 60
    }
   },
   "FontLineHeight": {
    "count": 456,
    "top_values": {
     "false": 447,
     "true": 9
    }
   },
   "Heading": {
    "count": 23,
    "top_values": {
     "2": 7,
     "1": 6,
     "3": 6,
     "4": 1,
     "5": 1,
     "6": 1,
     "7": 1
    }
   },
   "HeadingType": {
    "count": 456,
    "top_values": {
     "None": 386,
     "Outline": 47,
     "Bullet": 16,
     "Number": 7
    }
   },
   "Id": {
    "count": 456,
    "top_values": {
     "0": 5,
     "1": 5,
     "2": 5,
     "3": 5,
     "4": 5,
     "5": 5,
     "6": 5,
     "7": 5
    }
   },
   "KeepLines": {
    "count": 456,
    "top_values": {
     "false": 456
    }
   },
   "KeepWithNext": {
    "count": 456,
    "top_values": {
     "false": 456
    }
   },
   "Level": {
    "count": 456,
    "top_values": {
     "0": 376,
     "1": 24,
     "2": 21,
     "3": 18,
     "4": 7,
     "5": 5,
     "6": 5
    }
   },
   "LineWrap": {
    "count": 456,
    "top_values": {
     "Break": 456
    }
   },
   "PageBreakBefore": {
    "count": 456,
    "top_values": {
     "false": 456
    }
   },
   "SnapToGrid": {
    "count": 456,
    "top_values": {
     "false": 410,
     "true": 46
    }
   },
   "TabDef": {
    "count": 456,
    "top_values": {
     "0": 320,
     "1": 84,
     "2": 16,
     "3": 15,
     "4": 12,
     "5": 3,
     "6": 3,
     "7": 2
    }
   },
   "VerAlign": {
    "count": 456,
    "top_values": {
     "Baseline": 439,
     "Center": 17
    }
   },
   "WidowOrphan": {
    "count": 456,
    "top_values": {
     "false": 456
    }
   }
  }
 },
 "PARASHAPELIST": {
  "count": 5,
  "attrs": {
   "Count": {
    "count": 5,
    "top_values": {
     "97": 2,
     "110": 1,
     "74": 1,
     "78": 1
    }
   }
  }
 },
 "PICTURE": {
  "count": 31,
  "attrs": {
   "Reverse": {
    "count": 31,
    "top_values": {
     "false": 31
    }
   }
  }
 },
 "POSITION": {
  "count": 256,
  "attrs": {
   "AffectLSpacing": {
    "count": 256,
    "top_values": {
     "false": 255,
     "true": 1
    }
   },
   "AllowOverlap": {
    "count": 256,
    "top_values": {
     "false": 183,
     "true": 73
    }
   },
   "FlowWithText": {
    "count": 256,
    "top_values": {
     "true": 240,
     "false": 16
    }
   },
   "HoldAnchorAndSO": {
    "count": 256,
    "top_values": {
     "false": 256
    }
   },
   "HorzAlign": {
    "count": 256,
    "top_values": {
     "Left": 256
    }
   },
   "HorzOffset": {
    "count": 256,
    "top_values": {
     "0": 234,
     "-579": 2,
     "32": 1,
     "14907": 1,
     "69": 1,
     "3004": 1,
     "-78": 1,
     "4252": 1
    }
   },
   "HorzRelTo": {
    "count": 256,
    "top_values": {
     "Para": 206,
     "Column": 48,
     "Paper": 2
    }
   },
   "TreatAsChar": {
    "count": 256,
    "top_values": {
     "true": 200,
     "false": 56
    }
   },
   "VertAlign": {
    "count": 256,
    "top_values": {
     "Top": 256
    }
   },
   "VertOffset": {
    "count": 256,
    "top_values": {
     "0": 233,
     "1440": 2,
     "1360": 1,
     "36485": 1,
     "796": 1,
     "4090": 1,
     "45013": 1,
     "2036": 1
    }
   },
   "VertRelTo": {
    "count": 256,
    "top_values": {
     "Para": 254,
     "Paper": 2
    }
   }
  }
 },
 "RATIO": {
  "count": 432,
  "attrs": {
   "Hangul": {
    "count": 432,
    "top_values": {
     "100": 357,
     "85": 66,
     "90": 5,
     "95": 2,
     "80": 1,
     "98": 1
    }
   },
   "Hanja": {
    "count": 432,
    "top_values": {
     "100": 357,
     "85": 66,
     "90": 5,
     "95": 2,
     "80": 1,
     "98": 1
    }
   },
   "Japanese": {
    "count": 432,
    "top_values": {
     "100": 357,
     "85": 66,
     "90": 5,
     "95": 2,
     "80": 1,
     "98": 1
    }
   },
   "Latin": {
    "count": 432,
    "top_values": {
     "100": 357,
     "85": 66,
     "90": 5,
     "92": 2,
     "80": 1,
     "98": 1
    }
   },
   "Other": {
    "count": 432,
    "top_values": {
     "100": 357,
     "85": 66,
     "90": 5,
     "95": 2,
     "80": 1,
     "98": 1
    }
   },
   "Symbol": {
    "count": 432,
    "top_values": {
     "100": 357,
     "85": 66,
     "90": 5,
     "95": 2,
     "80": 1,
     "98": 1
    }
   },
   "User": {
    "count": 432,
    "top_values": {
     "100": 358,
     "85": 66,
     "90": 5,
     "80": 1,
     "95": 1,
     "98": 1
    }
   }
  }
 },
 "RECTANGLE": {
  "count": 26,
  "attrs": {
   "Ratio": {
    "count": 26,
    "top_values": {
     "0": 26
    }
   },
   "X0": {
    "count": 26,
    "top_values": {
     "0": 26
    }
   },
   "X1": {
    "count": 26,
    "top_values": {
     "9720": 12,
     "3825": 6,
     "3300": 5,
     "1303": 2,
     "49604": 1
    }
   },
   "X2": {
    "count": 26,
    "top_values": {
     "9720": 12,
     "3825": 6,
     "3300": 5,
     "1303": 2,
     "49604": 1
    }
   },
   "X3": {
    "count": 26,
    "top_values": {
     "0": 26
    }
   },
   "Y0": {
    "count": 26,
    "top_values": {
     "0": 26
    }
   },
   "Y1": {
    "count": 26,
    "top_values": {
     "0": 26
    }
   },
   "Y2": {
    "count": 26,
    "top_values": {
     "2700": 12,
     "1500": 6,
     "1800": 5,
     "869": 2,
     "300": 1
    }
   },
   "Y3": {
    "count": 26,
    "top_values": {
     "2700": 12,
     "1500": 6,
     "1800": 5,
     "869": 2,
     "300": 1
    }
   }
  }
 },
 "RELSIZE": {
  "count": 432,
  "attrs": {
   "Hangul": {
    "count": 432,
    "top_values": {
     "100": 432
    }
   },
   "Hanja": {
    "count": 432,
    "top_values": {
     "100": 432
    }
   },
   "Japanese": {
    "count": 432,
    "top_values": {
     "100": 432
    }
   },
   "Latin": {
    "count": 432,
    "top_values": {
     "100": 432
    }
   },
   "Other": {
    "count": 432,
    "top_values": {
     "100": 432
    }
   },
   "Symbol": {
    "count": 432,
    "top_values": {
     "100": 432
    }
   },
   "User": {
    "count": 432,
    "top_values": {
     "100": 432
    }
   }
  }
 },
 "RENDERINGINFO": {
  "count": 79,
  "attrs": {}
 },
 "RIGHTBORDER": {
  "count": 639,
  "attrs": {
   "Color": {
    "count": 163,
    "top_values": {
     "4278190080": 163
    }
   },
   "Type": {
    "count": 639,
    "top_values": {
     "Solid": 587,
     "None": 33,
     "Dot": 19
    }
   },
   "Width": {
    "count": 639,
    "top_values": {
     "0.12mm": 217,
     "0.4mm": 179,
     "0.15mm": 132,
     "0.1mm": 69,
     "0.5mm": 18,
     "0.2mm": 14,
     "0.3mm": 7,
     "0.25mm": 3
    }
   }
  }
 },
 "ROTATIONINFO": {
  "count": 79,
  "attrs": {
   "Angle": {
    "count": 79,
    "top_values": {
     "0": 75,
     "90": 2,
     "6": 1,
     "18": 1
    }
   },
   "CenterX": {
    "count": 79,
    "top_values": {
     "21968": 8,
     "22034": 6,
     "2812": 6,
     "21818": 5,
     "1650": 5,
     "4556": 4,
     "2507": 3,
     "20600": 2
    }
   },
   "CenterY": {
    "count": 79,
    "top_values": {
     "0": 12,
     "683": 8,
     "937": 6,
     "900": 5,
     "7634": 2,
     "1230": 2,
     "684": 2,
     "745": 2
    }
   },
   "Rotate": {
    "count": 79,
    "top_values": {
     "0": 47,
     "1": 32
    }
   }
  }
 },
 "ROTMATRIX": {
  "count": 129,
  "attrs": {
   "E1": {
    "count": 129,
    "top_values": {
     "1.000000": 125,
     "0.000000": 2,
     "0.994522": 1,
     "0.951057": 1
    }
   },
   "E2": {
    "count": 129,
    "top_values": {
     "0.000000": 125,
     "-1.000000": 2,
     "-0.104528": 1,
     "-0.309017": 1
    }
   },
   "E3": {
    "count": 129,
    "top_values": {
     "0.000000": 127,
     "63410.000000": 1
    }
   },
   "E4": {
    "count": 129,
    "top_values": {
     "0.000000": 125,
     "1.000000": 2,
     "0.104528": 1,
     "0.309017": 1
    }
   },
   "E5": {
    "count": 129,
    "top_values": {
     "1.000000": 125,
     "0.000000": 2,
     "0.994522": 1,
     "0.951057": 1
    }
   },
   "E6": {
    "count": 129,
    "top_values": {
     "0.000000": 127,
     "23662.000000": 1
    }
   }
  }
 },
 "ROW": {
  "count": 1489,
  "attrs": {}
 },
 "SCAMATRIX": {
  "count": 129,
  "attrs": {
   "E1": {
    "count": 129,
    "top_values": {
     "1.000000": 49,
     "0.937386": 17,
     "440.680000": 6,
     "1.470588": 6,
     "436.360000": 4,
     "0.550412": 3,
     "0.508539": 2,
     "1.380660": 2
    }
   },
   "E2": {
    "count": 129,
    "top_values": {
     "0.000000": 127,
     "0.104528": 1,
     "0.309017": 1
    }
   },
   "E3": {
    "count": 129,
    "top_values": {
     "0.000000": 99,
     "2838.000000": 2,
     "-1045.399345": 1,
     "-1986.672006": 1,
     "-27.675282": 1,
     "-718.242446": 1,
     "-1400.544594": 1,
     "-2237.127048": 1
    }
   },
   "E4": {
    "count": 129,
    "top_values": {
     "0.000000": 127,
     "-0.104528": 1,
     "-0.309017": 1
    }
   },
   "E5": {
    "count": 129,
    "top_values": {
     "1.000000": 29,
     "1.091110": 17,
     "0.854856": 14,
     "0.000000": 12,
     "0.542963": 10,
     "1.249333": 6,
     "0.977037": 2,
     "-1.571922": 2
    }
   },
   "E6": {
    "count": 129,
    "top_values": {
     "0.000000": 82,
     "81.000000": 3,
     "1083.000000": 2,
     "1645.000000": 2,
     "265.772045": 1,
     "-294.351130": 1,
     "273.880878": 1,
     "-307.268907": 1
    }
   }
  }
 },
 "SCRIPTCODE": {
  "count": 5,
  "attrs": {
   "Type": {
    "count": 5,
    "top_values": {
     "JScript": 5
    }
   },
   "Version": {
    "count": 5,
    "top_values": {
     "1.0": 5
    }
   }
  }
 },
 "SCRIPTHEADER": {
  "count": 5,
  "attrs": {}
 },
 "SCRIPTSOURCE": {
  "count": 5,
  "attrs": {}
 },
 "SECDEF": {
  "count": 14,
  "attrs": {
   "CharGrid": {
    "count": 14,
    "top_values": {
     "0": 14
    }
   },
   "FirstBorder": {
    "count": 14,
    "top_values": {
     "false": 14
    }
   },
   "FirstFill": {
    "count": 14,
    "top_values": {
     "false": 14
    }
   },
   "LineGrid": {
    "count": 14,
    "top_values": {
     "0": 14
    }
   },
   "MemoShapeId": {
    "count": 1,
    "top_values": {
     "1": 1
    }
   },
   "OutlineShape": {
    "count": 4,
    "top_values": {
     "1": 4
    }
   },
   "SpaceColumns": {
    "count": 14,
    "top_values": {
     "1134": 14
    }
   },
   "TabStop": {
    "count": 14,
    "top_values": {
     "8000": 14
    }
   },
   "TextDirection": {
    "count": 14,
    "top_values": {
     "0": 14
    }
   },
   "TextVerticalWidthHead": {
    "count": 14,
    "top_values": {
     "0": 14
    }
   }
  }
 },
 "SECTION": {
  "count": 14,
  "attrs": {
   "Id": {
    "count": 14,
    "top_values": {
     "0": 5,
     "1": 5,
     "2": 3,
     "3": 1
    }
   }
  }
 },
 "SHADOW": {
  "count": 43,
  "attrs": {
   "Alpha": {
    "count": 43,
    "top_values": {
     "0": 43
    }
   },
   "Color": {
    "count": 43,
    "top_values": {
     "0": 42,
     "11711154": 1
    }
   },
   "OffsetX": {
    "count": 43,
    "top_values": {
     "0": 43
    }
   },
   "OffsetY": {
    "count": 43,
    "top_values": {
     "0": 43
    }
   },
   "Type": {
    "count": 43,
    "top_values": {
     "0": 43
    }
   }
  }
 },
 "SHAPECOMMENT": {
  "count": 33,
  "attrs": {}
 },
 "SHAPECOMPONENT": {
  "count": 79,
  "attrs": {
   "CurHeight": {
    "count": 51,
    "top_values": {
     "2945": 12,
     "948": 2,
     "21202": 2,
     "21353": 2,
     "-172": 1,
     "-54": 1,
     "26745": 1,
     "15269": 1
    }
   },
   "CurWidth": {
    "count": 61,
    "top_values": {
     "9111": 12,
     "43936": 7,
     "44068": 6,
     "43636": 5,
     "1221": 2,
     "28939": 2,
     "36844": 2,
     "43575": 1
    }
   },
   "GroupLevel": {
    "count": 79,
    "top_values": {
     "0": 49,
     "2": 20,
     "1": 10
    }
   },
   "HorzFlip": {
    "count": 79,
    "top_values": {
     "false": 79
    }
   },
   "InstID": {
    "count": 79,
    "top_values": {
     "851017995": 1,
     "435810208": 1,
     "435810209": 1,
     "435810211": 1,
     "435810218": 1,
     "471229164": 1,
     "435810273": 1,
     "872171192": 1
    }
   },
   "OriHeight": {
    "count": 79,
    "top_values": {
     "100": 16,
     "2700": 12,
     "1500": 6,
     "1800": 5,
     "869": 2,
     "383760": 2,
     "84180": 2,
     "5280": 1
    }
   },
   "OriWidth": {
    "count": 79,
    "top_values": {
     "100": 16,
     "9720": 12,
     "3825": 6,
     "3300": 5,
     "43952": 2,
     "1303": 2,
     "523800": 2,
     "145260": 2
    }
   },
   "VertFlip": {
    "count": 79,
    "top_values": {
     "false": 79
    }
   },
   "XPos": {
    "count": 79,
    "top_values": {
     "0": 37,
     "-2838": 2,
     "2504": 1,
     "5824": 1,
     "16240": 1,
     "21052": 1,
     "19560": 1,
     "16964": 1
    }
   },
   "YPos": {
    "count": 79,
    "top_values": {
     "0": 31,
     "-81": 3,
     "-1645": 2,
     "172": 1,
     "54": 1,
     "80": 1,
     "432": 1,
     "416": 1
    }
   }
  }
 },
 "SHAPEOBJECT": {
  "count": 256,
  "attrs": {
   "InstId": {
    "count": 256,
    "top_values": {
     "1696447872": 4,
     "1258795543": 3,
     "1924759818": 1,
     "1244788074": 1,
     "1696447863": 1,
     "1257889392": 1,
     "1257889393": 1,
     "1463196147": 1
    }
   },
   "Lock": {
    "count": 256,
    "top_values": {
     "false": 256
    }
   },
   "NumberingType": {
    "count": 256,
    "top_values": {
     "Table": 198,
     "Figure": 49,
     "None": 9
    }
   },
   "TextFlow": {
    "count": 16,
    "top_values": {
     "BothSides": 16
    }
   },
   "TextWrap": {
    "count": 256,
    "top_values": {
     "TopAndBottom": 224,
     "Square": 16,
     "BehindText": 3
    }
   },
   "ZOrder": {
    "count": 256,
    "top_values": {
     "2": 5,
     "5": 5,
     "4": 5,
     "3": 5,
     "6": 5,
     "1": 5,
     "7": 5,
     "9": 5
    }
   }
  }
 },
 "SIZE": {
  "count": 256,
  "attrs": {
   "Height": {
    "count": 256,
    "top_values": {
     "1": 7,
     "4170": 7,
     "0": 4,
     "5679": 4,
     "56858": 3,
     "8528": 3,
     "4264": 3,
     "50391": 2
    }
   },
   "HeightRelTo": {
    "count": 256,
    "top_values": {
     "Absolute": 256
    }
   },
   "Protect": {
    "count": 256,
    "top_values": {
     "false": 256
    }
   },
   "Width": {
    "count": 256,
    "top_values": {
     "43085": 37,
     "43936": 7,
     "44260": 7,
     "40831": 7,
     "44068": 6,
     "43636": 5,
     "39124": 4,
     "38318": 4
    }
   },
   "WidthRelTo": {
    "count": 256,
    "top_values": {
     "Absolute": 255,
     "Para": 1
    }
   }
  }
 },
 "STARTNUMBER": {
  "count": 14,
  "attrs": {
   "Equation": {
    "count": 14,
    "top_values": {
     "0": 14
    }
   },
   "Figure": {
    "count": 14,
    "top_values": {
     "0": 14
    }
   },
   "Page": {
    "count": 14,
    "top_values": {
     "0": 14
    }
   },
   "PageStartsOn": {
    "count": 14,
    "top_values": {
     "Both": 14
    }
   },
   "Table": {
    "count": 14,
    "top_values": {
     "0": 14
    }
   }
  }
 },
 "STYLE": {
  "count": 232,
  "attrs": {
   "CharShape": {
    "count": 232,
    "top_values": {
     "69": 15,
     "38": 15,
     "70": 14,
     "6": 12,
     "76": 12,
     "40": 10,
     "13": 9,
     "1": 9
    }
   },
   "EngName": {
    "count": 132,
    "top_values": {
     "Normal": 5,
     "xl66": 3,
     "xl70": 3,
     "xl69": 3,
     "xl67": 3,
     "xl68": 3,
     "Body": 2,
     "xl76": 2
    }
   },
   "Id": {
    "count": 232,
    "top_values": {
     "0": 5,
     "1": 5,
     "2": 5,
     "3": 5,
     "4": 5,
     "5": 5,
     "6": 5,
     "7": 5
    }
   },
   "LangId": {
    "count": 232,
    "top_values": {
     "1042": 232
    }
   },
   "LockForm": {
    "count": 232,
    "top_values": {
     "0": 227,
     "1": 5
    }
   },
   "Name": {
    "count": 232,
    "top_values": {
     "xl66": 3,
     "xl70": 3,
     "xl69": 3,
     "xl67": 3,
     "xl68": 3,
     "xl76": 2,
     "xl81": 2,
     "xl79": 2
    }
   },
   "NextStyle": {
    "count": 232,
    "top_values": {
     "6": 6,
     "0": 5,
     "1": 5,
     "3": 5,
     "4": 5,
     "5": 5,
     "7": 5,
     "8": 5
    }
   },
   "ParaShape": {
    "count": 232,
    "top_values": {
     "71": 29,
     "83": 16,
     "81": 11,
     "1": 10,
     "75": 9,
     "84": 7,
     "8": 6,
     "4": 6
    }
   },
   "Type": {
    "count": 232,
    "top_values": {
     "Para": 232
    }
   }
  }
 },
 "STYLELIST": {
  "count": 5,
  "attrs": {
   "Count": {
    "count": 5,
    "top_values": {
     "22": 2,
     "96": 1,
     "60": 1,
     "32": 1
    }
   }
  }
 },
 "SUBJECT": {
  "count": 1,
  "attrs": {}
 },
 "SUBSTFONT": {
  "count": 124,
  "attrs": {
   "Name": {
    "count": 124,
    "top_values": null
   },
   "Type": {
    "count": 124,
    "top_values": {
     "ttf": 121,
     "hft": 3
    }
   }
  }
 },
 "TAB": {
  "count": 1337,
  "attrs": {}
 },
 "TABDEF": {
  "count": 31,
  "attrs": {
   "AutoTabLeft": {
    "count": 31,
    "top_values": {
     "false": 26,
     "true": 5
    }
   },
   "AutoTabRight": {
    "count": 31,
    "top_values": {
     "false": 31
    }
   },
   "Id": {
    "count": 31,
    "top_values": {
     "0": 5,
     "1": 5,
     "2": 5,
     "3": 5,
     "4": 4,
     "5": 2,
     "6": 2,
     "7": 2
    }
   }
  }
 },
 "TABDEFLIST": {
  "count": 5,
  "attrs": {
   "Count": {
    "count": 5,
    "top_values": {
     "5": 2,
     "9": 1,
     "8": 1,
     "4": 1
    }
   }
  }
 },
 "TABITEM": {
  "count": 222,
  "attrs": {
   "Leader": {
    "count": 222,
    "top_values": {
     "None": 210,
     "Dot": 12
    }
   },
   "Pos": {
    "count": 222,
    "top_values": {
     "16000": 5,
     "24000": 5,
     "32000": 5,
     "40000": 5,
     "48000": 5,
     "56000": 5,
     "64000": 5,
     "72000": 5
    }
   },
   "Type": {
    "count": 222,
    "top_values": {
     "Left": 210,
     "Right": 12
    }
   }
  }
 },
 "TABLE": {
  "count": 207,
  "attrs": {
   "BorderFill": {
    "count": 207,
    "top_values": {
     "4": 113,
     "5": 43,
     "2": 30,
     "10": 10,
     "6": 3,
     "90": 2,
     "104": 1,
     "53": 1
    }
   },
   "CellSpacing": {
    "count": 207,
    "top_values": {
     "0": 207
    }
   },
   "ColCount": {
    "count": 207,
    "top_values": {
     "3": 52,
     "1": 50,
     "2": 43,
     "4": 26,
     "6": 14,
     "5": 9,
     "7": 7,
     "8": 3
    }
   },
   "PageBreak": {
    "count": 207,
    "top_values": {
     "Cell": 142,
     "None": 44,
     "Table": 21
    }
   },
   "RepeatHeader": {
    "count": 207,
    "top_values": {
     "true": 206,
     "false": 1
    }
   },
   "RowCount": {
    "count": 207,
    "top_values": {
     "1": 49,
     "5": 24,
     "3": 23,
     "2": 21,
     "7": 13,
     "8": 12,
     "11": 8,
     "6": 8
    }
   }
  }
 },
 "TAIL": {
  "count": 5,
  "attrs": {}
 },
 "TEXT": {
  "count": 9814,
  "attrs": {
   "CharShape": {
    "count": 9814,
    "top_values": {
     "2": 1155,
     "55": 761,
     "3": 752,
     "18": 634,
     "4": 632,
     "7": 506,
     "5": 446,
     "16": 386
    }
   }
  }
 },
 "TEXTMARGIN": {
  "count": 25,
  "attrs": {
   "Bottom": {
    "count": 25,
    "top_values": {
     "283": 20,
     "284": 5
    }
   },
   "Left": {
    "count": 25,
    "top_values": {
     "283": 20,
     "284": 5
    }
   },
   "Right": {
    "count": 25,
    "top_values": {
     "283": 20,
     "284": 5
    }
   },
   "Top": {
    "count": 25,
    "top_values": {
     "283": 20,
     "284": 5
    }
   }
  }
 },
 "TITLE": {
  "count": 2,
  "attrs": {}
 },
 "TOPBORDER": {
  "count": 639,
  "attrs": {
   "Color": {
    "count": 178,
    "top_values": {
     "4278190080": 178
    }
   },
   "Type": {
    "count": 639,
    "top_values": {
     "Solid": 570,
     "None": 62,
     "DoubleSlim": 7
    }
   },
   "Width": {
    "count": 639,
    "top_values": {
     "0.4mm": 242,
     "0.12mm": 186,
     "0.15mm": 94,
     "0.1mm": 68,
     "0.2mm": 19,
     "0.5mm": 15,
     "0.3mm": 12,
     "0.25mm": 3
    }
   }
  }
 },
 "TRANSMATRIX": {
  "count": 79,
  "attrs": {
   "E1": {
    "count": 79,
    "top_values": {
     "1.000000": 79
    }
   },
   "E2": {
    "count": 79,
    "top_values": {
     "0.000000": 79
    }
   },
   "E3": {
    "count": 79,
    "top_values": {
     "0.000000": 37,
     "-2838.000000": 2,
     "2504.000000": 1,
     "5824.000000": 1,
     "16240.000000": 1,
     "21052.000000": 1,
     "19560.000000": 1,
     "16964.000000": 1
    }
   },
   "E4": {
    "count": 79,
    "top_values": {
     "0.000000": 79
    }
   },
   "E5": {
    "count": 79,
    "top_values": {
     "1.000000": 79
    }
   },
   "E6": {
    "count": 79,
    "top_values": {
     "0.000000": 31,
     "-81.000000": 3,
     "-1645.000000": 2,
     "172.000000": 1,
     "54.000000": 1,
     "80.000000": 1,
     "432.000000": 1,
     "416.000000": 1
    }
   }
  }
 },
 "TYPEINFO": {
  "count": 296,
  "attrs": {
   "ArmStyle": {
    "count": 296,
    "top_values": {
     "1": 166,
     "0": 107,
     "2": 16,
     "5": 7
    }
   },
   "Contrast": {
    "count": 296,
    "top_values": {
     "0": 252,
     "2": 37,
     "5": 7
    }
   },
   "FamilyType": {
    "count": 296,
    "top_values": {
     "2": 242,
     "1": 52,
     "4": 2
    }
   },
   "Letterform": {
    "count": 296,
    "top_values": {
     "1": 166,
     "0": 86,
     "2": 44
    }
   },
   "Midline": {
    "count": 296,
    "top_values": {
     "1": 166,
     "0": 107,
     "2": 16,
     "3": 7
    }
   },
   "Proportion": {
    "count": 296,
    "top_values": {
     "0": 191,
     "4": 43,
     "9": 34,
     "3": 28
    }
   },
   "StrokeVariation": {
    "count": 296,
    "top_values": {
     "1": 166,
     "0": 107,
     "2": 16,
     "4": 7
    }
   },
   "Weight": {
    "count": 296,
    "top_values": {
     "6": 187,
     "0": 80,
     "5": 29
    }
   },
   "XHeight": {
    "count": 296,
    "top_values": {
     "1": 166,
     "0": 86,
     "4": 44
    }
   }
  }
 },
 "UNDERLINE": {
  "count": 7,
  "attrs": {
   "Color": {
    "count": 7,
    "top_values": {
     "0": 7
    }
   },
   "Shape": {
    "count": 7,
    "top_values": {
     "Solid": 7
    }
   },
   "Type": {
    "count": 7,
    "top_values": {
     "Bottom": 7
    }
   }
  }
 },
 "WINDOWBRUSH": {
  "count": 261,
  "attrs": {
   "Alpha": {
    "count": 261,
    "top_values": {
     "0": 261
    }
   },
   "FaceColor": {
    "count": 261,
    "top_values": {
     "14079702": 152,
     "4294967295": 30,
     "14277081": 27,
     "16777215": 24,
     "0": 18,
     "65535": 3,
     "15724527": 2,
     "8553090": 2
    }
   },
   "HatchColor": {
    "count": 261,
    "top_values": {
     "0": 215,
     "4278190080": 24,
     "10066329": 20,
     "9025279": 2
    }
   }
  }
 }
}
```

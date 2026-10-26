"""Synthetic two-section cover used only in regression tests."""
import test_write as tw
from fake_hwp import DECL16

def template():
    """공통 템플릿 흉내 HWPML — 표지(머리말·꼬리말·새 번호 그림 1·로고 표 칸 안 그림·결재란·이력서) + 본문 첫 장 제목 '개 요'
    (본문 쪽 설정·새 번호 표 1·쪽 1)."""
    P, table = tw.P, tw._table
    head = '<HEADER ApplyPageType="Both"><PARALIST>%s</PARALIST></HEADER>' % P("{{과제명}} {{문서명}}(v{{버전}})")
    foot = '<FOOTER ApplyPageType="Both"><PARALIST>%s</PARALIST></FOOTER>' % P("{{문서번호}}")
    box = table([[("경   고", "작성자  : {{작성자}}  일   자 : {{결재일자}}", "검토자1 : {{검토자}}  일   자 : {{결재일자}}",
                   "검토자2 : {{검토자}}  일   자 : {{결재일자}}", "승인자  : {{승인자}}    일   자 : {{결재일자}}")]])
    hist = table([["제·개정 일자", "버전번호", "개정내용", "관련근거"], ["{{발행일자}}", " V0.1", "신규 제정", ""],
                  ["{{발행일자}}", " V0.2", "ooo 기능 추가", "ROC 수정"]] + [["", "", "", ""]] * 8)
    logo = table([["로고"]]).replace("<CHAR>로고</CHAR>", '<PICTURE><SHAPEOBJECT NumberingType="Figure"/></PICTURE>')
    cover = [P("문서번호 : {{문서번호}}", pre="<SECDEF/>" + head + foot + '<NEWNUM Number="1" NumberType="Figure"/>'),
             P("제정일자 : {{제정일자}}"), P("개정일자 : {{개정일자}}"), logo,
             P("{{과제명}}", 2), P("{{문서명}}", 1), P("({{문서영문명}})", 1), P("(Ver {{버전}})"), P("{{발행일자}}"),
             P("{{작성기관}}", 1), box, P("제·개정 이력서", 1), hist, P("목     차", 1)]
    st = "".join('<STYLE Id="%d" Name="%s" ParaShape="%d"/>' % (i, n, (i - 7) if n.startswith("COMSAF") else 0)
                 for i, n in enumerate(tw.STYLES))
    ps = '<PARASHAPE Id="0" HeadingType="None" Level="0" Align="Justify"/>' + "".join(
        '<PARASHAPE Id="%d" HeadingType="Outline" Level="%d"/>' % (k + 1, k) for k in range(7))
    body = [P("개 요", tw.STYLES.index("COMSAF 개요 1"), pre=tw.SECDEF_BODY + '<NEWNUM Number="1" NumberType="Table"/>'
              '<NEWNUM Number="1" NumberType="Page"/>')]
    return (DECL16 + '<HWPML Version="2.91"><HEAD SecCnt="2"><MAPPINGTABLE><STYLELIST>%s</STYLELIST>'
            '<PARASHAPELIST>%s</PARASHAPELIST></MAPPINGTABLE></HEAD><BODY><SECTION Id="0">%s</SECTION>'
            '<SECTION Id="1">%s</SECTION></BODY></HWPML>' % (st, ps, "".join(cover), "".join(body)))

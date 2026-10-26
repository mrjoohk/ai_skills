"""HWPML(한/글 GetTextFile 'HWPML2X' 내보내기) → 문서에 포함된 그림 파일 (P-052, D-062).

DRM 문서도 허용 앱(한/글)이 내보낸 HWPML 의 BINDATA(Base64, 압축일 수 있음)를 풀어 쓴다 — 암호 해독·우회가 아니다.
그림을 평문 파일로 꺼내는 것은 사용자가 받은 보안담당자 허락(10-23)에 따른 결정 D-062(D-028 대체)다. 결과는 평문이다.

순서: 본문(BODY)의 PICTURE 를 문서 차례로 k = 1, 2, … — 머리말·꼬리말·바탕쪽 안 그림은 세지 않는다. 표·글상자 안 그림도 센다
(위치에 표시). 연결(Link) 그림·데이터가 없거나 형식을 알 수 없는 그림은 쓰지 않고 이유를 남긴다.
"""
import base64
import hashlib
import re
import xml.etree.ElementTree as ET
import zlib

_BINDATA = re.compile(r"<BINDATA\b([^>]*)>(.*?)</BINDATA>", re.S)
_ATTR = re.compile(r'(\w+)="([^"]*)"')
MM = 283.465
MAGIC = ((b"\x89PNG\r\n\x1a\n", "png"), (b"\xff\xd8\xff", "jpg"), (b"GIF87a", "gif"), (b"GIF89a", "gif"),
         (b"BM", "bmp"), (b"II*\x00", "tif"), (b"MM\x00*", "tif"), (b"\xd7\xcd\xc6\x9a", "wmf"))


def kind_of(b):
    """그림 바이트 → 형식 이름(머리 바이트로) 또는 None. EMF 는 40번째 바이트의 ' EMF'."""
    for m, k in MAGIC:
        if b.startswith(m):
            return k
    if len(b) > 44 and b[40:44] == b" EMF":
        return "emf"
    return None


def decode(payload):
    """BINDATA 내용 → (바이트, 형식, 방법) — Base64 를 풀고, 그림 머리가 아니면 deflate(원시·zlib)로 풀어 본다. 못 풀면
    (None, None, 이유)."""
    try:
        raw = base64.b64decode(re.sub(r"\s+", "", payload), validate=False)
    except (ValueError, TypeError) as e:
        return None, None, "base64 오류: %s" % e
    k = kind_of(raw)
    if k:
        return raw, k, "raw"
    for wbits, how in ((-15, "deflate"), (15, "zlib")):
        try:
            b = zlib.decompress(raw, wbits)
        except zlib.error:
            continue
        k = kind_of(b)
        if k:
            return b, k, how
    return None, None, "그림 형식을 알 수 없다(머리 %s)" % raw[:8].hex()


def bindata(x):
    """원 HWPML → {BINDATA Id: (속성, 내용)}."""
    return {a.get("Id"): (a, body) for a, body in ((dict(_ATTR.findall(m.group(1))), m.group(2))
                                                    for m in _BINDATA.finditer(x))}


def _root(x_clean):
    return ET.fromstring(re.sub("^﻿?\\s*<\\?xml[^>]*\\?>", "", x_clean, count=1))


def pictures(x_clean):
    """정리한 HWPML → 본문 그림 목록 [{"k", "where", "binitem", "title", "size_mm"}] (문서 차례). where = 's<구역>.p<문단>'
    (최상위 문단에 바로 든 그림) 또는 's<구역>.p<문단>+'(그 최상위 문단 안 표·글상자 등)."""
    root = _root(x_clean)
    out = []
    body = root.find("BODY")
    for si, sec in enumerate(body.findall("SECTION") if body is not None else []):
        for pi, p in enumerate(sec.findall("P")):
            direct = {id(e) for t in p.findall("TEXT") for e in t if e.tag == "PICTURE"}
            for pic in p.iter("PICTURE"):
                img = pic.find("IMAGE")
                cap = pic.find("SHAPEOBJECT/CAPTION")
                title = ""
                if cap is not None:
                    title = re.sub(r"^\s*그림\s*", "", " ".join("".join(c.text or "" for c in cap.iter("CHAR")).split()))
                sz = pic.find("SHAPEOBJECT/SIZE")
                size = [round(int(sz.get("Width")) / MM, 1), round(int(sz.get("Height")) / MM, 1)] \
                    if sz is not None and sz.get("Width", "").isdigit() and sz.get("Height", "").isdigit() else None
                out.append({"k": len(out) + 1, "where": "s%d.p%d%s" % (si, pi, "" if id(pic) in direct else "+"),
                            "binitem": img.get("BinItem") if img is not None else None, "title": title, "size_mm": size})
    return out


def binitems(x_clean):
    """정리한 HWPML → BINDATALIST 의 BINITEM 목록(1부터 — IMAGE BinItem 번호)."""
    root = _root(x_clean)
    return [dict(b.attrib) for b in root.iter("BINITEM")]


def extract(x_raw, x_clean):
    """→ (그림 기록 목록, 바이트 목록). 기록마다 file 이름 후보(figKK.형식)·형식·방법·바이트 수·sha256 또는 skip 이유."""
    items, data = binitems(x_clean), bindata(x_raw)
    recs, blobs = [], []
    for pic in pictures(x_clean):
        rec, blob = dict(pic), None
        try:
            bi = items[int(pic["binitem"]) - 1]
        except (TypeError, ValueError, IndexError):
            bi = None
        if bi is None:
            rec["skip"] = "그림 항목(BinItem %s)이 없다" % pic["binitem"]
        elif (bi.get("Type") or "").lower() != "embedding":
            rec["skip"] = "문서에 포함된 그림이 아니다(Type %s)" % bi.get("Type")
        elif bi.get("BinData") not in data:
            rec["skip"] = "그림 데이터(BINDATA %s)가 없다" % bi.get("BinData")
        else:
            blob, kind, how = decode(data[bi["BinData"]][1])
            if blob is None:
                rec["skip"] = how
            else:
                rec.update({"format": kind, "how": how, "bytes": len(blob), "sha256": hashlib.sha256(blob).hexdigest(),
                            "declared": bi.get("Format"), "file": "fig%02d.%s" % (pic["k"], kind)})
        recs.append(rec)
        blobs.append(blob)
    return recs, blobs

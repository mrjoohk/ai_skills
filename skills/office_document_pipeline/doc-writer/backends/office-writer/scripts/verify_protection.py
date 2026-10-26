#!/usr/bin/env python3
"""저장 결과가 DRM 보호를 받고 있는지 확인한다.

쓰기 작업의 마지막 단계는 항상 이것이다. 보호가 다시 걸리지 않은 파일은
원본과 같은 내용을 담은 '무방비 사본'이며, 그것이 유출 경로가 된다.

    python verify_protection.py <파일...>

종료코드: 0 = 전부 보호됨, 1 = 평문 또는 판정불가가 하나라도 있음, 2 = 인자 없음

보호 판정은 알려진 DRM 서명(DOCURAY_SIG)이 있을 때만 내린다. 예전에는 ZIP/OLE2 가
아니면 무엇이든 "보호됨"이라 해서 평문 PDF·TXT 를 놓쳤다 (F-001).
"""
import sys

OLE2 = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"
ZIP = b"PK\x03\x04"
DOCURAY_SIG = b"BMS DocuRay"


def check(path):
    """(protected: bool|None, 설명) 반환. None = 판정 불가."""
    try:
        with open(path, "rb") as f:
            head = f.read(16)
    except OSError as e:
        return None, f"열 수 없음: {e}"

    if not head:
        return None, "빈 파일"

    if head.startswith(DOCURAY_SIG):
        return True, "DocuRay 컨테이너 ('BMS DocuRay')"

    if head.startswith(ZIP):
        return False, "평문 OOXML (PK..) — 보호되지 않음"

    if head.startswith(OLE2):
        try:
            import olefile

            with olefile.OleFileIO(path) as ole:
                streams = {"/".join(p) for p in ole.listdir()}
            if "EncryptedPackage" in streams:
                # 열기암호는 DocuRay 보호가 아니다. write_office_doc.py 의 판정(ole2 → 종료코드 3)과 맞춘다.
                return None, "OLE2 + EncryptedPackage — 열기암호. DocuRay 보호 아님"
            return False, "평문 OLE2 (레거시 형식) — 보호되지 않음"
        except ImportError:
            return None, "OLE2 (olefile 미설치라 상세 판정 불가)"
        except Exception as e:
            return None, f"OLE2 파싱 실패: {e}"

    sig = "".join(chr(b) if 32 <= b < 127 else "." for b in head[:12])
    return None, f"미상 서명 ({sig!r}) — 보호 여부를 알 수 없다. PDF·텍스트 같은 평문일 수 있다"


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2

    leaked = False
    unknown = False
    for path in argv[1:]:
        protected, detail = check(path)
        if protected is True:
            mark = "보호됨"
        elif protected is False:
            mark = "평문 !!"
            leaked = True
        else:
            mark = "판정불가"
            unknown = True
        print(f"  [{mark}] {path}")
        print(f"           {detail}")

    if leaked:
        print()
        print("평문 파일이 있다. 원본이 보호 대상이었다면 이 사본은 통제 밖에 있다.")
        print("- 보호가 필요하면 write_office_doc.py --mode protect 로 다시 저장한다.")
        print("- 필요 없는 중간 산출물이면 삭제한다.")
    if unknown:
        print()
        print("판정불가 파일이 있다. 보호됐다고 가정하지 않는다 — 종료코드 1.")
    return 1 if (leaked or unknown) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

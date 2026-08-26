#!/usr/bin/env python3
"""문서 컨테이너 포맷을 판정해 어떤 판독 경로를 써야 하는지 알려준다.

COM은 느리고 Office 프로세스를 띄우므로, 평문 파일에 쓸 이유가 없다.
어떤 판독을 시도하기 전에 항상 이것부터 실행한다.

    python probe_format.py <파일...>

종료코드: 0 = 전부 평문(파이썬으로 처리 가능), 1 = COM/암호가 필요한 파일 있음
"""
import sys
import zipfile

OLE2 = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"
ZIP = b"PK\x03\x04"


def probe(path):
    """(verdict, detail, advice) 반환."""
    try:
        with open(path, "rb") as f:
            head = f.read(16)
    except OSError as e:
        return "unreadable", str(e), "경로를 확인한다."

    if not head:
        return "unknown", "빈 파일", "원본을 확인한다."

    if head.startswith(ZIP):
        return _probe_zip(path)

    if head.startswith(OLE2):
        return _probe_ole2(path)

    # 그 외 매직은 대개 DRM 래퍼다. 앞부분의 ASCII 서명을 벤더 힌트로 보여준다.
    sig = "".join(chr(b) if 32 <= b < 127 else "." for b in head[:12])
    return (
        "drm_container",
        f"미상 매직: {head[:8].hex(' ')}  ({sig!r})",
        "COM 경로. Read-OfficeDoc.ps1 을 Windows에서 실행한다.",
    )


def _probe_zip(path):
    try:
        with zipfile.ZipFile(path) as z:
            names = set(z.namelist())
            if "[Content_Types].xml" in names:
                kind = "문서"
                if any(n.startswith("xl/") for n in names):
                    kind = "xlsx (openpyxl)"
                elif any(n.startswith("word/") for n in names):
                    kind = "docx (python-docx)"
                elif any(n.startswith("ppt/") for n in names):
                    kind = "pptx (python-pptx)"
                return "plain_ooxml", kind, "파이썬으로 직접 읽는다. COM 불필요."

            mimetype = ""
            if "mimetype" in names:
                try:
                    mimetype = z.read("mimetype").decode("ascii", "replace").strip()
                except Exception:
                    pass
            if "hwp" in mimetype or any(
                n.startswith("Contents/section") for n in names
            ):
                n_sec = sum(1 for n in names if n.startswith("Contents/section"))
                return (
                    "plain_hwpx",
                    f"HWPX, 구역 {n_sec}개, mimetype={mimetype or '없음'}",
                    "read_hwpx.py 로 직접 읽는다. COM 불필요.",
                )
            return "unknown", f"ZIP인데 미상 (mimetype={mimetype!r})", "내용을 직접 확인한다."
    except zipfile.BadZipFile:
        return "drm_container", "ZIP 헤더인데 열리지 않음 (손상 또는 부분 암호화)", "COM 경로."


def _probe_ole2(path):
    try:
        import olefile
    except ImportError:
        return (
            "ole2_legacy",
            "OLE2 (olefile 미설치라 상세 판정 불가)",
            "pip install olefile 후 재실행. 그 전까지는 COM 경로.",
        )
    try:
        with olefile.OleFileIO(path) as ole:
            streams = {"/".join(p) for p in ole.listdir()}
    except Exception as e:
        return "ole2_legacy", f"OLE2 파싱 실패: {e}", "COM 경로."

    if "EncryptedPackage" in streams:
        return (
            "ole2_encrypted",
            "열기암호가 걸린 OOXML (EncryptedPackage 스트림)",
            "msoffcrypto-tool + 암호. 암호가 없으면 COM 경로.",
        )
    if "FileHeader" in streams:
        return (
            "hwp5",
            "HWP 5.0 바이너리",
            "pyhwp(hwp5txt) 를 먼저 시도. 실패하면 COM 경로.",
        )
    if any(s.startswith("Workbook") or s.startswith("Book") for s in streams):
        return "ole2_legacy", "레거시 .xls", "COM 경로 (또는 pandas/xlrd)."
    if "WordDocument" in streams:
        return "ole2_legacy", "레거시 .doc", "COM 경로."
    if "PowerPoint Document" in streams:
        return "ole2_legacy", "레거시 .ppt", "COM 경로."
    return "ole2_legacy", f"OLE2, 스트림 {len(streams)}개", "COM 경로."


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    need_com = False
    for path in argv[1:]:
        verdict, detail, advice = probe(path)
        if not verdict.startswith("plain_"):
            need_com = True
        print(f"{path}")
        print(f"  판정 : {verdict}")
        print(f"  상세 : {detail}")
        print(f"  경로 : {advice}")
    return 1 if need_com else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

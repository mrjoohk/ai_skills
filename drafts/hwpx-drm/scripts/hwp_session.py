#!/usr/bin/env python3
"""한/글(Hwp.exe) COM 세션 — hwpx-drm 스킬의 공통 바닥 (설계 rd/hwpx_drm_design.md UF-01, UF-02).

하는 일
- 한/글이 이미 떠 있으면 시작하지 않는다 (사용자가 편집 중인 문서 보호, F-026)
- pywin32 동적 디스패치로 COM 생성, 이 세션이 띄운 Hwp.exe PID 식별
- 보안승인 모듈 등록 시도 (실패하면 경고 — 열기·저장마다 '접근 허용' 팝업, U-12)
- 모든 COM 호출을 시간 제한으로 감싼다. 넘으면 이 세션의 PID만 종료 (F-019)
- 문서 XML 내보내기는 지원 형식만 (F-047) + UTF-16 선언 교체 (F-034)

DRM 파일은 한/글만 연다. 이 모듈은 파일 바이트를 직접 읽지 않는다 (선두 판정 제외).
"""
import csv
import io
import re
import subprocess
import threading
import time
from pathlib import Path

MODULE_NAME = "FilePathCheckerModule"     # HKCU\SOFTWARE\HNC\HwpAutomation\Modules 의 값 이름
SUPPORTED_EXPORT = ("HWPML2X", "TEXT", "UNICODE")
OPEN_ARG = "lock:false;versionwarning:false;forceopen:true"
_DECL = re.compile(r"^﻿?\s*<\?xml[^>]*\?>")


class HwpError(Exception):
    code = 1


class PreconditionError(HwpError):
    code = 2


class OpenFailed(HwpError):
    code = 4


class TimeoutKilled(HwpError):
    code = 5


class ComUnavailable(HwpError):
    code = 6


def fix_decl(x):
    """GetTextFile('HWPML2X') 문자열의 'encoding="UTF-16"' 선언을 UTF-8 로 바꾼다 (F-034)."""
    if not x:
        return x
    y, n = _DECL.subn('<?xml version="1.0" encoding="UTF-8"?>', x, count=1)
    return y if n else x.lstrip("﻿")


def hwp_pids():
    """실행 중인 Hwp.exe PID 집합 (Windows tasklist)."""
    try:
        out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq Hwp.exe", "/FO", "CSV", "/NH"],
                             capture_output=True, text=True, errors="replace").stdout
    except Exception:
        return set()
    pids = set()
    for row in csv.reader(io.StringIO(out)):
        if len(row) > 1 and row[0].lower() == "hwp.exe" and row[1].isdigit():
            pids.add(int(row[1]))
    return pids


def kill_pid(pid):
    subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True)


def _dispatch():
    import win32com.client.dynamic          # ImportError -> ComUnavailable
    return win32com.client.dynamic.Dispatch("HWPFrame.HwpObject")


def head_kind(path):
    """파일 선두 16바이트로 보호 여부만 판정한다. 내용은 읽지 않는다."""
    try:
        with open(path, "rb") as f:
            b = f.read(16)
    except OSError as e:
        return "UNREADABLE:" + type(e).__name__
    if not b:
        return "EMPTY"
    if b.startswith(b"BMS DocuRay"):
        return "DOCURAY"
    if b.startswith(b"PK\x03\x04"):
        return "PLAIN_ZIP"
    if b.startswith(b"\xd0\xcf\x11\xe0"):
        return "PLAIN_OLE2"
    return "OTHER:" + b[:8].hex()


class HwpSession:
    """with HwpSession() as s: s.open(path); x = s.export_hwpml()

    dispatch/pids/killer 는 시험에서 가짜로 바꿔 끼우기 위한 주입점이다.
    """

    def __init__(self, timeout=180, allow_running=False, dispatch=None, pids=None, killer=None, log=None):
        self.timeout = timeout
        self.allow_running = allow_running
        self._dispatch = dispatch or _dispatch
        self._pids = pids or hwp_pids
        self._kill = killer or kill_pid
        self.log = log or (lambda msg: None)
        self.hwp = None
        self.pid = None
        self.module_ok = False
        self.version = None
        self.fired = False
        self.open_arg_used = None
        self.calls = []                      # (이름, 초) — 실행 기록용, 본문 없음

    # ---------------------------------------------------------- 수명

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *exc):
        self.close()
        return False

    def start(self):
        before = self._pids()
        if before and not self.allow_running:
            raise PreconditionError("한/글(Hwp.exe)이 이미 실행 중이다 - PID %s. 창을 모두 닫고 다시 실행한다." % sorted(before))
        try:
            self.hwp = self._dispatch()
        except ImportError as e:
            raise ComUnavailable("pywin32 가 없다 -> python -m pip install pywin32 (%s)" % e)
        except Exception as e:
            raise ComUnavailable("한/글 COM 생성 실패: %s: %s" % (type(e).__name__, e))
        new = sorted(self._pids() - before)
        self.pid = new[0] if len(new) == 1 else None
        if self.pid is None:
            self.log("경고: 이 세션의 Hwp.exe PID 를 특정하지 못했다 - 시간 제한 감시를 끈다")
        try:
            self.module_ok = bool(self.hwp.RegisterModule("FilePathCheckDLL", MODULE_NAME))
        except Exception:
            self.module_ok = False
        if not self.module_ok:
            self.log("경고: 보안승인 모듈 미등록 - 열기·저장마다 '접근 허용' 창이 뜬다. "
                     "tools\\test_hwpx\\3.setup_hwp_security_module.bat 로 등록")
        try:
            self.version = str(self.hwp.Version)
        except Exception:
            self.version = None
        return self

    def close(self):
        if self.hwp is None:
            return
        if not self.fired:                    # 시간초과로 죽인 프로세스에는 더 부르지 않는다
            try:
                self.hwp.Clear(1)             # 1 = 변경 내용 버림. 이 세션은 명시적 save 외에는 저장하지 않는다
            except Exception:
                pass
            try:
                self.hwp.Quit()
            except Exception:
                pass
        self.hwp = None

    # ---------------------------------------------------------- 감시

    def call(self, name, fn, *args):
        """COM 호출 하나를 시간 제한으로 감싼다. 넘으면 이 세션 PID 만 종료하고 TimeoutKilled."""
        if self.fired:
            raise TimeoutKilled("이전 호출 시간초과로 한/글이 종료됐다")
        timer = None
        if self.pid:
            timer = threading.Timer(self.timeout, self._on_timeout)
            timer.daemon = True
            timer.start()
        t = time.time()
        try:
            result = fn(*args)
        except Exception as e:
            if self.fired:
                raise TimeoutKilled("%s 가 %d초를 넘겨 한/글(PID %s)을 종료했다" % (name, self.timeout, self.pid))
            raise
        finally:
            if timer:
                timer.cancel()
            self.calls.append((name, round(time.time() - t, 2)))
        if self.fired:
            raise TimeoutKilled("%s 가 %d초를 넘겨 한/글(PID %s)을 종료했다" % (name, self.timeout, self.pid))
        return result

    def _on_timeout(self):
        self.fired = True
        self._kill(self.pid)

    # ---------------------------------------------------------- 문서

    def open(self, path, fmt=""):
        p = Path(path).resolve()
        if not p.exists():
            raise PreconditionError("파일이 없다: %s" % p)
        ok = bool(self.call("Open", self.hwp.Open, str(p), fmt, OPEN_ARG))
        self.open_arg_used = OPEN_ARG
        if not ok:                            # 옵션 문자열을 받지 않는 필터 대비 - PoC 에서 검증된 빈 인자로 한 번 더
            ok = bool(self.call("Open", self.hwp.Open, str(p), fmt, ""))
            self.open_arg_used = ""
        if not ok:
            raise OpenFailed("열기 실패 - 열람 권한이 없거나 지원하지 않는 형식이다: %s. 우회하지 말고 권한을 확인한다." % p.name)
        return True

    def export(self, fmt):
        if fmt not in SUPPORTED_EXPORT:       # 지원 안 되는 형식은 %TEMP% 에 임시파일을 남긴다 (F-047)
            raise ValueError("지원하지 않는 내보내기 형식: %s" % fmt)
        v = self.call("GetTextFile:" + fmt, self.hwp.GetTextFile, fmt, "")
        return "" if v is None else str(v)

    def export_hwpml(self):
        return fix_decl(self.export("HWPML2X"))

    def export_text(self):
        return self.export("TEXT")

    def clear(self):
        self.call("Clear", self.hwp.Clear, 1)

    def run(self, action):
        return self.call("Run:" + action, self.hwp.Run, action)

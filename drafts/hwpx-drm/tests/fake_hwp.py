"""시험용 가짜 한/글 COM 객체 — 한/글 없이 hwpx-drm 의 흐름·판정 논리를 시험한다.

실제 한/글의 동작을 흉내 내지 않는다. 흉내 내는 것은 '호출 계약'(메서드 이름·인자·반환 형태)뿐이다.
호출 기록(self.log)으로 '지원 안 되는 형식을 부르지 않았는지' 같은 계약을 검사한다.
"""
import time
from pathlib import Path

DECL16 = '<?xml version="1.0" encoding="UTF-16" standalone="no" ?>'


class _PS:
    def __init__(self):
        self.HSet = object()


class _ParamSets:
    def __getattr__(self, name):              # HInsertText, HTableCreation, HStyle, HHeaderFooter ...
        if not name.startswith("H"):
            raise AttributeError(name)
        ps = _PS()
        object.__setattr__(self, name, ps)
        return ps


class _Action:
    def __init__(self, hwp):
        self.h = hwp

    def GetDefault(self, name, hset):
        return True

    def Execute(self, name, hset):
        self.h.log.append(("Action", name))
        ps = self.h.HParameterSet
        if name == "InsertText":
            self.h.texts.append(ps.HInsertText.Text)
        elif name == "AllReplace":
            f, r = ps.HFindReplace.FindString, ps.HFindReplace.ReplaceString
            self.h.texts = [t.replace(f, r) for t in self.h.texts]
        return True


class FakeHwp:
    def __init__(self, open_ok=True, slow_export=0, version="13, 0, 0, 3903", module_ok=False,
                 save_head=b"BMS DocuRay\x03\x01\x00\x00\x00", hwpml_body=None, fail_actions=()):
        self.open_ok, self.slow_export, self.Version, self.module_ok = open_ok, slow_export, version, module_ok
        self.save_head, self.hwpml_body, self.fail_actions = save_head, hwpml_body, set(fail_actions)
        self.HParameterSet = _ParamSets()
        self.HAction = _Action(self)
        self.log, self.texts, self.fields, self.saved = [], [], {}, {}
        self.quit = False

    # 수명
    def RegisterModule(self, a, b):
        self.log.append(("RegisterModule", a, b))
        return self.module_ok

    def Clear(self, opt):
        self.log.append(("Clear", opt))
        self.texts, self.fields = [], {}

    def Quit(self):
        self.log.append(("Quit",))
        self.quit = True

    # 문서
    def Open(self, path, fmt, arg):
        self.log.append(("Open", Path(path).name, fmt, arg))
        return self.open_ok(path, fmt, arg) if callable(self.open_ok) else self.open_ok

    def GetTextFile(self, fmt, opt):
        self.log.append(("GetTextFile", fmt))
        if self.slow_export:
            time.sleep(self.slow_export)
        if fmt == "HWPML2X":
            body = self.hwpml_body if self.hwpml_body is not None else "".join(
                "<P><TEXT><CHAR>%s</CHAR></TEXT></P>" % t for t in self.texts)
            return DECL16 + "<HWPML Version=\"2.8\"><HEAD/><BODY><SECTION>" + body + "</SECTION></BODY></HWPML>"
        if fmt in ("TEXT", "UNICODE"):
            return "\r\n".join(self.texts)
        return ""

    def SaveAs(self, path, fmt, arg):
        self.log.append(("SaveAs", Path(path).name, fmt))
        Path(path).write_bytes(self.save_head + b"\x00" * 64)
        self.saved[str(Path(path))] = fmt
        return True

    def Run(self, name):
        self.log.append(("Run", name))
        if name in self.fail_actions:
            raise RuntimeError("fake failure: " + name)
        return True

    # 필드
    def CreateField(self, direction, memo, name):
        self.fields[name] = ""
        return True

    def SetCurFieldName(self, name, opt, d, m):
        self.fields[name] = ""
        return True

    def PutFieldText(self, names, values):
        for n, v in zip(names.split("\x02"), values.split("\x02")):
            if n in self.fields:
                self.fields[n] = v

    def GetFieldText(self, names):
        return "\x02".join(self.fields.get(n, "") for n in names.split("\x02"))

    def FieldExist(self, name):
        return name in self.fields

    def GetFieldList(self, number, option):
        return "\x02".join(self.fields)


def make_env(fake, pids_before=(), new_pid=4242):
    """HwpSession 주입용 (dispatch, pids, killer, killed 기록)."""
    state = {"started": False, "killed": []}

    def dispatch():
        state["started"] = True
        return fake

    def pids():
        base = set(pids_before)
        return base | ({new_pid} if state["started"] and new_pid else set())

    def killer(pid):
        state["killed"].append(pid)
    return dispatch, pids, killer, state

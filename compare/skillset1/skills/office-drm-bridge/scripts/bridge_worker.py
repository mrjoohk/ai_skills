# -*- coding: utf-8 -*-
"""office-drm-bridge 워커 (Windows, 사용자가 직접 기동한다).

bridge/inbox 의 요청 JSON 을 폴링해 고정된 연산만 실행한다(오피스: office-com-reader/writer, 한/글: hwpx-drm).
기본은 자동 실행이다(사용자가 채팅에서 제안을 수락한 뒤의 요청). --confirm 을 주면
요청마다 이 콘솔에서 y/N 을 묻는다.

    python bridge_worker.py [--root <저장소>] [--confirm] [--poll 2] [--retention-hours 24]
종료: Ctrl+C
"""
import argparse
import hashlib
import json
import os
import signal
import sys
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bridge_core as core  # noqa: E402

SKILLS = os.path.abspath(os.path.join(HERE, "..", ".."))
SCRIPTS = {
    "read": os.path.join(SKILLS, "office-com-reader", "scripts", "read_office_doc.py"),
    "write": os.path.join(SKILLS, "office-com-writer", "scripts", "write_office_doc.py"),
    "hwpx": os.path.join(SKILLS, "hwpx-drm", "scripts", "hwpx_drm.py"),
}


def console_confirm(req, plan):
    print("\n--- 확인 요청 -----------------------------")
    print(" op      : %s" % plan["op"])
    print(" path    : %s" % req.get("path"))
    print(" 사유    : %s" % req.get("reason"))
    print(" 수락근거: %s" % req.get("plan_ref"))
    return input(" 실행할까요? [y/N] ").strip().lower() == "y"


def process_one(root, name, python, confirm, runner=core.default_runner, scripts=SCRIPTS):
    inbox = os.path.join(root, "bridge", "inbox")
    full = os.path.join(inbox, name)
    rid = name[:-5]
    with open(full, "rb") as f:
        raw = f.read(core.MAX_REQ_BYTES + 1)
    digest = hashlib.sha256(raw).hexdigest()
    done = os.path.join(root, "bridge", "done")
    outp = os.path.join(root, "bridge", "outbox", rid + ".json")
    if not core.ID_RE.match(rid):
        rid = "invalid_" + digest[:8]
        res = {"id": rid, "status": "rejected", "notes": ["파일명이 요청 id 형식이 아니다"]}
        outp = os.path.join(root, "bridge", "outbox", rid + ".json")
    elif os.path.exists(outp) or os.path.exists(os.path.join(done, rid + ".json")):
        res = {"id": rid, "status": "rejected", "notes": ["이미 처리된 id 다 (재사용 거부)"]}
        outp = os.path.join(root, "bridge", "outbox", rid + ".dup-%s.json" % digest[:6])
    else:
        res = core.handle_request(root, raw, rid, python, scripts, runner, confirm)
    core.write_json_atomic(outp, res)
    dest = os.path.join(done, rid + ".json")
    if os.path.exists(dest):
        dest = os.path.join(done, "%s.%s.json" % (rid, digest[:6]))
    os.replace(full, dest)
    core.audit(root, {"id": res.get("id"), "op": res.get("op"), "status": res["status"],
                      "exit_code": res.get("exit_code"), "req_sha256": digest,
                      "path": res.get("path"), "outputs": [o["path"] for o in res.get("outputs", [])]})
    return res


def heartbeat(root, seq, mode):
    core.write_json_atomic(os.path.join(root, "bridge", "worker_alive.json"),
                           {"pid": os.getpid(), "seq": seq, "ts": time.time(), "mode": mode,
                            "version": core.VERSION})


class Beater(object):
    """처리 중에도 하트비트가 이어지게 별도 스레드로 갱신한다.
    (한/글·오피스 요청은 수 초~수십 초 걸리는데, 그동안 갱신이 멈추면 클라이언트가 워커를 꺼진 것으로 오판한다)"""
    def __init__(self, root, mode, interval=2.0):
        self.root, self.mode, self.interval = root, mode, interval
        self.seq = 0
        self._stop = threading.Event()
        self._t = threading.Thread(target=self._run, name="bridge-heartbeat", daemon=True)

    def _run(self):
        while not self._stop.is_set():
            self.seq += 1
            try:
                heartbeat(self.root, self.seq, self.mode)
            except OSError:
                pass
            self._stop.wait(self.interval)

    def start(self):
        self.seq += 1
        heartbeat(self.root, self.seq, self.mode)       # 첫 요청 처리 전에 이미 살아 있음을 알린다
        self._t.start()

    def stop(self):
        self._stop.set()
        if self._t.is_alive():
            self._t.join(timeout=5)


def main(argv=None):
    ap = argparse.ArgumentParser(description="office-drm-bridge 워커")
    ap.add_argument("--root", default=os.path.abspath(os.path.join(HERE, "..", "..", "..", "..")))
    ap.add_argument("--confirm", action="store_true", help="요청마다 콘솔에서 y/N 을 묻는다")
    ap.add_argument("--poll", type=float, default=2.0)
    ap.add_argument("--retention-hours", type=float, default=24.0,
                    help="quarantine/work 의 평문 산출물 보존 시간(초과분 자동 삭제, 0=끔)")
    ap.add_argument("--once", action="store_true", help="대기 중인 요청만 처리하고 끝낸다(시험용)")
    opt = ap.parse_args(argv)
    try:
        sys.stdout.reconfigure(line_buffering=True, errors="replace")
    except Exception:
        pass
    # 콘솔 창을 닫거나 종료 신호를 받아도 하트비트를 지우고 끝낸다(클라이언트가 꺼진 것을 알게)
    for name in ("SIGTERM", "SIGBREAK"):
        if hasattr(signal, name):
            try:
                signal.signal(getattr(signal, name), lambda *a: sys.exit(0))
            except (ValueError, OSError):
                pass
    root = os.path.abspath(opt.root)
    core.ensure_dirs(root)
    mode = "confirm" if opt.confirm else "auto"
    print("office-drm-bridge 워커 v%s | root=%s | 모드=%s" % (core.VERSION, root, mode))
    if sys.platform == "win32":
        try:
            import win32com.client  # noqa: F401
        except ImportError:
            print("경고: pywin32 가 없다 — python -m pip install pywin32 (없으면 읽기/쓰기 요청이 실패한다)")
    for label, key in (("office-com-reader", "read"), ("office-com-writer", "write"), ("hwpx-drm", "hwpx")):
        ok = os.path.isfile(SCRIPTS[key])
        print("  백엔드 %-18s %s" % (label, "있음" if ok else "없음 — 해당 연산은 실패한다"))
    print("  hwpx-drm 지문: %s" % core.tree_sha(os.path.dirname(SCRIPTS["hwpx"])))
    for op, script in (("insert", core.INSERT_SCRIPT), ("figpack", core.FIGPACK_SCRIPT)):
        tool = os.path.join(root, *script)
        print("  백엔드 %-18s %s" % ("%s(doc-writer)" % op, ("있음 · 지문 %s" % core.tree_sha(os.path.dirname(tool)))
                                    if os.path.isfile(tool) else "없음 — %s 연산은 거절된다" % op))
    print("  (한/글 요청은 Hwp.exe 가 떠 있으면 종료코드 2 로 거부된다 — 한/글을 닫아 둔다)")
    print("종료: Ctrl+C\n")
    confirm = console_confirm if opt.confirm else None
    last_purge = 0.0
    beater = Beater(root, mode)
    try:
        beater.start()
        while True:
            if opt.retention_hours > 0 and time.time() - last_purge > 600:
                gone = core.purge_old(root, opt.retention_hours)
                if gone:
                    print("보존기간 초과 평문 산출물 %d개 삭제" % len(gone))
                last_purge = time.time()
            inbox = os.path.join(root, "bridge", "inbox")
            names = sorted(n for n in os.listdir(inbox) if n.endswith(".json"))
            for i, name in enumerate(names):
                if i >= core.MAX_QUEUE:
                    break
                print("[%s] 요청 %s" % (time.strftime("%H:%M:%S"), name))
                try:
                    res = process_one(root, name, sys.executable, confirm)
                    print("   -> %s (exit=%s)" % (res["status"], res.get("exit_code")))
                except Exception as e:
                    print("   -> 처리 중 오류: %s: %s" % (type(e).__name__, e))
            if opt.once:
                return 0
            time.sleep(opt.poll)
    except (KeyboardInterrupt, SystemExit):
        print("\n워커를 종료한다.")
        return 0
    finally:
        beater.stop()
        try:
            os.remove(os.path.join(root, "bridge", "worker_alive.json"))
        except OSError:
            pass


if __name__ == "__main__":
    sys.exit(main())

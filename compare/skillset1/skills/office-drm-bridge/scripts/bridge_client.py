# -*- coding: utf-8 -*-
"""office-drm-bridge 클라이언트 (에이전트 쪽, Linux/Windows 모두).

    python bridge_client.py status
    python bridge_client.py submit --op search --path reference/x.xlsx --reason "..." --plan-ref "..." \
        --args-json '{"pattern":"헬기"}' [--wait 120]
    python bridge_client.py result <id>

종료코드: 0 ok / 1 error·rejected·denied / 2 인자 오류 / 3 대기 시간 초과 / 4 워커가 꺼져 있음
"""
import argparse
import json
import os
import random
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bridge_core as core  # noqa: E402

DEFAULT_ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))


def new_id():
    return "%s_%04x" % (time.strftime("%y%m%d_%H%M%S"), random.randrange(0x10000))


def worker_alive(root, wait=4.0):
    p = os.path.join(root, "bridge", "worker_alive.json")

    def read():
        try:
            with open(p, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None
    hb = read()
    if not hb:
        return False, None
    if abs(time.time() - hb.get("ts", 0)) < 6:      # 워커는 2초마다 갱신한다
        return True, hb
    time.sleep(wait)                      # 시계가 어긋났을 수 있으니 seq 증가로 확인한다
    hb2 = read()
    return bool(hb2 and hb2.get("seq") != hb.get("seq")), hb2


def submit(root, op, path, args, reason, plan_ref, wait):
    if path:
        ap = os.path.abspath(path) if os.path.isabs(path) else path
        if os.path.isabs(ap):
            try:
                ap = os.path.relpath(ap, root)
            except ValueError:
                pass
        path = ap.replace("\\", "/")
    rid = new_id()
    req = {"id": rid, "op": op, "reason": reason, "plan_ref": plan_ref, "args": args}
    if path:
        req["path"] = path
    alive, _ = worker_alive(root)
    if not alive:
        print("워커가 꺼져 있다. 사용자 PC 에서 run_bridge_worker.bat 를 실행해야 한다.")
        return 4
    raw = json.dumps(req, ensure_ascii=False).encode("utf-8")
    try:
        core.validate_request(raw, rid, root)            # 미리 걸러 사유를 바로 본다
    except core.Reject as e:
        print("요청이 거부될 것이다: %s" % e)
        return 1
    tmp = os.path.join(root, "bridge", "inbox", rid + ".json.tmp")
    with open(tmp, "wb") as f:
        f.write(raw)
    os.replace(tmp, os.path.join(root, "bridge", "inbox", rid + ".json"))
    print("제출: %s" % rid)
    return wait_result(root, rid, wait)


def wait_result(root, rid, wait):
    outp = os.path.join(root, "bridge", "outbox", rid + ".json")
    end = time.time() + wait
    while time.time() < end:
        if os.path.exists(outp):
            time.sleep(0.2)
            with open(outp, encoding="utf-8") as f:
                res = json.load(f)
            print(json.dumps(res, ensure_ascii=False, indent=1))
            return 0 if res.get("status") == "ok" else 1
        time.sleep(1.0)
    print("대기 시간 초과 — 결과는 python bridge_client.py result %s 로 다시 확인한다." % rid)
    return 3


def main(argv=None):
    ap = argparse.ArgumentParser(description="office-drm-bridge 클라이언트")
    ap.add_argument("--root", default=DEFAULT_ROOT)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status")
    s = sub.add_parser("submit")
    s.add_argument("--op", required=True, choices=core.OPS,
                   help="오피스: read search dump protect replace fill / 한/글(.hwpx): inspect outline tables fields search verify fill replace / 공통: purge")
    s.add_argument("--path")
    s.add_argument("--args-json", default="{}")
    s.add_argument("--args-file")
    s.add_argument("--reason", required=True)
    s.add_argument("--plan-ref", required=True, help="사용자가 수락한 제안(계획)의 요지")
    s.add_argument("--wait", type=float, default=120.0)
    r = sub.add_parser("result")
    r.add_argument("id")
    opt = ap.parse_args(argv)
    root = os.path.abspath(opt.root)
    if opt.cmd == "status":
        alive, hb = worker_alive(root)
        print("워커: %s %s" % ("켜져 있다" if alive else "꺼져 있다", json.dumps(hb, ensure_ascii=False) if hb else ""))
        return 0 if alive else 4
    if opt.cmd == "result":
        return wait_result(root, opt.id, 0.5)
    try:
        if opt.args_file:
            with open(opt.args_file, encoding="utf-8") as f:
                args = json.load(f)
        else:
            args = json.loads(opt.args_json)
    except Exception as e:
        print("args 를 읽을 수 없다: %s" % e)
        return 2
    return submit(root, opt.op, opt.path, args, opt.reason, opt.plan_ref, opt.wait)


if __name__ == "__main__":
    sys.exit(main())

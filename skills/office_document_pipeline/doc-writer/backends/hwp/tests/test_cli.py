"""hwpx_drm.py 흐름 시험 (가짜 COM) — UF-04~09, 종료코드 계약 REQ-009 의 0~6 을 모두 재현한다."""
import contextlib
import io
import json
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "scripts"))
sys.path.insert(0, str(HERE))
import hwp_session as hs          # noqa: E402
import hwpx_api as api            # noqa: E402
import hwpx_drm as cli            # noqa: E402
from fake_hwp import FakeHwp, make_env, SYN_FULL_HWPML   # noqa: E402

DRM = b"BMS DocuRay\x03\x01" + b"\x00" * 32
SYN_FIELDS = [["SYN_FIELD_A", "clickhere", "SYN_FIELD_A_VALUE"], ["SYN_CELL_02", "cell", "SYN_A_R0C2"]]


class CliBase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.src = self.tmp / "문서.hwpx"
        self.src.write_bytes(DRM)
        self.md = self.tmp / "md"
        self._orig = hs.HwpSession
        self.fake = None

    def tearDown(self):
        hs.HwpSession = self._orig
        shutil.rmtree(self.tmp, ignore_errors=True)

    def use(self, fake, pids_before=(), dispatch=None):
        self.fake = fake
        orig = self._orig

        def factory(**kw):
            d, p, k, st = make_env(fake, pids_before=pids_before)
            self.state = st
            return orig(dispatch=dispatch or d, pids=p, killer=k, sleep=lambda t: None, **kw)
        hs.HwpSession = factory

    def main(self, *argv):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = cli.main([str(a) for a in argv])
        self.out = out.getvalue()
        return code

    def mapfile(self, obj, name="map.json"):
        p = self.tmp / name
        p.write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")
        return p


class TestRead(CliBase):
    def test_inspect_writes_md_only(self):                   # D-012: 읽기 결과는 .md 1개, 원본 불변
        self.use(FakeHwp(hwpml=SYN_FULL_HWPML, fields=SYN_FIELDS))
        before = set(self.tmp.iterdir())
        code = self.main("inspect", self.src, "--md-dir", self.md)
        self.assertEqual(code, 0, self.out)
        made = list(self.md.iterdir())
        self.assertEqual([p.name for p in made], ["문서.inspect.md"])
        self.assertEqual(set(self.tmp.iterdir()) - before, {self.md})
        self.assertEqual(self.src.read_bytes(), DRM)
        md = made[0].read_text(encoding="utf-8")
        self.assertIn("DRM 미보호 평문", md.splitlines()[2])
        for s in ("표 `s0.t1`", "⟨병합 1×2⟩", "⟨병합 2×1⟩", "◀", "▲", "↳ 셀 `s0.t0.r2c0` 안의 중첩 표",
                  "SYN_MEMO_TEXT", "SYN_HEADER", "SYN_FOOTNOTE", "⟦필드 SYN_CELL_02⟧", "### SYN_H1 개요 제목 `s0.p0`",
                  "SYN_P1 본문 첫 문단<br>SYN_P1_LINE2"):
            self.assertIn(s, md)
        self.assertIn("## 메모 (1)", md)
        self.assertNotIn("작성 안내가 많다", md)               # F-084: 메모 성격을 단정하지 않는다
        self.assertNotIn(("GetTextFile", "HWPX"), self.fake.log)
        self.assertNotIn("SaveAs", [e[0] for e in self.fake.log])  # 읽기는 저장하지 않는다

    def test_outline_tables_fields_search(self):
        self.use(FakeHwp(hwpml=SYN_FULL_HWPML, fields=SYN_FIELDS))
        self.assertEqual(self.main("outline", self.src, "--md-dir", self.md), 0)
        self.assertIn("SYN_H1", (self.md / "문서.outline.md").read_text(encoding="utf-8"))
        self.assertEqual(self.main("tables", self.src, "--md-dir", self.md, "--table", "s0.t0.r2c0.t0"), 0)
        t = (self.md / "문서.tables.md").read_text(encoding="utf-8")
        self.assertIn("SYN_N_R0C1", t)
        self.assertNotIn("SYN_B_R0C0", t)
        self.assertEqual(self.main("tables", self.src, "--md-dir", self.md, "--table", "s9.t9"), 1)
        self.assertEqual(self.main("fields", self.src, "--md-dir", self.md, "--json"), 0)
        js = json.loads(self.out[self.out.index("{"):self.out.rindex("}") + 1])
        self.assertEqual(sorted(r["name"] for r in js["input"]), ["SYN_CELL_02", "SYN_FIELD_A"])
        self.assertEqual(self.main("search", self.src, "--md-dir", self.md, "--pattern", "SYN_N_R0C1,없는말"), 0)
        self.assertIn("'SYN_N_R0C1' 1건", self.out)
        self.assertIn("'없는말' 0건", self.out)
        self.assertIn("`s0.t0.r2c0.t0.r0c1`", (self.md / "문서.search.md").read_text(encoding="utf-8"))

    def test_search_escaped_comma(self):                     # P-052: 검색어 안의 쉼표는 '\,' ('\\' = 역슬래시)
        sp = cli.split_patterns
        self.assertEqual(sp("a,b"), ["a", "b"])
        self.assertEqual(sp("가\\, 나,다"), ["가, 나", "다"])
        self.assertEqual(sp("x\\\\,y"), ["x\\", "y"])                  # '\\' 는 역슬래시 하나, 뒤 쉼표는 구분자
        self.assertEqual(sp("C:\\path\\a,b"), ["C:\\path\\a", "b"])    # 다른 역슬래시는 그대로
        self.assertEqual(sp(" , a ,"), ["a"])
        self.assertEqual(sp("끝\\"), ["끝\\"])
        self.use(FakeHwp(hwpml=SYN_FULL_HWPML, fields=SYN_FIELDS))
        self.assertEqual(self.main("search", self.src, "--md-dir", self.md, "--pattern", "SYN_N_R0C1\\,없는말,SYN_N_R0C1"), 0)
        self.assertIn("'SYN_N_R0C1,없는말' 0건", self.out)            # 한 검색어(쉼표 포함)로 찾는다
        self.assertIn("'SYN_N_R0C1' 1건", self.out)

    def test_cp949_console_survives(self):                   # F-050 교훈: 콘솔이 cp949 여도 죽지 않는다
        self.use(FakeHwp(hwpml=SYN_FULL_HWPML))
        buf = io.TextIOWrapper(io.BytesIO(), encoding="cp949")
        old = sys.stdout
        sys.stdout = buf
        try:
            code = cli.main(["search", str(self.src), "--md-dir", str(self.md), "--pattern", "–\U0001F600"])
        finally:
            sys.stdout = old
        self.assertEqual(code, 0)
        with self.assertRaises(UnicodeEncodeError):          # 음성대조: errors=strict 면 같은 글자로 죽는다
            io.TextIOWrapper(io.BytesIO(), encoding="cp949").write("\U0001F600")

    def test_verify(self):
        self.use(FakeHwp(hwpml=SYN_FULL_HWPML))
        self.assertEqual(self.main("verify", self.src), 0)
        plain = self.tmp / "plain.hwpx"
        plain.write_bytes(b"PK\x03\x04" + b"\x00" * 20)
        self.assertEqual(self.main("verify", plain), 0)
        self.assertEqual(self.main("verify", plain, "--protection", "required"), 3)


class TestWrite(CliBase):
    def test_fill_and_missing_key(self):                     # REQ-005, C12
        self.use(FakeHwp(hwpml=SYN_FULL_HWPML, fields=SYN_FIELDS))
        m = self.mapfile({"SYN_FIELD_A": "새 값\n둘째 줄", "NO_SUCH": "x"})
        code = self.main("fill", self.src, "--map", m)
        self.assertEqual(code, 1)                            # 없는 키 → 1 (조용히 넘어가지 않는다)
        self.assertIn("없는 필드 1 NO_SUCH", self.out)
        puts = [e for e in self.fake.log if e[0] == "PutFieldText"]
        self.assertEqual(puts, [("PutFieldText", "SYN_FIELD_A")])   # 없는 키는 넣지도 않는다
        self.assertEqual(self.fake.fields["SYN_FIELD_A"], "새 값\r\n둘째 줄")
        out = self.tmp / "문서_out.hwpx"
        self.assertTrue(out.exists())
        self.assertEqual(hs.head_kind(out), "DOCURAY")
        self.assertEqual(self.src.read_bytes(), DRM)          # 원본 불변
        self.assertIn("원본 불변 True", self.out)

    def test_fill_verifies_by_reading_back(self):            # 음성대조: 넣은 척만 하면 불일치로 1
        self.use(FakeHwp(hwpml=SYN_FULL_HWPML, fields=SYN_FIELDS, put_broken=True))
        code = self.main("fill", self.src, "--map", self.mapfile({"SYN_FIELD_A": "V"}))
        self.assertEqual(code, 1)
        self.assertIn("불일치 1", self.out)

    def test_fill_all_same_name_fields(self):
        fake = FakeHwp(hwpml=SYN_FULL_HWPML, fields=[["F", "clickhere", ""], ["F", "cell", ""]])
        self.use(fake)
        self.assertEqual(self.main("fill", self.src, "--map", self.mapfile({"F": "V"})), 0, self.out)
        self.assertEqual([f[2] for f in fake.flist], ["V", "V"])
        self.assertIn(("PutFieldText", "F"), fake.log)

    def test_fill_indexed_instance(self):                    # 이름{{n}} 은 그 필드 하나만
        fake = FakeHwp(hwpml=SYN_FULL_HWPML, fields=[["F", "clickhere", ""], ["F", "clickhere", ""]])
        self.use(fake)
        self.assertEqual(self.main("fill", self.src, "--map", self.mapfile({"F{{1}}": "둘째"})), 0, self.out)
        self.assertEqual([f[2] for f in fake.flist], ["", "둘째"])

    def test_replace_counts_and_value_containing_key(self):  # REQ-006
        fake = FakeHwp(hwpml=SYN_FULL_HWPML.replace("SYN_P1_TAB", "{{A}}와 {{A}}").replace("SYN_END", "{{B}}"))
        self.use(fake)
        m = self.mapfile({"{{A}}": "x", "{{B}}": "y{{B}}", "{{C}}": "z"})
        code = self.main("replace", self.src, "--map", m, "--log", self.tmp / "log.md")
        self.assertEqual(code, 0, self.out)
        self.assertIn("'{{A}}' 전 2 → 후 0", self.out)
        self.assertIn("'{{B}}' 전 1 → 후 1", self.out)          # 값 안에 키가 있어도 '남음'이 아니다
        self.assertIn("'{{C}}' 전 0 → 후 0 (문서에 없음)", self.out)
        self.assertEqual(sum(1 for e in fake.log if e == ("Action", "AllReplace")), 2)   # 0건 키는 부르지 않는다
        log = (self.tmp / "log.md").read_text(encoding="utf-8")
        self.assertIn("| `{{A}}` | 2 | 0 | 0 |", log)
        self.assertNotIn("SYN_P1", log)                      # 실행 기록에 본문 없음

    def test_replace_leftover_is_code1(self):                # 음성대조: 바뀌지 않으면 남은 위치와 함께 1
        self.use(FakeHwp(hwpml=SYN_FULL_HWPML.replace("SYN_HEADER", "{{H}}"), fail_actions={"AllReplace"}))
        code = self.main("replace", self.src, "--map", self.mapfile({"{{H}}": "머리"}))
        self.assertEqual(code, 1)
        self.assertIn("남음 1: s0.hd0", self.out)

    def test_nothing_to_replace_does_not_save(self):
        self.use(FakeHwp(hwpml=SYN_FULL_HWPML))
        self.assertEqual(self.main("replace", self.src, "--map", self.mapfile({"{{Z}}": "z"})), 1)
        self.assertFalse((self.tmp / "문서_out.hwpx").exists())

    def test_output_exists_force_overwrite(self):            # REQ-007
        self.use(FakeHwp(hwpml=SYN_FULL_HWPML, fields=SYN_FIELDS))
        m = self.mapfile({"SYN_FIELD_A": "V"})
        out = self.tmp / "문서_out.hwpx"
        out.write_bytes(b"old")
        self.assertEqual(self.main("fill", self.src, "--map", m), 2)
        self.assertEqual(out.read_bytes(), b"old")
        self.assertEqual(self.main("fill", self.src, "--map", m, "--force"), 0)
        self.assertEqual(hs.head_kind(out), "DOCURAY")
        self.assertEqual(self.main("fill", self.src, "--map", m, "--overwrite"), 0, self.out)
        baks = sorted(p.name for p in self.tmp.glob("*.bak"))
        self.assertEqual(baks, ["문서.hwpx.bak"])
        self.assertEqual((self.tmp / "문서.hwpx.bak").read_bytes(), DRM)
        self.assertEqual(list(self.tmp.glob("*__hwpxdrm_tmp__*")), [])
        self.assertEqual(self.main("fill", self.src, "--map", m, "--overwrite"), 0)
        self.assertEqual(len(list(self.tmp.glob("*.bak"))), 2)   # .bak 을 덮지 않는다
        self.assertEqual(self.main("fill", self.src, "--map", m, "--overwrite", "--out", out), 2)

    def test_plaintext_save_is_code3(self):
        self.use(FakeHwp(hwpml=SYN_FULL_HWPML, fields=SYN_FIELDS, save_head=b"PK\x03\x04"))
        code = self.main("fill", self.src, "--map", self.mapfile({"SYN_FIELD_A": "V"}))
        self.assertEqual(code, 3)
        self.assertIn("DRM 미적용", self.out)
        self.assertIn("만든 파일:", self.out)

    def test_saveas_hwpx_format_only(self):                  # F-005: 'HWP' 형식으로 저장하지 않는다
        self.use(FakeHwp(hwpml=SYN_FULL_HWPML, fields=SYN_FIELDS))
        self.main("fill", self.src, "--map", self.mapfile({"SYN_FIELD_A": "V"}))
        self.assertEqual({e[2] for e in self.fake.log if e[0] == "SaveAs"}, {"HWPX"})
        self.assertIn(("Open", "문서_out.hwpx", "HWPX", ""), self.fake.log)   # 저장본을 HWPX 로 다시 연다


class TestReviewFixes(CliBase):
    """P-016 당일 델타 검토(독립 검토자) 지적 사항의 회귀 시험. 번호는 검토 보고 번호."""

    def test_r1_overwrite_plaintext_keeps_original(self):    # 평문 결과를 원본 자리에 끼우지 않는다
        self.use(FakeHwp(hwpml=SYN_FULL_HWPML, fields=SYN_FIELDS, save_head=b"PK\x03\x04"))
        code = self.main("fill", self.src, "--map", self.mapfile({"SYN_FIELD_A": "V"}), "--overwrite")
        self.assertEqual(code, 3)
        self.assertEqual(self.src.read_bytes(), DRM)          # 원본 그대로
        self.assertTrue((self.tmp / "문서.hwpx.bak").exists())
        self.assertIn("문서.hwpx.bak", self.out)               # 만든 파일 목록에 원본 사본도
        self.assertIn("__hwpxdrm_tmp__", self.out)

    def test_r1_overwrite_reopen_fail_keeps_original(self):
        fake = FakeHwp(hwpml=SYN_FULL_HWPML, fields=SYN_FIELDS,
                       open_ok=lambda p, f, a: "__hwpxdrm_tmp__" not in str(p))
        self.use(fake)
        code = self.main("fill", self.src, "--map", self.mapfile({"SYN_FIELD_A": "V"}), "--overwrite")
        self.assertEqual(code, 1)
        self.assertEqual(self.src.read_bytes(), DRM)

    def test_r2_write_commands_accept_json(self):
        self.use(FakeHwp(hwpml=SYN_FULL_HWPML, fields=SYN_FIELDS))
        code = self.main("fill", self.src, "--map", self.mapfile({"SYN_FIELD_A": "V"}), "--json")
        self.assertEqual(code, 0, self.out)
        js = json.loads(self.out[self.out.index("\n{") + 1:self.out.rindex("}") + 1])
        self.assertEqual(js["fill"]["filled"], ["SYN_FIELD_A"])
        self.assertEqual(js["save"]["head"], "DOCURAY")

    def test_r3_longer_key_first(self):                       # '○○○' 가 '○○○○' 를 갉아먹지 않는다
        fake = FakeHwp(hwpml=SYN_FULL_HWPML.replace("SYN_END 마지막 문단", "과제: ○○○ / 책임자: ○○○○"))
        self.use(fake)
        code = self.main("replace", self.src, "--map", self.mapfile({"○○○": "AI 개발", "○○○○": "홍길동"}))
        self.assertEqual(code, 0, self.out)
        self.assertIn("과제: AI 개발 / 책임자: 홍길동", fake.hwpml)
        # 음성대조: 입력 순서대로(짧은 키 먼저) 바꾸면 깨진다 - 검토자가 재현한 결과
        self.assertEqual("과제: ○○○ / 책임자: ○○○○".replace("○○○", "AI 개발").replace("○○○○", "홍길동"),
                         "과제: AI 개발 / 책임자: AI 개발○")

    def test_r3_cascade_rejected(self):
        self.use(FakeHwp(hwpml=SYN_FULL_HWPML.replace("SYN_END", "{{A}}")))
        self.assertEqual(self.main("replace", self.src, "--map", self.mapfile({"{{A}}": "{{B}}", "{{B}}": "x"})), 2)
        self.assertIn("연쇄 치환", self.out)

    def test_r4_allreplace_options_explicit(self):
        fake = FakeHwp(hwpml=SYN_FULL_HWPML.replace("SYN_END", "{{A}}"))
        self.use(fake)
        self.main("replace", self.src, "--map", self.mapfile({"{{A}}": "x"}))
        ps = fake.HParameterSet.HFindReplace
        for k, v in api.REPLACE_OPTIONS.items():
            self.assertEqual(getattr(ps, k), v, k)
        self.assertEqual((ps.MatchCase, ps.FindRegExp, ps.UseWildCards, ps.IgnoreMessage, ps.Direction), (1, 0, 0, 1, 2))

    def test_r5_json_ascii_on_cp949(self):
        self.use(FakeHwp(hwpml=SYN_FULL_HWPML.replace("SYN_END", "• 목표 – 시험")))
        raw = io.BytesIO()
        buf = io.TextIOWrapper(raw, encoding="cp949")
        old = sys.stdout
        sys.stdout = buf
        try:
            cli.main(["search", str(self.src), "--md-dir", str(self.md), "--pattern", "목표", "--json"])
        finally:
            buf.flush()
            sys.stdout = old
        text = raw.getvalue().decode("cp949")
        js = json.loads(text[text.index("\n{") + 1:text.rindex("}") + 1])
        self.assertIn("• 목표 – 시험", js["hits"][0]["context"])  # '?' 로 깨지지 않는다

    def test_r6_unexpected_error_still_logs(self):
        class Boom(FakeHwp):
            def FieldExist(self, name):
                raise RuntimeError("com_error 흉내")
        self.use(Boom(hwpml=SYN_FULL_HWPML, fields=SYN_FIELDS))
        log = self.tmp / "log.md"
        code = self.main("fill", self.src, "--map", self.mapfile({"SYN_FIELD_A": "V"}), "--log", log)
        self.assertEqual(code, 1)
        self.assertIn("예상 못 한 오류", self.out)
        self.assertTrue(log.exists())

    def test_r8_plain_and_indexed_keys(self):
        fake = FakeHwp(hwpml=SYN_FULL_HWPML, fields=[["담당", "clickhere", ""], ["담당", "clickhere", ""]])
        self.use(fake)
        m = self.mapfile({"담당{{1}}": "부", "담당": "주"})       # 개별 지정을 먼저 적어도
        self.assertEqual(self.main("fill", self.src, "--map", m), 0, self.out)
        self.assertEqual([f[2] for f in fake.flist], ["주", "부"])   # 개별 지정이 덮이지 않는다

    def test_r9_textbox_table_counted_once_and_drawn(self):
        box = ('<P><TEXT><RECTANGLE><DRAWTEXT><PARALIST><P><TEXT><CHAR>상자</CHAR></TEXT></P><P><TEXT>'
               '<TABLE RowCount="1" ColCount="1"><ROW><CELL RowAddr="0" ColAddr="0" RowSpan="1" ColSpan="1"><PARALIST>'
               '<P><TEXT><CHAR>상자표_ZQ</CHAR></TEXT></P></PARALIST></CELL></ROW></TABLE></TEXT></P>'
               '</PARALIST></DRAWTEXT></RECTANGLE></TEXT></P>')
        self.use(FakeHwp(hwpml=SYN_FULL_HWPML.replace("</SECTION>", box + "</SECTION>")))
        self.main("search", self.src, "--md-dir", self.md, "--pattern", "상자표_ZQ,[표")
        self.assertIn("'상자표_ZQ' 1건", self.out)              # 글상자 글자와 셀에서 두 번 세지 않는다
        self.assertIn("'[표' 0건", self.out)                    # 자리표시가 검색되지 않는다
        self.main("tables", self.src, "--md-dir", self.md)
        self.assertIn("상자표_ZQ", (self.md / "문서.tables.md").read_text(encoding="utf-8"))

    def test_r11_replace_newline_rejected(self):
        self.use(FakeHwp(hwpml=SYN_FULL_HWPML.replace("SYN_END", "{{A}}")))
        self.assertEqual(self.main("replace", self.src, "--map", self.mapfile({"{{A}}": "1\n2"})), 2)

    def test_r12_hwp_source_not_overwritten(self):
        hwp = self.tmp / "old.hwp"
        hwp.write_bytes(DRM)
        self.use(FakeHwp(hwpml=SYN_FULL_HWPML, fields=SYN_FIELDS))
        m = self.mapfile({"SYN_FIELD_A": "V"})
        self.assertEqual(self.main("fill", hwp, "--map", m, "--overwrite"), 2)
        self.assertEqual(hwp.read_bytes(), DRM)
        self.assertEqual(self.main("fill", hwp, "--map", m, "--out", self.tmp / "x.hwp"), 2)
        self.assertEqual(self.main("fill", hwp, "--map", m), 0)  # 기본 출력은 old_out.hwpx
        self.assertTrue((self.tmp / "old_out.hwpx").exists())


class TestExitCodes(CliBase):
    def test_codes_2_4_5_6(self):
        self.use(FakeHwp(), pids_before={999})
        self.assertEqual(self.main("inspect", self.src, "--md-dir", self.md), 2)          # 한/글 실행 중
        self.use(FakeHwp())
        self.assertEqual(self.main("inspect", self.tmp / "없음.hwpx", "--md-dir", self.md), 2)
        self.use(FakeHwp(open_ok=False))
        self.assertEqual(self.main("inspect", self.src, "--md-dir", self.md), 4)
        self.use(FakeHwp(slow_export=1.2))
        self.assertEqual(self.main("inspect", self.src, "--md-dir", self.md, "--timeout", "1"), 5)

        def no_pywin32():
            raise ImportError("No module named 'win32com'")
        self.use(FakeHwp(), dispatch=no_pywin32)
        self.assertEqual(self.main("inspect", self.src, "--md-dir", self.md), 6)
        self.assertFalse(self.md.exists())                    # 실패하면 .md 도 남기지 않는다

    def test_bad_map_is_code2(self):
        self.use(FakeHwp(hwpml=SYN_FULL_HWPML, fields=SYN_FIELDS))
        bad = self.tmp / "bad.json"
        bad.write_text('{"a": "1", "a": "2"}', encoding="utf-8")
        self.assertEqual(self.main("fill", self.src, "--map", bad), 2)
        self.assertIn("중복 키", self.out)


class TestStaticContracts(unittest.TestCase):
    """코드 전체에 걸친 금지 사항 - 누가 나중에 넣어도 시험이 잡는다."""
    SRC = "".join(p.read_text(encoding="utf-8") for p in sorted((HERE.parent / "scripts").glob("*.py")))

    def test_no_whole_document_reinsert(self):               # F-033: 문서 전체 되넣기 금지
        self.assertNotRegex(self.SRC, r"\.SetTextFile\s*\(")

    def test_saveas_only_hwpx_literal(self):                 # F-005: SaveAs 형식 인자는 'HWPX' 하나뿐
        calls = re.findall(r"SaveAs,\s*str\(dest\),\s*\"(\w+)\"", self.SRC)
        self.assertEqual(set(calls), {"HWPX"})


class TestLoadMap(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def w(self, name, text, bom=False):
        p = self.tmp / name
        p.write_bytes((b"\xef\xbb\xbf" if bom else b"") + text.encode("utf-8"))
        return p

    def test_json_bom_and_numbers(self):
        self.assertEqual(api.load_map(self.w("a.json", '{"과제명": "가", "n": 3, "f": 1.10, "g": 1e3, "e": null}', bom=True)),
                         {"과제명": "가", "n": "3", "f": "1.10", "g": "1e3", "e": ""})   # 숫자는 적힌 그대로 (검토 14)

    def test_md_blocks_merged(self):
        p = self.w("a.md", '# 값\n\n```json\n{"a": "1"}\n```\n\n설명\n\n```json\n{"b": "2"}\n```\n')
        self.assertEqual(api.load_map(p), {"a": "1", "b": "2"})

    def test_errors(self):
        for name, text in (("d.json", '{"a": "1", "a": "2"}'), ("n.json", '{"a": {"b": 1}}'),
                           ("x.json", '{"a\\u0002": "1"}'), ("l.json", "[1, 2]"), ("e.json", "{}"),
                           ("m.md", "no json here"), ("b.json", '{"a": true}'), ("dup.md", '```json\n{"a": "1"}\n```\n```json\n{"a": "2"}\n```')):
            with self.assertRaises(api.MapError, msg=name):
                api.load_map(self.w(name, text))
        with self.assertRaises(api.MapError):
            api.load_map(self.tmp / "없음.json")


if __name__ == "__main__":
    unittest.main()

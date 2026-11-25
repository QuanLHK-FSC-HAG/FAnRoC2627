#!/usr/bin/env python3
"""Kiểm chứng webapp FAnRoC2627 sau khi tách bằng tools/split.py.

    python3 tools/verify.py <file-export.html> <thu-muc-repo>

Kiểm tra:
1. node --check mọi file JS.
2. Nội dung main tái tạo từ data/sections/*.js (đúng thứ tự) khớp 100% với
   phần main của bản export (sau khi chuẩn hoá blob .docx về href="").
3. Đủ 9 section đúng thứ tự, đủ 11 bảng, số dòng <tr> mỗi bảng khớp export.
4. Blob .docx trong data/files/ke-hoach-docx.js giống hệt blob trong export.
5. Mọi file < 3,5 MiB.
"""

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

BLOB_RE = re.compile(r"data:application/octet-stream;base64,[A-Za-z0-9+/=]+")
EXPECTED_SECTIONS = [
    "tong-quan", "moc-chinh", "robotics", "drone", "giai-thuong",
    "thiet-bi", "quy-trinh", "cktq", "thuat-ngu",
]
LIMIT = 3_670_016  # 3,5 MiB


def fail(msg):
    print("FAIL:", msg)
    sys.exit(1)


def main():
    if len(sys.argv) != 3:
        print("Dùng: python3 tools/verify.py <file-export.html> <thu-muc-repo>")
        sys.exit(1)
    export = Path(sys.argv[1]).read_text(encoding="utf-8")
    repo = Path(sys.argv[2])
    ok = []

    # 1. node --check
    js_files = sorted(repo.rglob("*.js"))
    for f in js_files:
        r = subprocess.run(["node", "--check", str(f)],
                           capture_output=True, text=True)
        if r.returncode != 0:
            fail(f"node --check {f}: {r.stderr.strip()}")
    ok.append(f"node --check: {len(js_files)} file JS hợp lệ")

    # 2. Blob trong export và trong data file
    blobs = BLOB_RE.findall(export)
    assert len(blobs) == 2 and len({hashlib.md5(b.encode()).hexdigest()
                                     for b in blobs}) == 1
    blob = blobs[0]
    docx_js = (repo / "data/files/ke-hoach-docx.js").read_text(encoding="utf-8")
    m = re.search(r'window\.FANROC_DOCX = (".*");\s*$', docx_js, re.S)
    assert m, "không tìm thấy window.FANROC_DOCX"
    stored = json.loads(m.group(1))
    if stored != blob:
        fail("blob .docx trong data/files/ke-hoach-docx.js KHÁC blob trong export")
    ok.append(f"blob .docx khớp export (md5 "
              f"{hashlib.md5(blob.encode()).hexdigest()}, {len(blob.encode()):,} byte)")

    # 3. Tái tạo nội dung main từ data files, so với export
    #    (export chuẩn hoá: blob -> "" trong href)
    export_nb = export.replace(blob, "")
    exp_main_start = export_nb.find('<main class="wrap">') + len('<main class="wrap">')
    exp_main_end = export_nb.find("</main>")
    exp_main = export_nb[exp_main_start:exp_main_end]

    rebuilt = ""
    for sid in EXPECTED_SECTIONS:
        f = repo / f"data/sections/{sid}.js"
        if not f.exists():
            fail(f"thiếu file data/sections/{sid}.js")
        txt = f.read_text(encoding="utf-8")
        m = re.search(rf'window\.FANROC_SECTIONS\["{sid}"\] = (".*");\s*$',
                      txt, re.S)
        assert m, f"không parse được {f}"
        rebuilt += json.loads(m.group(1))
    if rebuilt != exp_main:
        # Chênh lệch ở đâu (in tối đa 300 ký tự quanh điểm khác đầu tiên)
        i = next((k for k, (a, b) in enumerate(zip(rebuilt, exp_main))
                  if a != b), min(len(rebuilt), len(exp_main)))
        fail(f"nội dung main tái tạo KHÁC export tại ký tự {i}: "
             f"rebuild={rebuilt[max(0, i-80):i+80]!r} "
             f"export={exp_main[max(0, i-80):i+80]!r}")
    ok.append("nội dung <main> tái tạo từ data files khớp 100% bản export")

    # 4. Section / bảng / số dòng
    sec_ids = re.findall(r'<section[^>]*id="([^"]+)"', rebuilt)
    if sec_ids != EXPECTED_SECTIONS:
        fail(f"section sai thứ tự: {sec_ids}")
    exp_tables = re.findall(r"<table[^>]*>(.*?)</table>", export_nb, re.S)
    got_tables = re.findall(r"<table[^>]*>(.*?)</table>", rebuilt, re.S)
    if len(got_tables) != len(exp_tables) != 11:
        fail(f"số bảng: export {len(exp_tables)}, rebuild {len(got_tables)} (cần 11)")
    for i, (e, g) in enumerate(zip(exp_tables, got_tables), 1):
        if e.count("<tr") != g.count("<tr"):
            fail(f"bảng {i}: export {e.count('<tr')} dòng, "
                 f"rebuild {g.count('<tr')} dòng")
    ok.append(f"9 section đúng thứ tự; 11 bảng, số dòng mỗi bảng khớp export "
              f"({[t.count('<tr') for t in got_tables]})")

    # 5. Kích thước file
    biggest = []
    for f in sorted(repo.rglob("*")):
        if f.is_file() and f.suffix != ".py":
            n = f.stat().st_size
            biggest.append((n, str(f.relative_to(repo))))
            if n >= LIMIT:
                fail(f"{f} vượt 3,5 MiB ({n:,} byte)")
    biggest.sort(reverse=True)
    ok.append("mọi file < 3,5 MiB (lớn nhất: "
              + ", ".join(f"{p} {n:,} byte" for n, p in biggest[:3]) + ")")

    # 6. index.html nạp đủ script theo đúng thứ tự
    index = (repo / "index.html").read_text(encoding="utf-8")
    srcs = re.findall(r'<script src="([^"]+)"></script>', index)
    want = (["data/files/ke-hoach-docx.js"] +
            [f"data/sections/{s}.js" for s in EXPECTED_SECTIONS] +
            ["assets/js/app.js"])
    if srcs != want:
        fail(f"thẻ <script> trong index.html sai: {srcs}")
    if 'href="" download' not in index:
        fail("index.html thiếu anchor tải .docx (href=\"\" download)")
    ok.append("index.html nạp đủ 11 script đúng thứ tự; anchor tải .docx có mặt")

    print("VERIFY OK:")
    for line in ok:
        print("  -", line)


if __name__ == "__main__":
    main()

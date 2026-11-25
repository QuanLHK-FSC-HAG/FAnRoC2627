#!/usr/bin/env python3
"""Tách bản export 1 file của không gian FAnRoC (artifact web_static) thành
webapp tĩnh modular cho repo FAnRoC2627.

Chạy lại sau mỗi lần export mới từ không gian:
    python3 tools/split.py <file-export.html> <thu-muc-repo>

Nguyên tắc:
- CHỈ tách cấu trúc, KHÔNG đổi nội dung: mọi section, bảng, dòng, chữ giữ
  nguyên; thứ tự section và id/anchor giữ nguyên.
- CSS (1 khối <style>) -> assets/css/style.css.
- Mỗi section -> data/sections/<id>.js (HTML của section dưới dạng chuỗi JS,
  kèm comment <!-- ... --> đứng trước section đó trong bản export).
- File Word gốc (.docx) được nhúng base64 TRONG BẢN EXPORT TỚI 2 LẦN
  (nút tải ở hero + card "Tài liệu gốc" ở mục Thuật ngữ) và 2 bản giống hệt
  nhau (cùng md5). Script chỉ lưu 1 lần duy nhất tại
  data/files/ke-hoach-docx.js; app.js gán chuỗi này vào href của cả 2 nút
  tải (a[download]) lúc chạy — DOM render ra giống hệt bản export, repo
  nhẹ đi ~2,8 MB. Nếu 2 bản base64 trong export khác nhau, script dừng
  lại và báo lỗi (không tự dedupe).
- Script tìm kiếm + nav của bản export được giữ nguyên verbatim trong
  assets/js/app.js (chạy sau khi các section đã được lắp vào trang).

Giới hạn đẩy GitHub (theo kỹ năng thoc-fschag-webapp): mỗi file < 3,5 MiB,
mỗi lần đẩy <= ~3,5 MiB, chỉ file UTF-8, không file nhị phân.
"""

import hashlib
import json
import re
import sys
from pathlib import Path

EXPECTED_SECTIONS = [
    "tong-quan", "moc-chinh", "robotics", "drone", "giai-thuong",
    "thiet-bi", "quy-trinh", "cktq", "thuat-ngu",
]

BLOB_RE = re.compile(r"data:application/octet-stream;base64,[A-Za-z0-9+/=]+")

APP_JS_TEMPLATE = """/* FAnRoC 2627 — Không gian quản lý nội bộ BTC (webapp tĩnh, không có bước build).
   Lắp các section từ data/sections/*.js vào <main>, khôi phục link tải file
   Word gốc, rồi chạy logic tìm kiếm + nav của bản export (giữ nguyên). */
(function () {
  'use strict';
  var ORDER = __ORDER_JSON__;
  var main = document.querySelector('main.wrap');
  if (main && window.FANROC_SECTIONS) {
    main.innerHTML = ORDER.map(function (id) {
      return window.FANROC_SECTIONS[id] || '';
    }).join('');
  }
  /* File Word gốc (.docx) nhúng base64 1 lần duy nhất tại
     data/files/ke-hoach-docx.js; cả 2 nút tải (hero + mục Thuật ngữ) dùng
     chung chuỗi này — DOM render ra giống hệt bản export. */
  if (window.FANROC_DOCX) {
    document.querySelectorAll('a[download]').forEach(function (a) {
      a.href = window.FANROC_DOCX;
    });
  }
})();
__ORIGINAL_SCRIPT__
"""

README_TEMPLATE = """# FAnRoC 2627 — Không gian quản lý nội bộ BTC

Webapp tĩnh (HTML + CSS + JS, không có bước build) của Không gian quản lý
nội bộ FAnRoC 2026–2027 — FSC Hậu Giang: thể lệ, lịch trình, số đội, giải
vòng cơ sở, thiết bị và quy trình vòng cơ sở (chủ đề CYAN FLAMES — Thanh Hỏa).

> **Lưu hành nội bộ.** Tài liệu này chỉ dùng trong BTC cơ sở FSC Hậu Giang,
> không dùng truyền thông. File Word gốc
> `FAnRoC_2026-2027_Ke_hoach_to_chuc_noi_bo.docx` được nhúng sẵn trong
> webapp (nút "Tải file Word gốc (.docx)" ở đầu trang và ở mục Thuật ngữ).

## Cấu trúc

```
├── index.html            # Shell: hero, nav, <main> (section lắp bằng JS), footer
├── assets/
│   ├── css/style.css     # Toàn bộ CSS từ bản export
│   └── js/app.js         # Lắp section, khôi phục link tải .docx, tìm kiếm + nav
├── data/
│   ├── files/ke-hoach-docx.js   # File Word gốc, nhúng base64 1 lần duy nhất
│   └── sections/*.js     # Mỗi section một file (HTML dưới dạng chuỗi JS)
├── tools/
│   ├── split.py          # Tách bản export mới thành cấu trúc này
│   └── verify.py         # Kiểm chứng sau khi tách
├── vercel.json           # Site tĩnh, không có bước build
└── README.md
```

Nội dung 9 section (đúng thứ tự bản export): Tổng quan, Mốc chính, Robotics,
Drone Soccer, Giải cơ sở, Thiết bị, Quy trình, Tóm tắt CKTQ, Thuật ngữ —
11 bảng. File Word gốc chỉ lưu 1 lần (trong bản export nó bị nhúng 2 lần
giống hệt nhau) nên repo nhẹ hơn bản export ~2,8 MB; trang render ra
giống hệt bản export.

## Deploy lên Vercel

1. Import repo này trên Vercel (Add New → Project → chọn repo `FAnRoC2627`).
2. Framework Preset: **Other** (không chọn framework nào).
3. Build Command: để trống; Output Directory: để trống (thư mục gốc).
4. Deploy. Vercel cấp link `*.vercel.app`; có thể gắn tên miền riêng sau.

## Chạy local

Mở trực tiếp `index.html` bằng trình duyệt (webapp không dùng `fetch()`
nên chạy được cả với `file://`), hoặc chạy server tĩnh:

```bash
python3 -m http.server 8000
# mở http://localhost:8000
```

## Cập nhật nội dung

Một nguồn sự thật là không gian trên Muse (artifact
`fanroc-2627-khong-gian-quan-ly-noi-bo-btc`): sửa nội dung trên không gian
trước, rồi export bản mới và chạy lại:

```bash
python3 tools/split.py <file-export.html> .
python3 tools/verify.py <file-export.html> .
```

Kiểm chứng: `node --check` mọi file JS; đủ 9 section đúng thứ tự, đủ
11 bảng, số dòng mỗi bảng khớp bản export; mọi file < 3,5 MiB.
"""


def js_string(text: str) -> str:
    """Mã hoá HTML thành chuỗi JS (JSON string là chuỗi JS hợp lệ)."""
    return json.dumps(text, ensure_ascii=False)


def main() -> None:
    if len(sys.argv) != 3:
        print("Dùng: python3 tools/split.py <file-export.html> <thu-muc-repo>")
        sys.exit(1)
    export_path = Path(sys.argv[1])
    repo = Path(sys.argv[2])
    html = export_path.read_text(encoding="utf-8")

    # --- 1. Kiểm tra các blob base64 của file .docx: phải giống hệt nhau ---
    blobs = BLOB_RE.findall(html)
    if not blobs:
        print("LỖI: không tìm thấy link base64 file .docx trong bản export.")
        sys.exit(1)
    md5s = {hashlib.md5(b.encode()).hexdigest() for b in blobs}
    if len(md5s) != 1:
        print(f"LỖI: bản export có {len(blobs)} blob base64 KHÁC nhau "
              f"({len(md5s)} md5) — không dedupe được, dừng lại.")
        sys.exit(1)
    blob = blobs[0]
    print(f"Blob .docx: {len(blobs)} lần nhúng, giống hệt nhau "
          f"(md5 {md5s.pop()}, {len(blob.encode()):,} byte) -> lưu 1 lần.")

    # Bỏ blob khỏi HTML, để lại href="" (app.js gán lại lúc chạy).
    html_nb = html.replace(blob, "")

    # --- 2. CSS ---
    m_style = re.search(r"<style>(.*?)</style>", html_nb, re.S)
    assert m_style, "không tìm thấy khối <style>"
    css = m_style.group(1)
    (repo / "assets/css").mkdir(parents=True, exist_ok=True)
    (repo / "assets/css/style.css").write_text(css, encoding="utf-8")
    print(f"CSS: {len(css.encode()):,} byte -> assets/css/style.css")

    # --- 3. Script gốc (tìm kiếm + nav), giữ nguyên verbatim ---
    m_script = re.search(r"<script>(.*?)</script>", html_nb, re.S)
    assert m_script, "không tìm thấy khối <script>"
    # Chỉ lấy NỘI DUNG bên trong <script> (bản thân nó đã là một IIFE);
    # thẻ <script> không được đưa vào file .js.
    orig_script = m_script.group(1)

    # --- 4. Thứ tự section ---
    sec_ids = re.findall(r'<section[^>]*id="([^"]+)"', html_nb)
    assert sec_ids == EXPECTED_SECTIONS, f"thứ tự section lạ: {sec_ids}"
    print(f"Sections: {len(sec_ids)} ({', '.join(sec_ids)})")

    # --- 5. Tách từng section (kèm comment + khoảng trắng đứng trước nó) ---
    sec_positions = [(m.group(1), m.start()) for m in
                     re.finditer(r'<section[^>]*id="([^"]+)"', html_nb)]
    main_open_end = html_nb.find('<main class="wrap">') + len('<main class="wrap">')
    (repo / "data/sections").mkdir(parents=True, exist_ok=True)
    (repo / "data/files").mkdir(parents=True, exist_ok=True)
    for i, (sid, start) in enumerate(sec_positions):
        prev_end = main_open_end if i == 0 else html_nb.find(
            "</section>", sec_positions[i - 1][1]) + len("</section>")
        end = html_nb.find("</section>", start) + len("</section>")
        if i == len(sec_positions) - 1:
            # Section cuối: lấy luôn khoảng trắng tới </main> để nội dung
            # <main> tái tạo khớp 100% bản export.
            end = html_nb.find("</main>", start)
        chunk = html_nb[prev_end:end]
        assert chunk.lstrip().startswith("<!--") or i == 0, sid
        assert chunk.rstrip().endswith("</section>"), sid
        out = (repo / f"data/sections/{sid}.js")
        out.write_text(
            f"// FAnRoC 2627 — section \"{sid}\" "
            f"(tách từ bản export của không gian; nội dung giữ nguyên)\n"
            f"window.FANROC_SECTIONS = window.FANROC_SECTIONS || {{}};\n"
            f"window.FANROC_SECTIONS[{json.dumps(sid)}] = "
            f"{js_string(chunk)};\n",
            encoding="utf-8")
        print(f"  {sid}: {len(chunk.encode()):,} byte -> {out.relative_to(repo)}")

    # --- 6. File .docx nhúng 1 lần ---
    docx_js = (repo / "data/files/ke-hoach-docx.js")
    docx_js.write_text(
        "// File Word gốc FAnRoC_2026-2027_Ke_hoach_to_chuc_noi_bo.docx, "
        "nhúng base64 1 lần duy nhất.\n"
        "// Trong bản export, file này bị nhúng 2 lần giống hệt nhau (nút tải "
        "ở hero + card \"Tài liệu gốc\" ở mục Thuật ngữ); cả 2 nút đều dùng "
        "chung chuỗi này, app.js gán vào href lúc chạy.\n"
        f"window.FANROC_DOCX = {js_string(blob)};\n",
        encoding="utf-8")
    print(f"  ke-hoach-docx.js: {len(blob.encode()) + 22:,} byte "
          f"(blob {len(blob.encode()):,} byte)")

    # --- 7. index.html: shell ---
    head_end = html_nb.find("</head>") + len("</head>")
    head = html_nb[:head_end]
    head = re.sub(r"<style>.*?</style>",
                  '<link rel="stylesheet" href="assets/css/style.css">',
                  head, flags=re.S, count=1)
    body_open = html_nb[html_nb.find("<body>"):
                        html_nb.find('<main class="wrap">') + len('<main class="wrap">')]
    # Phần sau section cuối: </main> + footer (bỏ script gốc, thay bằng thẻ script)
    last_sec_end = html_nb.find("</section>", sec_positions[-1][1]) + len("</section>")
    tail = html_nb[last_sec_end:]
    tail = re.sub(r"<script>.*?</script>", "", tail, flags=re.S, count=1)
    script_tags = "\n".join(
        ['<script src="data/files/ke-hoach-docx.js"></script>'] +
        [f'<script src="data/sections/{sid}.js"></script>' for sid in sec_ids] +
        ['<script src="assets/js/app.js"></script>'])
    tail = tail.replace("</body>", script_tags + "\n</body>")
    index_html = head + "\n" + body_open + tail
    (repo / "index.html").write_text(index_html, encoding="utf-8")
    print(f"index.html: {len(index_html.encode()):,} byte")

    # --- 8. app.js ---
    app_js = (APP_JS_TEMPLATE
              .replace("__ORDER_JSON__", json.dumps(sec_ids))
              .replace("__ORIGINAL_SCRIPT__", orig_script))
    (repo / "assets/js/app.js").write_text(app_js, encoding="utf-8")
    print(f"assets/js/app.js: {len(app_js.encode()):,} byte")

    # --- 9. vercel.json + README.md ---
    (repo / "vercel.json").write_text(
        '{"$schema": "https://openapi.vercel.sh/vercel.json"}',
        encoding="utf-8")
    (repo / "README.md").write_text(README_TEMPLATE, encoding="utf-8")
    print("vercel.json + README.md: xong")

    # --- 10. Kiểm tra kích thước ---
    print("\nKích thước file (giới hạn 3,5 MiB = 3.670.016 byte):")
    too_big = False
    for f in sorted(repo.rglob("*")):
        if f.is_file() and f.suffix not in {".py"}:
            n = f.stat().st_size
            flag = "  <-- VƯỢT GIỚI HẠN" if n >= 3_670_016 else ""
            if flag:
                too_big = True
            print(f"  {f.relative_to(repo)}: {n:,} byte{flag}")
    if too_big:
        print("LỖI: có file vượt 3,5 MiB.")
        sys.exit(1)
    print("\nXong. Chạy tiếp: python3 tools/verify.py <file-export.html> .")


if __name__ == "__main__":
    main()

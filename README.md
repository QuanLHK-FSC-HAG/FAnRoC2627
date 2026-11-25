# FAnRoC 2627 — Không gian quản lý nội bộ BTC

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

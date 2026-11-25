#!/usr/bin/env node
/* Kiểm chứng render thật của webapp FAnRoC2627 bằng jsdom:
   nạp index.html + toàn bộ script, rồi kiểm tra DOM render ra.
   Dùng: node tools/render-check.js [thu-muc-repo] */
const fs = require('fs');
const path = require('path');
const { JSDOM, VirtualConsole } = require('/tmp/jsdom-test/node_modules/jsdom');

const repo = process.argv[2] || path.join(__dirname, '..');
const indexPath = path.resolve(path.join(repo, 'index.html'));
let html = fs.readFileSync(indexPath, 'utf8');
// Bỏ link Google Fonts để test không cần mạng (không ảnh hưởng cấu trúc).
html = html.replace(/<link[^>]*fonts\.googleapis\.com[^>]*>/g, '');

const errors = [];
const vc = new VirtualConsole();
vc.on('jsdomError', (e) => errors.push('jsdomError: ' + (e.detail && e.detail.stack || e.message)));
vc.on('error', (...a) => errors.push('console.error: ' + a.join(' ')));

const dom = new JSDOM(html, {
  url: 'file://' + indexPath,
  runScripts: 'dangerously',
  resources: 'usable',
  virtualConsole: vc,
  beforeParse(window) {
    window.IntersectionObserver = class {
      constructor() {}
      observe() {}
      unobserve() {}
      disconnect() {}
    };
  },
});

function fail(msg) { console.error('RENDER FAIL:', msg); process.exit(1); }

dom.window.addEventListener('load', () => {
  setTimeout(() => {
    const d = dom.window.document;
    const ok = [];
    try {
      // 1. Sections trong <main>
      const secs = [...d.querySelectorAll('main.wrap > section')].map((s) => s.id);
      const want = ['tong-quan', 'moc-chinh', 'robotics', 'drone', 'giai-thuong', 'thiet-bi', 'quy-trinh', 'cktq', 'thuat-ngu'];
      if (JSON.stringify(secs) !== JSON.stringify(want)) fail('section trong main sai: ' + JSON.stringify(secs));
      ok.push('9 section trong <main>, đúng thứ tự: ' + secs.join(', '));

      // 2. Bảng + số dòng
      const tables = [...d.querySelectorAll('table')];
      if (tables.length !== 11) fail('số bảng: ' + tables.length);
      const rows = tables.map((t) => t.querySelectorAll('tr').length);
      const wantRows = [3, 7, 4, 4, 9, 7, 6, 20, 21, 25, 7];
      if (JSON.stringify(rows) !== JSON.stringify(wantRows)) fail('số dòng/bảng sai: ' + JSON.stringify(rows));
      ok.push('11 bảng, số dòng mỗi bảng khớp export: [' + rows.join(', ') + ']');

      // 3. Hai nút tải .docx: href là blob đầy đủ, giống nhau
      const crypto = require('crypto');
      const dls = [...d.querySelectorAll('a[download]')];
      if (dls.length !== 2) fail('số nút tải .docx: ' + dls.length);
      const hrefs = dls.map((a) => a.getAttribute('href'));
      const md5s = hrefs.map((h) => crypto.createHash('md5').update(h).digest('hex'));
      if (md5s[0] !== md5s[1]) fail('2 nút tải có href khác nhau');
      if (!hrefs[0].startsWith('data:application/octet-stream;base64,UEsDB')) fail('href tải không phải file .docx base64');
      ok.push('2 nút tải .docx có href đầy đủ, giống nhau (md5 ' + md5s[0] + ', ' + hrefs[0].length.toLocaleString('en-US') + ' ký tự)');

      // 4. Nav: 9 link anchor đúng section (thứ tự nav trong bản export:
      //    cktq đứng trước thiet-bi, khác thứ tự section — giữ nguyên)
      const navHrefs = [...d.querySelectorAll('.nav a')].map((a) => a.getAttribute('href'));
      const wantNav = ['#tong-quan', '#moc-chinh', '#robotics', '#drone', '#giai-thuong', '#cktq', '#thiet-bi', '#quy-trinh', '#thuat-ngu'];
      if (JSON.stringify(navHrefs) !== JSON.stringify(wantNav)) fail('nav sai: ' + JSON.stringify(navHrefs));
      ok.push('nav đủ 9 link anchor đúng section (đúng thứ tự bản export)');

      // 5. Tìm kiếm: gõ "robotics" chỉ còn section chứa từ đó; xoá thì hiện lại hết
      const q = d.getElementById('q');
      q.value = 'robotics';
      q.dispatchEvent(new dom.window.Event('input', { bubbles: true }));
      const hidden = [...d.querySelectorAll('section.hidden-by-search')].map((s) => s.id);
      const visible = secs.filter((id) => !hidden.includes(id));
      if (!visible.includes('robotics') || visible.length >= secs.length) fail('tìm kiếm sai: visible=' + JSON.stringify(visible));
      q.value = '';
      q.dispatchEvent(new dom.window.Event('input', { bubbles: true }));
      if (d.querySelectorAll('section.hidden-by-search').length !== 0) fail('xoá tìm kiếm không hiện lại hết');
      ok.push('tìm kiếm hoạt động: gõ "robotics" còn ' + visible.length + ' section hiện (' + visible.join(', ') + '), xoá thì hiện lại đủ 9');

      // 6. Hero + footer
      const h1 = d.querySelector('.hero h1');
      if (!h1 || !h1.textContent.includes('FAnRoC')) fail('thiếu tiêu đề hero');
      const footer = d.querySelector('footer');
      if (!footer || !footer.textContent.includes('CYAN FLAMES')) fail('thiếu footer');
      ok.push('hero + footer đầy đủ');

      if (errors.length) fail('lỗi JS/console khi render: ' + errors.slice(0, 3).join(' | '));
      ok.push('không có lỗi JS/console khi render');
    } catch (e) {
      fail(e.message);
    }
    console.log('RENDER OK:');
    ok.forEach((l) => console.log('  -', l));
    process.exit(0);
  }, 800);
});

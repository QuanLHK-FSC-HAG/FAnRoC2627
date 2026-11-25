/* FAnRoC 2627 — Không gian quản lý nội bộ BTC (webapp tĩnh, không có bước build).
   Lắp các section từ data/sections/*.js vào <main>, khôi phục link tải file
   Word gốc, rồi chạy logic tìm kiếm + nav của bản export (giữ nguyên). */
(function () {
  'use strict';
  var ORDER = ["tong-quan", "moc-chinh", "robotics", "drone", "giai-thuong", "thiet-bi", "quy-trinh", "cktq", "thuat-ngu"];
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

(function(){
  var q=document.getElementById('q');
  var secs=document.querySelectorAll('[data-search]');
  function norm(s){return (s||'').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/đ/g,'d');}
  q.addEventListener('input',function(){
    var v=norm(q.value.trim());
    secs.forEach(function(s){
      if(!v){s.classList.remove('hidden-by-search');return;}
      s.classList.toggle('hidden-by-search', norm(s.textContent).indexOf(v)===-1);
    });
  });
  // active nav
  var links=document.querySelectorAll('.nav a');
  var obs=new IntersectionObserver(function(es){
    es.forEach(function(e){
      if(e.isIntersecting){
        links.forEach(function(a){a.classList.toggle('active', a.getAttribute('href')==='#'+e.target.id);});
      }
    });
  },{rootMargin:'-30% 0px -60% 0px'});
  secs.forEach(function(s){obs.observe(s);});
  ['giai-thuong','thiet-bi','quy-trinh','cktq','thuat-ngu'].forEach(function(id){var el=document.getElementById(id); if(el) obs.observe(el);});
})();


// tests/test_thanh_dau_khong_vo_dong.js
//
// Tên tệp đang mở KHÔNG được quấn dòng trong thanh đầu.
//
// VÌ SAO CÓ TỆP NÀY. 01/09/2026, Sếp chụp màn hình: chỗ hiện tên bài mẫu biến
// thành MỘT CỤC TRÒN cao nghều, chữ "Hàm cộng hai số" quấn 4-5 dòng, và nó đè
// lên dòng "Hợp lệ · 0 Lỗi · 0 Cảnh báo" bên dưới.
//
// Đo được, cùng khung 1920, chỉ đổi tên tệp:
//     a.py                          1 dòng · pill 44px · y=6    ✓
//     dong_ho.py                    1 dòng · pill 44px · y=6    ✓
//     core/local_first_gateway.py   1 dòng · pill 59px · y=-2    (chỉ tràn ngang)
//     "1. Hàm cộng hai số"          3 DÒNG · pill 62px · y=-3   ✗
// Ở 1366: tên co còn 32px rộng / 80px cao (5 dòng), pill cao 94px từ y=-19.
//
// Thủ phạm là DẤU CÁCH. `.file-name` không có lấy một dòng CSS nên nhận
// `white-space: normal`; tên có dấu cách thì quấn. Tên không dấu cách không
// quấn được nên chỉ tràn ngang — chính vì thế bệnh nấp được lâu.
//
// Đắt gấp đôi vì "1. Hàm cộng hai số" là BÀI MẪU MỞ SẴN: mọi người mở app lần
// đầu đều gặp nó ở màn hình đầu tiên — kể cả người thử nhận gói .exe.
//
// GỐC vẫn là `min-width: auto` của flex item — đúng con đã cắn `.header-actions`
// ngày 30/08. Lần này ở phần tử anh em mà lượt vá trước bỏ sót. Cửa này canh cả
// bốn khai báo, vì gỡ bất kỳ cái nào cũng đủ làm bệnh quay lại.

const assert = require('node:assert');
const { test } = require('node:test');
const fs = require('node:fs');
const path = require('node:path');

const { bocChuThich } = require('../tools/boc_chu_thich.js');

// Bọc qua bocChuThich: 30/08 đo được 5/6 cửa dò chuỗi bị chú thích lừa, và
// chú thích ở ĐẦU chính tệp này có đủ mọi chữ mà các khẳng định dưới đang tìm.
const CSS = bocChuThich(fs.readFileSync(
  path.join(__dirname, '..', 'interface', 'web', 'the_v1', 'style.css'), 'utf8'));

/**
 * Đọc các khai báo của MỘT bộ chọn, không dò chuỗi con trên cả tệp.
 *
 * Dò chuỗi con ở đây sai theo đúng kiểu CLAUDE.md mục 4 cảnh báo: tìm
 * `white-space: nowrap` trên cả `style.css` thì khớp ở 40 chỗ khác, và cửa
 * xanh kể cả khi `.file-name` không có dòng nào.
 */
function khaiBaoCua(boChon) {
  const cacKhoi = [];
  // Bắt cả khi bộ chọn đứng chung nhóm: `.a,\n.b { ... }`
  const re = new RegExp(
    `(^|})([^{}]*?(?:^|,|\\s)${boChon.replace('.', '\\.')}\\s*(?:,[^{}]*?)?)\\{([^}]*)\\}`,
    'gm');
  let m;
  while ((m = re.exec(CSS)) !== null) {
    const dauKhoi = m[2];
    const dungLa = dauKhoi
      .split(',')
      .map((s) => s.trim())
      .some((s) => s === boChon);
    if (dungLa) cacKhoi.push(m[3]);
  }
  const ra = new Map();
  for (const than of cacKhoi) {
    for (const dong of than.split(';')) {
      const i = dong.indexOf(':');
      if (i < 0) continue;
      ra.set(dong.slice(0, i).trim(), dong.slice(i + 1).trim());
    }
  }
  return ra;
}

test('bộ đọc CSS tự nó phải đúng — không thì mọi khẳng định dưới vô nghĩa', () => {
  // Ca đối chứng cho chính máy đo: một bộ chọn CHẮC CHẮN có và một cái chắc
  // chắn không. Thiếu cái này thì `khaiBaoCua` trả Map rỗng cho mọi thứ và cả
  // tệp xanh vì lý do sai.
  assert.ok(khaiBaoCua('.file-status-bar').size > 0, 'không đọc nổi .file-status-bar');
  assert.strictEqual(khaiBaoCua('.khong-he-ton-tai-abc123').size, 0,
    'đọc ra khai báo cho một bộ chọn không tồn tại — bộ đọc khớp bừa');
});

test('.file-name cắt bằng … thay vì quấn dòng', () => {
  const kb = khaiBaoCua('.file-name');
  assert.strictEqual(kb.get('white-space'), 'nowrap',
    'thiếu nowrap là tên có dấu cách quấn dòng — đúng cục tròn 01/09');
  assert.strictEqual(kb.get('overflow'), 'hidden');
  assert.strictEqual(kb.get('text-overflow'), 'ellipsis',
    'không có ellipsis thì tên dài bị cắt cụt mà không có dấu hiệu gì');
  assert.strictEqual(kb.get('min-width'), '0',
    'flex item mặc định `min-width: auto` — từ chối co, đẩy tràn cả thanh');
});

test('.file-status-bar giữ đủ chỗ cho tên, có trần', () => {
  const kb = khaiBaoCua('.file-status-bar');
  assert.strictEqual(kb.get('flex-shrink'), '0',
    'để nó co theo tỉ lệ thì tên hụt chữ ngay ở 1920: cần 112px, được 86px');
  assert.ok(kb.has('max-width'),
    'không có trần thì một đường dẫn dài đẩy mọi thứ khác ra ngoài màn hình');
  assert.strictEqual(kb.get('min-width'), '0');
});

test('.tab-bar phải NHƯỜNG — nó có overflow-x nên cuộn được', () => {
  const kb = khaiBaoCua('.tab-bar');
  assert.strictEqual(kb.get('overflow-x'), 'auto');
  assert.strictEqual(kb.get('flex-shrink'), '1',
    'trước đây là 0: có cửa cuộn mà không bao giờ được dùng. Đo ở 1024: ' +
    'trang tràn 122px và btnRun mép phải 1106 -> ngoài màn hình');
  assert.strictEqual(kb.get('min-width'), '0');
});

test('.header-actions-scroll nhường TRƯỚC mọi thứ khác', () => {
  const kb = khaiBaoCua('.header-actions-scroll');
  assert.strictEqual(kb.get('overflow-x'), 'auto');
  const hs = Number(kb.get('flex-shrink'));
  assert.ok(Number.isFinite(hs) && hs >= 10,
    `flex-shrink phải cao hơn hẳn phần còn lại (đang là ${kb.get('flex-shrink')}). ` +
    'Bằng 1 thì flexbox chia đều phần thiếu và tên tệp cũng gánh, dù ô cuộn ' +
    'ngay bên cạnh còn thừa chỗ để nhường');
});

test('nhóm chính vẫn ghim — btnRun không bao giờ bị đẩy ra ngoài', () => {
  // Bản vá 30/08 phải còn nguyên: sửa chỗ này mà làm hỏng chỗ kia thì
  // btnRun lại ra ngoài màn hình như cũ.
  for (const bc of ['.header-actions > #btnRun', '.header-actions > #btnDebug']) {
    const kb = khaiBaoCua(bc);
    assert.strictEqual(kb.get('flex-shrink'), '0', `${bc} mất ghim`);
  }
});

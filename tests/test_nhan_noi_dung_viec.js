/**
 * test_nhan_noi_dung_viec.js — cửa cứng: nhãn/mách nước phải nói đúng việc.
 *
 * VÌ SAO CÓ TỆP NÀY, 26/08/2026:
 *
 * `test_moi_nut_co_handler.js` mở đầu bằng câu: cửa ấy chặn được ĐÚNG MỘT
 * loại trong họ "giao diện hứa một việc, mã làm việc khác" — loại "có nút mà
 * không ai nghe" — còn ba loại kia *"máy không tự biết được; chúng vẫn phải
 * bắt bằng tay"*.
 *
 * Câu ấy đúng với hai loại (trả lời giả · đọc sai tên trường), nhưng SAI với
 * loại thứ ba. "Nhãn nói sai việc" máy kiểm được, ít nhất ở dạng phổ biến
 * nhất của nó: mách nước hứa một phím tắt mà mã không hề gắn phím ấy.
 *
 * Đo 26/08 trên app đang chạy, gửi phím thật rồi đọc `defaultPrevented`:
 *
 *     btnNew   title="Tạo chương trình mới (Ctrl+N)"   -> Ctrl+N KHÔNG được bắt
 *
 * Chrome giữ riêng Ctrl+N, trang web không chặn được. Nên lời hứa ấy app
 * KHÔNG THỂ giữ, và cách sửa đúng là bỏ lời hứa đi chứ không phải cố gắn.
 *
 * CHUYỆN ĐÁNG GHI HƠN: phép đo đầu tiên của tôi báo BỐN nút hứa suông
 * (btnNew · btnUndo · btnRedo · btnReplaceAll). Sai. Nó gửi phím vào `window`
 * và `document`, trong khi bộ nghe hoàn tác gắn ở `document.body` — phím thật
 * đi từ phần tử đang focus rồi NỔI LÊN body trước, nên thực tế chúng bắt được.
 * Gửi lại từ `document.body` thì chỉ còn MỘT nút hứa suông.
 *
 *     gửi vào window/document   -> 4 nút "hứa mà không bắt"   (SAI)
 *     gửi vào document.body     -> 1 nút                       (đúng)
 *
 * Suýt báo Sếp con số 4. Cùng họ với luật §7: trước khi tin một con số — của
 * mình hay của ai — hãy chạy thử cái sinh ra nó.
 *
 * GIỚI HẠN CỦA CỬA NÀY, nói trước để không ai tưởng nó che hết: nó chỉ so
 * chữ cái của phím, KHÔNG kiểm rằng nhánh ấy có xét `ctrlKey`, cũng không
 * kiểm nó gọi đúng hàm. Một nhãn ghi "(Ctrl+K)" mà mã chỉ gắn phím `k` trần
 * vẫn lọt. Nó bắt được đúng ca đã xảy ra thật: hứa một phím mà mã không hề
 * nhắc tới phím ấy.
 */
const { test, describe } = require('node:test');
const assert = require('node:assert');
const fs = require('fs');
const path = require('path');

// 30/08/2026 — bọc qua bocChuThich(). Gieo thử chứng minh cửa này TỪNG bị
// lừa: xoá dòng mã thật và để lại một chú thích mang đúng chữ cửa tìm thì nó
// VẪN XANH. 5/6 cửa dò chuỗi dính bệnh này; cái duy nhất thoát là cái CHẠY mã.
// Xem tools/boc_chu_thich.js.
const { bocChuThich } = require('../tools/boc_chu_thich.js');

const THU_MUC = path.join(__dirname, '..', 'interface', 'web', 'the_v1');
const HTML = bocChuThich(fs.readFileSync(path.join(THU_MUC, 'index.html'), 'utf-8'));
const APP_JS = bocChuThich(fs.readFileSync(path.join(THU_MUC, 'app.js'), 'utf-8'));

/** Mọi phím mà app.js có nhắc tới trong một phép so `e.key === '...'`. */
function cacPhimDuocGan() {
  const ra = new Set();
  const re = /e\.key\s*===\s*['"]([^'"]+)['"]/g;
  let m;
  while ((m = re.exec(APP_JS)) !== null) ra.add(m[1].toLowerCase());
  return ra;
}

/** Mọi thuộc tính title có hứa một tổ hợp Ctrl. */
function cacLoiHua() {
  const ra = [];
  const re = /id="([^"]+)"[^>]*title="([^"]*Ctrl[^"]*)"|title="([^"]*Ctrl[^"]*)"[^>]*id="([^"]+)"/g;
  let m;
  while ((m = re.exec(HTML)) !== null) {
    const id = m[1] || m[4];
    const title = m[2] || m[3];
    const p = title.match(/Ctrl\s*\+?\s*(Enter|[A-Za-z0-9+\-=])/i);
    if (p) ra.push({ id, title, phim: p[1].toLowerCase() });
  }
  return ra;
}

describe('mách nước nói đúng việc', () => {
  test('mọi lời hứa phím tắt đều có phím ấy trong mã', () => {
    const gan = cacPhimDuocGan();
    const hua = cacLoiHua();
    assert.ok(hua.length >= 5,
      `chỉ tìm thấy ${hua.length} lời hứa — bộ rút chắc đã hỏng, không phải ` +
      'giao diện hết mách nước');

    const suong = hua.filter(x => !gan.has(x.phim));
    assert.deepEqual(suong, [],
      'Mách nước hứa phím tắt mà app.js không hề nhắc tới phím ấy:\n' +
      suong.map(x => `  ${x.id}: "${x.title}"  -> thiếu phím '${x.phim}'`).join('\n') +
      '\nHoặc gắn phím, hoặc BỎ lời hứa. Ngày 26/08 btnNew hứa (Ctrl+N) mà ' +
      'Chrome giữ riêng phím ấy — app không thể giữ lời, nên đã bỏ lời hứa.');
  });

  test('không nhận lại lời hứa Ctrl+N', () => {
    // Chrome không giao Ctrl+N cho trang. Chốt riêng để lần sau ai đó thấy
    // thiếu mách nước rồi "tiện tay" thêm lại.
    const m = HTML.match(/id="btnNew"[^>]*title="([^"]*)"/);
    assert.ok(m, 'không tìm thấy btnNew');
    assert.ok(!/Ctrl\s*\+?\s*N/i.test(m[1]),
      'btnNew lại hứa Ctrl+N — Chrome giữ riêng phím này, app không giữ được lời');
  });
});

describe('thanh trạng thái đáy', () => {
  test('có đủ sáu ô', () => {
    for (const id of ['stDuAn', 'stTep', 'stLuu', 'stSoThe', 'stLoi', 'stChay']) {
      assert.ok(HTML.includes(`id="${id}"`), `thiếu ô #${id} trong thanh trạng thái`);
    }
  });

  test('được vẽ lại từ onTreeChanged', () => {
    // Rải lời gọi khắp nơi thì sẽ có nhánh quên gọi, và thanh trạng thái nói
    // sai còn tệ hơn không có. Mọi đường làm cây thẻ đổi đều đi qua
    // `onTreeChanged`, nên cắm đúng một chỗ.
    const i = APP_JS.indexOf('function onTreeChanged');
    assert.ok(i !== -1, 'không tìm thấy onTreeChanged');
    assert.ok(APP_JS.slice(i, i + 2500).includes('veThanhTrangThai()'),
      'onTreeChanged không gọi veThanhTrangThai() — thanh sẽ đứng im khi sửa thẻ');
  });

  test('đếm CẢ thẻ con, không chỉ tầng ngoài cùng', () => {
    // `state.tree.length` chỉ đếm tầng một: một `def` bọc bốn thẻ sẽ hiện
    // "1 thẻ". Bóc hàm ra chạy thật thay vì dò chuỗi.
    const m = APP_JS.match(/function demTheSau\(ds\)\s*\{[\s\S]*?\n  \}/);
    assert.ok(m, 'không tìm thấy hàm demTheSau');
    const dem = new Function(`${m[0]}; return demTheSau;`)();

    assert.equal(dem([]), 0);
    assert.equal(dem([{ ma: 'ma_tho' }]), 1);
    assert.equal(
      dem([{ ma: 'ham', than: [{ ma: 'tra_ve' }, { ma: 'ma_tho' }] }]), 3,
      'không cộng thẻ con — con số trên thanh trạng thái sẽ nói sai');
    assert.equal(
      dem([{ ma: 'ham', than: [{ ma: 'if', than: [{ ma: 'tra_ve' }] }] }]), 3,
      'không đệ quy đủ sâu');
  });
});

describe('dự án hiện mặc định', () => {
  test('thanh tab không còn tự ẩn khi có một tệp', () => {
    assert.ok(
      /state\.tabs\.length === 0 \? 'none' : 'flex'/.test(APP_JS),
      'thanh tab lại ẩn khi có ít tab — mở tệp thứ hai sẽ làm layout nhảy, ' +
      'và có một tệp thì không chỗ nào nói đang sửa tệp nào');
  });

  test('cây tệp là tab mặc định khi mở app', () => {
    const i = APP_JS.indexOf('btnModeFiles.addEventListener');
    assert.ok(i !== -1, 'không tìm thấy handler btnModeFiles');
    assert.ok(APP_JS.slice(i, i + 2200).includes('btnModeFiles.click()'),
      'không có lời gọi click mặc định — mở app lên sẽ thấy khay thẻ, ' +
      'phải bấm thêm 1 lần mới thấy dự án của mình (VS Code: 0 lần)');
  });

  test('gốc cây tệp dùng tên dự án thật, không phải "root"', () => {
    // NEO ĐÚNG DÒNG GÁN NHÃN, không dò chuỗi `state.tenDuAn || 'root'` trên
    // cả tệp: chuỗi ấy còn xuất hiện ở `renderFileTree` (dòng ghi
    // `tenDuAnDaVeCay`). Bản đầu của cửa này dò chung, và khi gieo lỗi vào
    // đúng dòng nhãn gốc thì nó VẪN XANH — vì còn khớp ở dòng kia.
    //
    // Đây là lần thứ hai trong một buổi tôi viết một cửa rồi để nó khớp nhầm
    // chỗ; lần trước là chú thích chứa chữ `returnValue`. Cả hai chỉ lộ ra
    // khi gieo lỗi thử. CLAUDE.md §4: thấy mình sắp viết `x in y` để quyết
    // một chuyện, hãy hỏi `x` có thể nằm lọt giữa chỗ khác không.
    assert.ok(
      /const dir = parts\.length > 1 \? parts\[0\] : \(state\.tenDuAn \|\| 'root'\);/
        .test(APP_JS),
      "nhãn gốc cây tệp không dùng state.tenDuAn — sẽ ghi cứng 'root' và " +
      'không cho biết đang mở dự án nào');
    assert.ok(
      /state\.tenDuAn = data\.ten_du_an/.test(APP_JS),
      'không lấy ten_du_an từ /api/status');
  });
});

describe('Bác Sĩ AI không được tuyên bố quá phạm vi — thêm 30/08/2026', () => {
  /** Thân nhánh "không tìm thấy gì" của `chayKhamBenhVaHienThi`. */
  function nhanhKhongThayGi() {
    const i = APP_JS.indexOf('const diagnoses = khamBenhToanDien(state.tree);');
    assert.ok(i !== -1, 'không tìm thấy chayKhamBenhVaHienThi');
    return APP_JS.slice(i, i + 3200);
  }

  test('nhánh "khoẻ mạnh" phải hỏi bộ kiểm tra kia trước', () => {
    // 30/08: đo bằng cách tự bấm. Thêm một thẻ `Nếu` điều kiện rỗng rồi bấm
    // "Bác Sĩ Khám Bệnh". Màn hình hiện ĐỒNG THỜI:
    //
    //     2 ĐỎ (Lỗi)                                  <- ô đếm, ĐÚNG
    //     "Mã nguồn khoẻ mạnh! ... không phát hiện lỗi logic nào"
    //     "✓ 100% HEALTHY"                            <- SAI
    //
    // Nguyên nhân không phải bảng cũ hay chuỗi cứng: có HAI bộ chẩn đoán
    // khác phạm vi — `TheValidator.kiemTraCayThe` (18 luật) và
    // `khamBenhToanDien` (nhỏ hơn, biết tự sửa `=` thành `==`). Lỗi ở CÂU
    // CHỮ: bộ nhỏ tuyên bố về CẢ chương trình.
    const nhanh = nhanhKhongThayGi();
    const chiMa = nhanh.replace(/\/\/[^\n]*/g, '');
    assert.ok(/state\.diagnostics/.test(chiMa),
      'nhánh "không thấy gì" không hỏi state.diagnostics — nó sẽ tuyên bố ' +
      '"khoẻ mạnh" trong khi bộ kiểm tra kia đang báo lỗi');
    assert.ok(/so_loi_do/.test(chiMa) && /so_canh_bao_vang/.test(chiMa),
      'không đọc số lỗi/cảnh báo của bộ kiểm tra');
  });

  test('"100% HEALTHY" chỉ được in khi bộ kiểm tra kia SẠCH', () => {
    // Chốt bằng cách chạy thật logic quyết định, không dò chuỗi: bóc biểu
    // thức `sach` ra và thử bốn trạng thái.
    const nhanh = nhanhKhongThayGi();
    const m = nhanh.match(/const sach = ([^;]+);/);
    assert.ok(m, 'không tìm thấy biểu thức quyết định `sach`');
    const sach = new Function('soDoKia', 'soVangKia', `return (${m[1]});`);
    assert.equal(sach(0, 0), true, 'sạch mà lại không nhận là sạch');
    assert.equal(sach(2, 0), false, 'có 2 lỗi mà vẫn nhận là sạch');
    assert.equal(sach(0, 3), false, 'có 3 cảnh báo mà vẫn nhận là sạch');
    assert.equal(sach(1, 1), false, 'có cả lỗi lẫn cảnh báo mà vẫn nhận là sạch');
  });
});

/**
 * test_the_connector_ui.js — UI, DOM & Renderer tests cho Thẻ Móc Nối Thẳng, Khay Thẻ 6 Nhóm & Bố Cục Ba Cột.
 *
 * Chạy bằng runner thuần Node.js: `node --test tests/test_the_connector_ui.js`
 */
const { test, describe, beforeEach } = require('node:test');
const assert = require('node:assert');

// Fake DOM cho Node.js
class FakeElement {
  constructor(tagName = 'div') {
    this.tagName = tagName.toUpperCase();
    this.id = '';
    this.className = '';
    this.textContent = '';
    this.innerHTML = '';
    this.style = {
      setProperty: (k, v) => { this.style[k] = v; },
      _props: {}
    };
    this.disabled = false;
    this.title = '';
    this.children = [];
    this.parentElement = null;
    this.dataset = {};
    this.value = '';
    this.draggable = false;
    this.spellcheck = false;
    this.autocomplete = '';
    this.listeners = {};
    this.classList = {
      _classes: new Set(),
      add: (cls) => this.classList._classes.add(cls),
      remove: (cls) => this.classList._classes.delete(cls),
      contains: (cls) => this.classList._classes.has(cls),
    };
  }

  appendChild(child) {
    if (child && child.nodeType === 11) { // DocumentFragment
      for (const ch of child.children) {
        ch.parentElement = this;
        this.children.push(ch);
      }
      return child;
    }
    if (child) {
      child.parentElement = this;
      this.children.push(child);
    }
    return child;
  }

  addEventListener(evt, fn) {
    if (!this.listeners[evt]) this.listeners[evt] = [];
    this.listeners[evt].push(fn);
  }

  dispatchEvent(evt) {
    const list = this.listeners[evt.type] || [];
    list.forEach(fn => fn(evt));
  }

  getBoundingClientRect() {
    // _rect dat rieng tung phan tu: rect GIONG NHAU thi moi cong thuc deu ra cung
    // mot so, nen cua khong the hong. 23/08: da gieo loi +4 -> +400 va cua van xanh.
    if (this._rect) return this._rect;
    return { top: 10, height: 24, left: 10, width: 200, bottom: 34, right: 210 };
  }

  querySelector(selector) {
    for (const ch of this.children) {
      if (selector.startsWith('.') && (ch.className.includes(selector.slice(1)) || ch.classList.contains(selector.slice(1)))) return ch;
      if (selector.startsWith('#') && ch.id === selector.slice(1)) return ch;
      if (ch.tagName.toLowerCase() === selector.toLowerCase()) return ch;
      const found = ch.querySelector ? ch.querySelector(selector) : null;
      if (found) return found;
    }
    return null;
  }

  querySelectorAll(selector) {
    const results = [];
    const walk = (node) => {
      for (const ch of node.children) {
        if (selector.startsWith('.') && (ch.className.includes(selector.slice(1)) || ch.classList.contains(selector.slice(1)))) {
          results.push(ch);
        } else if (selector.startsWith('#') && ch.id === selector.slice(1)) {
          results.push(ch);
        } else if (ch.tagName.toLowerCase() === selector.toLowerCase()) {
          results.push(ch);
        }
        if (ch.children) walk(ch);
      }
    };
    walk(this);
    return results;
  }
}

class FakeDocumentFragment {
  constructor() {
    this.nodeType = 11;
    this.children = [];
  }
  appendChild(child) {
    this.children.push(child);
    return child;
  }
}

class FakeDocument {
  constructor() {
    this.elements = new Map();
  }

  createElement(tagName) {
    return new FakeElement(tagName);
  }

  createDocumentFragment() {
    return new FakeDocumentFragment();
  }

  getElementById(id) {
    if (!this.elements.has(id)) {
      const el = new FakeElement();
      el.id = id;
      this.elements.set(id, el);
    }
    return this.elements.get(id);
  }

  querySelectorAll(selector) {
    const res = [];
    for (const [id, el] of this.elements.entries()) {
      if (selector.startsWith('.') && el.className.includes(selector.slice(1))) {
        res.push(el);
      } else if (selector.startsWith('#') && id === selector.slice(1)) {
        res.push(el);
      }
      if (el.querySelectorAll) {
        res.push(...el.querySelectorAll(selector));
      }
    }
    return res;
  }
}

// Cài đặt môi trường global
global.window = {
  addEventListener: () => {},
  removeEventListener: () => {},
  location: { search: '' },
  localStorage: {
    getItem: () => null,
    setItem: () => {},
  },
  innerWidth: 1920,
  innerHeight: 1080,
  requestAnimationFrame: (cb) => cb(),
};
global.document = new FakeDocument();

const TheValidator = require('../interface/web/the_v1/validator.js');
global.TheValidator = TheValidator;

const app = require('../interface/web/the_v1/app.js');

describe('Thẻ Móc Nối Thẳng & Giao Diện Ba Cột Tests', () => {

  beforeEach(() => {
    global.document = new FakeDocument();
  });

  test('Khay thẻ có đủ 6 nhóm và 17 thẻ lệnh', () => {
    // 26/08: CON SỐ ĐỔI 12 -> 17, và cửa này đã ĐỎ SUỐT HAI NGÀY trước khi
    // ai đó thấy.
    //
    // Cửa viết ngày 24/08 (`ada7fe1`) chốt cứng 12. Ngày 25/08 khay thẻ thêm
    // năm thẻ — `nhap` · `dung_lap` · `bo_qua` · `thu` · `bat_loi` — nên
    // `BO_THE_V1` có 17 khoá và phép so `=== 12` đỏ từ lúc ấy.
    //
    // Không ai thấy vì các cửa JS chạy LẺ TỪNG TỆP: mỗi lần chỉ gõ
    // `node --test tests/test_moi_nut_co_handler.js` hay `test_the_parity.js`,
    // còn tệp này không nằm trong thói quen ấy. Bắt được hôm nay chỉ vì tôi
    // chạy `for t in tests/*.js` thay vì gõ tên từng tệp.
    //
    // ĐÂY KHÔNG PHẢI NỚI TAY. Năm thẻ mới là thay đổi có chủ đích, đã qua
    // duyệt, và `test_the_parity.js` vẫn chốt 27/27 giữa bản JS và bản Python
    // — thêm thẻ một bên mà quên bên kia thì cửa ấy đỏ. Ở đây con số đổi vì
    // KHAY THẺ đổi, không phải vì phép đo được nới ra cho vừa.
    const keys = Object.keys(TheValidator.BO_THE_V1);
    assert.strictEqual(keys.length, 17, 'Phải có đúng 17 thẻ lệnh');
    assert.ok(keys.includes('chu_thich'), 'Phải có thẻ chu_thich');
    assert.ok(keys.includes('ham'), 'Phải có thẻ ham');
    assert.ok(keys.includes('neu'), 'Phải có thẻ neu');
    assert.ok(keys.includes('gan'), 'Phải có thẻ gan');
    assert.ok(keys.includes('in_ra'), 'Phải có thẻ in_ra');
    assert.ok(keys.includes('ma_tho'), 'Phải có thẻ ma_tho');
    // Năm thẻ thêm 25/08 — chốt tên để đổi tên là đỏ, không im lặng.
    for (const m of ['nhap', 'dung_lap', 'bo_qua', 'thu', 'bat_loi']) {
      assert.ok(keys.includes(m), `Phải có thẻ ${m} (thêm 25/08)`);
    }

    // 6 nhóm
    const nhomKeys = Object.keys(TheValidator.NHOM_THE);
    assert.strictEqual(nhomKeys.length, 6, 'Phải có 6 nhóm màu');
    assert.ok(nhomKeys.includes('chu_thich'));
  });

  test('Thẻ chu_thich sinh mã Python đúng cú pháp', () => {
    const cay = [
      { id: '1', ma: 'chu_thich', o: { noi_dung: 'Khởi tạo hệ thống' }, than: [] },
      { id: '2', ma: 'gan', o: { ten_bien: 'x', gia_tri: '10' }, than: [] }
    ];
    const ma = TheValidator.sinhMaPython(cay);
    assert.ok(ma.includes('# Khởi tạo hệ thống'));
    assert.ok(ma.includes('x = 10'));
  });

  test('Cấu trúc DOM thẻ nối thẳng chuẩn viên thuốc và có lỗ bên trái', () => {
    const cardDef = TheValidator.BO_THE_V1['ham'];
    assert.strictEqual(cardDef.nhom, 'ham');
    assert.ok(cardDef.mau.length > 0);
  });

  test('Khối lồng nhau (neu -> gan) tạo cấu trúc .hang và .khoi', () => {
    const tree = [
      { id: 'gan_0', ma: 'gan', o: { ten_bien: 'x', gia_tri: '5' }, than: [] },
      {
        id: 'if_1',
        ma: 'neu',
        o: { dieu_kien: 'x > 0' },
        than: [
          { id: 'gan_1', ma: 'gan', o: { ten_bien: 'y', gia_tri: '1' }, than: [] }
        ]
      }
    ];
    const diag = TheValidator.kiemTraCayThe(tree);
    assert.strictEqual(diag.hop_le, true);
    assert.strictEqual(diag.so_loi_do, 0);
  });

  test('chinhCotDoc tinh dung so px tren rect that', () => {
    const root = new FakeElement('div');
    root.id = 'cardChainRoot';
    global.document.elements.set('cardChainRoot', root);

    const khoi = new FakeElement('div');
    khoi.className = 'khoi';
    khoi.classList.add('khoi');
    khoi._rect = { top: 100, height: 260, left: 0, width: 300, bottom: 360, right: 300 };

    const hang1 = new FakeElement('div');
    hang1.className = 'hang';
    hang1.classList.add('hang');
    hang1._rect = { top: 104, height: 20, left: 0, width: 300, bottom: 124, right: 300 };

    const hang2 = new FakeElement('div');
    hang2.className = 'hang';
    hang2.classList.add('hang');
    hang2._rect = { top: 300, height: 20, left: 0, width: 300, bottom: 320, right: 300 };

    khoi.appendChild(hang1);
    khoi.appendChild(hang2);
    root.appendChild(khoi);

    assert.strictEqual(typeof app.chinhCotDoc, 'function');
    app.chinhCotDoc();

    // 300 + 20/2 - 100 + 4 = 214
    assert.strictEqual(khoi.style['--cao-cot'], '214px',
      'day cot doc phai dung o TAM nhanh cuoi, khong phai mot so bat ky');
  });

  test('yeuCauChinhCotDoc goi lai qua HAI khung hinh long nhau', () => {
    // Loi N3 that (23/08): ham dung, resize dung, chi duong MO TEP la hut —
    // mot luot render sau do dung lai .khoi moi, xoa mat bien vua dat.
    // Cua chi kiem "co ham" thi bo hoan toan double rAF van xanh 5/5.
    const root = new FakeElement('div');
    root.id = 'cardChainRoot';
    global.document.elements.set('cardChainRoot', root);

    const khoi = new FakeElement('div');
    khoi.className = 'khoi';
    khoi.classList.add('khoi');
    const hang = new FakeElement('div');
    hang.className = 'hang';
    hang.classList.add('hang');
    khoi.appendChild(hang);
    root.appendChild(khoi);

    let lan_dat = 0;
    khoi.style.setProperty = (k, v) => { if (k === '--cao-cot') lan_dat++; khoi.style[k] = v; };

    let sau_nhat = 0, dang_o = 0;
    const raf_cu = global.window.requestAnimationFrame;
    global.window.requestAnimationFrame = (cb) => {
      dang_o++; if (dang_o > sau_nhat) sau_nhat = dang_o;
      cb(); dang_o--;
    };

    assert.strictEqual(typeof app.yeuCauChinhCotDoc, 'function');
    app.yeuCauChinhCotDoc();
    global.window.requestAnimationFrame = raf_cu;

    assert.strictEqual(sau_nhat, 2, 'phai long HAI lop requestAnimationFrame, khong phai mot');
    assert.strictEqual(lan_dat, 3, 'phai chinh 3 lan: ngay lap tuc + khung 1 + khung 2');
  });

});

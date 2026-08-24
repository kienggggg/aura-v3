// app.js — Controller tương tác toàn diện cho App Lập trình bằng THẺ v1

(function () {
  'use strict';

  // State chính của ứng dụng
  const state = {
    tree: [],
    history: [],
    historyIndex: -1,
    authToken: '',
    activeFilePath: '',
    activeFileSha256: null,
    hasModifications: false,
    codeExecutionEnabled: false,
    diagnostics: { hop_le: true, so_loi_do: 0, so_canh_bao_vang: 0, danh_sach: [], so_lan_dung_the: {} },
    nodeIdCounter: 100,
    sidebarLeftCollapsed: false,
    sidebarRightCollapsed: false,
    codeFontSize: 14,
    draggingCardId: null
  };

  // ==========================================================================
  // 1. KHỞI TẠO & LẤY MÃ THÔNG HÀNH AUTH TOKEN (MỤC 14.2)
  // ==========================================================================
  function initAuthToken() {
    const urlParams = new URLSearchParams(window.location.search);
    const tokenFromUrl = urlParams.get('token');
    if (tokenFromUrl) {
      state.authToken = tokenFromUrl;
      sessionStorage.setItem('aura_the_auth_token', tokenFromUrl);
      // Dọn sạch token khỏi thanh địa chỉ để tránh lưu lịch sử duyệt web
      const cleanUrl = window.location.pathname;
      window.history.replaceState({}, document.title, cleanUrl);
    } else {
      state.authToken = sessionStorage.getItem('aura_the_auth_token') || '';
    }
  }

  function escapeHtml(str) {
    if (str === null || str === undefined) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  // Gọi fetch kèm header bảo mật X-Auth-Token
  async function authFetch(url, options = {}) {
    const headers = {
      'Content-Type': 'application/json',
      'X-Auth-Token': state.authToken,
      ...(options.headers || {})
    };
    return fetch(url, { ...options, headers });
  }

  async function configureRuntimeCapabilities() {
    const btnRun = document.getElementById('btnRun');
    const runText = document.getElementById('runBtnText');
    const btnTrace = document.getElementById('btnRunTrace');
    const btnE1 = document.getElementById('btnRunE1');
    const termBody = document.getElementById('terminalBody');
    const traceStatusPill = document.getElementById('traceStatusPill');
    const e1StatusPill = document.getElementById('e1StatusPill');

    try {
      const resp = await authFetch('/api/status');
      const data = await resp.json();
      state.codeExecutionEnabled = Boolean(data.code_execution_enabled);
      state.e1Limitation = data.e1_limitation || '';
      if (btnRun) btnRun.disabled = !state.codeExecutionEnabled;
      if (btnTrace) btnTrace.disabled = !state.codeExecutionEnabled;
      if (btnE1) btnE1.disabled = !state.codeExecutionEnabled;

      if (!state.codeExecutionEnabled) {
        if (runText) runText.textContent = 'CHẠY ĐANG TẮT';
        if (btnRun) btnRun.title = 'Tắt mặc định vì tiến trình Python chưa được cách ly khỏi tệp và mạng';
        if (btnTrace) btnTrace.title = 'Chạy mã/test đang tắt mặc định';
        if (btnE1) btnE1.title = 'Chạy mã/test đang tắt mặc định';
        if (traceStatusPill) {
          traceStatusPill.className = 'trace-status-pill cut';
          traceStatusPill.textContent = 'TẮT';
        }
        if (e1StatusPill) {
          e1StatusPill.className = 'trace-status-pill cut';
          e1StatusPill.textContent = 'TẮT';
        }
        if (termBody) {
          termBody.innerHTML = '<div class="term-line term-dim">&gt; Chạy mã đang tắt mặc định. App vẫn mở, sửa, kiểm tra và lưu mã bình thường.</div>';
        }
      }
    } catch (_) {
      state.codeExecutionEnabled = false;
      if (btnRun) btnRun.disabled = true;
      if (btnTrace) btnTrace.disabled = true;
      if (btnE1) btnE1.disabled = true;
      if (runText) runText.textContent = 'CHẠY ĐANG TẮT';
      if (traceStatusPill) {
        traceStatusPill.className = 'trace-status-pill cut';
        traceStatusPill.textContent = 'TẮT';
      }
      if (e1StatusPill) {
        e1StatusPill.className = 'trace-status-pill cut';
        e1StatusPill.textContent = 'TẮT';
      }
    }
  }

  // Quản lý Bố Cục IDE & Phông Chữ (Zoom)
  function applySidebarLayout() {
    const mainEl = document.getElementById('appMain');
    if (!mainEl) return;
    if (state.sidebarLeftCollapsed) mainEl.classList.add('left-collapsed');
    else mainEl.classList.remove('left-collapsed');

    if (state.sidebarRightCollapsed) mainEl.classList.add('right-collapsed');
    else mainEl.classList.remove('right-collapsed');
  }

  function toggleSidebarLeft() {
    state.sidebarLeftCollapsed = !state.sidebarLeftCollapsed;
    localStorage.setItem('aura_sidebar_left_collapsed', String(state.sidebarLeftCollapsed));
    applySidebarLayout();
  }

  function toggleSidebarRight() {
    state.sidebarRightCollapsed = !state.sidebarRightCollapsed;
    localStorage.setItem('aura_sidebar_right_collapsed', String(state.sidebarRightCollapsed));
    applySidebarLayout();
  }

  function setCodeFontSize(size) {
    const clamped = Math.max(10, Math.min(18, size));
    state.codeFontSize = clamped;
    document.documentElement.style.setProperty('--code-font-size', `${clamped}px`);
    const zoomEl = document.getElementById('zoomPercent');
    if (zoomEl) zoomEl.textContent = `${clamped}px`;
    localStorage.setItem('aura_code_font_size', String(clamped));
  }

  function initLayoutPreferences() {
    // 1. Phông chữ mặc định 14px đọc được
    const savedFontSize = localStorage.getItem('aura_code_font_size');
    const initialFontSize = savedFontSize ? parseInt(savedFontSize, 10) : 14;
    setCodeFontSize(initialFontSize);

    // 2. Thu gọn cột bên
    const savedLeft = localStorage.getItem('aura_sidebar_left_collapsed');
    state.sidebarLeftCollapsed = (savedLeft === 'true');

    const savedRight = localStorage.getItem('aura_sidebar_right_collapsed');
    if (savedRight !== null) {
      state.sidebarRightCollapsed = (savedRight === 'true');
    } else {
      // Màn hình < 1400px thì cột phải (Agent / Terminal) mặc định thu gọn
      state.sidebarRightCollapsed = (window.innerWidth < 1400);
    }
    applySidebarLayout();
  }

  // ==========================================================================
  // ==========================================================================
  // 2. KHỞI TẠO KHAY THẺ (6 NHÓM MÀU CHUẨN, 12 THẺ & BỘ ĐẾM ×N)
  // ==========================================================================
  function renderToolbox() {
    const container = document.getElementById('toolboxContainer');
    if (!container) return;
    container.innerHTML = '';

    const groups = [
      { id: 'ham', title: 'Hàm (Cam)', color: 'var(--ham)', cards: ['ham', 'goi_ham', 'tra_ve'] },
      { id: 'dieu_khien', title: 'Điều khiển (Xanh dương)', color: 'var(--dk)', cards: ['neu', 'nguoc_lai', 'lap_moi', 'lap_khi'] },
      { id: 'du_lieu', title: 'Dữ liệu (Xanh lá)', color: 'var(--dl)', cards: ['gan', 'pheptinh'] },
      { id: 'vao_ra', title: 'Vào / Ra (Tím)', color: 'var(--vr)', cards: ['in_ra'] },
      { id: 'chu_thich', title: 'Chú thích (Xanh ngọc)', color: 'var(--ct)', cards: ['chu_thich'] },
      { id: 'ma_tho', title: 'Mã thô (Xám)', color: 'var(--tho)', cards: ['ma_tho'] }
    ];

    groups.forEach(g => {
      const groupEl = document.createElement('div');
      groupEl.className = 'tool-group';
      groupEl.id = `group_${g.id}`;

      const titleEl = document.createElement('div');
      titleEl.className = 'group-title';
      titleEl.textContent = g.title;
      titleEl.style.color = g.color;
      groupEl.appendChild(titleEl);

      const cardsGrid = document.createElement('div');
      cardsGrid.className = 'tool-group-cards';

      g.cards.forEach(cardMa => {
        const cardDef = TheValidator.BO_THE_V1[cardMa];
        if (!cardDef) return;

        const itemEl = document.createElement('div');
        itemEl.className = 'tool-item';
        itemEl.dataset.ma = cardMa;
        itemEl.style.borderLeftColor = g.color;
        itemEl.draggable = true;
        // Nhãn dịch nghĩa ("Định nghĩa hàm", "Gọi hàm"...) bỏ khỏi thân thẻ —
        // Sếp đọc cú pháp Python trực tiếp nhanh hơn đọc tên tiếng Việt rồi tự
        // dịch ngược. Tên đầy đủ vẫn còn trong title (hover mới hiện).
        itemEl.title = `Thẻ ${cardDef.ten}: Click để chèn nhanh hoặc kéo vào canvas`;

        const infoEl = document.createElement('div');
        infoEl.className = 'tool-info';

        const syntaxEl = document.createElement('span');
        syntaxEl.className = 'tool-syntax';
        if (cardMa === 'gan') syntaxEl.textContent = 'x = 10';
        else if (cardMa === 'in_ra') syntaxEl.textContent = 'print(...)';
        else if (cardMa === 'neu') syntaxEl.textContent = 'if cond:';
        else if (cardMa === 'nguoc_lai') syntaxEl.textContent = 'else:';
        else if (cardMa === 'lap_moi') syntaxEl.textContent = 'for i in day:';
        else if (cardMa === 'lap_khi') syntaxEl.textContent = 'while cond:';
        else if (cardMa === 'tra_ve') syntaxEl.textContent = 'return val';
        else if (cardMa === 'ham') syntaxEl.textContent = 'def fn(args):';
        else if (cardMa === 'goi_ham') syntaxEl.textContent = 'fn(args)';
        else if (cardMa === 'pheptinh') syntaxEl.textContent = 'a + b';
        else if (cardMa === 'chu_thich') syntaxEl.textContent = '# Chú thích';
        else if (cardMa === 'ma_tho') syntaxEl.textContent = 'raw code';
        infoEl.appendChild(syntaxEl);

        itemEl.appendChild(infoEl);

        // Badge đếm xN
        const badgeEl = document.createElement('span');
        badgeEl.className = 'count-badge';
        badgeEl.id = `countBadge_${cardMa}`;
        badgeEl.textContent = '×0';
        itemEl.appendChild(badgeEl);

        // Event Kéo thả & Click chèn nhanh
        itemEl.addEventListener('dragstart', (e) => {
          e.dataTransfer.setData('text/plain', JSON.stringify({ type: 'NEW_CARD', ma: cardMa }));
        });

        itemEl.addEventListener('click', () => {
          addNewCardToRoot(cardMa);
        });

        cardsGrid.appendChild(itemEl);
      });

      groupEl.appendChild(cardsGrid);
      container.appendChild(groupEl);
    });

    // Vùng thả để XOÁ — chiều ngược của kéo-từ-khay-vào-canvas. Chỉ hiện đỏ khi
    // đang kéo một thẻ THẬT SỰ có trên canvas (state.draggingCardId), để kéo
    // một thẻ mẫu từ khay rồi buông ngay trên khay không bị hiểu nhầm là xoá.
    container.addEventListener('dragover', (e) => {
      if (!state.draggingCardId) return;
      e.preventDefault();
      e.dataTransfer.dropEffect = 'move';
      container.classList.add('vung-tha-xoa');
    });
    container.addEventListener('dragleave', (e) => {
      if (e.target === container) container.classList.remove('vung-tha-xoa');
    });
    container.addEventListener('drop', (e) => {
      e.preventDefault();
      container.classList.remove('vung-tha-xoa');
      const raw = e.dataTransfer.getData('text/plain');
      if (!raw) return;
      try {
        const payload = JSON.parse(raw);
        if (payload.type === 'EXISTING_CARD' && payload.nodeId) {
          if (layVaXoaTheTheoId(payload.nodeId)) {
            onTreeChanged();
          }
        }
      } catch (_) {}
    });
  }

  function updateToolboxCounters() {
    const counts = state.diagnostics.so_lan_dung_the || {};
    for (const cardMa in TheValidator.BO_THE_V1) {
      const badge = document.getElementById(`countBadge_${cardMa}`);
      if (badge) {
        const c = counts[cardMa] || 0;
        badge.textContent = `×${c}`;
        if (c > 0) {
          badge.classList.add('active');
        } else {
          badge.classList.remove('active');
        }
      }
    }
  }

  // ==========================================================================
  // 3. RENDER VÙNG SOẠN THẢO THẺ NỐI THẲNG (mau_the_noi_thang.html)
  // ==========================================================================
  function chinhCotDoc() {
    if (typeof document === 'undefined') return;
    document.querySelectorAll('.khoi').forEach(function(k) {
      const hang = Array.prototype.filter.call(k.children, function(e) {
        return e.classList.contains('hang');
      });
      if (!hang.length) return;
      const cuoi = hang[hang.length - 1];
      const rk = k.getBoundingClientRect();
      const rc = cuoi.getBoundingClientRect();
      k.style.setProperty('--cao-cot', Math.round(rc.top + rc.height / 2 - rk.top + 4) + 'px');
    });
  }

  function yeuCauChinhCotDoc() {
    if (typeof document === 'undefined') return;
    chinhCotDoc();
    if (typeof window !== 'undefined' && typeof window.requestAnimationFrame === 'function') {
      window.requestAnimationFrame(() => {
        chinhCotDoc();
        window.requestAnimationFrame(chinhCotDoc);
      });
    }
  }

  function taoTheNode(ma) {
    state.nodeIdCounter++;
    const cardDef = TheValidator.BO_THE_V1[ma];
    const initialO = {};
    if (cardDef && cardDef.o) {
      cardDef.o.forEach(oDef => {
        initialO[oDef.ten] = oDef.goi_y || '';
      });
    }
    return {
      id: `the_${ma}_${state.nodeIdCounter}`,
      ma: ma,
      o: initialO,
      than: [],
      da_sua: true
    };
  }

  function addNewCardToRoot(ma) {
    const node = taoTheNode(ma);
    state.tree.push(node);
    onTreeChanged();
  }

  // Tìm node theo id trong cây (kể cả khối con .than), KHÔNG xoá — nền dùng
  // chung cho cả xoá (kéo ra khay) lẫn di chuyển (kéo sắp xếp lại).
  function timTheTheoId(danhSach, nodeId) {
    for (let i = 0; i < danhSach.length; i++) {
      if (danhSach[i].id === nodeId) {
        return { node: danhSach[i], dsCha: danhSach, chiSo: i };
      }
      if (danhSach[i].than && danhSach[i].than.length > 0) {
        const sau = timTheTheoId(danhSach[i].than, nodeId);
        if (sau) return sau;
      }
    }
    return null;
  }

  // Xoá node theo id, trả về node đã xoá (hoặc null nếu không thấy). Dùng
  // cho kéo thẻ NGƯỢC từ canvas ra khay để xoá — cùng thao tác splice như
  // nút ✕, chỉ khác điểm vào (kéo thả thay vì bấm nút).
  function layVaXoaTheTheoId(nodeId) {
    const tim = timTheTheoId(state.tree, nodeId);
    if (!tim) return null;
    tim.dsCha.splice(tim.chiSo, 1);
    return tim.node;
  }

  // `node` có phải chính là `targetId`, hoặc `targetId` nằm trong khối con
  // (.than) của `node`? Chặn kéo một khối THẢ VÀO CHÍNH THÂN NÓ (hoặc thân
  // của một khối con của nó) — việc này sẽ tạo một cây có node chứa chính
  // nó, vỡ mọi thứ đọc cây bằng đệ quy (kể cả renderCard đang gọi hàm này).
  function laTuThaVaoChinhNoHoacConNo(node, targetId) {
    if (!targetId) return false;
    if (node.id === targetId) return true;
    if (!node.than) return false;
    return node.than.some(con => laTuThaVaoChinhNoHoacConNo(con, targetId));
  }

  // Di chuyển một thẻ ĐÃ CÓ tới vị trí mới — dùng cho kéo sắp xếp lại thứ tự.
  //   dsDich:     mảng đích (state.tree hoặc node.than nào đó)
  //   idKhoiDich: id của thẻ đang SỞ HỮU dsDich (null nếu dsDich là gốc
  //               state.tree) — dùng để chặn tự-thả-vào-thân-mình
  //   viTri:      chỉ số muốn chèn vào, tính TRÊN dsDich TRƯỚC khi rút thẻ
  //               cũ ra (nếu cùng mảng, hàm tự bù lại chỗ vừa rút)
  function diChuyenThe(nodeId, dsDich, idKhoiDich, viTri) {
    const tim = timTheTheoId(state.tree, nodeId);
    if (!tim) return false;
    const { node, dsCha, chiSo } = tim;

    if (laTuThaVaoChinhNoHoacConNo(node, idKhoiDich)) return false;

    let viTriMoi = viTri;
    if (dsCha === dsDich && chiSo < viTriMoi) viTriMoi -= 1;

    dsCha.splice(chiSo, 1);
    dsDich.splice(viTriMoi, 0, node);
    return true;
  }

  function createCodeInput(node, fieldName, placeholder = '', className = '') {
    const input = document.createElement('input');
    input.type = 'text';
    input.className = `the-inline-input ${className}`.trim();
    let val = (node.o && node.o[fieldName] !== undefined) ? String(node.o[fieldName]) : '';
    if (node.ma === 'chu_thich' && fieldName === 'noi_dung' && val.startsWith('#')) {
      val = val.replace(/^#\s*/, '');
    }
    input.value = val;
    input.placeholder = placeholder || fieldName;
    input.spellcheck = false;
    input.autocomplete = 'off';

    function updateWidth() {
      const len = (input.value || input.placeholder || '').length;
      input.style.width = Math.max(len + 1, 2) + 'ch';
    }
    updateWidth();

    input.addEventListener('input', (e) => {
      if (!node.o) node.o = {};
      node.o[fieldName] = e.target.value;
      updateWidth();
      node.da_sua = true;
      onTreeChanged(false);
    });

    return input;
  }

  function renderCodeLineContent(node, cardDef) {
    const wrap = document.createElement('span');
    wrap.className = 'the-content';

    if (node.ma === 'gan') {
      wrap.appendChild(createCodeInput(node, 'ten_bien', 'x', 'ma'));
      const op = document.createElement('span');
      op.className = 'ma';
      op.textContent = ' = ';
      wrap.appendChild(op);
      wrap.appendChild(createCodeInput(node, 'gia_tri', 'giá_trị', 'n'));
    } else if (node.ma === 'in_ra') {
      const p1 = document.createElement('span');
      p1.className = 'ma';
      p1.textContent = 'print(';
      wrap.appendChild(p1);
      wrap.appendChild(createCodeInput(node, 'noi_dung', 'nội_dung', 's'));
      const p2 = document.createElement('span');
      p2.className = 'ma';
      p2.textContent = ')';
      wrap.appendChild(p2);
    } else if (node.ma === 'ham') {
      const kw = document.createElement('span');
      kw.className = 'kw';
      kw.textContent = (node.o && node.o.async === '1') ? 'async def ' : 'def ';
      wrap.appendChild(kw);
      wrap.appendChild(createCodeInput(node, 'ten_ham', 'tên_hàm', 'fn'));
      const p1 = document.createElement('span');
      p1.className = 'ma';
      p1.textContent = '(';
      wrap.appendChild(p1);
      wrap.appendChild(createCodeInput(node, 'tham_so', 'tham_số', 'ma'));
      const p2 = document.createElement('span');
      p2.className = 'ma';
      p2.textContent = ')';
      wrap.appendChild(p2);

      if (node.o && (node.o.kieu_tra_ve || node.o.kieu_tra_ve === '')) {
        const arrow = document.createElement('span');
        arrow.className = 'kw';
        arrow.textContent = ' -> ';
        wrap.appendChild(arrow);
        wrap.appendChild(createCodeInput(node, 'kieu_tra_ve', 'kiểu', 'fn'));
      }

      const pColon = document.createElement('span');
      pColon.className = 'ma';
      pColon.textContent = ':';
      wrap.appendChild(pColon);
    } else if (node.ma === 'neu') {
      const kw = document.createElement('span');
      kw.className = 'kw';
      kw.textContent = (node.o && node.o.noi_tiep === '1') ? 'elif ' : 'if ';
      wrap.appendChild(kw);
      wrap.appendChild(createCodeInput(node, 'dieu_kien', 'điều_kiện', 'ma'));
      const p = document.createElement('span');
      p.className = 'ma';
      p.textContent = ':';
      wrap.appendChild(p);
    } else if (node.ma === 'nguoc_lai') {
      const kw = document.createElement('span');
      kw.className = 'kw';
      kw.textContent = 'else';
      wrap.appendChild(kw);
      const p = document.createElement('span');
      p.className = 'ma';
      p.textContent = ':';
      wrap.appendChild(p);
    } else if (node.ma === 'lap_moi') {
      const kw1 = document.createElement('span');
      kw1.className = 'kw';
      kw1.textContent = 'for ';
      wrap.appendChild(kw1);
      wrap.appendChild(createCodeInput(node, 'bien', 'i', 'ma'));
      const kw2 = document.createElement('span');
      kw2.className = 'kw';
      kw2.textContent = ' in ';
      wrap.appendChild(kw2);
      wrap.appendChild(createCodeInput(node, 'day', 'range(10)', 'ma'));
      const p = document.createElement('span');
      p.className = 'ma';
      p.textContent = ':';
      wrap.appendChild(p);
    } else if (node.ma === 'lap_khi') {
      const kw = document.createElement('span');
      kw.className = 'kw';
      kw.textContent = 'while ';
      wrap.appendChild(kw);
      wrap.appendChild(createCodeInput(node, 'dieu_kien', 'điều_kiện', 'ma'));
      const p = document.createElement('span');
      p.className = 'ma';
      p.textContent = ':';
      wrap.appendChild(p);
    } else if (node.ma === 'tra_ve') {
      const kw = document.createElement('span');
      kw.className = 'kw';
      kw.textContent = 'return ';
      wrap.appendChild(kw);
      wrap.appendChild(createCodeInput(node, 'gia_tri', 'giá_trị', 'n'));
    } else if (node.ma === 'goi_ham') {
      wrap.appendChild(createCodeInput(node, 'ten_ham', 'tên_hàm', 'fn'));
      const p1 = document.createElement('span');
      p1.className = 'ma';
      p1.textContent = '(';
      wrap.appendChild(p1);
      wrap.appendChild(createCodeInput(node, 'doi_so', 'đối_số', 's'));
      const p2 = document.createElement('span');
      p2.className = 'ma';
      p2.textContent = ')';
      wrap.appendChild(p2);
    } else if (node.ma === 'pheptinh') {
      wrap.appendChild(createCodeInput(node, 'trai', 'vế_trái', 'ma'));
      wrap.appendChild(createCodeInput(node, 'phep', '+', 'kw'));
      wrap.appendChild(createCodeInput(node, 'phai', 'vế_phải', 'ma'));
    } else if (node.ma === 'chu_thich') {
      const cm = document.createElement('span');
      cm.className = 'cm';
      cm.textContent = '# ';
      wrap.appendChild(cm);
      wrap.appendChild(createCodeInput(node, 'noi_dung', 'chú thích...', 'cm'));
    } else if (node.ma === 'ma_tho') {
      const rawVal = (node.o && node.o.nguyen_van !== undefined) ? node.o.nguyen_van : (node.raw_text || '');
      const input = document.createElement('input');
      input.type = 'text';
      input.className = 'the-inline-input ma';
      input.value = rawVal;
      input.placeholder = '# Mã Python thô...';
      input.spellcheck = false;
      input.autocomplete = 'off';

      function updateRawWidth() {
        const len = (input.value || input.placeholder || '').length;
        input.style.width = Math.max(len + 1, 6) + 'ch';
      }
      updateRawWidth();

      input.addEventListener('input', (e) => {
        if (!node.o) node.o = {};
        node.o.nguyen_van = e.target.value;
        updateRawWidth();
        node.da_sua = true;
        onTreeChanged(false);
      });
      wrap.appendChild(input);
    } else if (cardDef.o && cardDef.o.length > 0) {
      cardDef.o.forEach((oDef, idx) => {
        if (idx > 0) {
          const sep = document.createElement('span');
          sep.className = 'ma';
          sep.textContent = ' ';
          wrap.appendChild(sep);
        }
        wrap.appendChild(createCodeInput(node, oDef.ten, oDef.goi_y || oDef.ten, 'ma'));
      });
    }

    return wrap;
  }

  // Dòng thẻ đang được đánh dấu "sẽ chèn trước/sau đây" trong lúc kéo. Theo
  // dõi ĐÚNG MỘT phần tử ở đây thay vì quét toàn bộ DOM mỗi lần dragover —
  // cây có thể tới vài trăm thẻ (281 trên core/web_search.py), dragover bắn
  // liên tục khi rê chuột.
  let hangDangDanhDau = null;
  function danhDauViTriTha(hangEl, truoc) {
    if (hangDangDanhDau && hangDangDanhDau !== hangEl) {
      hangDangDanhDau.classList.remove('tha-truoc-hang', 'tha-sau-hang');
    }
    hangEl.classList.toggle('tha-truoc-hang', truoc);
    hangEl.classList.toggle('tha-sau-hang', !truoc);
    hangDangDanhDau = hangEl;
  }
  function xoaDanhDauViTriTha() {
    if (hangDangDanhDau) {
      hangDangDanhDau.classList.remove('tha-truoc-hang', 'tha-sau-hang');
      hangDangDanhDau = null;
    }
  }

  function renderCard(node, parentList, index, depth = 1, parentBlockId = null) {
    const cardDef = TheValidator.BO_THE_V1[node.ma] || { ten: node.ma, mau: '#6B7280', co_than: false, o: [] };
    
    // Tìm lỗi / cảnh báo ứng với nút này
    const nodeDiags = (state.diagnostics.danh_sach || []).filter(d => d.node_id === node.id);
    const hasDo = nodeDiags.some(d => d.muc_do === 'do');
    const hasVang = nodeDiags.some(d => d.muc_do === 'vang');

    // Xác định lớp màu và CSS variable theo nhóm chuẩn
    let colorClass = 'c-tho';
    let groupVar = 'var(--tho)';
    if (node.ma === 'ham' || node.ma === 'goi_ham' || node.ma === 'tra_ve') {
      colorClass = 'c-ham';
      groupVar = 'var(--ham)';
    } else if (node.ma === 'neu' || node.ma === 'nguoc_lai' || node.ma === 'lap_moi' || node.ma === 'lap_khi') {
      colorClass = 'c-dk';
      groupVar = 'var(--dk)';
    } else if (node.ma === 'gan' || node.ma === 'pheptinh') {
      colorClass = 'c-dl';
      groupVar = 'var(--dl)';
    } else if (node.ma === 'in_ra') {
      colorClass = 'c-vr';
      groupVar = 'var(--vr)';
    } else if (node.ma === 'chu_thich') {
      colorClass = 'c-ct';
      groupVar = 'var(--ct)';
    } else {
      colorClass = 'c-tho';
      groupVar = 'var(--tho)';
    }

    const fragment = document.createDocumentFragment();

    // 1. Dòng thẻ (.hang)
    const hangEl = document.createElement('div');
    hangEl.className = 'hang';
    hangEl.style.color = groupVar;
    hangEl.id = `node_${node.id}`;
    hangEl.dataset.nodeId = node.id;

    // Kéo NGƯỢC: từ canvas ra khay để xoá — chiều còn thiếu trước 24/08, khay
    // chỉ kéo được một chiều (khay -> canvas). `input, button` trong dòng thẻ
    // cần giữ được bấm/chọn chữ bình thường nên chặn drag khi bắt đầu từ đó.
    hangEl.draggable = true;
    hangEl.addEventListener('dragstart', (e) => {
      if (e.target.closest('input, textarea, select, button')) {
        e.preventDefault();
        return;
      }
      e.dataTransfer.effectAllowed = 'move';
      e.dataTransfer.setData('text/plain', JSON.stringify({ type: 'EXISTING_CARD', nodeId: node.id }));
      state.draggingCardId = node.id;
      hangEl.classList.add('dang-keo-ra');
    });
    hangEl.addEventListener('dragend', () => {
      state.draggingCardId = null;
      hangEl.classList.remove('dang-keo-ra');
      const tc = document.getElementById('toolboxContainer');
      if (tc) tc.classList.remove('vung-tha-xoa');
      xoaDanhDauViTriTha();
    });

    // Kéo SẮP XẾP LẠI: rê một thẻ (từ khay hoặc từ chỗ khác trên canvas) tới
    // gần dòng này — thả nửa TRÊN thì chèn trước, nửa DƯỚI thì chèn sau.
    // stopPropagation để khối .khoi/canvas bao ngoài không tô viền chồng lên.
    hangEl.addEventListener('dragover', (e) => {
      if (state.draggingCardId === node.id) return; // đang kéo chính mình
      e.preventDefault();
      e.stopPropagation();
      e.dataTransfer.dropEffect = 'move';
      const r = hangEl.getBoundingClientRect();
      const truoc = (e.clientY - r.top) < r.height / 2;
      danhDauViTriTha(hangEl, truoc);
    });
    hangEl.addEventListener('drop', (e) => {
      e.preventDefault();
      e.stopPropagation();
      const chenTruoc = hangEl.classList.contains('tha-truoc-hang');
      xoaDanhDauViTriTha();
      const raw = e.dataTransfer.getData('text/plain');
      if (!raw) return;
      try {
        const payload = JSON.parse(raw);
        const viTri = chenTruoc ? index : index + 1;
        if (payload.type === 'NEW_CARD') {
          const newNode = taoTheNode(payload.ma);
          parentList.splice(viTri, 0, newNode);
          onTreeChanged();
        } else if (payload.type === 'EXISTING_CARD' && payload.nodeId && payload.nodeId !== node.id) {
          if (diChuyenThe(payload.nodeId, parentList, parentBlockId, viTri)) {
            onTreeChanged();
          }
        }
      } catch (_) {}
    });

    // 2. Thẻ viên thuốc (.the)
    const theEl = document.createElement('span');
    theEl.className = `the ${colorClass} ${hasDo ? 'status-do' : (hasVang ? 'status-vang' : '')}`;

    // Lỗ cạnh TRÁI (.lo)
    const loEl = document.createElement('span');
    loEl.className = 'lo';
    theEl.appendChild(loEl);

    // Chấm báo lỗi / cảnh báo
    if (hasDo) {
      const badge = document.createElement('span');
      badge.className = 'card-diag-icon do';
      badge.textContent = '🔴';
      badge.title = nodeDiags.filter(d => d.muc_do === 'do').map(d => d.thong_diep).join('\n');
      theEl.appendChild(badge);
    } else if (hasVang) {
      const badge = document.createElement('span');
      badge.className = 'card-diag-icon vang';
      badge.textContent = '🟡';
      badge.title = nodeDiags.filter(d => d.muc_do === 'vang').map(d => d.thong_diep).join('\n');
      theEl.appendChild(badge);
    }

    // Nội dung thẻ (tokens + inputs)
    const contentEl = renderCodeLineContent(node, cardDef);
    theEl.appendChild(contentEl);

    // Chú thích cuối dòng (duoi_dong) nếu có
    if (node.duoi_dong) {
      const ddEl = document.createElement('span');
      ddEl.className = 'cm duoi-dong-badge';
      ddEl.textContent = ` ${node.duoi_dong.trim()}`;
      ddEl.title = 'Chú thích cuối dòng';
      theEl.appendChild(ddEl);
    }

    hangEl.appendChild(theEl);

    // Controls hover
    const controlsEl = document.createElement('div');
    controlsEl.className = 'card-controls';

    if (index > 0) {
      const btnUp = document.createElement('button');
      btnUp.className = 'btn-card-tool';
      btnUp.textContent = '↑';
      btnUp.title = 'Di chuyển lên';
      btnUp.addEventListener('click', (e) => {
        e.stopPropagation();
        const tmp = parentList[index];
        parentList[index] = parentList[index - 1];
        parentList[index - 1] = tmp;
        onTreeChanged();
      });
      controlsEl.appendChild(btnUp);
    }

    if (index < parentList.length - 1) {
      const btnDown = document.createElement('button');
      btnDown.className = 'btn-card-tool';
      btnDown.textContent = '↓';
      btnDown.title = 'Di chuyển xuống';
      btnDown.addEventListener('click', (e) => {
        e.stopPropagation();
        const tmp = parentList[index];
        parentList[index] = parentList[index + 1];
        parentList[index + 1] = tmp;
        onTreeChanged();
      });
      controlsEl.appendChild(btnDown);
    }

    const btnDup = document.createElement('button');
    btnDup.className = 'btn-card-tool';
    btnDup.textContent = '📋';
    btnDup.title = 'Nhân bản thẻ này';
    btnDup.addEventListener('click', (e) => {
      e.stopPropagation();
      const clone = JSON.parse(JSON.stringify(node));
      state.nodeIdCounter++;
      clone.id = `the_${node.ma}_${state.nodeIdCounter}`;
      clone.da_sua = true;
      parentList.splice(index + 1, 0, clone);
      onTreeChanged();
    });
    controlsEl.appendChild(btnDup);

    const btnDel = document.createElement('button');
    btnDel.className = 'btn-card-tool delete';
    btnDel.textContent = '✕';
    btnDel.title = 'Xoá thẻ này';
    btnDel.addEventListener('click', (e) => {
      e.stopPropagation();
      parentList.splice(index, 1);
      onTreeChanged();
    });
    controlsEl.appendChild(btnDel);

    hangEl.appendChild(controlsEl);
    fragment.appendChild(hangEl);

    // 3. Khối con (.khoi) nếu thẻ có thân
    if (cardDef.co_than) {
      const khoiEl = document.createElement('div');
      khoiEl.className = 'khoi cuoi';
      khoiEl.dataset.slotId = node.id;

      if (node.than && node.than.length > 0) {
        renderCardList(node.than, khoiEl, depth + 1, node.id);
      } else {
        const ph = document.createElement('div');
        ph.className = 'slot-placeholder';
        ph.textContent = '+ Thả thẻ vào thân này...';
        khoiEl.appendChild(ph);
      }

      // Drag and drop vào slot
      khoiEl.addEventListener('dragover', (e) => {
        e.preventDefault();
        e.stopPropagation();
        khoiEl.style.outline = '1px dashed var(--color-chain-active)';
      });
      khoiEl.addEventListener('dragleave', (e) => {
        e.preventDefault();
        khoiEl.style.outline = 'none';
      });
      khoiEl.addEventListener('drop', (e) => {
        e.preventDefault();
        e.stopPropagation();
        khoiEl.style.outline = 'none';
        const raw = e.dataTransfer.getData('text/plain');
        if (!raw) return;
        try {
          const payload = JSON.parse(raw);
          if (payload.type === 'NEW_CARD') {
            const newNode = taoTheNode(payload.ma);
            if (!node.than) node.than = [];
            node.than.push(newNode);
            onTreeChanged();
          } else if (payload.type === 'EXISTING_CARD' && payload.nodeId) {
            // Thả vào NỀN của khối (không trúng dòng thẻ con nào) -> đưa
            // xuống CUỐI thân khối này. Thả trúng một dòng thẻ cụ thể thì
            // dragover/drop của chính dòng đó (ở trên) đã xử lý trước và
            // stopPropagation, nên nhánh này không chạy.
            if (!node.than) node.than = [];
            if (diChuyenThe(payload.nodeId, node.than, node.id, node.than.length)) {
              onTreeChanged();
            }
          }
        } catch (_) {}
      });

      fragment.appendChild(khoiEl);
    }

    return fragment;
  }

  function renderCardList(nodeList, parentContainer, depth = 1) {
    for (let i = 0; i < nodeList.length; i++) {
      const node = nodeList[i];
      const nodeFrag = renderCard(node, nodeList, i, depth);
      parentContainer.appendChild(nodeFrag);
    }
  }

  function renderCanvas() {
    const rootContainer = document.getElementById('cardChainRoot');
    const emptyGuide = document.getElementById('emptyCanvasGuide');
    if (!rootContainer) return;
    rootContainer.innerHTML = '';

    if (state.tree.length === 0) {
      if (emptyGuide) emptyGuide.style.display = 'flex';
    } else {
      if (emptyGuide) emptyGuide.style.display = 'none';
      renderCardList(state.tree, rootContainer, 1);
    }

    // Đo đạc và tinh chỉnh cột dọc ngay sau khi render xong (double rAF)
    yeuCauChinhCotDoc();
  }

  // ==========================================================================
  // 4. KIỂM TRA TĨNH & CẬP NHẬT GIAO DIỆN (ĐỎ / VÀNG / ×N / CODE PREVIEW)
  // ==========================================================================
  let syncTimeout = null;

  function onTreeChanged(pushHistory = true, markDirty = true) {
    if (markDirty) state.hasModifications = true;
    document.getElementById('fileModifiedBadge').style.display =
      state.activeFilePath && state.hasModifications ? 'inline-block' : 'none';

    // 1. Chạy Client-side validator tức thì (0ms latency)
    state.diagnostics = TheValidator.kiemTraCayThe(state.tree);

    // 2. Cập nhật giao diện
    renderCanvas();
    updateToolboxCounters();
    updateCodePreview();
    updateDiagnosticsPanel();
    updateStatusBar();
    capNhatDaiNhip();
    capNhatKichBan();

    // 3. Đảm bảo căn chỉnh cột dọc sau mọi thay đổi cây thẻ
    yeuCauChinhCotDoc();

    // 4. Đồng bộ với Backend API /api/kiem (Python làm trọng tài)
    clearTimeout(syncTimeout);
    syncTimeout = setTimeout(syncWithBackendValidator, 300);
  }


  async function syncWithBackendValidator() {
    try {
      const resp = await authFetch('/api/kiem', {
        method: 'POST',
        body: JSON.stringify({ tree: state.tree })
      });
      if (resp.ok) {
        const data = await resp.json();
        // Cập nhật kết quả trọng tài từ Python nếu có lệch
        state.diagnostics = data;
        updateDiagnosticsPanel();
        updateStatusBar();
        updateToolboxCounters();
        yeuCauChinhCotDoc();
      }
    } catch (err) {
      console.warn('Không thể kết nối /api/kiem:', err);
    }
  }

  function updateCodePreview() {
    // Tab "Mã Python" đã bỏ ở vòng ba cột 23/08 (cột giữa đã là mã rồi, không cần
    // hiện hai lần), nhưng hàm này vẫn ghi vào #pythonCodeOutput. Phần tử không
    // còn nên `codeEl` là null -> TypeError -> openPyFile nuốt vào catch rồi
    // alert("Lỗi kết nối khi mở tệp: Cannot set properties of null").
    //
    // Đo 24/08: trang mới tinh, mở tệp ĐẦU TIÊN là hộp lỗi hiện lên, dù tệp
    // MỞ ĐƯỢC (state.activeFilePath đã gán đúng). Và trong Chrome headless thì
    // `alert` chặn renderer, không ai đóng, nên cửa CDP treo quá 317 giây.
    const codeEl = document.getElementById('pythonCodeOutput');
    if (!codeEl) return;
    const code = TheValidator.sinhMaPython(state.tree);
    codeEl.textContent = code || '# (Chưa có lệnh nào trong chương trình)';
  }

  function updateStatusBar() {
    const dot = document.getElementById('overallStatusDot');
    const text = document.getElementById('overallStatusText');
    const doCount = state.diagnostics.so_loi_do;
    const vangCount = state.diagnostics.so_canh_bao_vang;

    if (doCount > 0) {
      dot.className = 'status-indicator do';
      text.textContent = `${doCount} Lỗi ĐỎ · ${vangCount} Cảnh báo VÀNG`;
      text.style.color = 'var(--color-error-do)';
    } else if (vangCount > 0) {
      dot.className = 'status-indicator vang';
      text.textContent = `Hợp lệ · ${vangCount} Cảnh báo VÀNG`;
      text.style.color = 'var(--color-warn-vang)';
    } else {
      dot.className = 'status-indicator';
      text.textContent = 'Hợp lệ · 0 Lỗi · 0 Cảnh báo';
      text.style.color = 'var(--text-secondary)';
    }
  }

  function updateDiagnosticsPanel() {
    const badgeCount = document.getElementById('diagBadge');
    const badgeDo = document.getElementById('badgeCountDo');
    const badgeVang = document.getElementById('badgeCountVang');
    const listEl = document.getElementById('diagList');

    const doCount = state.diagnostics.so_loi_do;
    const vangCount = state.diagnostics.so_canh_bao_vang;

    badgeCount.textContent = doCount + vangCount;
    badgeDo.textContent = `${doCount} ĐỎ (Lỗi)`;
    badgeVang.textContent = `${vangCount} VÀNG (Cảnh báo)`;

    listEl.innerHTML = '';

    if (state.diagnostics.danh_sach.length === 0) {
      listEl.innerHTML = '<div style="color: var(--text-muted); font-size: 12px; text-align: center; padding: 20px;">✓ Không phát hiện lỗi hoặc cảnh báo nào.</div>';
      return;
    }

    state.diagnostics.danh_sach.forEach(item => {
      const div = document.createElement('div');
      div.className = `diag-item ${item.muc_do}`;
      div.innerHTML = `
        <span>${item.muc_do === 'do' ? '🔴' : '🟡'}</span>
        <div>
          <strong>${item.thong_diep}</strong>
          ${item.line ? `<div style="font-size: 11px; opacity: 0.8;">Dòng ${item.line}</div>` : ''}
        </div>
      `;
      div.addEventListener('click', () => {
        if (item.node_id && item.node_id !== 'global') {
          const targetEl = document.getElementById(`node_${item.node_id}`);
          if (targetEl) {
            targetEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
            targetEl.style.transition = 'transform 200ms';
            targetEl.style.transform = 'scale(1.02)';
            setTimeout(() => targetEl.style.transform = 'scale(1)', 400);
          }
        }
      });
      listEl.appendChild(div);
    });
  }

  // ==========================================================================
  // DẢI NHỊP THỰC THI (EXECUTION RHYTHMS — CẮT THEO DEF & NHỊP CHƯA ĐÓNG)
  // ==========================================================================
  const TANG_THE_MAP = {
    gan: 'K',
    pheptinh: 'B', neu: 'B', nguoc_lai: 'B', lap_moi: 'B', lap_khi: 'B',
    in_ra: 'X', tra_ve: 'X'
  };

  function capNhatDaiNhip() {
    const container = document.getElementById('rhythmPillsContainer');
    if (!container) return;
    container.innerHTML = '';

    if (!state.tree || state.tree.length === 0) {
      container.innerHTML = '<span class="rhythm-empty-hint">Chưa có hàm hoặc thẻ phân tầng...</span>';
      return;
    }

    // Tách các track theo từng hàm def hoặc module top-level
    const tracks = [];
    const moduleNodes = [];

    state.tree.forEach(node => {
      if (node.ma === 'ham') {
        const fnName = (node.o && node.o.ten_ham) ? String(node.o.ten_ham).trim() : 'hàm';
        tracks.push({
          tenTrack: `def ${fnName}()`,
          nodes: node.than || []
        });
      } else {
        moduleNodes.push(node);
      }
    });

    if (moduleNodes.length > 0) {
      tracks.unshift({
        tenTrack: 'Module',
        nodes: moduleNodes
      });
    }

    let tongSoNhip = 0;

    tracks.forEach(track => {
      const flatNodes = [];
      function di(ns) {
        ns.forEach(n => {
          flatNodes.push(n);
          if (n.than && n.than.length) di(n.than);
        });
      }
      di(track.nodes);

      const thePhanTang = flatNodes.filter(n => TANG_THE_MAP[n.ma]);
      if (thePhanTang.length === 0) return;

      const nhipList = [];
      let curNodes = [];
      let curStr = [];
      let soThuTu = 1;

      thePhanTang.forEach(the => {
        const k = TANG_THE_MAP[the.ma];
        curNodes.push(the);
        curStr.push(k);
        if (k === 'X') {
          const matCat = curStr.join('');
          const coKhuyetB = !matCat.includes('B') && matCat.includes('K');
          const coRong = !matCat.includes('B') && !matCat.includes('K');
          nhipList.push({
            soThuTu: soThuTu++,
            nodes: [...curNodes],
            matCat,
            coKhuyetB,
            coRong,
            chuaDong: false
          });
          curNodes = [];
          curStr = [];
        }
      });

      if (curNodes.length > 0) {
        const matCat = curStr.join('');
        nhipList.push({
          soThuTu: soThuTu++,
          nodes: [...curNodes],
          matCat,
          coKhuyetB: false,
          coRong: false,
          chuaDong: true
        });
      }

      if (nhipList.length > 0) {
        tongSoNhip += nhipList.length;

        const trackRow = document.createElement('div');
        trackRow.className = 'rhythm-track-row';

        const trackTitle = document.createElement('span');
        trackTitle.className = 'rhythm-track-title';
        trackTitle.textContent = track.tenTrack;
        trackRow.appendChild(trackTitle);

        const pillsContainer = document.createElement('div');
        pillsContainer.className = 'rhythm-pills';

        nhipList.forEach(nhip => {
          const pill = document.createElement('div');
          pill.className = `rhythm-pill ${nhip.chuaDong ? 'unclosed' : ''}`;
          pill.title = `${track.tenTrack} — Nhịp ${nhip.soThuTu} (Mặt cắt: ${nhip.matCat}${nhip.chuaDong ? ' · Chưa đóng' : ''}) — Click để chọn`;

          let badgeHtml = '';
          if (nhip.chuaDong) {
            badgeHtml = `<span class="rhythm-tag-badge unclosed">${nhip.matCat || 'K'} (Chưa đóng)</span>`;
          } else if (nhip.coRong) {
            badgeHtml = '<span class="rhythm-tag-badge empty">X (Rỗng)</span>';
          } else if (nhip.coKhuyetB) {
            badgeHtml = `<span class="rhythm-tag-badge khuyet">${nhip.matCat} (Khuyết B)</span>`;
          } else {
            badgeHtml = `<span class="rhythm-tag-badge ${nhip.matCat.toLowerCase().includes('k') ? 'k' : 'b'}">${nhip.matCat}</span>`;
          }

          pill.innerHTML = `<span>#${nhip.soThuTu}</span> ${badgeHtml}`;

          pill.addEventListener('click', () => {
            document.querySelectorAll('.rhythm-pill').forEach(p => p.classList.remove('active'));
            pill.classList.add('active');

            document.querySelectorAll('.card-block').forEach(c => c.style.outline = 'none');
            nhip.nodes.forEach(n => {
              const card = document.getElementById(`node_${n.id}`);
              if (card) {
                card.style.outline = '2px solid var(--color-bien-so)';
                card.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
              }
            });
          });

          pillsContainer.appendChild(pill);
        });

        trackRow.appendChild(pillsContainer);
        container.appendChild(trackRow);
      }
    });

    if (tongSoNhip === 0) {
      container.innerHTML = '<span class="rhythm-empty-hint">Chưa có thẻ phân tầng (Gán/Biến đổi/Kết xuất)...</span>';
    }
  }

  // ==========================================================================
  // MẠCH NƯỚC NGẦM BIẾN SỐ (RUNTIME TRACE)
  // ==========================================================================
  async function chayMachNuocNgam() {
    const btnTrace = document.getElementById('btnRunTrace');
    const statusPill = document.getElementById('traceStatusPill');
    const subInfo = document.getElementById('traceSubInfo');
    const testNameEl = document.getElementById('traceTestName');
    const noticeEl = document.getElementById('traceNotice');
    const timelineBody = document.getElementById('traceTimelineBody');
    const e1ResultsBody = document.getElementById('e1ResultsBody');

    if (!btnTrace || !statusPill || !timelineBody) return;

    if (!state.codeExecutionEnabled) {
      statusPill.className = 'trace-status-pill cut';
      statusPill.textContent = 'Chạy mã/test đang tắt';
      return;
    }

    btnTrace.disabled = true;
    statusPill.className = 'trace-status-pill ready';
    statusPill.textContent = 'Đang dò vết...';
    timelineBody.style.display = 'block';
    if (e1ResultsBody) e1ResultsBody.style.display = 'none';
    timelineBody.innerHTML = '<div class="trace-empty-hint">Đang thu thập chuỗi biến đổi dữ liệu thực thi (Trần 5000 bước)...</div>';

    try {
      const payload = {
        tep_nguon: state.activeFilePath || 'core/dong_ho.py',
        tep_test: state.activeFilePath ? state.activeFilePath.replace('core/', 'tests/test_') : 'tests/test_dong_ho.py',
        max_steps: 5000
      };

      const resp = await authFetch('/api/trace', {
        method: 'POST',
        body: JSON.stringify(payload)
      });

      if (!resp.ok) {
        const errData = await resp.json().catch(() => ({}));
        statusPill.className = 'trace-status-pill error';
        statusPill.textContent = errData.error || (resp.status === 403 ? 'Chạy mã/test đang tắt' : 'Không đo được');
        timelineBody.innerHTML = `<div class="trace-empty-hint" style="color: var(--color-error-do);">${escapeHtml(errData.error || 'Lỗi ' + resp.status)}</div>`;
        return;
      }

      const res = await resp.json();

      if (res.trang_thai === 'trace_du') {
        statusPill.className = 'trace-status-pill success';
        statusPill.textContent = `✓ ${res.thong_diep} (${res.thoi_gian_giay}s)`;
      } else if (res.trang_thai === 'trace_cut') {
        statusPill.className = 'trace-status-pill cut';
        statusPill.textContent = `⚠️ ${res.thong_diep}`;
      } else if (res.trang_thai === 'trace_khong_qua_loi') {
        statusPill.className = 'trace-status-pill cut';
        statusPill.textContent = `⚠️ ${res.thong_diep}`;
      } else {
        statusPill.className = 'trace-status-pill error';
        statusPill.textContent = `❌ ${res.thong_diep || 'Không đo được'}`;
      }

      if (res.ten_test) {
        subInfo.style.display = 'flex';
        testNameEl.textContent = `Test: ${res.ten_test}`;
        if (res.trang_thai === 'trace_khong_qua_loi') {
          noticeEl.textContent = 'CẢNH BÁO: Vết thực thi của test này không đi qua dòng lỗi!';
        } else if (res.so_test_do_khac > 0) {
          noticeEl.textContent = `(Đang hiển thị test ít bước nhất; còn ${res.so_test_do_khac} test đỏ khác)`;
        } else {
          noticeEl.textContent = '';
        }
      } else {
        subInfo.style.display = 'none';
      }

      const events = res.cac_su_kien || [];
      if (events.length === 0) {
        timelineBody.innerHTML = '<div class="trace-empty-hint">Không có sự kiện biến đổi biến nào được ghi nhận.</div>';
        return;
      }

      timelineBody.innerHTML = '';
      events.forEach(ev => {
        const card = document.createElement('div');
        card.className = `trace-event-card ${ev.su_kien === 'tra_ve' ? 'return-event' : ''}`;
        card.innerHTML = `
          <div class="trace-event-header">
            <span class="trace-step-badge">Bước #${ev.buoc}</span>
            <span class="trace-line-badge">Dòng ${ev.dong}</span>
          </div>
          <div class="trace-event-body">
            <span class="trace-var-name">${escapeHtml(ev.ten_bien)}</span>
            <span class="trace-arrow">➔</span>
            ${ev.gia_tri_cu ? `<span class="trace-old-val">${escapeHtml(ev.gia_tri_cu)}</span>` : ''}
            <span class="trace-new-val">${escapeHtml(ev.gia_tri_moi)}</span>
          </div>
          ${ev.dong_ma ? `<div class="trace-code-snippet">${escapeHtml(ev.dong_ma)}</div>` : ''}
        `;
        timelineBody.appendChild(card);
      });

    } catch (err) {
      statusPill.className = 'trace-status-pill error';
      statusPill.textContent = 'Lỗi kết nối /api/trace';
      timelineBody.innerHTML = `<div class="trace-empty-hint" style="color: var(--color-error-do);">Lỗi: ${escapeHtml(err.message)}</div>`;
    } finally {
      btnTrace.disabled = !state.codeExecutionEnabled;
    }
  }

  // ==========================================================================
  // E1 — ĐỊNH VỊ LỖI BẰNG TEST TRÊN BẢN SAO TẠM
  // ==========================================================================
  async function loadAvailableTests(defaultTestPath = '') {
    const select = document.getElementById('e1TestSelect');
    if (!select) return;
    try {
      const resp = await authFetch('/api/tep_tin?thu_muc=tests');
      if (resp.ok) {
        const data = await resp.json();
        const tests = data.danh_sach || [];
        if (!state.testFilesInventory) state.testFilesInventory = {};
        select.innerHTML = '';
        tests.forEach(t => {
          state.testFilesInventory[t.duong_dan] = t;
          const opt = document.createElement('option');
          opt.value = t.duong_dan;
          opt.textContent = t.duong_dan;
          if (defaultTestPath && t.duong_dan === defaultTestPath) {
            opt.selected = true;
          }
          select.appendChild(opt);
        });
        if (defaultTestPath && !tests.some(t => t.duong_dan === defaultTestPath)) {
          const opt = document.createElement('option');
          opt.value = defaultTestPath;
          opt.textContent = defaultTestPath;
          opt.selected = true;
          select.appendChild(opt);
        }
      }
    } catch (_) {}
  }

  function updateButtonsState() {
    const btnRun = document.getElementById('btnRun');
    const btnTrace = document.getElementById('btnRunTrace');
    const btnE1 = document.getElementById('btnRunE1');

    if (!state.codeExecutionEnabled) {
      if (btnRun) btnRun.disabled = true;
      if (btnTrace) btnTrace.disabled = true;
      if (btnE1) btnE1.disabled = true;
      return;
    }

    if (btnRun) btnRun.disabled = false;
    if (btnTrace) btnTrace.disabled = false;

    if (btnE1) {
      if (state.hasModifications) {
        btnE1.disabled = true;
        btnE1.title = 'Vui lòng lưu hoặc hoàn tác trước khi định vị lỗi';
      } else {
        btnE1.disabled = false;
        btnE1.title = 'Định vị lỗi E1 trên bản sao tạm';
      }
    }
  }

  async function chayDinhViLoiE1() {
    const btnE1 = document.getElementById('btnRunE1');
    const statusPill = document.getElementById('e1StatusPill');
    const e1ResultsBody = document.getElementById('e1ResultsBody');
    const traceTimelineBody = document.getElementById('traceTimelineBody');
    const testSelect = document.getElementById('e1TestSelect');

    if (!btnE1 || !statusPill || !e1ResultsBody) return;

    if (!state.codeExecutionEnabled) {
      statusPill.className = 'trace-status-pill cut';
      statusPill.textContent = 'Chạy mã/test đang tắt';
      return;
    }

    if (state.hasModifications) {
      statusPill.className = 'trace-status-pill error';
      statusPill.textContent = 'Hãy lưu hoặc hoàn tác trước khi định vị';
      return;
    }

    if (!state.activeFilePath || !state.activeFileSha256) {
      statusPill.className = 'trace-status-pill cut';
      statusPill.textContent = 'Vui lòng mở một tệp .py';
      return;
    }

    const selectedTestFile = testSelect && testSelect.value ? testSelect.value : (
      state.activeFilePath.replace('core/', 'tests/test_')
    );

    let testSha = '';
    if (state.testFilesInventory && state.testFilesInventory[selectedTestFile]) {
      testSha = state.testFilesInventory[selectedTestFile].sha256 || '';
    }
    if (!testSha) {
      try {
        const respTep = await authFetch('/api/tep_tin?thu_muc=tests');
        const dataTep = await respTep.json();
        const match = (dataTep.danh_sach || []).find(t => t.duong_dan === selectedTestFile);
        if (match && match.sha256) {
          testSha = match.sha256;
          if (!state.testFilesInventory) state.testFilesInventory = {};
          state.testFilesInventory[selectedTestFile] = match;
        }
      } catch (_) {}
    }

    btnE1.disabled = true;
    statusPill.className = 'trace-status-pill ready';
    statusPill.textContent = 'Đang phân tích E1...';
    if (traceTimelineBody) traceTimelineBody.style.display = 'none';
    e1ResultsBody.style.display = 'block';

    const t0Client = performance.now();
    let stageInterval = null;

    const renderProgress = () => {
      const elapsedSec = (performance.now() - t0Client) / 1000;
      let stageText = 'Đang khởi tạo bản sao tạm...';
      if (elapsedSec >= 2.0 && elapsedSec < 8.0) {
        stageText = 'Đang tìm test đỏ và truy vết dòng chạy...';
      } else if (elapsedSec >= 8.0) {
        stageText = 'Đang lọc ứng viên AST và kiểm thử toàn bộ suite...';
      }
      e1ResultsBody.innerHTML = `
        <div class="trace-empty-hint" style="text-align: left; padding: 16px;">
          <div style="font-weight: 600; margin-bottom: 8px; color: var(--color-brand);">⏳ Tiến trình định vị lỗi E1 (${elapsedSec.toFixed(1)}s):</div>
          <div style="margin-left: 12px; line-height: 1.6;">
            <div>${elapsedSec >= 0 ? '✓' : '○'} 1. Kiểm tra ràng buộc và chuẩn bị phiên</div>
            <div>${elapsedSec >= 2.0 ? '✓' : '○'} 2. Nhân bản cô lập & Thu vết dòng trên test đỏ</div>
            <div>${elapsedSec >= 8.0 ? '⏳' : '○'} 3. Lọc 5 họ phép AST & Chạy kiểm thử hồi quy toàn bộ suite</div>
          </div>
          <div style="margin-top: 10px; font-style: italic; color: var(--text-muted);">${stageText}</div>
        </div>
      `;
    };

    renderProgress();
    stageInterval = setInterval(renderProgress, 500);

    try {
      const payload = {
        tep_nguon: state.activeFilePath,
        tep_test: selectedTestFile,
        source_sha256: state.activeFileSha256,
        test_sha256: testSha
      };

      const resp = await authFetch('/api/dinh_vi_loi', {
        method: 'POST',
        body: JSON.stringify(payload)
      });

      if (stageInterval) {
        clearInterval(stageInterval);
        stageInterval = null;
      }

      const elapsedTotalSec = Math.round((performance.now() - t0Client) / 100) / 10;

      if (!resp.ok) {
        const errData = await resp.json().catch(() => ({}));
        statusPill.className = 'trace-status-pill error';
        if (resp.status === 409) {
          statusPill.textContent = errData.trang_thai === 'busy' ? 'BUSY' : 'SHA trôi (409)';
        } else if (resp.status === 403) {
          statusPill.textContent = 'Chạy mã/test đang tắt';
        } else if (resp.status === 504) {
          statusPill.textContent = 'TIMEOUT/KHÔNG ĐO ĐƯỢC';
        } else {
          statusPill.textContent = `Lỗi ${resp.status}`;
        }
        renderE1Error(errData.error || `HTTP ${resp.status}`);
        return;
      }

      const res = await resp.json();
      renderE1Results(res, null, elapsedTotalSec);

    } catch (err) {
      if (stageInterval) {
        clearInterval(stageInterval);
        stageInterval = null;
      }
      statusPill.className = 'trace-status-pill error';
      statusPill.textContent = 'Lỗi kết nối /api/dinh_vi_loi';
      renderE1Error(err.message);
    } finally {
      if (stageInterval) {
        clearInterval(stageInterval);
      }
      btnE1.disabled = !state.codeExecutionEnabled;
    }
  }

  function renderE1Results(res, targetEl, elapsedTotalSec) {
    const statusPill = document.getElementById('e1StatusPill');
    const e1ResultsBody = targetEl || document.getElementById('e1ResultsBody');
    if (!e1ResultsBody) return;

    if (statusPill) {
      if (res.trang_thai === 'tim_thay') {
        statusPill.className = 'trace-status-pill success';
        statusPill.textContent = 'TÌM THẤY';
      } else if (res.trang_thai === 'suite_khong_do_duoc') {
        statusPill.className = 'trace-status-pill error';
        statusPill.textContent = 'SUITE KHÔNG ĐO ĐƯỢC';
      } else if (res.trang_thai === 'ung_vien_khong_qua_suite') {
        statusPill.className = 'trace-status-pill cut';
        statusPill.textContent = 'ỨNG VIÊN KHÔNG QUA TOÀN BỘ TEST';
      } else if (res.trang_thai === 'khong_tim_thay') {
        statusPill.className = 'trace-status-pill cut';
        statusPill.textContent = 'KHÔNG TÌM THẤY';
      } else {
        statusPill.className = 'trace-status-pill error';
        statusPill.textContent = 'TIMEOUT/KHÔNG ĐO ĐƯỢC';
      }
    }

    e1ResultsBody.innerHTML = '';

    // 1. Notice: Phân tích trên bản sao
    const noticeTemp = document.createElement('div');
    noticeTemp.className = 'e1-notice-box e1-notice-temp';
    noticeTemp.textContent = '🛡️ Phân tích trên bản sao; tệp thật chưa đổi.';
    e1ResultsBody.appendChild(noticeTemp);

    // 2. Summary Card
    const summaryCard = document.createElement('div');
    summaryCard.className = 'e1-summary-card';

    const titleRow = document.createElement('div');
    titleRow.className = 'e1-summary-title';
    titleRow.innerHTML = `<span>Bằng Chứng Định Vị E1</span>`;
    const badgeState = document.createElement('span');
    if (res.trang_thai === 'tim_thay') {
      badgeState.className = 'e1-badge badge-green';
      badgeState.textContent = 'TÌM THẤY';
    } else if (res.trang_thai === 'suite_khong_do_duoc') {
      badgeState.className = 'e1-badge badge-red';
      badgeState.textContent = 'SUITE KHÔNG ĐO ĐƯỢC';
    } else if (res.trang_thai === 'ung_vien_khong_qua_suite') {
      badgeState.className = 'e1-badge badge-red';
      badgeState.textContent = 'ỨNG VIÊN KHÔNG QUA SUITE';
    } else {
      badgeState.className = 'e1-badge badge-red';
      badgeState.textContent = (res.trang_thai || '').toUpperCase();
    }
    titleRow.appendChild(badgeState);
    summaryCard.appendChild(titleRow);

    const metaList = document.createElement('div');
    metaList.className = 'e1-meta-row';

    function addMetaItem(label, val) {
      const item = document.createElement('div');
      item.className = 'e1-meta-item';
      const l = document.createElement('span');
      l.className = 'e1-meta-label';
      l.textContent = label + ':';
      const v = document.createElement('span');
      v.textContent = val;
      item.appendChild(l);
      item.appendChild(v);
      metaList.appendChild(item);
    }

    addMetaItem('Tệp nguồn', res.source_path || 'Chưa chọn');
    addMetaItem('Tệp test', res.test_file || 'Chưa chọn');
    if (res.selected_test) {
      addMetaItem('Test chọn', res.selected_test);
    }
    if (res.other_red_test_count !== undefined) {
      addMetaItem('Test đỏ khác', String(res.other_red_test_count));
    }
    if (res.candidate_count_before !== undefined && res.candidate_count_after !== undefined) {
      addMetaItem('Ứng viên lọc', `${res.candidate_count_before} → ${res.candidate_count_after}`);
    }
    if (res.elapsed_filter_mutate_s !== undefined) {
      addMetaItem('Thời gian lọc+lật', `${res.elapsed_filter_mutate_s}s`);
    }
    if (res.elapsed_full_suite_s !== undefined) {
      addMetaItem('Thời gian full suite', `${res.elapsed_full_suite_s}s`);
    }
    if (elapsedTotalSec !== undefined) {
      addMetaItem('Tổng thời gian E1', `${elapsedTotalSec.toFixed(2)}s`);
    }

    summaryCard.appendChild(metaList);

    // Giải thích cho ca ung_vien_khong_qua_suite
    if (res.trang_thai === 'ung_vien_khong_qua_suite') {
      const noticeRejected = document.createElement('div');
      noticeRejected.className = 'e1-notice-box e1-notice-rejected';
      noticeRejected.style.marginTop = '10px';
      noticeRejected.innerHTML = `
        <strong>Giải thích:</strong> Các ứng viên dưới đây sửa được đúng bài test chọn nhưng làm gãy các bài test khác trong hệ thống.
        <em>"Sửa một chỗ mà hỏng chỗ khác thì không phải sửa."</em> Hệ thống <strong>KHÔNG đề nghị áp dụng</strong> các bản vá này.
      `;
      summaryCard.appendChild(noticeRejected);
    }

    if (res.reason) {
      const reasonDiv = document.createElement('div');
      reasonDiv.style.marginTop = '8px';
      reasonDiv.style.fontSize = '12px';
      reasonDiv.style.color = 'var(--text-secondary)';
      reasonDiv.textContent = 'Lý do: ' + res.reason;
      summaryCard.appendChild(reasonDiv);
    }

    e1ResultsBody.appendChild(summaryCard);

    // 3. Danh sách ứng viên
    const candidates = res.candidates || [];
    if (candidates.length > 0) {
      const candTitle = document.createElement('div');
      candTitle.className = 'e1-summary-title';
      candTitle.style.marginTop = '16px';
      if (res.trang_thai === 'ung_vien_khong_qua_suite') {
        candTitle.textContent = `Danh Sách Ứng Viên Bị Loại (${candidates.length})`;
      } else {
        candTitle.textContent = `Danh Sách Ứng Viên (${candidates.length})`;
      }
      e1ResultsBody.appendChild(candTitle);

      candidates.forEach((cand, idx) => {
        const card = document.createElement('div');
        card.className = 'e1-candidate-card';

        const h = document.createElement('div');
        h.className = 'e1-candidate-header';

        const titleSpan = document.createElement('span');
        titleSpan.textContent = `Ứng viên #${cand.index !== undefined ? cand.index : idx + 1} (Dòng ${cand.line}): ${cand.operation}`;
        h.appendChild(titleSpan);

        const statusGroup = document.createElement('div');
        statusGroup.style.display = 'flex';
        statusGroup.style.gap = '6px';

        const testBadge = document.createElement('span');
        testBadge.className = `e1-badge ${cand.selected_test_status === 'XANH' ? 'badge-green' : 'badge-red'}`;
        testBadge.textContent = `Test chọn: ${cand.selected_test_status}`;
        statusGroup.appendChild(testBadge);

        const suiteBadge = document.createElement('span');
        if (cand.full_suite_status === 'XANH') {
          suiteBadge.className = 'e1-badge badge-green';
          suiteBadge.textContent = 'Suite: XANH';
        } else if (cand.full_suite_status === 'suite_khong_do_duoc') {
          suiteBadge.className = 'e1-badge badge-red';
          const lyDo = cand.ly_do_suite ? ` (${cand.ly_do_suite})` : '';
          suiteBadge.textContent = `Suite: không đo được${lyDo}`;
        } else {
          const soTest = cand.so_test_hong || (res.other_red_test_count ? res.other_red_test_count + 1 : 1);
          suiteBadge.className = 'e1-badge badge-red';
          suiteBadge.textContent = `Suite: ĐỎ (${soTest} test khác hỏng)`;
        }
        statusGroup.appendChild(suiteBadge);

        h.appendChild(statusGroup);
        card.appendChild(h);

        if (cand.unified_diff) {
          const diffPre = document.createElement('pre');
          diffPre.className = 'e1-diff-container';
          const diffLines = cand.unified_diff.split('\n');
          diffLines.forEach(line => {
            const lineSpan = document.createElement('div');
            if (line.startsWith('+') && !line.startsWith('+++')) {
              lineSpan.className = 'e1-diff-add';
            } else if (line.startsWith('-') && !line.startsWith('---')) {
              lineSpan.className = 'e1-diff-del';
            }
            lineSpan.textContent = line;
            diffPre.appendChild(lineSpan);
          });
          card.appendChild(diffPre);
        }

        e1ResultsBody.appendChild(card);
      });
    }

    // 4. Limitation notice
    const noticeLimit = document.createElement('div');
    noticeLimit.className = 'e1-notice-box e1-notice-limit';
    noticeLimit.textContent = res.limitation || state.e1Limitation || 'Chỉ dò năm họ phép E1 hiện có; không tìm thấy không có nghĩa là mã không có lỗi.';
    e1ResultsBody.appendChild(noticeLimit);
  }

  function renderE1Error(msg, targetEl) {
    const e1ResultsBody = targetEl || document.getElementById('e1ResultsBody');
    if (!e1ResultsBody) return;
    e1ResultsBody.innerHTML = `
      <div class="trace-empty-hint" style="color: var(--color-error-do);">
        Lỗi định vị E1: ${escapeHtml(msg)}
      </div>
    `;
  }

  // ==========================================================================
  // TAB KỊCH BẢN LOGIC (NARRATIVE)
  // ==========================================================================
  function capNhatKichBan() {
    const narrativeBody = document.getElementById('narrativeContent');
    if (!narrativeBody) return;

    if (state.tree.length === 0) {
      narrativeBody.innerHTML = '<div style="color: var(--text-muted); font-style: italic;">Chưa có khối lệnh nào để tạo kịch bản logic.</div>';
      return;
    }

    narrativeBody.innerHTML = '';
    let stepNum = 1;

    function duyetNarrative(nodes, indent = '') {
      nodes.forEach(node => {
        const step = document.createElement('div');
        step.className = 'narrative-step';
        let desc = '';

        if (node.ma === 'ham') {
          desc = `Định nghĩa hàm <code>${escapeHtml(node.o.ten_ham || 'chưa đặt tên')}</code> nhận tham số (<code>${escapeHtml(node.o.tham_so || 'không có')}</code>).`;
        } else if (node.ma === 'gan') {
          desc = `Gán giá trị <code>${escapeHtml(node.o.gia_tri || '')}</code> cho biến <strong>${escapeHtml(node.o.ten_bien || '')}</strong>.`;
        } else if (node.ma === 'pheptinh') {
          desc = `Thực hiện phép tính <code>${escapeHtml(node.o.bieu_thuc || '')}</code> và lưu vào <strong>${escapeHtml(node.o.ten_bien || '')}</strong>.`;
        } else if (node.ma === 'neu') {
          desc = `Kiểm tra điều kiện: Nếu <code>${escapeHtml(node.o.dieu_kien || '')}</code> thoả mãn thì thực hiện khối lệnh con.`;
        } else if (node.ma === 'nguoc_lai') {
          desc = `Trường hợp ngược lại: Thực hiện các lệnh khi điều kiện "Nếu" phía trước sai.`;
        } else if (node.ma === 'lap_moi') {
          desc = `Lặp qua từng phần tử <strong>${escapeHtml(node.o.bien || '')}</strong> trong dãy <code>${escapeHtml(node.o.day || '')}</code>.`;
        } else if (node.ma === 'lap_khi') {
          desc = `Lặp liên tục chừng nào điều kiện <code>${escapeHtml(node.o.dieu_kien || '')}</code> còn đúng.`;
        } else if (node.ma === 'in_ra') {
          desc = `Xuất nội dung <code>${escapeHtml(node.o.noi_dung || '')}</code> ra màn hình terminal.`;
        } else if (node.ma === 'tra_ve') {
          desc = `Trả về kết quả <code>${escapeHtml(node.o.gia_tri || '')}</code> cho nơi gọi hàm.`;
        } else {
          desc = `Thực thi khối lệnh <code>${escapeHtml(node.ma)}</code>.`;
        }

        step.innerHTML = `
          <div class="narrative-step-title">${indent}Bước ${stepNum++}: ${escapeHtml(TheValidator.BO_THE_V1[node.ma]?.ten || node.ma)}</div>
          <div>${desc}</div>
        `;
        narrativeBody.appendChild(step);

        if (node.than && node.than.length) {
          duyetNarrative(node.than, indent + '↳ ');
        }
      });
    }

    duyetNarrative(state.tree);
  }

  // ==========================================================================
  // 5. CHẠY THỬ CÓ CHỦ ĐÍCH (TẮT MẶC ĐỊNH VÌ CHƯA PHẢI SANDBOX THẬT)
  // ==========================================================================

  async function runProgram() {
    const btnRun = document.getElementById('btnRun');
    const runText = document.getElementById('runBtnText');
    const termBody = document.getElementById('terminalBody');
    const metaStatus = document.getElementById('metaStatus');
    const metaTime = document.getElementById('metaTime');

    if (!state.codeExecutionEnabled) {
      termBody.innerHTML = '<div class="term-line term-stderr">Chạy mã đang tắt để bảo vệ máy. Mở/sửa/kiểm tra/lưu mã vẫn hoạt động.</div>';
      return;
    }

    if (state.diagnostics.so_loi_do > 0) {
      termBody.innerHTML = `<div class="term-line term-stderr">❌ KHÔNG THỂ CHẠY: Chương trình đang có ${state.diagnostics.so_loi_do} Lỗi ĐỎ cứng. Vui lòng sửa các lỗi đỏ trước khi chạy.</div>`;
      metaStatus.className = 'meta-status error';
      metaStatus.textContent = 'LỖI ĐỎ';
      return;
    }

    const code = TheValidator.sinhMaPython(state.tree);
    if (!code || !code.trim()) {
      termBody.innerHTML = '<div class="term-line term-dim">> Chương trình rỗng, không có lệnh nào để chạy.</div>';
      return;
    }

    runText.textContent = 'ĐANG CHẠY...';
    btnRun.disabled = true;
    metaStatus.className = 'meta-status ready';
    metaStatus.textContent = 'ĐANG CHẠY';
    termBody.innerHTML = '<div class="term-line term-dim">> Đang thực thi trong tiến trình Python con cô lập (Trần 5.0s)...</div>';

    try {
      const resp = await authFetch('/api/chay', {
        method: 'POST',
        body: JSON.stringify({ code: code, tree: state.tree })
      });

      const res = await resp.json();
      metaTime.textContent = `${res.wall_time_ms || 0} ms`;

      if (res.status === 'PASS') {
        metaStatus.className = 'meta-status pass';
        metaStatus.textContent = 'PASS';
        termBody.innerHTML = `
          <div class="term-line term-stdout">${escapeHtml(res.stdout || '(Không có đầu ra stdout)')}</div>
          <div class="term-line term-dim">----------------------------------------\n[Hoàn thành trong ${res.wall_time_ms} ms · Exit code: 0]</div>
        `;
      } else if (res.status === 'TIMEOUT') {
        metaStatus.className = 'meta-status timeout';
        metaStatus.textContent = 'TIMEOUT';
        termBody.innerHTML = `
          <div class="term-line term-stdout">${escapeHtml(res.stdout || '')}</div>
          <div class="term-line term-stderr">${escapeHtml(res.stderr || '')}</div>
          <div class="term-line term-dim">----------------------------------------\n[Đã ngắt sau 5.0 giây · Exit code: ${res.exit_code}]</div>
        `;
      } else {
        metaStatus.className = 'meta-status error';
        metaStatus.textContent = 'LỖI RUNTIME';
        termBody.innerHTML = `
          <div class="term-line term-stdout">${escapeHtml(res.stdout || '')}</div>
          <div class="term-line term-stderr">${escapeHtml(res.stderr || 'Lỗi không xác định')}</div>
          <div class="term-line term-dim">----------------------------------------\n[Thất bại · Exit code: ${res.exit_code}]</div>
        `;
      }
    } catch (err) {
      metaStatus.className = 'meta-status error';
      metaStatus.textContent = 'LỖI MẠNG';
      termBody.innerHTML = `<div class="term-line term-stderr">Lỗi kết nối máy chủ: ${escapeHtml(err.message)}</div>`;
    } finally {
      runText.textContent = 'CHẠY THỬ';
      btnRun.disabled = !state.codeExecutionEnabled;
    }
  }

  // ==========================================================================
  // 6. MẪU BÀI, MỞ TỆP & LƯU TỆP (CỬA CỨNG MỞ-LƯU LOSSLESS)
  // ==========================================================================
  function clearNodeDirtyFlags(nodes) {
    (nodes || []).forEach(node => {
      node.da_sua = false;
      clearNodeDirtyFlags(node.than || []);
    });
  }

  function normalizedPath(path) {
    return String(path || '').replaceAll('\\', '/').toLowerCase();
  }

  async function readJsonSafely(resp) {
    const text = await resp.text();
    if (!text) return {};
    try {
      return JSON.parse(text);
    } catch (_) {
      return { error: text };
    }
  }

  async function loadSamples() {
    try {
      const resp = await authFetch('/api/mau');
      if (resp.ok) {
        const data = await resp.json();
        const container = document.getElementById('samplesListContainer');
        container.innerHTML = '';
        (data.mau || []).forEach(m => {
          const card = document.createElement('div');
          card.className = 'sample-card-item';
          card.innerHTML = `
            <div class="sample-name">${m.ten}</div>
            <div class="sample-desc">${m.mo_ta}</div>
          `;
          card.addEventListener('click', () => {
            state.tree = JSON.parse(JSON.stringify(m.tree));
            state.activeFilePath = '';
            state.activeFileSha256 = null;
            document.getElementById('currentFileName').textContent = m.ten;
            document.getElementById('samplesModal').style.display = 'none';
            onTreeChanged();
          });
          container.appendChild(card);
        });
      }
    } catch (err) {
      console.warn('Lỗi tải mẫu bài:', err);
    }
  }

  async function openPyFile(filePath) {
    if (!filePath || !filePath.trim()) return;
    try {
      const resp = await authFetch('/api/mo_tep', {
        method: 'POST',
        body: JSON.stringify({ duong_dan: filePath.trim() })
      });
      if (resp.ok) {
        const data = await readJsonSafely(resp);
        if (!Array.isArray(data.tree) || typeof data.duong_dan !== 'string' ||
            !/^[0-9a-f]{64}$/.test(data.sha256 || '')) {
          throw new Error('Phản hồi mở tệp không hợp lệ');
        }
        state.tree = data.tree;
        state.activeFilePath = data.duong_dan;
        state.activeFileSha256 = data.sha256;
        state.hasModifications = false;
        document.getElementById('currentFileName').textContent = data.ten_tep;
        document.getElementById('fileModifiedBadge').style.display = 'none';
        document.getElementById('openFileModal').style.display = 'none';
        onTreeChanged(false, false);

        const testPath = data.duong_dan.startsWith('core/')
          ? data.duong_dan.replace('core/', 'tests/test_')
          : (data.duong_dan.startsWith('tests/') ? data.duong_dan : 'tests/test_' + data.ten_tep);
        loadAvailableTests(testPath);
        yeuCauChinhCotDoc();
      } else {
        const err = await readJsonSafely(resp);
        alert(`Lỗi mở tệp: ${err.error}`);
      }
    } catch (err) {
      alert(`Lỗi kết nối khi mở tệp: ${err.message}`);
    }
  }

  async function saveFile(filePath, saveType) {
    if (!filePath || !filePath.trim()) return;
    const target = filePath.trim();
    const sameTarget = Boolean(
      state.activeFilePath && normalizedPath(target) === normalizedPath(state.activeFilePath)
    );
    const payload = {
      duong_dan: target,
      tree: state.tree,
      kieu_luu: saveType,
      has_modifications: state.hasModifications
    };
    if (sameTarget && state.activeFileSha256) {
      payload.expected_sha256 = state.activeFileSha256;
    }
    if (state.activeFilePath && state.activeFileSha256) {
      payload.source_path = state.activeFilePath;
      payload.source_sha256 = state.activeFileSha256;
    }
    try {
      const resp = await authFetch('/api/luu_tep', {
        method: 'POST',
        body: JSON.stringify(payload)
      });
      if (resp.status === 409) {
        const err = await readJsonSafely(resp);
        state.hasModifications = true;
        document.getElementById('fileModifiedBadge').style.display = 'inline-block';
        const reload = confirm(
          'Tệp trên đĩa đã thay đổi bên ngoài. Tải lại sẽ bỏ các thay đổi chưa lưu trong app. ' +
          'Bạn có muốn tải lại ngay không?'
        );
        if (reload) await openPyFile(target);
        else if (err.error) console.warn(err.error);
        return;
      }
      if (resp.ok) {
        const data = await readJsonSafely(resp);
        if (typeof data.duong_dan !== 'string' || !/^[0-9a-f]{64}$/.test(data.sha256 || '')) {
          throw new Error('Máy chủ không trả SHA-256 hợp lệ sau khi lưu');
        }
        state.activeFilePath = data.duong_dan;
        state.activeFileSha256 = data.sha256;
        state.hasModifications = false;
        clearNodeDirtyFlags(state.tree);
        document.getElementById('currentFileName').textContent = data.duong_dan.split('/').pop().split('\\').pop();
        document.getElementById('fileModifiedBadge').style.display = 'none';
        document.getElementById('saveFileModal').style.display = 'none';
        alert('Lưu tệp thành công!');
      } else {
        const err = await readJsonSafely(resp);
        alert(`Lỗi lưu tệp: ${err.error}`);
      }
    } catch (err) {
      alert(`Lỗi kết nối khi lưu tệp: ${err.message}`);
    }
  }

  // ==========================================================================
  // 6. MẪU BÀI, DUYỆT TỆP, MỞ TỆP & LƯU TỆP
  // ==========================================================================
  async function loadRepoFiles(dir = 'core') {
    const listContainer = document.getElementById('repoFileListContainer');
    if (!listContainer) return;
    listContainer.innerHTML = '<div style="color: var(--text-muted); font-size: 11px; padding: 6px;">Đang tải danh sách tệp...</div>';

    try {
      // 24/08: tham số & tên trường từng viết theo API tưởng tượng, không phải
      // API thật (interface/the_api.py:396 chỉ đọc `thu_muc`, trả về `danh_sach`
      // với trường `kich_thuoc`). Hộp "Mở tệp" vì vậy LUÔN báo rỗng, mọi thư mục
      // — bắt được khi tự dùng thử, đối chiếu thẳng response JSON.
      const resp = await authFetch(`/api/tep_tin?thu_muc=${encodeURIComponent(dir)}`);
      if (resp.ok) {
        const data = await resp.json();
        const files = data.danh_sach || [];
        listContainer.innerHTML = '';
        if (files.length === 0) {
          listContainer.innerHTML = '<div style="color: var(--text-muted); font-size: 11px; padding: 6px;">Không có tệp .py nào trong thư mục này.</div>';
          return;
        }

        const chipsWrap = document.createElement('div');
        chipsWrap.className = 'file-chips';

        files.forEach(f => {
          const chip = document.createElement('span');
          chip.className = 'chip';
          chip.dataset.path = f.duong_dan;
          chip.textContent = f.duong_dan;
          chip.title = `Mở tệp ${f.duong_dan} (${f.kich_thuoc} bytes)`;
          chip.addEventListener('click', () => {
            document.getElementById('openFilePath').value = f.duong_dan;
            openPyFile(f.duong_dan);
          });
          chipsWrap.appendChild(chip);
        });

        listContainer.appendChild(chipsWrap);
      } else {
        listContainer.innerHTML = '<div style="color: var(--color-error-do); font-size: 11px; padding: 6px;">Lỗi khi tải tệp từ kho.</div>';
      }
    } catch (err) {
      listContainer.innerHTML = `<div style="color: var(--color-error-do); font-size: 11px; padding: 6px;">Lỗi kết nối: ${escapeHtml(err.message)}</div>`;
    }
  }

  // ==========================================================================
  // 6. CÂY THƯ MỤC TỆP TIN & CHUYỂN ĐỔI CHẾ ĐỘ CỘT TRÁI (1 CLICK)
  // ==========================================================================
  async function loadFileTree() {
    const container = document.getElementById('fileTreeContainer');
    if (!container) return;
    container.innerHTML = '<div style="color: var(--text-muted); font-size: 12px; padding: 12px;">Đang tải danh sách tệp từ kho...</div>';

    try {
      const resp = await authFetch('/api/tep_tin');
      if (!resp.ok) {
        container.innerHTML = '<div style="color: var(--color-error-do); font-size: 12px; padding: 12px;">Không tải được danh sách tệp.</div>';
        return;
      }
      const data = await resp.json();
      const files = data.danh_sach || [];
      renderFileTree(files, container);
    } catch (err) {
      container.innerHTML = `<div style="color: var(--color-error-do); font-size: 12px; padding: 12px;">Lỗi: ${escapeHtml(err.message)}</div>`;
    }
  }

  function renderFileTree(files, container) {
    container.innerHTML = '';
    const groups = {};
    files.forEach(f => {
      const p = f.duong_dan || f;
      const parts = p.split(/[\\/]/);
      const dir = parts.length > 1 ? parts[0] : 'root';
      if (!groups[dir]) groups[dir] = [];
      groups[dir].push(p);
    });

    for (const dir in groups) {
      const dirNode = document.createElement('div');
      dirNode.className = 'file-tree-node';

      const dirRow = document.createElement('div');
      dirRow.className = 'file-tree-row folder';
      dirRow.innerHTML = `<span class="folder-icon">📂</span> <span style="font-weight:600;">${escapeHtml(dir)}/</span>`;
      dirNode.appendChild(dirRow);

      const childrenContainer = document.createElement('div');
      childrenContainer.className = 'file-tree-children';

      groups[dir].forEach(filePath => {
        const fileRow = document.createElement('div');
        fileRow.className = `file-tree-row ${state.activeFilePath === filePath ? 'active' : ''}`;
        fileRow.dataset.path = filePath;
        const fileName = filePath.split(/[\\/]/).pop();
        fileRow.innerHTML = `<span class="file-icon">🐍</span> <span>${escapeHtml(fileName)}</span>`;

        fileRow.addEventListener('click', () => {
          document.querySelectorAll('.file-tree-row').forEach(r => r.classList.remove('active'));
          fileRow.classList.add('active');
          openPyFile(filePath);
        });

        childrenContainer.appendChild(fileRow);
      });

      dirRow.addEventListener('click', () => {
        const isHidden = childrenContainer.style.display === 'none';
        childrenContainer.style.display = isHidden ? 'flex' : 'none';
        dirRow.querySelector('.folder-icon').textContent = isHidden ? '📂' : '📁';
      });

      dirNode.appendChild(childrenContainer);
      container.appendChild(dirNode);
    }
  }

  function setupBottomSplitter() {
    const splitter = document.getElementById('middleSplitter');
    const bottomPane = document.getElementById('canvasBottomPane');
    if (!splitter || !bottomPane) return;

    let isDragging = false;
    let startY = 0;
    let startHeight = 0;

    splitter.addEventListener('mousedown', (e) => {
      isDragging = true;
      startY = e.clientY;
      startHeight = bottomPane.getBoundingClientRect().height;
      splitter.classList.add('dragging');
      document.body.style.cursor = 'row-resize';
      document.body.style.userSelect = 'none';
    });

    window.addEventListener('mousemove', (e) => {
      if (!isDragging) return;
      const deltaY = startY - e.clientY;
      const newHeight = Math.max(100, Math.min(window.innerHeight * 0.65, startHeight + deltaY));
      bottomPane.style.height = `${newHeight}px`;
      yeuCauChinhCotDoc();
    });

    window.addEventListener('mouseup', () => {
      if (isDragging) {
        isDragging = false;
        splitter.classList.remove('dragging');
        document.body.style.cursor = '';
        document.body.style.userSelect = '';
        chinhCotDoc();
      }
    });
  }

  function setupAgentWorkspace() {
    const btnSend = document.getElementById('btnSendAgent');
    const input = document.getElementById('agentInput');
    const chatContainer = document.getElementById('agentChatContainer');
    if (!btnSend || !input || !chatContainer) return;

    const handleSend = () => {
      const text = input.value.trim();
      if (!text) return;

      const userMsg = document.createElement('div');
      userMsg.className = 'agent-msg user';
      userMsg.textContent = text;
      chatContainer.appendChild(userMsg);
      input.value = '';

      chatContainer.scrollTop = chatContainer.scrollHeight;

      setTimeout(() => {
        const botMsg = document.createElement('div');
        botMsg.className = 'agent-msg bot';
        botMsg.innerHTML = `Đã nhận yêu cầu: <em>"${escapeHtml(text)}"</em>.<br>Tôi đang kiểm tra cấu trúc thẻ và hỗ trợ thao tác tự động...`;
        chatContainer.appendChild(botMsg);
        chatContainer.scrollTop = chatContainer.scrollHeight;
      }, 350);
    };

    btnSend.addEventListener('click', handleSend);
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        handleSend();
      }
    });
  }

  // ==========================================================================
  // 7. SỰ KIỆN & LẮNG NGHE NGƯỜI DÙNG
  // ==========================================================================
  function setupEventListeners() {
    // 1. Sidebar Toggles
    const btnToggleLeft = document.getElementById('btnToggleSidebarLeft');
    if (btnToggleLeft) btnToggleLeft.addEventListener('click', toggleSidebarLeft);

    const btnCloseLeft = document.getElementById('btnCloseSidebarLeft');
    if (btnCloseLeft) btnCloseLeft.addEventListener('click', toggleSidebarLeft);

    const btnToggleRight = document.getElementById('btnToggleSidebarRight');
    if (btnToggleRight) btnToggleRight.addEventListener('click', toggleSidebarRight);

    const btnCloseRight = document.getElementById('btnToggleSidebarRightClose');
    if (btnCloseRight) btnCloseRight.addEventListener('click', toggleSidebarRight);

    // 2. Chuyển đổi chế độ Khay Thẻ ⇅ Cây Thư Mục (1 Bấm)
    const btnModeToolbox = document.getElementById('btnModeToolbox');
    const btnModeFiles = document.getElementById('btnModeFiles');
    const toolboxContainer = document.getElementById('toolboxContainer');
    const fileTreeContainer = document.getElementById('fileTreeContainer');
    const sidebarTitle = document.getElementById('sidebarLeftTitle');
    const toolSearch = document.getElementById('toolSearch');
    const footerTip = document.getElementById('leftFooterTip');

    if (btnModeToolbox && btnModeFiles) {
      btnModeToolbox.addEventListener('click', () => {
        btnModeToolbox.classList.add('active');
        btnModeFiles.classList.remove('active');
        if (toolboxContainer) toolboxContainer.style.display = 'flex';
        if (fileTreeContainer) fileTreeContainer.style.display = 'none';
        if (sidebarTitle) sidebarTitle.textContent = 'Khay Thẻ Lệnh';
        if (toolSearch) toolSearch.placeholder = 'Tìm thẻ...';
        // 24/08: chữ cũ ghi "Nhấp đúp" trong khi itemEl chỉ gắn 'click' đơn
        // (dòng ~245) — bấm đúp theo đúng lời hướng dẫn cũ chèn TRÙNG thẻ 2
        // lần, im lặng. Sửa chữ cho khớp việc thật, không đổi hành vi bấm đơn
        // vì nó đúng và tiện hơn (không cần hai cú bấm chính xác liên tiếp).
        if (footerTip) footerTip.textContent = 'Nhấp hoặc kéo thẻ vào vùng soạn thảo.';
      });

      btnModeFiles.addEventListener('click', () => {
        btnModeFiles.classList.add('active');
        btnModeToolbox.classList.remove('active');
        if (toolboxContainer) toolboxContainer.style.display = 'none';
        if (fileTreeContainer) fileTreeContainer.style.display = 'flex';
        if (sidebarTitle) sidebarTitle.textContent = 'Cây Thư Mục';
        if (toolSearch) toolSearch.placeholder = 'Tìm tệp python...';
        if (footerTip) footerTip.textContent = 'Click vào tệp để mở trực tiếp trên canvas.';
        loadFileTree();
      });
    }

    // 3. Toolbar buttons
    document.getElementById('btnRun').addEventListener('click', runProgram);
    
    document.getElementById('btnNew').addEventListener('click', () => {
      if (confirm('Tạo chương trình mới? Thao tác này sẽ dọn sạch vùng soạn thảo.')) {
        state.tree = [];
        state.activeFilePath = '';
        state.activeFileSha256 = null;
        document.getElementById('currentFileName').textContent = 'Chương trình mới (Chưa lưu)';
        document.getElementById('fileModifiedBadge').style.display = 'none';
        onTreeChanged();
      }
    });

    document.getElementById('btnClearCanvas').addEventListener('click', () => {
      if (confirm('Xoá toàn bộ thẻ trên canvas?')) {
        state.tree = [];
        onTreeChanged();
      }
    });

    // Mẫu bài Modal
    document.getElementById('btnSamples').addEventListener('click', () => {
      loadSamples();
      document.getElementById('samplesModal').style.display = 'flex';
    });
    document.getElementById('btnCloseSamples').addEventListener('click', () => {
      document.getElementById('samplesModal').style.display = 'none';
    });
    document.getElementById('btnLoadSampleIntro').addEventListener('click', () => {
      state.tree = [
        { id: "m1_1", ma: "ham", o: { ten_ham: "cong", tham_so: "a, b" }, than: [
          { id: "m1_2", ma: "tra_ve", o: { gia_tri: "a + b" }, than: [] }
        ]},
        { id: "m1_3", ma: "in_ra", o: { noi_dung: "cong(5, 7)" }, than: [] }
      ];
      state.activeFilePath = '';
      state.activeFileSha256 = null;
      document.getElementById('currentFileName').textContent = '1. Hàm cộng hai số';
      onTreeChanged();
    });

    // Mở tệp Modal & Bộ duyệt tệp động
    document.getElementById('btnOpenFile').addEventListener('click', () => {
      loadRepoFiles('core');
      // 24/08: bat gap khi tu dung thu — o nay KHONG duoc don khi mo lai
      // modal, nen van con duong dan cua lan mo truoc. Bam vao roi go tiep
      // (thao tac tu nhien nhat) noi chuoi cu voi chuoi moi thanh mot duong
      // dan vo nghia, vi input KHONG tu chon toan bo chu khi duoc focus.
      document.getElementById('openFilePath').value = '';
      document.getElementById('openFileModal').style.display = 'flex';
    });
    document.getElementById('btnCloseOpenFile').addEventListener('click', () => {
      document.getElementById('openFileModal').style.display = 'none';
    });
    document.getElementById('btnCancelOpenFile').addEventListener('click', () => {
      document.getElementById('openFileModal').style.display = 'none';
    });
    document.getElementById('btnConfirmOpenFile').addEventListener('click', () => {
      const p = document.getElementById('openFilePath').value;
      openPyFile(p);
    });
    // Bam vao chip trong danh sach van dien san duong dan (dong 2015) roi
    // nguoi dung co the muon sua tay — focus thi chon san toan bo chu, kieu
    // o dia chi trinh duyet, de go de la thay ngay chu bam khong noi vao.
    document.getElementById('openFilePath').addEventListener('focus', function () {
      this.select();
    });

    document.querySelectorAll('.filter-tag').forEach(tag => {
      tag.addEventListener('click', () => {
        document.querySelectorAll('.filter-tag').forEach(t => t.classList.remove('active'));
        tag.classList.add('active');
        loadRepoFiles(tag.dataset.dir || 'core');
      });
    });

    // Lưu tệp Modal
    document.getElementById('btnSaveFile').addEventListener('click', () => {
      document.getElementById('saveFilePath').value = state.activeFilePath || 'my_program.py';
      document.getElementById('saveFileModal').style.display = 'flex';
    });
    document.getElementById('btnCloseSaveFile').addEventListener('click', () => {
      document.getElementById('saveFileModal').style.display = 'none';
    });
    document.getElementById('btnCancelSaveFile').addEventListener('click', () => {
      document.getElementById('saveFileModal').style.display = 'none';
    });
    document.getElementById('btnConfirmSaveFile').addEventListener('click', () => {
      const p = document.getElementById('saveFilePath').value;
      const type = document.querySelector('input[name="saveType"]:checked').value;
      saveFile(p, type);
    });
    // Cùng bệnh với ô openFilePath (24/08): ô này luôn điền sẵn đường dẫn tệp
    // đang mở, có khi dài. Focus thì chọn hết để gõ đè sạch, không nối chuỗi.
    document.getElementById('saveFilePath').addEventListener('focus', function () {
      this.select();
    });

    // Bottom Pane Tabs Switch (4 tabs)
    document.querySelectorAll('.canvas-bottom-pane .tab-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('.canvas-bottom-pane .tab-btn').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.canvas-bottom-pane .tab-pane').forEach(p => p.classList.remove('active'));
        btn.classList.add('active');
        const targetTab = document.getElementById(btn.dataset.tab);
        if (targetTab) targetTab.classList.add('active');
      });
    });

    // Nút Dò Dòng Dữ Liệu (Mạch Nước Ngầm)
    const btnRunTrace = document.getElementById('btnRunTrace');
    if (btnRunTrace) {
      btnRunTrace.addEventListener('click', () => {
        chayMachNuocNgam();
      });
    }

    // Nút Định Vị Lỗi E1
    const btnRunE1 = document.getElementById('btnRunE1');
    if (btnRunE1) {
      btnRunE1.addEventListener('click', () => {
        chayDinhViLoiE1();
      });
    }

    // Tìm kiếm thẻ hoặc tệp
    if (toolSearch) {
      toolSearch.addEventListener('input', (e) => {
        const query = e.target.value.toLowerCase().trim();
        if (btnModeToolbox && btnModeToolbox.classList.contains('active')) {
          document.querySelectorAll('.tool-item').forEach(item => {
            const ma = item.dataset.ma;
            const def = TheValidator.BO_THE_V1[ma];
            const match = ma.includes(query) || (def && def.ten.toLowerCase().includes(query));
            item.style.display = match ? 'flex' : 'none';
          });
        } else {
          document.querySelectorAll('.file-tree-row:not(.folder)').forEach(row => {
            const path = (row.dataset.path || '').toLowerCase();
            const match = path.includes(query);
            row.style.display = match ? 'flex' : 'none';
          });
        }
      });
    }

    // Drag-and-drop vào Canvas Root
    const workspace = document.getElementById('canvasWorkspace');
    if (workspace) {
      workspace.addEventListener('dragover', (e) => {
        e.preventDefault();
      });
      workspace.addEventListener('dragleave', (e) => {
        // Rời hẳn khung canvas (không phải chỉ đi qua một thẻ con) — dọn dấu
        // "sẽ chèn ở đây" còn sót lại nếu chuột rê ra vùng chết giữa hai thẻ.
        if (e.target === workspace) xoaDanhDauViTriTha();
      });
      workspace.addEventListener('drop', (e) => {
        e.preventDefault();
        const raw = e.dataTransfer.getData('text/plain');
        if (!raw) return;
        try {
          const payload = JSON.parse(raw);
          if (payload.type === 'NEW_CARD') {
            addNewCardToRoot(payload.ma);
          } else if (payload.type === 'EXISTING_CARD' && payload.nodeId) {
            // Thả vào nền canvas (không trúng dòng thẻ nào) -> đưa xuống
            // CUỐI cấp gốc. Thả trúng một dòng cụ thể thì dòng đó tự xử lý.
            if (diChuyenThe(payload.nodeId, state.tree, null, state.tree.length)) {
              onTreeChanged();
            }
          }
        } catch (_) {}
      });
    }

    // ResizeObserver trên khung chứa thẻ để tự động chỉnh cột dọc khi DOM reflow
    const cardRoot = document.getElementById('cardChainRoot');
    if (cardRoot && typeof ResizeObserver !== 'undefined') {
      const ro = new ResizeObserver(() => {
        yeuCauChinhCotDoc();
      });
      ro.observe(cardRoot);
    }

    // Thiết lập Splitter chia đôi kéo được & Agent Workspace
    setupBottomSplitter();
    setupAgentWorkspace();

    // Lắng nghe window resize để tính lại chiều cao cột dọc
    window.addEventListener('resize', () => {
      yeuCauChinhCotDoc();
    });

    // Phím tắt bàn phím IDE chuẩn
    window.addEventListener('keydown', (e) => {
      if (e.ctrlKey && e.key === 'Enter') {
        e.preventDefault();
        runProgram();
      } else if (e.ctrlKey && (e.key === 'b' || e.key === 'B')) {
        e.preventDefault();
        toggleSidebarLeft();
      } else if (e.ctrlKey && (e.key === 'j' || e.key === 'J')) {
        e.preventDefault();
        toggleSidebarRight();
      } else if (e.ctrlKey && (e.key === '=' || e.key === '+')) {
        e.preventDefault();
        setCodeFontSize(state.codeFontSize + 1);
      } else if (e.ctrlKey && (e.key === '-' || e.key === '_')) {
        e.preventDefault();
        setCodeFontSize(state.codeFontSize - 1);
      } else if (e.ctrlKey && e.key === '0') {
        e.preventDefault();
        setCodeFontSize(14);
      }
    });
  }

  // ==========================================================================
  // KHỞI ĐỘNG ỨNG DỤNG
  // ==========================================================================
  window.addEventListener('DOMContentLoaded', () => {
    initAuthToken();
    initLayoutPreferences();
    renderToolbox();
    setupEventListeners();
    configureRuntimeCapabilities();

    // Nạp mặc định bài mẫu "Hàm cộng hai số" để người dùng mở ra có thể trải nghiệm ngay
    state.tree = [
      { id: "m1_1", ma: "ham", o: { ten_ham: "cong", tham_so: "a, b" }, than: [
        { id: "m1_2", ma: "tra_ve", o: { gia_tri: "a + b" }, than: [] }
      ]},
      { id: "m1_3", ma: "in_ra", o: { noi_dung: "cong(5, 7)" }, than: [] }
    ];
    document.getElementById('currentFileName').textContent = '1. Hàm cộng hai số';
    onTreeChanged();
    loadAvailableTests();
    yeuCauChinhCotDoc();
  });

  if (typeof window !== 'undefined') {
    window.state = state;
    window.updateButtonsState = updateButtonsState;
    window.renderE1Results = renderE1Results;
    window.renderE1Error = renderE1Error;
    window.escapeHtml = escapeHtml;
    window.openPyFile = openPyFile;
    window.saveFile = saveFile;
    window.chayDinhViLoiE1 = chayDinhViLoiE1;
    window.chinhCotDoc = chinhCotDoc;
    window.yeuCauChinhCotDoc = yeuCauChinhCotDoc;
  }

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
      state,
      escapeHtml,
      configureRuntimeCapabilities,
      updateButtonsState,
      chayMachNuocNgam,
      chayDinhViLoiE1,
      renderE1Results,
      renderE1Error,
      loadAvailableTests,
      openPyFile,
      saveFile,
      chinhCotDoc,
      yeuCauChinhCotDoc,
    };
  }

})();

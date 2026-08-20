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
    hasModifications: false,
    diagnostics: { hop_le: true, so_loi_do: 0, so_canh_bao_vang: 0, danh_sach: [], so_lan_dung_the: {} },
    nodeIdCounter: 100
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

  // Gọi fetch kèm header bảo mật X-Auth-Token
  async function authFetch(url, options = {}) {
    const headers = {
      'Content-Type': 'application/json',
      'X-Auth-Token': state.authToken,
      ...(options.headers || {})
    };
    return fetch(url, { ...options, headers });
  }

  // ==========================================================================
  // 2. KHỞI TẠO KHAY THẺ (5 NHÓM MÀU & BỘ ĐẾM ×N)
  // ==========================================================================
  function renderToolbox() {
    const container = document.getElementById('toolboxContainer');
    container.innerHTML = '';

    const groups = [
      { id: 'dieu_khien', title: 'Điều khiển (Xanh dương)', cards: ['neu', 'nguoc_lai', 'lap_moi', 'lap_khi'] },
      { id: 'du_lieu', title: 'Dữ liệu (Xanh lá)', cards: ['gan', 'pheptinh'] },
      { id: 'vao_ra', title: 'Vào / Ra (Tím)', cards: ['in_ra'] },
      { id: 'ham', title: 'Hàm (Cam)', cards: ['ham', 'goi_ham', 'tra_ve'] },
      { id: 'ma_tho', title: 'Mã thô (Xám)', cards: ['ma_tho'] }
    ];

    groups.forEach(g => {
      const groupEl = document.createElement('div');
      groupEl.className = 'tool-group';
      groupEl.id = `group_${g.id}`;

      const titleEl = document.createElement('div');
      titleEl.className = 'group-title';
      titleEl.textContent = g.title;
      titleEl.style.color = TheValidator.NHOM_THE[g.id].mau;
      groupEl.appendChild(titleEl);

      g.cards.forEach(cardMa => {
        const cardDef = TheValidator.BO_THE_V1[cardMa];
        if (!cardDef) return;

        const itemEl = document.createElement('div');
        itemEl.className = 'tool-item';
        itemEl.dataset.ma = cardMa;
        itemEl.style.borderLeftColor = cardDef.mau;
        itemEl.draggable = true;

        const infoEl = document.createElement('div');
        infoEl.className = 'tool-info';

        const nameEl = document.createElement('span');
        nameEl.className = 'tool-name';
        nameEl.textContent = cardDef.ten;
        infoEl.appendChild(nameEl);

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

        groupEl.appendChild(itemEl);
      });

      container.appendChild(groupEl);
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
  // 3. RENDER VÙNG SOẠN THẢO & MẮT XÍCH NỐI ĐỘNG (MỤC 3.3)
  // ==========================================================================
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

  function renderCard(node, parentList, index, depth = 1) {
    const cardDef = TheValidator.BO_THE_V1[node.ma] || { ten: node.ma, mau: '#6B7280', co_than: false, o: [] };
    
    // Tìm lỗi / cảnh báo ứng với nút này
    const nodeDiags = (state.diagnostics.danh_sach || []).filter(d => d.node_id === node.id);
    const hasDo = nodeDiags.some(d => d.muc_do === 'do');
    const hasVang = nodeDiags.some(d => d.muc_do === 'vang');

    const cardEl = document.createElement('div');
    cardEl.className = `card-block ${hasDo ? 'status-do' : (hasVang ? 'status-vang' : '')}`;
    cardEl.id = `node_${node.id}`;
    cardEl.style.borderLeftColor = cardDef.mau;
    cardEl.dataset.nodeId = node.id;

    // Header bar
    const headerEl = document.createElement('div');
    headerEl.className = 'card-header-bar';

    const titleEl = document.createElement('div');
    titleEl.className = 'card-title-tag';
    titleEl.style.color = cardDef.mau;
    titleEl.textContent = cardDef.ten;

    // Icon cảnh báo nhỏ nếu có
    if (hasDo) {
      const doBadge = document.createElement('span');
      doBadge.textContent = '❌ Lỗi';
      doBadge.style.cssText = 'font-size: 10px; background: #EF4444; color: #fff; padding: 1px 5px; border-radius: 4px;';
      titleEl.appendChild(doBadge);
    } else if (hasVang) {
      const vangBadge = document.createElement('span');
      vangBadge.textContent = '⚠️ Cảnh báo';
      vangBadge.style.cssText = 'font-size: 10px; background: #EAB308; color: #000; padding: 1px 5px; border-radius: 4px;';
      titleEl.appendChild(vangBadge);
    }

    headerEl.appendChild(titleEl);

    // Nút điều khiển
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

    headerEl.appendChild(controlsEl);
    cardEl.appendChild(headerEl);

    // Body content (Ô nhập liệu)
    const bodyEl = document.createElement('div');
    bodyEl.className = 'card-body-content';

    if (node.ma === 'ma_tho') {
      const ta = document.createElement('textarea');
      ta.className = 'field-textarea';
      ta.value = (node.o && node.o.nguyen_van) || node.raw_text || '';
      ta.placeholder = '# Nhập mã Python thô tại đây...';
      ta.addEventListener('input', (e) => {
        if (!node.o) node.o = {};
        node.o.nguyen_van = e.target.value;
        node.da_sua = true;
        onTreeChanged(false);
      });
      bodyEl.appendChild(ta);
    } else if (cardDef.o && cardDef.o.length > 0) {
      cardDef.o.forEach(oDef => {
        const fieldWrap = document.createElement('div');
        fieldWrap.className = 'leaf-field';

        const label = document.createElement('span');
        label.className = 'field-label';
        if (oDef.ten === 'ten_bien') label.textContent = 'Biến:';
        else if (oDef.ten === 'gia_tri') label.textContent = '=';
        else if (oDef.ten === 'noi_dung') label.textContent = 'In:';
        else if (oDef.ten === 'dieu_kien') label.textContent = 'Nếu:';
        else if (oDef.ten === 'bien') label.textContent = 'Lặp biến:';
        else if (oDef.ten === 'day') label.textContent = 'trong:';
        else if (oDef.ten === 'ten_ham') label.textContent = 'Hàm:';
        else if (oDef.ten === 'tham_so') label.textContent = 'Tham số:';
        else if (oDef.ten === 'doi_so') label.textContent = 'Đối số:';
        else if (oDef.ten === 'trai') label.textContent = 'Vế trái:';
        else if (oDef.ten === 'phep') label.textContent = 'Toán tử:';
        else if (oDef.ten === 'phai') label.textContent = 'Vế phải:';
        else label.textContent = `${oDef.ten}:`;
        fieldWrap.appendChild(label);

        const input = document.createElement('input');
        input.type = 'text';
        input.className = 'field-input';
        input.value = (node.o && node.o[oDef.ten]) || '';
        input.placeholder = oDef.goi_y || '';
        input.size = Math.max(input.value.length || input.placeholder.length || 6, 6);

        input.addEventListener('input', (e) => {
          if (!node.o) node.o = {};
          node.o[oDef.ten] = e.target.value;
          input.size = Math.max(e.target.value.length || 6, 6);
          node.da_sua = true;
          onTreeChanged(false);
        });

        fieldWrap.appendChild(input);
        bodyEl.appendChild(fieldWrap);
      });
    } else if (node.ma === 'nguoc_lai') {
      const infoSpan = document.createElement('span');
      infoSpan.style.fontSize = '12px';
      infoSpan.style.color = 'var(--text-muted)';
      infoSpan.textContent = 'Khối thực thi khi điều kiện Nếu sai:';
      bodyEl.appendChild(infoSpan);
    }

    cardEl.appendChild(bodyEl);

    // Thân con lồng nhau (Nested slot)
    if (cardDef.co_than) {
      const slotEl = document.createElement('div');
      slotEl.className = 'nested-body-slot';
      slotEl.dataset.slotId = node.id;

      if (node.than && node.than.length > 0) {
        renderCardList(node.than, slotEl, depth + 1);
      } else {
        const ph = document.createElement('div');
        ph.className = 'slot-placeholder';
        ph.textContent = '+ Thả thẻ vào thân này...';
        slotEl.appendChild(ph);
      }

      // Hỗ trợ thả thẻ vào slot con
      slotEl.addEventListener('dragover', (e) => {
        e.preventDefault();
        e.stopPropagation();
        slotEl.style.borderColor = 'var(--color-chain-active)';
      });
      slotEl.addEventListener('dragleave', (e) => {
        e.preventDefault();
        slotEl.style.borderColor = 'var(--border-color)';
      });
      slotEl.addEventListener('drop', (e) => {
        e.preventDefault();
        e.stopPropagation();
        slotEl.style.borderColor = 'var(--border-color)';
        const raw = e.dataTransfer.getData('text/plain');
        if (!raw) return;
        try {
          const payload = JSON.parse(raw);
          if (payload.type === 'NEW_CARD') {
            const newNode = taoTheNode(payload.ma);
            if (!node.than) node.than = [];
            node.than.push(newNode);
            onTreeChanged();
          }
        } catch (err) {}
      });

      cardEl.appendChild(slotEl);
    }

    return cardEl;
  }

  function renderCardList(nodeList, parentContainer, depth = 1) {
    for (let i = 0; i < nodeList.length; i++) {
      const node = nodeList[i];
      const cardEl = renderCard(node, nodeList, i, depth);

      // Nếu không phải thẻ đầu tiên -> Kiểm tra điều kiện hiện XÍCH NỐI (Mục 3.3)
      if (i > 0) {
        const prevNode = nodeList[i - 1];
        const prevHasDo = (state.diagnostics.danh_sach || []).some(d => d.node_id === prevNode.id && d.muc_do === 'do');
        const currHasDo = (state.diagnostics.danh_sach || []).some(d => d.node_id === node.id && d.muc_do === 'do');

        // Hai thẻ liền nhau, cả hai đều không đỏ -> Hiện mắt xích ở giữa
        if (!prevHasDo && !currHasDo) {
          const chainEl = document.createElement('div');
          chainEl.className = 'chain-link-wrapper';
          chainEl.innerHTML = `
            <div class="chain-icon-badge">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path>
                <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path>
              </svg>
              <span>Nối</span>
            </div>
          `;
          parentContainer.appendChild(chainEl);
        }
      }

      parentContainer.appendChild(cardEl);
    }
  }

  function renderCanvas() {
    const rootContainer = document.getElementById('cardChainRoot');
    const emptyGuide = document.getElementById('emptyCanvasGuide');
    rootContainer.innerHTML = '';

    if (state.tree.length === 0) {
      emptyGuide.style.display = 'flex';
    } else {
      emptyGuide.style.display = 'none';
      renderCardList(state.tree, rootContainer, 1);
    }
  }

  // ==========================================================================
  // 4. KIỂM TRA TĨNH & CẬP NHẬT GIAO DIỆN (ĐỎ / VÀNG / ×N / CODE PREVIEW)
  // ==========================================================================
  let syncTimeout = null;

  function onTreeChanged(pushHistory = true) {
    state.hasModifications = true;
    document.getElementById('fileModifiedBadge').style.display = state.activeFilePath ? 'inline-block' : 'none';

    // 1. Chạy Client-side validator tức thì (0ms latency)
    state.diagnostics = TheValidator.kiemTraCayThe(state.tree);

    // 2. Cập nhật giao diện
    renderCanvas();
    updateToolboxCounters();
    updateCodePreview();
    updateDiagnosticsPanel();
    updateStatusBar();

    // 3. Đồng bộ với Backend API /api/kiem (Python làm trọng tài)
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
      }
    } catch (err) {
      console.warn('Không thể kết nối /api/kiem:', err);
    }
  }

  function updateCodePreview() {
    const code = TheValidator.sinhMaPython(state.tree);
    const codeEl = document.getElementById('pythonCodeOutput');
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
  // 5. THỰC THI SANDBOX CHẠY THỬ (CHẠY TRONG TIẾN TRÌNH RIÊNG 5S)
  // ==========================================================================
  async function runProgram() {
    const btnRun = document.getElementById('btnRun');
    const runText = document.getElementById('runBtnText');
    const termBody = document.getElementById('terminalBody');
    const metaStatus = document.getElementById('metaStatus');
    const metaTime = document.getElementById('metaTime');

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
      btnRun.disabled = false;
    }
  }

  function escapeHtml(text) {
    const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
    return String(text).replace(/[&<>"']/g, m => map[m]);
  }

  // ==========================================================================
  // 6. MẪU BÀI, MỞ TỆP & LƯU TỆP (CỬA CỨNG MỞ-LƯU LOSSLESS)
  // ==========================================================================
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
        const data = await resp.json();
        state.tree = data.tree || [];
        state.activeFilePath = data.duong_dan;
        state.hasModifications = false;
        document.getElementById('currentFileName').textContent = data.ten_tep;
        document.getElementById('fileModifiedBadge').style.display = 'none';
        document.getElementById('openFileModal').style.display = 'none';
        onTreeChanged();
      } else {
        const err = await resp.json();
        alert(`Lỗi mở tệp: ${err.error}`);
      }
    } catch (err) {
      alert(`Lỗi kết nối khi mở tệp: ${err.message}`);
    }
  }

  async function saveFile(filePath, saveType) {
    if (!filePath || !filePath.trim()) return;
    try {
      const resp = await authFetch('/api/luu_tep', {
        method: 'POST',
        body: JSON.stringify({
          duong_dan: filePath.trim(),
          tree: state.tree,
          kieu_luu: saveType,
          has_modifications: state.hasModifications
        })
      });
      if (resp.ok) {
        const data = await resp.json();
        state.activeFilePath = filePath.trim();
        state.hasModifications = false;
        document.getElementById('currentFileName').textContent = filePath.split('/').pop().split('\\').pop();
        document.getElementById('fileModifiedBadge').style.display = 'none';
        document.getElementById('saveFileModal').style.display = 'none';
        alert('Lưu tệp thành công!');
      } else {
        const err = await resp.json();
        alert(`Lỗi lưu tệp: ${err.error}`);
      }
    } catch (err) {
      alert(`Lỗi kết nối khi lưu tệp: ${err.message}`);
    }
  }

  // ==========================================================================
  // 7. SỰ KIỆN & LẮNG NGHE NGƯỜI DÙNG
  // ==========================================================================
  function setupEventListeners() {
    // Toolbar buttons
    document.getElementById('btnRun').addEventListener('click', runProgram);
    
    document.getElementById('btnNew').addEventListener('click', () => {
      if (confirm('Tạo chương trình mới? Thao tác này sẽ dọn sạch vùng soạn thảo.')) {
        state.tree = [];
        state.activeFilePath = '';
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
      document.getElementById('currentFileName').textContent = '1. Hàm cộng hai số';
      onTreeChanged();
    });

    // Mở tệp Modal
    document.getElementById('btnOpenFile').addEventListener('click', () => {
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

    document.querySelectorAll('#repoFileChips .chip').forEach(chip => {
      chip.addEventListener('click', () => {
        const p = chip.dataset.path;
        document.getElementById('openFilePath').value = p;
        openPyFile(p);
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

    // Copy Code Button
    document.getElementById('btnCopyCode').addEventListener('click', () => {
      const code = document.getElementById('pythonCodeOutput').textContent;
      navigator.clipboard.writeText(code).then(() => {
        const btn = document.getElementById('btnCopyCode');
        btn.textContent = 'Đã chép!';
        setTimeout(() => btn.textContent = 'Sao chép', 1500);
      });
    });

    // Right Tabs Switch
    document.querySelectorAll('.tab-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
        btn.classList.add('active');
        const targetTab = document.getElementById(btn.dataset.tab);
        if (targetTab) targetTab.classList.add('active');
      });
    });

    // Tìm kiếm thẻ trên khay
    document.getElementById('toolSearch').addEventListener('input', (e) => {
      const query = e.target.value.toLowerCase().trim();
      document.querySelectorAll('.tool-item').forEach(item => {
        const ma = item.dataset.ma;
        const def = TheValidator.BO_THE_V1[ma];
        const match = ma.includes(query) || (def && def.ten.toLowerCase().includes(query));
        item.style.display = match ? 'flex' : 'none';
      });
    });

    // Drag-and-drop vào Canvas Root
    const workspace = document.getElementById('canvasWorkspace');
    workspace.addEventListener('dragover', (e) => {
      e.preventDefault();
    });
    workspace.addEventListener('drop', (e) => {
      e.preventDefault();
      const raw = e.dataTransfer.getData('text/plain');
      if (!raw) return;
      try {
        const payload = JSON.parse(raw);
        if (payload.type === 'NEW_CARD') {
          addNewCardToRoot(payload.ma);
        }
      } catch (err) {}
    });

    // Phím tắt bàn phím
    window.addEventListener('keydown', (e) => {
      if (e.ctrlKey && e.key === 'Enter') {
        e.preventDefault();
        runProgram();
      }
    });
  }

  // ==========================================================================
  // KHỞI ĐỘNG ỨNG DỤNG
  // ==========================================================================
  window.addEventListener('DOMContentLoaded', () => {
    initAuthToken();
    renderToolbox();
    setupEventListeners();

    // Nạp mặc định bài mẫu "Hàm cộng hai số" để người dùng mở ra có thể trải nghiệm ngay
    state.tree = [
      { id: "m1_1", ma: "ham", o: { ten_ham: "cong", tham_so: "a, b" }, than: [
        { id: "m1_2", ma: "tra_ve", o: { gia_tri: "a + b" }, than: [] }
      ]},
      { id: "m1_3", ma: "in_ra", o: { noi_dung: "cong(5, 7)" }, than: [] }
    ];
    document.getElementById('currentFileName').textContent = '1. Hàm cộng hai số';
    onTreeChanged();
  });

})();

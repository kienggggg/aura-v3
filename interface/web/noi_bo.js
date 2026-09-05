// noi_bo.js — Frontend Engine cho AURA Command Center v3.0

(function () {
  'use strict';

  const state = {
    activeView: 'viewWarRoom',
    activeAgentId: 'aura',
    rooms: [],
    vitals: {},
    chatHistories: {}, // Keyed by agentId
    polyglotSourceLang: 'python',
    polyglotTargetLang: 'javascript',
    languages: []
  };

  // ==========================================================================
  // 1. KHỞI TẠO & NẠP DỮ LIỆU BAN ĐẦU
  // ==========================================================================
  async function initCommandCenter() {
    setupNavigation();
    await capNhatTrangThaiHeThong();
    veSidebarAgents();
    veWarRoomGrid();
    chonAgent('aura');
    taiLedgerVaEvidence();
    await initPolyglotStudio();

    // Tự động làm mới Vitals mỗi 4 giây
    setInterval(capNhatTrangThaiHeThong, 4000);
  }

  // ==========================================================================
  // 2. ĐIỀU HƯỚNG VIEW (WAR ROOM / CONSOLE / POLYGLOT / PIPELINE / LEDGER)
  // ==========================================================================
  function setupNavigation() {
    document.querySelectorAll('.nav-tab').forEach(tab => {
      tab.addEventListener('click', () => {
        const viewId = tab.dataset.view;
        chuyenView(viewId);
      });
    });

    document.getElementById('btnQuickLaunchPipeline')?.addEventListener('click', () => {
      chuyenView('viewPipeline');
    });

    document.getElementById('btnSendTask')?.addEventListener('click', guiNhiemVuAgent);
    document.getElementById('consoleInput')?.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        guiNhiemVuAgent();
      }
    });

    document.getElementById('btnTriggerPipeline')?.addEventListener('click', kichHoatPipeline);
    document.getElementById('btnReloadLedgerFull')?.addEventListener('click', taiLedgerVaEvidence);
    document.getElementById('btnRefreshLedgerPreview')?.addEventListener('click', taiLedgerVaEvidence);

    // Xử lý 8 Thẻ Quy Trình 1-Click
    const presetPrompts = {
      card_video_shorts: 'Sản xuất video ngắn 60s về Lập trình Thẻ AURA v3 và Xuất bản tự động',
      card_code_doctor: 'Khám bệnh mã nguồn Python, định vị lỗi AST và sinh bản vá tự động',
      card_polyglot_transpiler: 'Chuyển đổi logic Python AST sang JavaScript/Go/Rust/C++ và kiểm tra cú pháp',
      card_deep_scout: 'Tra cứu đa nguồn Internet về xu hướng AI 2026 và kiểm chứng sự thật',
      card_novel_writer: 'Sáng tác chương truyện đời thường Quán Cà Phê Cuối Ngõ và chấm điểm TTR',
      card_fullstack_builder: 'Tạo giao diện web tương tác HTML5/JS và API backend aiohttp',
      card_security_guard: 'Kiểm toán bảo mật AST, quét rò rỉ secret key và kiểm tra đường dẫn an toàn',
      card_system_audit: 'Kiểm toán toàn diện sinh tồn hệ thống, RAM/CPU và quét 714 test cases'
    };

    document.querySelectorAll('.preset-card, .btn-preset-run').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const presetId = btn.dataset.preset || btn.closest('.preset-card')?.dataset.preset;
        if (presetId && presetPrompts[presetId]) {
          const input = document.getElementById('pipelineTopicInput');
          if (input) input.value = presetPrompts[presetId];
          chuyenView('viewPipeline');
          kichHoatPipeline(presetId);
        }
      });
    });
  }

  function chuyenView(viewId) {
    state.activeView = viewId;
    document.querySelectorAll('.nav-tab').forEach(tab => {
      tab.classList.toggle('active', tab.dataset.view === viewId);
    });
    document.querySelectorAll('.view-pane').forEach(pane => {
      pane.classList.toggle('active', pane.id === viewId);
    });
  }

  // ==========================================================================
  // 3. NẠP DỮ LIỆU TỪ SERVER (/api/status, /api/ledger, /api/evidence)
  // ==========================================================================
  async function capNhatTrangThaiHeThong() {
    try {
      const resp = await fetch('/api/status');
      const data = await resp.json();
      if (data.status === 'PASS') {
        state.vitals = data.vitals;
        state.rooms = data.rooms;

        // Cập nhật Vitals Bar
        const vRam = document.getElementById('vitalRam');
        const vCpu = document.getElementById('vitalCpu');
        const vTasks = document.getElementById('vitalTasks');

        if (vRam) vRam.textContent = `${data.vitals.ram_used_gb || 0} / ${data.vitals.ram_total_gb || 16} GB`;
        if (vCpu) vCpu.textContent = `${data.vitals.cpu_percent || 0}%`;
        if (vTasks) vTasks.textContent = `${data.vitals.tasks_count || 0} việc`;
      }
    } catch (_) {}
  }

  // ==========================================================================
  // 4. HIỂN THỊ SIDEBAR VÀ WAR ROOM GRID
  // ==========================================================================
  function veSidebarAgents() {
    const list = document.getElementById('agentsSidebarList');
    if (!list) return;

    list.innerHTML = state.rooms.map(r => `
      <div class="agent-nav-item ${r.id === state.activeAgentId ? 'active' : ''}" data-id="${r.id}">
        <div class="agent-icon-box" style="background: ${r.mau_sac}20; color: ${r.mau_sac};">
          ${r.bieu_tuong}
        </div>
        <div class="agent-meta">
          <div class="agent-name-row">
            <span class="agent-name">${r.code_name}</span>
            <span class="agent-status-dot"></span>
          </div>
          <div class="agent-role">${r.vai_tro}</div>
        </div>
      </div>
    `).join('');

    list.querySelectorAll('.agent-nav-item').forEach(item => {
      item.addEventListener('click', () => {
        const id = item.dataset.id;
        chonAgent(id);
        chuyenView('viewConsole');
      });
    });
  }

  function veWarRoomGrid() {
    const grid = document.getElementById('warRoomGrid');
    if (!grid) return;

    grid.innerHTML = state.rooms.map(r => `
      <div class="room-card" style="border-top: 3px solid ${r.mau_sac};">
        <div class="room-card-header">
          <div class="room-badge-group">
            <span class="room-icon">${r.bieu_tuong}</span>
            <span class="room-name">${r.code_name}</span>
          </div>
          <span class="room-status-badge">${r.trang_thai}</span>
        </div>
        <div class="room-desc">${r.moTa || r.mo_ta}</div>
        <div class="room-tools-chips">
          ${(r.cong_cu || []).map(c => `<span class="tool-chip">${c}</span>`).join('')}
        </div>
        <div class="room-card-footer">
          <span style="font-size: 11px; color: #64748B;">${r.ten}</span>
          <button class="btn-room-action" data-id="${r.id}">Giao Việc ➔</button>
        </div>
      </div>
    `).join('');

    grid.querySelectorAll('.btn-room-action').forEach(btn => {
      btn.addEventListener('click', () => {
        const id = btn.dataset.id;
        chonAgent(id);
        chuyenView('viewConsole');
      });
    });
  }

  // ==========================================================================
  // 5. CHỌN VÀ TƯƠNG TÁC BÀN LÀM VIỆC AGENT CONSOLE
  // ==========================================================================
  function chonAgent(agentId) {
    state.activeAgentId = agentId;
    const room = state.rooms.find(r => r.id === agentId);
    if (!room) return;

    // Cập nhật sidebar active
    document.querySelectorAll('.agent-nav-item').forEach(el => {
      el.classList.toggle('active', el.dataset.id === agentId);
    });

    // Cập nhật Header Console
    const header = document.getElementById('consoleAgentHeader');
    if (header) {
      header.innerHTML = `
        <div style="display: flex; align-items: center; gap: 12px;">
          <div style="font-size: 28px; width: 44px; height: 44px; border-radius: 10px; background: ${room.mau_sac}25; display: flex; align-items: center; justify-content: center;">
            ${room.bieu_tuong}
          </div>
          <div>
            <h3 style="font-size: 16px; font-weight: 800; color: #FFF;">${room.code_name} — ${room.ten}</h3>
            <span style="font-size: 12px; color: ${room.mau_sac}; font-weight: 600;">${room.vai_tro}</span>
          </div>
        </div>
        <span class="room-status-badge">${room.trang_thai}</span>
      `;
    }

    // Cập nhật Quick Prompts
    const quickBar = document.getElementById('quickPromptsBar');
    if (quickBar) {
      quickBar.innerHTML = (room.cong_cu || []).map(c => `
        <button class="quick-prompt-chip" data-text="${c}">${c}</button>
      `).join('');

      quickBar.querySelectorAll('.quick-prompt-chip').forEach(chip => {
        chip.addEventListener('click', () => {
          const txt = chip.dataset.text;
          const input = document.getElementById('consoleInput');
          if (input) {
            input.value = `Thực hiện tác vụ: ${txt}`;
            input.focus();
          }
        });
      });
    }

    // Hiển thị lịch sử chat của phòng
    hienThiLichSuChat(agentId);
  }

  function hienThiLichSuChat(agentId) {
    const container = document.getElementById('chatLogsContainer');
    if (!container) return;

    const history = state.chatHistories[agentId] || [];
    if (history.length === 0) {
      const room = state.rooms.find(r => r.id === agentId);
      container.innerHTML = `
        <div style="text-align: center; color: #64748B; margin: auto; padding: 40px;">
          <div style="font-size: 36px; margin-bottom: 8px;">${room?.bieu_tuong || '⚡'}</div>
          <h4 style="color: #FFF; font-size: 15px; margin-bottom: 4px;">Bàn Làm Việc Đặc Nhiệm ${room?.code_name || ''}</h4>
          <p style="font-size: 12px;">Nhập câu hỏi hoặc chọn tác vụ nhanh bên dưới để bắt đầu giao việc.</p>
        </div>
      `;
      return;
    }

    container.innerHTML = history.map(msg => `
      <div class="chat-bubble ${msg.role}">
        <div style="font-size: 11px; font-weight: 700; margin-bottom: 4px; opacity: 0.8;">
          ${msg.role === 'user' ? '👤 ĐIỀU HÀNH VIÊN' : `${state.rooms.find(r => r.id === agentId)?.code_name || 'AGENT'}`}
        </div>
        <div style="white-space: pre-wrap;">${escapeHtml(msg.text)}</div>
      </div>
    `).join('');

    container.scrollTop = container.scrollHeight;
  }

  async function guiNhiemVuAgent() {
    const input = document.getElementById('consoleInput');
    if (!input || !input.value.trim()) return;

    const promptText = input.value.trim();
    input.value = '';

    const agentId = state.activeAgentId;
    if (!state.chatHistories[agentId]) state.chatHistories[agentId] = [];
    state.chatHistories[agentId].push({ role: 'user', text: promptText });
    hienThiLichSuChat(agentId);

    const btn = document.getElementById('btnSendTask');
    if (btn) btn.disabled = true;

    try {
      const resp = await fetch('/api/dispatch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phong_id: agentId, prompt: promptText })
      });
      const data = await resp.json();

      if (data.status === 'PASS') {
        state.chatHistories[agentId].push({
          role: 'agent',
          text: data.tra_loi
        });
      } else {
        state.chatHistories[agentId].push({
          role: 'agent',
          text: `🛑 Lỗi thực thi: ${data.error || 'Không xác định'}`
        });
      }
    } catch (err) {
      state.chatHistories[agentId].push({
        role: 'agent',
        text: `🛑 Lỗi kết nối mạng: ${err.message}`
      });
    } finally {
      if (btn) btn.disabled = false;
      hienThiLichSuChat(agentId);
      taiLedgerVaEvidence();
    }
  }

  // ==========================================================================
  // 6. PIPELINE AUTOMATOR (Quy trình liên phòng ban)
  // ==========================================================================
  // Ánh xạ mã phòng -> id ô trên màn hình. Bước nào không có ô thì bỏ qua,
  // không nổ: chuỗi tùy biến có thể gọi phòng không nằm trong sơ đồ cố định.
  const O_BUOC = {
    zeta: 'step_zeta', aura: 'step_aura', alpha: 'step_alpha',
    omega: 'step_omega', gamma: 'step_gamma'
  };
  const NHAN = {
    DANG_CHAY: ['running', 'ĐANG CHẠY'],
    PASS: ['done', 'HOÀN TẤT ✓'],
    FAIL: ['fail', 'HỎNG ✕'],
    KHONG_CHAY_DUOC: ['fail', 'KHÔNG CHẠY ĐƯỢC'],
    CHUA_CHAY: ['', 'CHƯA CHẠY'],
    DAT: ['done', 'HOÀN TẤT ✓'],
    KHONG_DAT: ['fail', 'KHÔNG ĐẠT']
  };

  function veMotBuoc(phongId, trangThai, giay) {
    const el = document.getElementById(O_BUOC[phongId]);
    if (!el) return;
    const n = NHAN[trangThai] || ['', trangThai];
    el.className = 'flow-step ' + n[0];
    const s = el.querySelector('.step-status');
    if (s) {
      s.textContent = (trangThai === 'DANG_CHAY' && giay != null)
        ? `${n[1]} · ${giay.toFixed(1)}s` : n[1];
    }
  }

  async function kichHoatPipeline(presetId) {
    // `presetId` TỪNG BỊ VỨT. Dòng gọi ở thẻ kịch bản truyền nó vào, nhưng hàm
    // không khai tham số nên nó rơi mất — và máy chủ không bao giờ nhận được.
    // Từ 05/09/2026 `preset_id` quyết định thể loại lời nhắc, nên không gửi thì
    // khâu ấy chưa từng chạy được từ màn hình.
    const input = document.getElementById('pipelineTopicInput');
    const chuDe = (input && input.value.trim()) || 'Chiến dịch sản xuất & phân phối nội dung tự động AURA v3';

    // Client tự đặt id để POLL được NGAY. Máy chủ kiểm lại bằng đúng luật của
    // nó; id xấu thì máy tự sinh và ta sẽ không poll thấy gì — đó là hành vi
    // đúng, không phải lỗi im lặng.
    const pipelineId = 'pipe_ui_' + Date.now() + '_' +
      Math.random().toString(36).slice(2, 8);

    Object.values(O_BUOC).forEach(id => {
      const el = document.getElementById(id);
      if (el) {
        el.className = 'flow-step';
        const s = el.querySelector('.step-status');
        if (s) s.textContent = 'ĐANG ĐỢI';
      }
    });

    const resultBox = document.getElementById('pipelineResultsBox');
    const logBox = document.getElementById('pipelineStepsLog');
    if (resultBox) resultBox.style.display = 'none';

    // KHÔNG `await` — chuỗi chạy 166 giây, phải poll SONG SONG với nó.
    // Bản trước chạy một hoạt ảnh `setTimeout` 450ms/bước TRƯỚC khi gọi, nên
    // cả 5 bước báo "HOÀN TẤT ✓" sau 2,25 giây — trước lúc dây chuyền bắt đầu.
    const chay = fetch('/api/pipeline/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        chu_de: chuDe, pipeline_id: pipelineId,
        ...(presetId ? { preset_id: presetId } : {})
      })
    }).then(r => r.json());

    let xong = false;
    const poll = setInterval(async () => {
      try {
        const r = await fetch('/api/tien_do/' + encodeURIComponent(pipelineId));
        const td = await r.json();
        (td.cac_dong || []).forEach(d => {
          if (d.phong_id) veMotBuoc(d.phong_id, d.trang_thai, null);
        });
        const dang = td.buoc_dang_chay;
        if (dang) veMotBuoc(dang.phong_id, 'DANG_CHAY', td.giay_da_troi);
        if (td.trang_thai === 'XONG') { xong = true; clearInterval(poll); }
      } catch (_) { /* một nhịp poll hụt không được làm dừng cả vòng */ }
    }, 1000);

    let data;
    try {
      data = await chay;
    } catch (err) {
      clearInterval(poll);
      if (resultBox && logBox) {
        resultBox.style.display = 'block';
        logBox.innerHTML = `<div style="padding:8px 12px;background:rgba(239,68,68,0.08);border-radius:6px;color:#F87171;font-size:12px;">
          🛑 Không gọi được dây chuyền: ${escapeHtml(err.message || String(err))}</div>`;
      }
      return;
    }
    clearInterval(poll);

    // VẼ MỌI TRẠNG THÁI, không chỉ PASS. Bản trước chỉ hiện khi `status ===
    // 'PASS'`, nên một lượt FAIL trông y hệt một lượt chưa bấm.
    (data.cac_buoc || []).forEach(b => veMotBuoc(b.phong_id, b.trang_thai, null));
    if (resultBox && logBox) {
      resultBox.style.display = 'block';
      const mau = { PASS: '#34D399', FAIL: '#F87171',
                    KHONG_CHAY_DUOC: '#FBBF24', CHUA_CHAY: '#64748B' };
      logBox.innerHTML =
        `<div style="padding:6px 12px;margin-bottom:8px;font-size:12px;font-weight:700;color:${mau[data.status] || '#94A3B8'};">
           ${escapeHtml(data.status || '?')} · ${data.buoc_dat}/${data.tong_buoc} bước đạt · ${Math.round((data.tong_thoi_gian_ms || 0) / 1000)}s
         </div>` +
        (data.cac_buoc || []).map(b => `
          <div style="padding: 8px 12px; background: rgba(255,255,255,0.03); border-radius: 6px; margin-bottom: 6px; font-size: 12px;">
            <strong style="color: #60A5FA;">[Bước ${b.buoc}] ${escapeHtml(b.phong_ten || '')}:</strong> ${escapeHtml(b.hanh_dong || '')}
            <div style="color: ${mau[b.trang_thai] || '#94A3B8'}; margin-top: 2px;">➔ ${escapeHtml(b.trang_thai || '')} — ${escapeHtml(b.ket_qua || '')}</div>
          </div>
        `).join('');
    }
  }

  // ==========================================================================
  // 7. SỔ CÁI & BẰNG CHỨNG THẬT TRÊN ĐĨA
  // ==========================================================================
  async function taiLedgerVaEvidence() {
    // 1. Sổ cái
    try {
      const respL = await fetch('/api/ledger');
      const dataL = await respL.json();
      if (dataL.status === 'PASS') {
        const tbodyFull = document.getElementById('tbodyLedgerFull');
        const previewList = document.getElementById('ledgerPreviewList');

        if (tbodyFull) {
          tbodyFull.innerHTML = (dataL.entries || []).map(e => `
            <tr>
              <td><code>${e.task_id}</code></td>
              <td><span class="tool-chip" style="font-weight: 700;">${(e.phong_id || '').toUpperCase()}</span></td>
              <td>${escapeHtml(e.yeu_cau || '')}</td>
              <td style="color: #64748B;">${(e.timestamp || '').replace('T', ' ').slice(0, 19)}</td>
              <td>${e.latency_ms || 0} ms</td>
              <td><span class="card-badge pass">PASS</span></td>
            </tr>
          `).join('');
        }

        if (previewList) {
          previewList.innerHTML = (dataL.entries || []).slice(0, 4).map(e => `
            <div class="ledger-row">
              <span style="font-weight: 700; color: #60A5FA;">[${(e.phong_id || '').toUpperCase()}]</span>
              <span style="flex: 1; margin: 0 8px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${escapeHtml(e.yeu_cau || '')}</span>
              <span style="color: #34D399; font-weight: 700;">PASS</span>
            </div>
          `).join('');
        }
      }
    } catch (_) {}

    // 2. Evidence Runs
    try {
      const respE = await fetch('/api/evidence');
      const dataE = await respE.json();
      if (dataE.status === 'PASS') {
        const tbodyEv = document.getElementById('tbodyEvidenceRuns');
        if (tbodyEv) {
          tbodyEv.innerHTML = (dataE.runs || []).map(r => `
            <tr>
              <td><code>${r.run_id}</code></td>
              <td>${r.has_manifest ? '✓ Có manifest.json' : '✕'}</td>
              <td>${r.has_metrics ? '✓ Có metrics.json' : '✕'}</td>
              <td><span class="card-badge pass">${r.status || 'PASS'}</span></td>
            </tr>
          `).join('');
        }
      }
    } catch (_) {}
  }

  // ==========================================================================
  // 8. STUDIO ĐA NGÔN NGỮ (POLYGLOT STUDIO)
  // ==========================================================================
  async function initPolyglotStudio() {
    try {
      const resp = await fetch('/api/polyglot/languages');
      const data = await resp.json();
      if (data.status === 'PASS') {
        state.languages = data.languages || [];
      }
    } catch (_) {}

    // Gắn sự kiện chọn ngôn ngữ nguồn
    document.querySelectorAll('#polyglotSourcePills .lang-pill').forEach(btn => {
      btn.addEventListener('click', () => {
        state.polyglotSourceLang = btn.dataset.lang;
        document.querySelectorAll('#polyglotSourcePills .lang-pill').forEach(b => {
          b.classList.toggle('active', b.dataset.lang === state.polyglotSourceLang);
        });
        capNhatPolyglotUI();
        taiMauChuanPolyglot();
      });
    });

    // Gắn sự kiện chọn ngôn ngữ đích
    document.querySelectorAll('#polyglotTargetPills .lang-pill').forEach(btn => {
      btn.addEventListener('click', () => {
        state.polyglotTargetLang = btn.dataset.lang;
        document.querySelectorAll('#polyglotTargetPills .lang-pill').forEach(b => {
          b.classList.toggle('active', b.dataset.lang === state.polyglotTargetLang);
        });
        capNhatPolyglotUI();
      });
    });

    // Gắn sự kiện các nút hành động
    document.getElementById('btnPolyglotTemplate')?.addEventListener('click', taiMauChuanPolyglot);
    document.getElementById('btnPolyglotTranslate')?.addEventListener('click', dichMaPolyglot);
    document.getElementById('btnPolyglotValidate')?.addEventListener('click', kiemTraCuPhapPolyglot);
    document.getElementById('btnPolyglotRun')?.addEventListener('click', chaySandboxPolyglot);

    document.getElementById('btnCopySource')?.addEventListener('click', () => saoChepCode('polyglotSourceEditor', 'btnCopySource'));
    document.getElementById('btnCopyTarget')?.addEventListener('click', () => saoChepCode('polyglotTargetEditor', 'btnCopyTarget'));

    capNhatPolyglotUI();
    taiMauChuanPolyglot();
  }

  function capNhatPolyglotUI() {
    const srcInfo = state.languages.find(l => l.id === state.polyglotSourceLang);
    const tgtInfo = state.languages.find(l => l.id === state.polyglotTargetLang);

    const srcBadge = document.getElementById('sourceLangBadge');
    const tgtBadge = document.getElementById('targetLangBadge');

    if (srcBadge && srcInfo) {
      srcBadge.textContent = `${srcInfo.bieu_tuong} ${srcInfo.ten}`;
      srcBadge.style.color = srcInfo.mau_sac;
      srcBadge.style.background = `${srcInfo.mau_sac}20`;
      srcBadge.style.borderColor = `${srcInfo.mau_sac}40`;
    }
    if (tgtBadge && tgtInfo) {
      tgtBadge.textContent = `${tgtInfo.bieu_tuong} ${tgtInfo.ten}`;
      tgtBadge.style.color = tgtInfo.mau_sac;
      tgtBadge.style.background = `${tgtInfo.mau_sac}20`;
      tgtBadge.style.borderColor = `${tgtInfo.mau_sac}40`;
    }
  }

  function taiMauChuanPolyglot() {
    const srcInfo = state.languages.find(l => l.id === state.polyglotSourceLang);
    const srcEditor = document.getElementById('polyglotSourceEditor');
    if (srcEditor && srcInfo && srcInfo.ma_mau) {
      srcEditor.value = srcInfo.ma_mau;
      inConsolePolyglot(`Đã nạp mã mẫu chuẩn cho ${srcInfo.ten} (${srcInfo.duoi_tep})`, 'SẴN SÀNG', 'info');
    }
  }

  async function dichMaPolyglot() {
    const srcEditor = document.getElementById('polyglotSourceEditor');
    const tgtEditor = document.getElementById('polyglotTargetEditor');
    const ma = srcEditor ? srcEditor.value.trim() : '';

    if (!ma) {
      inConsolePolyglot('Vui lòng nhập mã nguồn trước khi chuyển đổi!', 'LỖI', 'error');
      return;
    }

    inConsolePolyglot(`Đang phân tích AST và dịch từ ${state.polyglotSourceLang.toUpperCase()} sang ${state.polyglotTargetLang.toUpperCase()}...`, 'ĐANG XỬ LÝ...', 'info');

    try {
      const resp = await fetch('/api/polyglot/translate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ma: ma,
          lang_nguon: state.polyglotSourceLang,
          lang_dich: state.polyglotTargetLang
        })
      });
      const data = await resp.json();

      if (data.status === 'PASS') {
        if (tgtEditor) tgtEditor.value = data.ma_dich || '';
        const notes = (data.notes || []).join('; ');
        inConsolePolyglot(
          `✓ Chuyển đổi thành công!\n` +
          `• Ngôn ngữ: ${data.source_lang} ➔ ${data.target_lang}\n` +
          `• Số nodes AST đã chuyển: ${data.nodes_translated || 0}\n` +
          (notes ? `• Ghi chú: ${notes}\n` : '') +
          `• Trạng thái: Mã đích đạt chuẩn cấu trúc.`,
          'HOÀN TẤT ✓',
          'success'
        );
      } else {
        inConsolePolyglot(`✕ Lỗi chuyển đổi mã:\n${data.error || 'Không xác định'}`, 'LỖI BIÊN DỊCH', 'error');
      }
    } catch (err) {
      inConsolePolyglot(`✕ Lỗi kết nối máy chủ: ${err.message}`, 'LỖI MẠNG', 'error');
    }
  }

  async function kiemTraCuPhapPolyglot() {
    const srcEditor = document.getElementById('polyglotSourceEditor');
    const ma = srcEditor ? srcEditor.value.trim() : '';

    if (!ma) {
      inConsolePolyglot('Mã nguồn rỗng, không có gì để kiểm tra.', 'LỖI', 'error');
      return;
    }

    inConsolePolyglot(`Đang kiểm định cú pháp ${state.polyglotSourceLang.toUpperCase()}...`, 'ĐANG QUÉT...', 'info');

    try {
      const resp = await fetch('/api/polyglot/validate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ma: ma,
          lang: state.polyglotSourceLang
        })
      });
      const data = await resp.json();

      if (data.valid) {
        inConsolePolyglot(
          `✅ CÚ PHÁP CHUẨN XÁC (Syntax Valid)\n` +
          `• Ngôn ngữ: ${data.language || state.polyglotSourceLang}\n` +
          `• Đánh giá: ${data.message || 'Mã hợp lệ không có lỗi cú pháp.'}`,
          'PASS 100%',
          'success'
        );
      } else {
        const details = (data.details || []).join('\n');
        inConsolePolyglot(
          `❌ PHÁT HIỆN LỖI CÚ PHÁP (Syntax Error)\n` +
          `• Chi tiết lỗi: ${data.error || 'Lỗi cú pháp'}\n` +
          (details ? `• Vị trí:\n${details}` : ''),
          'SYNTAX ERROR',
          'error'
        );
      }
    } catch (err) {
      inConsolePolyglot(`✕ Lỗi kiểm tra cú pháp: ${err.message}`, 'LỖI', 'error');
    }
  }

  async function chaySandboxPolyglot() {
    const srcEditor = document.getElementById('polyglotSourceEditor');
    const ma = srcEditor ? srcEditor.value.trim() : '';

    if (!ma) {
      inConsolePolyglot('Vui lòng nhập mã trước khi chạy thử!', 'LỖI', 'error');
      return;
    }

    inConsolePolyglot(`Đang chạy mã ${state.polyglotSourceLang.toUpperCase()} trong một tiến trình con (trần 5,0s, KHÔNG có hộp cát)...`, 'ĐANG CHẠY...', 'info');

    try {
      const resp = await fetch('/api/polyglot/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ma: ma,
          lang: state.polyglotSourceLang,
          timeout_s: 5.0
        })
      });
      const data = await resp.json();

      const out = data.stdout ? `--- STDOUT ---\n${data.stdout}\n` : '';
      const err = data.stderr ? `--- STDERR ---\n${data.stderr}\n` : '';

      // BA TRẠNG THÁI, không phải hai. `KHONG_CHAY_DUOC` nghĩa là máy chưa
      // có bộ công cụ cho ngôn ngữ ấy: chương trình CHƯA HỀ CHẠY. Gộp nó vào
      // xanh thì người dùng tưởng đã đỗ; gộp vào đỏ thì tưởng mã mình sai.
      // Đo 01/09: 6/8 ngôn ngữ đi vào nhánh này, và trước đây cả sáu đều nhận
      // huy hiệu xanh "EXIT CODE 0" — kể cả `bash exit 3` trên máy CÓ bash.
      const chuaChay = data.status === 'KHONG_CHAY_DUOC';
      const dat = data.status === 'PASS';
      inConsolePolyglot(
        (chuaChay ? `[KHÔNG CHẠY ĐƯỢC — chỉ kiểm cú pháp]\n`
                  : `[KẾT QUẢ CHẠY THẬT]\n`) +
        `• Ngôn ngữ: ${data.language || state.polyglotSourceLang}\n` +
        (chuaChay ? '' : `• Exit Code: ${data.exit_code}\n`) +
        `• Thời gian: ${data.latency_ms || 0} ms\n` +
        `• Trạng thái: ${data.status}\n\n` +
        (out || err || '(Chương trình chạy xong mà không in kết quả ra terminal)'),
        chuaChay ? 'CHƯA CHẠY' : (dat ? 'EXIT CODE 0' : 'EXIT ERROR'),
        chuaChay ? 'info' : (dat ? 'success' : 'error')
      );
    } catch (err) {
      inConsolePolyglot(`✕ Không gọi được máy chủ: ${err.message}`, 'HỎNG', 'error');
    }
  }

  function inConsolePolyglot(noiDung, trangThaiText, loai = 'info') {
    const outBox = document.getElementById('polyglotConsoleOutput');
    const metaTag = document.querySelector('#polyglotConsoleMeta .meta-tag');

    if (metaTag) {
      metaTag.textContent = `Trạng thái: ${trangThaiText}`;
      metaTag.className = `meta-tag ${loai === 'error' ? 'fail' : loai === 'success' ? 'pass' : ''}`;
    }

    if (outBox) {
      outBox.innerHTML = `<pre class="console-text ${loai}">${escapeHtml(noiDung)}</pre>`;
    }
  }

  function saoChepCode(editorId, btnId) {
    const editor = document.getElementById(editorId);
    if (!editor || !editor.value) return;

    navigator.clipboard.writeText(editor.value).then(() => {
      const btn = document.getElementById(btnId);
      if (btn) {
        const oldText = btn.textContent;
        btn.textContent = '✓ Đã Chép!';
        setTimeout(() => { btn.textContent = oldText; }, 1800);
      }
    });
  }

  function escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  // Khởi chạy khi tài liệu tải xong
  window.addEventListener('DOMContentLoaded', initCommandCenter);
})();

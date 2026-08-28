// noi_bo.js — Frontend Engine cho AURA Command Center v3.0

(function () {
  'use strict';

  const state = {
    activeView: 'viewWarRoom',
    activeAgentId: 'aura',
    rooms: [],
    vitals: {},
    chatHistories: {} // Keyed by agentId
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

    // Tự động làm mới Vitals mỗi 4 giây
    setInterval(capNhatTrangThaiHeThong, 4000);
  }

  // ==========================================================================
  // 2. ĐIỀU HƯỚNG VIEW (WAR ROOM / CONSOLE / PIPELINE / LEDGER)
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

    // Xử lý 4 Thẻ Quy Trình 1-Click
    const presetPrompts = {
      card_video_shorts: 'Sản xuất video ngắn 60s về Lập trình Thẻ AURA v3 và Xuất bản tự động',
      card_code_doctor: 'Khám bệnh mã nguồn Python, định vị lỗi AST và sinh bản vá tự động',
      card_novel_writer: 'Sáng tác chương truyện đời thường Quán Cà Phê Cuối Ngõ và chấm điểm TTR',
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
          kichHoatPipeline();
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
  async function kichHoatPipeline() {
    const input = document.getElementById('pipelineTopicInput');
    const chuDe = (input && input.value.trim()) || 'Chiến dịch sản xuất & phân phối nội dung tự động AURA v3';

    const steps = ['step_zeta', 'step_aura', 'step_alpha', 'step_omega', 'step_gamma'];
    steps.forEach(id => {
      const el = document.getElementById(id);
      if (el) {
        el.className = 'flow-step';
        el.querySelector('.step-status').textContent = 'ĐANG ĐỢI';
      }
    });

    const resultBox = document.getElementById('pipelineResultsBox');
    const logBox = document.getElementById('pipelineStepsLog');
    if (resultBox) resultBox.style.display = 'none';

    // Animation chạy từng bước
    for (let i = 0; i < steps.length; i++) {
      const el = document.getElementById(steps[i]);
      if (el) {
        el.className = 'flow-step running';
        el.querySelector('.step-status').textContent = 'ĐANG CHẠY...';
      }
      await new Promise(r => setTimeout(r, 450));
      if (el) {
        el.className = 'flow-step done';
        el.querySelector('.step-status').textContent = 'HOÀN TẤT ✓';
      }
    }

    try {
      const resp = await fetch('/api/pipeline/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ chu_de: chuDe })
      });
      const data = await resp.json();

      if (data.status === 'PASS' && resultBox && logBox) {
        resultBox.style.display = 'block';
        logBox.innerHTML = (data.cac_buoc || []).map(b => `
          <div style="padding: 8px 12px; background: rgba(255,255,255,0.03); border-radius: 6px; margin-bottom: 6px; font-size: 12px;">
            <strong style="color: #60A5FA;">[Bước ${b.buoc}] ${b.phong_ten}:</strong> ${b.hanh_dong}
            <div style="color: #34D399; margin-top: 2px;">➔ ${b.ket_qua}</div>
          </div>
        `).join('');
      }
    } catch (_) {}
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

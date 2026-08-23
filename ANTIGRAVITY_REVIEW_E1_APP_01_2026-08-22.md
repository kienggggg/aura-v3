# TRẢ LẠI ANTIGRAVITY — NGHIỆM THU E1 APP THẺ LẦN 01

**Ngày:** 22/08/2026  
**Run bị xem xét:** `data/evidence_sprint/runs/e1_app_20260822_115114/`  
**Phán quyết:** **KHÔNG DUYỆT `PASS 7/7`**  
**Nguyên tắc:** Giữ nguyên hiện vật cũ. Không sửa raw/manifest cũ để biến kết quả. Thêm `audit.json` đánh dấu run trên là `INVALID(false_pass_verifier)` và tạo run mới sau khi sửa.

## 1. Bằng chứng chạy lại

### 1.1 Job Object không gắn nhưng supervisor vẫn READY

Lệnh chạy thật trên máy này:

```powershell
'{}' | venv\Scripts\python.exe -B -X utf8 tools\e1_supervisor_bootstrap.py
```

Kết quả đầu ra:

```text
===E1_SUPERVISOR_READY===
{"supervisor_pid": 27476, "job_attached": false}
```

`tools/e1_supervisor_bootstrap.py:27-99` chưa khai báo `argtypes/restype` đúng cho WinAPI HANDLE 64-bit. Tuy vậy `:127-134` vẫn phát READY, còn `interface/the_api.py:1049-1060` đọc PID nhưng bỏ qua `job_attached=false`. Vì vậy lời hứa KILL_ON_JOB_CLOSE trong báo cáo không tồn tại ở run đã PASS.

### 1.2 Cửa E không nhìn thấy tiến trình con

`SocketCanary` chỉ monkeypatch `socket` trong tiến trình verifier (`tools/do_cua_cung_e1_app.py:98-148`). Supervisor, worker và pytest là các interpreter mới. Biến `AURA_CHILD_CANARY=1` được đặt ở `tools/e1_supervisor_bootstrap.py:214-222`, nhưng không có mã nào đọc nó.

Probe tiến trình con trả `socket.socket.connect` nguyên bản và `parent_violations=[]`. Do đó `socket_canary_log.json` chỉ chứng minh verifier tự bắt probe 8.8.8.8 của chính nó; không chứng minh worker/test không dùng mạng hay model.

### 1.3 Cửa G đi vòng qua luồng UI → API

`tools/_cdp_browser_test.js:204-228` gọi thẳng `window.renderE1Results()` với JSON hard-code `65 → 15`, dòng 150. Nó không mở tệp qua UI, không chọn test, không bấm `#btnRunE1`, không phát POST `/api/dinh_vi_loi` và không render response thật.

`tools/_cdp_browser_test.js:274-279` luôn in `trang_thai: PASS`; verifier ở `tools/do_cua_cung_e1_app.py:698-700` chỉ cần exit 0 và hai file tồn tại. Receipt run cũ đúng là chứa dữ liệu giả này; CDP mất 3,199 giây trong khi một API E1 thật mất 44–108 giây.

Dirty-state cũng chưa đạt đúng hợp đồng: script tự gán `window.state.hasModifications=true`, nhưng `pass` ở `:247-254` bỏ qua cả `dirtyStateDisabled` lẫn `dirtyNoRequest`. Nhánh cờ tắt dùng ID `btnRunPython` không tồn tại; HTML dùng `btnRun`.

## 2. Các cửa còn PASS giả hoặc đo thiếu

### P0 — Cửa D/A vẫn tin worker ở chỗ quyết định

- `do_cua_cung_e1_app.py:598-610` lấy số trước/sau và status trực tiếp từ response worker.
- Oracle chỉ áp ở ba ca dương. Ca âm `loai_cau_hoi` ở `:641-646` có thể trả cứng `10 → 2`, `candidates=[]`, `khong_tim_thay` rồi vẫn PASS.
- Oracle bỏ qua `cand_line` và `cand_operation`; verifier không khóa đúng index/operation đã duyệt.
- Cửa A tuyên bố 5 họ phép nhưng fixture E2E chỉ thực thi 4 họ; thiếu integer constant. A lại được gán PASS chung với D ở `:652-656`.

### P0 — B/C/F không đo đủ hợp đồng kế hoạch v2.2

- B chỉ đo vài ca auth/path cơ bản; thiếu ma trận schema/SHA kiểu-rỗng-hex, absolute path, symlink/junction, trace payload/max_steps và spy runner=0.
- C chỉ đo app-disabled và token-cross; không snapshot toàn bộ `core/`, `tests/`, không kiểm PID/temp/no-write.
- F tự đặt `busy_info=True` thay vì hai request thật; không đo timeout 504, kill tree, shutdown/disconnect, temp cleanup và reset busy sau cleanup.

### P1 — Các lỗ hổng kiến trúc cần sửa trước run mới

1. Preflight pytest collection (`e1_supervisor_bootstrap.py:188-203`) chạy trước `clean_env`, kế thừa toàn bộ biến môi trường và quyền mạng.
2. `tao_app()` không có `on_cleanup`; `active_job_process`/`cleanup_task` được khai báo nhưng không bảo đảm dừng job khi server shutdown.
3. Bootstrap được lấy từ `project_root` đang phân tích (`the_api.py:980-1046`), không phải mã server-owned đã khóa hash. Repo đích có thể thay supervisor.
4. Temp clone chỉ là bản sao thư mục, **không phải sandbox** filesystem/network; child vẫn có quyền của tài khoản Windows.
5. Token mặc định không thật sự per-app: `interface/the_app.py:32` dùng token module-global cho mọi app không truyền token.
6. Snapshot chỉ khóa SHA source và một test; dependency/các test còn lại có thể tạo clone lai phiên bản trong lúc copy.
7. API chờ 300 giây nhưng thông báo lỗi ghi 180 giây (`the_api.py:1072-1105`).

## 3. Phần đã đạt và phải giữ

- Unit/API chọn lọc chạy lại: `14 passed` (`tests/test_e1_app.py` + `tests/test_cua_a_guard.py`).
- UI unit: `5 passed`.
- Full suite chạy lại: `606 passed, 1 skipped` trong `64,64 giây`.
- Renderer E1 dùng `textContent` cho dữ liệu động; XSS canary hiện không kích hoạt.
- Không có nút Apply trong luồng E1; không thấy E1 gọi `/api/luu_tep`.
- Hash bảy raw artifact của run cũ khớp `artifacts.json`.

Các điểm này là PASS cục bộ, không được suy rộng thành 7/7.

## 4. Yêu cầu sửa bắt buộc

### R1 — Job/lifecycle phải fail-closed

- Khai báo WinAPI types đúng; nếu attach Job Object thất bại thì **không phát READY hợp lệ** và API không chạy worker.
- READY phải có schema và API phải yêu cầu `job_attached is true`.
- Thêm cleanup hook của app.
- Integration test phải tạo supervisor → worker → descendant thật, rồi kiểm lần lượt cancel, client disconnect, timeout và app shutdown: toàn bộ PID chết, temp biến mất, busy chỉ nhả sau cleanup.

### R2 — Chặn và đo mạng ở đúng tiến trình

- Cài guard vào supervisor, preflight, worker và mọi pytest child **trước import/collection** (ví dụ `sitecustomize` do server sở hữu, được hash).
- Môi trường child là allowlist, không truyền bí mật không cần thiết.
- Negative control bắt buộc: một test con thử kết nối ngoài phải bị chặn và ghi receipt; loopback policy phải được ghi rõ và test riêng.
- Verifier phải kiểm log từ child, không chỉ log parent.

### R3 — Browser E2E phải đi hết đường thật

- Chrome mở tệp qua UI, chọn test thật, tạo dirty bằng thao tác sửa thật, kiểm nút bị disable và không fetch.
- Sau save/undo, click `#btnRunE1`; receipt phải có đúng một POST `/api/dinh_vi_loi`, status thật và DOM render từ response đó.
- Chạy cả `allow_code_execution=false` và `true`; dùng ID nút thật.
- Verdict CDP phải là AND của mọi subgate; một subgate false phải exit 1.
- Chụp đúng tab/panel E1 và lưu DOM snapshot/request list đủ để verifier độc lập đọc lại.

### R4 — Oracle phải độc lập với worker

- Verifier tự tính lại số ứng viên trước/sau, index, line, operation và diff từ bytes clone; không lấy số worker khai làm chân lý.
- Ca âm cũng phải có oracle độc lập.
- Thêm fifth-family fixture cho integer constant.
- Negative-control test sửa response worker thành số/status hard-code; verifier bắt buộc FAIL.

### R5 — Hoàn thiện B/C/F và snapshot

- Chạy đủ ma trận trong kế hoạch v2.2, bao gồm symlink/junction nếu máy hỗ trợ; trường hợp không tạo được phải ghi BLOCKED, không tự PASS.
- Hash manifest toàn bộ snapshot liên quan, mã bootstrap/worker/verifier/API và git commit/worktree state.
- Bootstrap phải là mã installation/server-owned, không lấy từ repo đích.
- Commands receipt phải có argv, cwd, exit code, duration, stdout/stderr hoặc hash của chúng.

### R6 — Token và mô tả an toàn

- Mỗi `tao_app()` không truyền token phải sinh token riêng.
- Tài liệu/UI phải nói đúng: temp clone không đồng nghĩa filesystem/network sandbox.

## 5. Trình tự chạy lại

Không chạy verifier 10 phút trước khi các test focused dưới đây xanh:

```powershell
venv\Scripts\python.exe -X utf8 -m pytest tests\test_e1_app.py tests\test_cua_a_guard.py -q -p no:cacheprovider
node --test tests\test_e1_ui.js
```

Thêm test mới cho Job child, child-network canary, shutdown/disconnect, concurrent request thật, timeout thật, Chrome E2E thật và oracle tamper. Sau đó mới chạy:

```powershell
venv\Scripts\python.exe -X utf8 tools\do_cua_cung_e1_app.py
venv\Scripts\python.exe -X utf8 -m pytest tests -q -p no:cacheprovider
```

**Điều kiện duyệt lại:** run mới không dùng dữ liệu hard-code ở cửa G; Job attach thật; child-network negative control bị bắt; oracle tamper test đỏ khi verifier bị lừa; toàn bộ PID/temp/hash được verifier đọc lại từ đĩa.

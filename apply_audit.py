import os
import json

runs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'data', 'evidence_sprint', 'runs'))

audit_runs = [
    ("run_20260814_002756_ad08cfe8", "INVALID", "False PASS from Review 01"),
    ("run_20260814_003009_2d4f8b37", "INVALID", "False PASS from Review 01"),
    ("run_20260814_031600_c615095d", "STUB_FAILED", "Studio stub false PASS from Review 03"),
    ("run_20260814_031602_c81ca1e7", "STUB_FAILED", "Scout stub false PASS from Review 03"),
    ("run_20260814_031605_91e748f5", "STUB_FAILED", "Alpha stub false PASS from Review 03"),
    ("run_20260814_021840_492f7bed", "INVALID", "Incorrect exit code for BLOCKED run")
]

for run_id, status, reason in audit_runs:
    d = os.path.join(runs_dir, run_id)
    if os.path.exists(d):
        audit = {"audit_status": status, "reason": reason}
        with open(os.path.join(d, 'audit.json'), 'w', encoding='utf-8') as f:
            json.dump(audit, f)
            
# Fix exit code for run_20260814_021840_492f7bed
broken_run = os.path.join(runs_dir, "run_20260814_021840_492f7bed")
if os.path.exists(broken_run):
    cmds_path = os.path.join(broken_run, 'commands.jsonl')
    if os.path.exists(cmds_path):
        lines = []
        with open(cmds_path, 'r') as f:
            for line in f:
                try:
                    data = json.loads(line)
                    data['exit_code'] = 2
                    lines.append(json.dumps(data))
                except:
                    lines.append(line.strip())
        with open(cmds_path, 'w') as f:
            for l in lines:
                f.write(l + '\n')

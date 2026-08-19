import os
import subprocess

runs = {
    "run_known_good": "PASS",
    "run_bad_word_count_low": "FAIL",
    "run_bad_word_count_high": "FAIL",
    "run_bad_mojibake": "FAIL",
    "run_bad_control_char": "FAIL",
    "run_bad_missing_char": "FAIL",
    "run_bad_prompt_leak": "FAIL"
}

python_exe = os.path.abspath("venv/Scripts/python.exe")

all_passed = True
for run_id, expected in runs.items():
    env = os.environ.copy()
    env["TARGET_RUN_ID"] = run_id
    env["EXPECTED_STATUS"] = expected
    print(f"\nTesting {run_id} (Expected {expected})...")
    
    result = subprocess.run([python_exe, "-m", "pytest", "experiments/evidence_sprint/tests/test_writer_gates.py::test_run_status"], env=env, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"FAILED (Unexpected exit code for status test): {run_id}")
        print(result.stdout)
        all_passed = False
    else:
        print(f"OK (Status)")

    res2 = subprocess.run([python_exe, "-m", "pytest", "experiments/evidence_sprint/tests/test_writer_gates.py::test_writer_gates"], env=env, capture_output=True, text=True)
    if expected == "PASS":
        if res2.returncode != 0:
            print(f"FAILED (Gates failed for GOOD run): {run_id}")
            print(res2.stdout)
            all_passed = False
        else:
            print(f"OK (Gates)")
    elif expected == "FAIL":
        if res2.returncode == 0:
            print(f"FAILED (Gates passed for BAD run): {run_id}")
            print(res2.stdout)
            all_passed = False
        else:
            print(f"OK (Gates failed as expected)")

# Test logger constraints
print("\nTesting logger zero-byte...")
res3 = subprocess.run([python_exe, "-m", "pytest", "experiments/evidence_sprint/tests/test_writer_gates.py::test_logger_zero_byte"], capture_output=True, text=True)
if res3.returncode == 0:
    print("OK")
else:
    print("FAILED")
    print(res3.stdout)

print("\nTesting logger outside-path...")
res4 = subprocess.run([python_exe, "-m", "pytest", "experiments/evidence_sprint/tests/test_writer_gates.py::test_logger_outside_path"], capture_output=True, text=True)
if res4.returncode == 0:
    print("OK")
else:
    print("FAILED")
    print(res4.stdout)

print("\nTesting hash mismatch...")
res5 = subprocess.run([python_exe, "-m", "pytest", "experiments/evidence_sprint/tests/test_writer_gates.py::test_hash_mismatch"], capture_output=True, text=True)
if res5.returncode == 0:
    print("OK")
else:
    print("FAILED")
    print(res5.stdout)

print("\nTesting missing artifact...")
res6 = subprocess.run([python_exe, "-m", "pytest", "experiments/evidence_sprint/tests/test_writer_gates.py::test_missing_artifact"], capture_output=True, text=True)
if res6.returncode == 0:
    print("OK")
else:
    print("FAILED")
    print(res6.stdout)

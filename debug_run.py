import subprocess
import sys

print("--- START DEBUG ---")
try:
    result = subprocess.run(
        [sys.executable, "check_types.py"],
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='replace'
    )
    print("STDOUT:\n", result.stdout)
    print("STDERR:\n", result.stderr)
except Exception as e:
    print("Execution Error:", e)
print("--- END DEBUG ---")

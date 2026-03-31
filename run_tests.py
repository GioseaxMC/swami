import subprocess
from pathlib import *

TEST_DIR = "./examples"
TEST_PATH = Path(TEST_DIR)
files = [p for p in TEST_PATH.iterdir()]

import os

total = len(files)
success = 0

for file in files:
    file_path = str(file)
    cmd_list = ["myswami.bat", file_path, "-o", "a"]
    print(cmd_list)
    res = subprocess.run(
        cmd_list,
        capture_output=True,
        env={**os.environ, "PYTHONIOENCODING": "utf-8"}
    )
    SUCCESS = not res.returncode
    success += SUCCESS
    if SUCCESS:
        print("SUCCESS")
    else:
        print("FAILED")
        print(res.stderr.decode("utf-8"))

print("passed:", success, "/", total)
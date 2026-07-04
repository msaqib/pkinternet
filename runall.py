import subprocess
import time

TOTAL      = 1877
BATCH_SIZE = 20

for start in range(780, TOTAL, BATCH_SIZE):
    print(f"\n===== BATCH starting at {start} =====")
    
    # read the script
    with open("scripts/measurement/pk_multi_probe.py", "r") as f:
        code = f.read()
    
    # update BATCH_START and BATCH_SIZE
    import re
    code = re.sub(r"BATCH_START\s*=\s*\d+", f"BATCH_START = {start}", code)
    code = re.sub(r"BATCH_SIZE\s*=\s*\d+",  f"BATCH_SIZE  = {BATCH_SIZE}", code)
    
    # write it back
    with open("scripts/measurement/pk_multi_probe.py", "w") as f:
        f.write(code)
    
    # run it, auto-answer yes
    result = subprocess.run(
        ["python3", "scripts/measurement/pk_multi_probe.py"],
        input="yes\n",
        text=True
    )
    
    print(f"Batch {start}-{start+BATCH_SIZE} done. Waiting 2 min...")
    time.sleep(120)  # 2 min gap between batches
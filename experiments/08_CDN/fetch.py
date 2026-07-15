import requests, os
from dotenv import load_dotenv
load_dotenv()

API_KEY = os.environ.get("RIPE_API_KEY")
HDR = {"Authorization": f"Key {API_KEY}"}
BASE = "https://atlas.ripe.net/api/v2"

ids = [190359536, 190359548, 190359552, 190359555, 190359556, 190359558]
for mid in ids:
    r = requests.get(f"{BASE}/measurements/{mid}/results/", headers=HDR, timeout=15)
    results = r.json()
    print(f"\n=== {mid} ===")
    for result in results:
        for hop in result.get("result", []):
            hop_num = hop.get("hop")
            replies = hop.get("result", [])
            chosen = next((r for r in replies if "from" in r), None)
            if chosen:
                ip = chosen["from"]
                rtt = chosen.get("rtt", 0)
                note = "<<< PIE KARACHI!" if ip.startswith("58.181.127.") else ""
                print(f"  hop {hop_num:<3} {rtt:<8.1f}ms  {ip} {note}")
            else:
                print(f"  hop {hop_num:<3} *")
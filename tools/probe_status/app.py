#!/usr/bin/env python3
"""
Probe-status dashboard — which probes in the Google-Sheet roster are online on
RIPE Atlas right now, grouped by section (Our Probes / Existing probes).
On every refresh it also pulls each probe's RIPE Atlas label (description) + tags.

Reads the roster live from a Google Sheet (share link -> CSV) server-side (no CORS),
queries the public RIPE Atlas probes API for live status + first-connected, joins,
and serves a colour-coded auto-refreshing table grouped by section.

Run (PowerShell):
    $env:SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/<ID>/edit?gid=0#gid=0"
    python tools/probe_status/app.py
    # then open http://127.0.0.1:5000

Optional env: ID_COL=...  PORT=5000
"""
import os, re, io, csv, sys
import requests
from flask import Flask, jsonify, Response

SHEET  = os.environ.get("SHEET_CSV_URL", "").strip()
ID_COL = os.environ.get("ID_COL", "").strip()
HOST   = os.environ.get("HOST", "127.0.0.1")     # set HOST=0.0.0.0 to share on your tailnet/LAN
PORT   = int(os.environ.get("PORT", "5000"))
RIPE   = "https://atlas.ripe.net/api/v2/probes/"
GROUP_ORDER = ["Our Probes", "Existing probes"]

# RIPE API key (optional) so our own probes' labels/descriptions are visible.
KEY = os.environ.get("RIPE_API_KEY", "").strip()
if not KEY:
    try:
        from dotenv import load_dotenv, find_dotenv
        load_dotenv(find_dotenv())
        KEY = os.environ.get("RIPE_API_KEY", "").strip()
    except Exception:
        pass

app = Flask(__name__)


def csv_url(u):
    m = re.search(r"/spreadsheets/d/([\w-]+)", u)
    if not m:
        return u
    sid = m.group(1)
    g = re.search(r"[#&?]gid=(\d+)", u)
    return f"https://docs.google.com/spreadsheets/d/{sid}/export?format=csv&gid={g.group(1) if g else '0'}"


def fetch_roster():
    """Read the sheet, tolerating a blank/title row before the header and a leading
    empty column. Tags each row with a __group__ from the 'Existing probes' section
    divider (everything before it is the Local Project pool). Returns (rows, fields)."""
    r = requests.get(csv_url(SHEET), timeout=20)
    r.raise_for_status()
    grid = list(csv.reader(io.StringIO(r.content.decode("utf-8-sig"))))
    if not grid:
        return [], []
    hdr = None
    for i, row in enumerate(grid[:12]):
        j = " ".join(c.lower() for c in row)
        if ("ripe" in j and "id" in j) or "probe id" in j:
            hdr = i; break
    if hdr is None:
        hdr = max(range(min(12, len(grid))), key=lambda i: sum(1 for c in grid[i] if c.strip()))
    cols = [(idx, h.strip()) for idx, h in enumerate(grid[hdr]) if h.strip()]
    fields = [h for _, h in cols]
    rows, section = [], GROUP_ORDER[0]
    for row in grid[hdr + 1:]:
        cells = [c.strip() for c in row]
        if not any(cells):
            continue
        joined = " ".join(cells).lower()
        has_id = any(c.isdigit() and 5 <= len(c) <= 8 for c in cells)
        if not has_id and "existing" in joined:
            section = "Existing probes"; continue
        d = {h: (row[idx].strip() if idx < len(row) else "") for idx, h in cols}
        d["__group__"] = section
        rows.append(d)
    return rows, fields


def detect_id_col(rows, fields):
    if ID_COL:
        return ID_COL
    for f in fields:
        lf = f.lower()
        if ("ripe" in lf and "id" in lf) or "probe id" in lf:
            return f
    best, score = None, -1
    for f in fields:
        n = sum(1 for r in rows if r.get(f, "").isdigit() and 5 <= len(r[f]) <= 8)
        if n > score:
            best, score = f, n
    return best


def find_col(fields, *keys):
    for f in fields:
        if any(k in f.lower() for k in keys):
            return f
    return None


PK_CITIES = ["Dera Ghazi Khan", "Rawalpindi", "Islamabad", "Faisalabad", "Gujranwala",
             "Karachi", "Lahore", "Peshawar", "Sialkot", "Mianwali", "Haripur", "Burewala",
             "Multan", "Quetta", "Hyderabad", "Sargodha", "Abbottabad", "Bahawalpur"]


def city_of(row, addrc):
    """City from the address (falls back to scanning the whole row). LUMS -> Lahore."""
    blob = (row.get(addrc, "") + " | " + " ".join(row.values())) if addrc else " ".join(row.values())
    for c in PK_CITIES:                                  # longest/specific names first
        if re.search(r"\b" + re.escape(c) + r"\b", blob, re.I):
            return c
    if re.search(r"\bLUMS\b", blob, re.I):
        return "Lahore"
    return ""


def ripe_status(ids):
    out = {}
    for i in range(0, len(ids), 100):
        chunk = ids[i:i + 100]
        params = {"id__in": ",".join(chunk), "page_size": 100,
                  "fields": "id,status,is_anchor,asn_v4,first_connected,description,tags,country_code"}
        if KEY:
            params["key"] = KEY                        # surfaces our own probes' labels
        try:
            r = requests.get(RIPE, params=params, timeout=25)
            if not r.ok:
                continue
            for p in r.json().get("results", []):
                st = p.get("status") or {}
                out[str(p["id"])] = {"status": st.get("name"), "since": st.get("since"),
                    "asn": p.get("asn_v4"), "anchor": p.get("is_anchor"),
                    "first_connected": p.get("first_connected"),
                    "ripe_label": (p.get("description") or "").strip(),
                    "tags": [t.get("name") or t.get("slug") for t in (p.get("tags") or [])]}
        except Exception:
            pass
    return out


@app.route("/api/status")
def api_status():
    if not SHEET:
        return jsonify(error="SHEET_CSV_URL not set. Restart with SHEET_CSV_URL=<your sheet link>."), 400
    try:
        rows, fields = fetch_roster()
    except Exception as e:
        return jsonify(error=f"Could not read the sheet: {e}. Make sure it is shared 'anyone with link can view'."), 502

    idc = detect_id_col(rows, fields)
    volc = find_col(fields, "volunteer") or find_col(fields, "name")
    ispc = find_col(fields, "isp")
    addrc = find_col(fields, "address")
    ids = [r[idc] for r in rows if r.get(idc, "").isdigit()]
    live = ripe_status(ids)

    out = []
    for r in rows:
        pid = r.get(idc, "")
        if not pid.isdigit() and (" " in pid or len(pid) > 12):
            continue                                   # prose / divider row
        group = r.get("__group__", GROUP_ORDER[0])
        registered = pid.isdigit()
        info = live.get(pid, {}) if registered else {}
        status = info.get("status")
        online = status == "Connected"
        ever = bool(info.get("first_connected"))
        # deployed: Local Project pool -> has a RIPE id ; Existing -> has ever connected
        deployed = registered if group == GROUP_ORDER[0] else ever
        disp = status or ("no RIPE ID" if not registered else "unknown")
        if registered and not ever and disp in ("Abandoned", "Never Connected", "unknown"):
            disp = "not configured"                    # has an ID but never came online
        out.append({
            "group": group, "id": pid or "—",
            "label": (r.get(volc, "") if volc else ""), "isp": (r.get(ispc, "") if ispc else ""),
            "ripe_label": info.get("ripe_label", ""), "city": city_of(r, addrc), "status": disp,
            "online": online, "registered": registered, "deployed": deployed,
            "since": info.get("since"), "asn": info.get("asn"), "anchor": info.get("anchor"),
            "mismatch": deployed and not online,        # deployed but not connected
        })

    groups = []
    for g in GROUP_ORDER:
        rs = [x for x in out if x["group"] == g]
        rs.sort(key=lambda x: (not x["online"], not x["registered"]))  # online -> disconnected -> no RIPE ID
        groups.append({"name": g, "rows": rs, "summary": {
            "total": len(rs), "online": sum(1 for x in rs if x["online"]),
            "deployed": sum(1 for x in rs if x["deployed"]),
            "mismatch": sum(1 for x in rs if x["mismatch"])}})
    overall = {"total": len(out), "online": sum(1 for x in out if x["online"]),
               "deployed": sum(1 for x in out if x["deployed"]),
               "mismatch": sum(1 for x in out if x["mismatch"])}
    return jsonify(groups=groups, overall=overall, id_col=idc)


PAGE = """
<!doctype html><html><head><meta charset="utf-8"><title>PK Probe Status</title>
<style>
 body{font-family:system-ui,Segoe UI,Arial;margin:24px;color:#1a1a1a}
 h1{font-size:20px;margin:0 0 4px} h2{font-size:15px;margin:22px 0 6px}
 .sub{color:#666;font-size:13px;margin-bottom:14px}
 .cards{display:flex;gap:12px;margin:10px 0}
 .card{padding:8px 14px;border-radius:8px;font-size:13px;border:1px solid #e0e0e0}
 .card b{font-size:19px;display:block}
 .gsum{color:#777;font-size:12px;font-weight:400;margin-left:8px}
 table{border-collapse:collapse;width:100%;font-size:13px;margin-bottom:8px}
 th,td{padding:6px 10px;text-align:left;border-bottom:1px solid #eee}
 th{cursor:pointer;background:#fafafa}
 tr.off{background:#fff6f6} tr.mis{box-shadow:inset 4px 0 0 #e6a700}
 .dot{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:6px}
 .g{background:#2ecc71}.r{background:#e74c3c}.y{background:#bbb}
 .err{color:#c0392b;background:#fdecea;padding:10px;border-radius:6px}
 .tag{font-size:11px;color:#e6a700;font-weight:600}
 .dep{color:#2ecc71}.nodep{color:#999}
</style></head><body>
<h1>PK Probe Status</h1>
<div class="sub">Roster from your Google Sheet vs live RIPE Atlas status. Updated <span id="upd">…</span> · auto-refresh 60s · <span id="idc"></span></div>
<div id="err"></div>
<div class="cards" id="cards"></div>
<div id="groups"></div>
<script>
let SORTK={}, ASC={};
function fmt(s){return s?new Date(s).toLocaleString():"";}
function table(gi,rows){
 const cols=[["online","Status"],["ripe_label","RIPE label"],["id","Probe ID"],["label","Label"],
   ["isp","ISP"],["city","City"],["deployed","Deployed"],["since","Since"]];
 let h='<table><thead><tr>'+cols.map(c=>`<th data-g="${gi}" data-k="${c[0]}"`
   +(c[0]==="since"?' title="Time the probe entered its current RIPE status (Connected/Disconnected) — i.e. how long it has been in that state"':'')
   +`>${c[1]}</th>`).join('')+'</tr></thead><tbody>';
 const k=SORTK[gi]; if(k){const asc=ASC[gi]===undefined?true:ASC[gi];
   rows=[...rows].sort((a,b)=>{let x=a[k],y=b[k];return (x>y?1:x<y?-1:0)*(asc?1:-1)});}
 for(const r of rows){
  const dot=r.online?"g":((!r.registered||r.status==="not configured")?"y":"r");
  let cls=!r.online?"off":""; if(r.mismatch)cls+=" mis";
  h+=`<tr class="${cls}">
   <td><span class="dot ${dot}"></span>${r.status}${r.anchor?" ⚓":""}</td>
   <td><b>${r.ripe_label||""}</b></td><td>${r.id}</td><td>${r.label||""}</td><td>${r.isp||""}</td>
   <td>${r.city||""}</td>
   <td>${r.deployed?'<span class="dep">✓ deployed</span>':'<span class="nodep">— not deployed</span>'}${r.mismatch?' <span class="tag">⚠ but offline</span>':''}</td>
   <td>${fmt(r.since)}</td></tr>`;
 }
 return h+'</tbody></table>';
}
function render(){ const j=window._data; if(!j)return;
 let html=""; j.groups.forEach((g,gi)=>{
  html+=`<h2>${g.name}<span class="gsum">${g.summary.online}/${g.summary.total} online · ${g.summary.deployed} deployed`
    +(g.summary.mismatch?` · <span style="color:#e6a700">${g.summary.mismatch} deployed-but-offline</span>`:``)+`</span></h2>`+table(gi,g.rows);});
 document.getElementById("groups").innerHTML=html;
 document.querySelectorAll("th").forEach(th=>th.onclick=()=>{const gi=th.dataset.g,k=th.dataset.k;ASC[gi]=(SORTK[gi]===k)?!ASC[gi]:true;SORTK[gi]=k;render();});
}
async function load(){
 try{
  const j=await (await fetch("/api/status")).json();
  const e=document.getElementById("err");
  if(j.error){e.innerHTML='<div class="err">'+j.error+'</div>';return;} e.innerHTML="";
  const o=j.overall;
  document.getElementById("cards").innerHTML=
   `<div class="card">Total<b>${o.total}</b></div>
    <div class="card" style="border-color:#2ecc71">Online<b style="color:#2ecc71">${o.online}</b></div>
    <div class="card" style="border-color:#888">Deployed<b>${o.deployed}</b></div>
    <div class="card" style="border-color:#e6a700">Deployed but offline<b style="color:#e6a700">${o.mismatch}</b></div>`;
  window._data=j;
  render();
  document.getElementById("upd").textContent=new Date().toLocaleTimeString();
  document.getElementById("idc").textContent="id col: "+j.id_col;
 }catch(err){document.getElementById("err").innerHTML='<div class="err">'+err+'</div>';}
}
load();setInterval(load,60000);
</script></body></html>
"""


@app.route("/")
def index():
    return Response(PAGE, mimetype="text/html")


if __name__ == "__main__":
    if not SHEET:
        print("WARNING: SHEET_CSV_URL not set — set it and restart.", file=sys.stderr)
    print(f"Probe-status dashboard on http://{HOST}:{PORT}", file=sys.stderr)
    try:
        from waitress import serve                       # production server if installed
        serve(app, host=HOST, port=PORT)
    except ImportError:
        app.run(host=HOST, port=PORT, debug=False)        # fallback: Flask dev server

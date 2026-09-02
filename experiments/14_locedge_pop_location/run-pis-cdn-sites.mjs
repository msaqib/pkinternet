// Runs locedge over the 40 CDN-class Exp 07 sites, once per vantage point
// (this laptop directly, plus any Pi reachable through an open SOCKS
// tunnel). For each (site, vantage) pair: saves a full headers dump for
// every resource on the page, and adds a summary row with the % of
// resources that were HIT / MISS / DYNAMIC, since some sites are mostly
// static and some are mostly dynamic.
//
// To add another Pi: open a tunnel (`ssh -D 1081 -N saqib@raslas-02`),
// then add a line to VANTAGE_POINTS below pointing at that port. No other
// code changes needed.
import { readFileSync, writeFileSync, mkdirSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import puppeteer from "puppeteer";
import PuppeteerHar from "puppeteer-har";
import locedge from "./index.js";

const __dirname = dirname(fileURLToPath(import.meta.url));
const TARGETS_CSV = join(__dirname, "../07_longitudinal_panel/analysis/targets_corrected.csv");
const stamp = new Date().toISOString().replace(/[:.]/g, "-");
const HEADERS_DIR = join(__dirname, `results/headers_dump_${stamp}`);
const SUMMARY_CSV = join(__dirname, `results/pis_cdn_summary_${stamp}.csv`);

const VANTAGE_POINTS = [
    { name: "laptop-direct-cybernet-lahore", proxy: null },
    { name: "raslas-01-nova-islamabad", proxy: "socks5://127.0.0.1:1080" },
    // { name: "raslas-02-...", proxy: "socks5://127.0.0.1:1081" },
];

mkdirSync(HEADERS_DIR, { recursive: true });

const lines = readFileSync(TARGETS_CSV, "utf-8").split("\n").filter(Boolean);
const header = lines[0].split(",");
const clsCol = header.indexOf("cls_corrected");
const sites = lines.slice(1)
    .map((l) => l.split(","))
    .filter((cols) => cols[clsCol] === "CDN")
    .map((cols) => cols[0]);

console.log(`${sites.length} CDN sites x ${VANTAGE_POINTS.length} vantage points = ${sites.length * VANTAGE_POINTS.length} page loads.\n`);

const csv = (v) => `"${String(v ?? "").replace(/"/g, '""')}"`;
const rows = ["site,vantage,provider,city,main_page_cache_status,total_resources,resources_with_cache_info,pct_hit,pct_miss,pct_dynamic,pct_other,comments"];

function classify(status) {
    if (!status) return null;
    const s = status.toLowerCase();
    if (s.includes("hit")) return "hit";
    if (s.includes("miss")) return "miss";
    if (s.includes("dynamic")) return "dynamic";
    return "other"; // expired, and anything else locedge returns
}

for (const vantage of VANTAGE_POINTS) {
    console.log(`=== Vantage: ${vantage.name} ===`);
    const vantageDir = join(HEADERS_DIR, vantage.name);
    mkdirSync(vantageDir, { recursive: true });
    const browser = await puppeteer.launch(vantage.proxy ? { args: [`--proxy-server=${vantage.proxy}`] } : {});

    for (const hostname of sites) {
        const harPath = join(vantageDir, `${hostname}.har`);
        const page = await browser.newPage();
        const har = new PuppeteerHar(page);
        let provider = "", city = "", mainCache = "", comments = "";
        let counts = { hit: 0, miss: 0, dynamic: 0, other: 0 };
        let totalResources = 0, withInfo = 0;

        try {
            await har.start({ path: harPath });
            await page.goto(`https://${hostname}`, { waitUntil: "networkidle2", timeout: 45000 });
            await har.stop();

            const parsed = locedge(JSON.parse(readFileSync(harPath, "utf-8")));
            totalResources = parsed.log.entries.length;

            const headersDump = parsed.log.entries.map((e) => ({
                url: e.request.url,
                edgeInfo: e._edgeInfo,
                responseHeaders: Object.fromEntries(e.response.headers.map((h) => [h.name, h.value])),
            }));
            writeFileSync(join(vantageDir, `${hostname}_headers.json`), JSON.stringify(headersDump, null, 2));

            const mainEntry = parsed.log.entries.find((e) => e.request.url.includes(hostname));
            const mainInfo = mainEntry?._edgeInfo ?? {};
            provider = mainInfo.provider ?? "";
            city = mainInfo.location ?? "";
            mainCache = mainInfo.cacheStatus ?? "";
            if (!provider) comments = "no CDN provider detected (locedge has no rule for this site's headers)";

            for (const e of parsed.log.entries) {
                const bucket = classify(e._edgeInfo?.cacheStatus);
                if (bucket) { counts[bucket]++; withInfo++; }
            }
        } catch (err) {
            comments = `page failed to load: ${err.message}`;
        }

        const pct = (n) => (withInfo ? ((n / withInfo) * 100).toFixed(0) : "");
        rows.push([
            hostname, vantage.name, provider, city, mainCache,
            totalResources, withInfo,
            pct(counts.hit), pct(counts.miss), pct(counts.dynamic), pct(counts.other),
            comments,
        ].map(csv).join(","));

        console.log(`  ${hostname}: provider=${provider || "-"} city=${city || "-"} hit=${pct(counts.hit) || "-"}% (${withInfo}/${totalResources} resources had cache info)`);
        await page.close();
    }
    await browser.close();
}

writeFileSync(SUMMARY_CSV, rows.join("\n") + "\n");
console.log(`\nSummary CSV: ${SUMMARY_CSV}`);
console.log(`Headers dump: ${HEADERS_DIR}`);

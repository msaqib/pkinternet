// Re-runs just the (site, vantage) pairs that failed to load on the first pass.
import { readFileSync, writeFileSync, mkdirSync } from "fs";
import { join } from "path";
import puppeteer from "puppeteer";
import PuppeteerHar from "puppeteer-har";
import locedge from "./index.js";

const TARGETS = [
    { site: "bnbwu.edu.pk", vantage: "raslas-01-nova-islamabad", proxy: "socks5://127.0.0.1:1080" },
    { site: "khushhalibank.com.pk", vantage: "raslas-02-cybernet-haripur", proxy: "socks5://127.0.0.1:1081" },
    { site: "meerzah.pk", vantage: "raslas-01-nova-islamabad", proxy: "socks5://127.0.0.1:1080" },
    { site: "pinkpetals.pk", vantage: "raslas-01-nova-islamabad", proxy: "socks5://127.0.0.1:1080" },
    { site: "thefrontierpost.com", vantage: "raslas-05-ptcl-karachi", proxy: "socks5://127.0.0.1:1083" },
    { site: "wancom.net.pk", vantage: "raslas-01-nova-islamabad", proxy: "socks5://127.0.0.1:1080" },
];

const HAR_DIR = "results/har_rerun";
mkdirSync(HAR_DIR, { recursive: true });

const csv = (v) => `"${String(v ?? "").replace(/"/g, '""')}"`;
const rows = ["site,vantage,provider,city,main_page_cache_status,total_resources,resources_with_cache_info,pct_hit,pct_miss,pct_dynamic,pct_other,comments"];

function classify(status) {
    if (!status) return null;
    const s = String(status).toLowerCase();
    if (s.includes("hit")) return "hit";
    if (s.includes("miss")) return "miss";
    if (s.includes("dynamic")) return "dynamic";
    return "other";
}

for (const { site, vantage, proxy } of TARGETS) {
    const harPath = join(HAR_DIR, `${site}__${vantage}.har`);
    const browser = await puppeteer.launch({ args: [`--proxy-server=${proxy}`] });
    const page = await browser.newPage();
    const har = new PuppeteerHar(page);
    let provider = "", city = "", mainCache = "", totalResources = 0, withInfo = 0;
    const counts = { hit: 0, miss: 0, dynamic: 0, other: 0 };
    let comments = "";
    try {
        await har.start({ path: harPath });
        await page.goto(`https://${site}`, { waitUntil: "networkidle2", timeout: 60000 });
        await har.stop();

        const parsed = locedge(JSON.parse(readFileSync(harPath, "utf-8")));
        totalResources = parsed.log.entries.length;
        const mainEntry = parsed.log.entries.find((e) => e.request.url.includes(site));
        const mainInfo = mainEntry?._edgeInfo ?? {};
        provider = mainInfo.provider ?? "";
        city = mainInfo.location ?? "";
        mainCache = mainInfo.cacheStatus ?? "";

        for (const e of parsed.log.entries) {
            const bucket = classify(e._edgeInfo?.cacheStatus);
            if (bucket) { counts[bucket]++; withInfo++; }
        }
        if (!provider) comments = "no CDN provider detected (locedge has no rule for this site's headers)";
        console.log(`${site} @ ${vantage}: provider=${provider || "-"} city=${city || "-"} cache=${mainCache || "-"} (${withInfo}/${totalResources} resources had cache info)`);
    } catch (err) {
        comments = `page failed to load: ${err.message}`;
        console.log(`${site} @ ${vantage}: FAILED (${err.message})`);
    }
    const pct = (n) => (withInfo ? Math.round((100 * n) / withInfo) : "");
    rows.push([site, vantage, provider, city, mainCache, totalResources, withInfo,
        pct(counts.hit), pct(counts.miss), pct(counts.dynamic), pct(counts.other), comments].map(csv).join(","));
    await browser.close();
}

const outPath = "results/rerun_missing_summary.csv";
writeFileSync(outPath, rows.join("\n") + "\n");
console.log(`\nSaved: ${outPath}`);

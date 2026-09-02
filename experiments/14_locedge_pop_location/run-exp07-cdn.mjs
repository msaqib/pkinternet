// Runs locedge over the 40 CDN-class sites from the Exp 07 panel
// (experiments/07_longitudinal_panel/analysis/targets_corrected.csv,
// cls_corrected == "CDN"), one browser instance reused across sites.
// Writes results/exp07_cdn_summary_<timestamp>.csv: site, provider, city,
// cache_status, comments.
import { readFileSync, writeFileSync, mkdirSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import puppeteer from "puppeteer";
import PuppeteerHar from "puppeteer-har";
import locedge from "./index.js";

const __dirname = dirname(fileURLToPath(import.meta.url));
const TARGETS_CSV = join(__dirname, "../07_longitudinal_panel/analysis/targets_corrected.csv");
const HAR_DIR = join(__dirname, "results/har_exp07");
const stamp = new Date().toISOString().replace(/[:.]/g, "-");
const SUMMARY_CSV = join(__dirname, `results/exp07_cdn_summary_${stamp}.csv`);

mkdirSync(HAR_DIR, { recursive: true });

const lines = readFileSync(TARGETS_CSV, "utf-8").split("\n").filter(Boolean);
const header = lines[0].split(",");
const clsCol = header.indexOf("cls_corrected");
const sites = lines.slice(1)
    .map((l) => l.split(","))
    .filter((cols) => cols[clsCol] === "CDN")
    .map((cols) => cols[0]);

console.log(`Found ${sites.length} CDN sites in the Exp 07 panel.\n`);

const csv = (v) => `"${String(v ?? "").replace(/"/g, '""')}"`;
const rows = ["site,provider,city,cache_status,comments"];

const browser = await puppeteer.launch();

for (const hostname of sites) {
    const harPath = join(HAR_DIR, `${hostname}.har`);
    const page = await browser.newPage();
    const har = new PuppeteerHar(page);
    let provider = "", city = "", cacheStatus = "", comments = "";
    try {
        await har.start({ path: harPath });
        await page.goto(`https://${hostname}`, { waitUntil: "networkidle2", timeout: 45000 });
        await har.stop();

        const parsed = locedge(JSON.parse(readFileSync(harPath, "utf-8")));
        const topEntry = parsed.log.entries.find((e) => e.request.url.includes(hostname));
        const info = topEntry?._edgeInfo ?? {};
        provider = info.provider ?? "";
        city = info.location ?? "";
        cacheStatus = info.cacheStatus ?? "";
        if (!provider) comments = "no CDN provider detected (locedge has no rule for this site's headers)";
        console.log(`${hostname}: provider=${provider || "-"} city=${city || "-"} cache=${cacheStatus || "-"}`);
    } catch (err) {
        comments = `page failed to load: ${err.message}`;
        console.log(`${hostname}: FAILED (${err.message})`);
    }
    rows.push([hostname, provider, city, cacheStatus, comments].map(csv).join(","));
    await page.close();
}

await browser.close();
writeFileSync(SUMMARY_CSV, rows.join("\n") + "\n");
console.log(`\nSummary written to ${SUMMARY_CSV}`);

// First pass: run the 17 new multi-provider sites through just ONE Pi
// (raslas-01, Nova) to sanity-check results before committing to all 5.
import { readFileSync, writeFileSync, mkdirSync } from "fs";
import { join } from "path";
import puppeteer from "puppeteer";
import PuppeteerHar from "puppeteer-har";
import locedge from "./index.js";

const SITES = [
    "adobe.com", "akamai.com", "music.apple.com",
    "raw.githubusercontent.com", "bbc.com", "cnn.com", "nytimes.com", "theguardian.com",
    "nike.com", "khushhalibank.com.pk",
    "apple.com", "icloud.com",
    "wikipedia.org", "wikidata.org", "wiktionary.org", "wikimedia.org",
    "linkedin.com", "waze.com", "youtube.com",
];

const VANTAGE = "raslas-01-nova-lahore";
const PROXY = "socks5://127.0.0.1:1080";
const HAR_DIR = "results/har_new_providers";
mkdirSync(HAR_DIR, { recursive: true });

const csv = (v) => `"${String(v ?? "").replace(/"/g, '""')}"`;
const rows = ["site,vantage,provider,city,cache_status,comments"];

const browser = await puppeteer.launch({ args: [`--proxy-server=${PROXY}`] });

for (const site of SITES) {
    const harPath = join(HAR_DIR, `${site.replace(/\//g, "_")}.har`);
    const page = await browser.newPage();
    const har = new PuppeteerHar(page);
    let provider = "", city = "", cacheStatus = "", comments = "";
    try {
        await har.start({ path: harPath });
        await page.goto(`https://${site}`, { waitUntil: "networkidle2", timeout: 45000 });
        await har.stop();

        const parsed = locedge(JSON.parse(readFileSync(harPath, "utf-8")));
        const mainEntry = parsed.log.entries.filter((e) => e.request.url === `https://${site}/`).pop()
            || parsed.log.entries.find((e) => e.request.url.includes(site));
        const info = mainEntry?._edgeInfo ?? {};
        provider = info.provider ?? "";
        city = info.location ?? "";
        cacheStatus = info.cacheStatus ?? "";
        if (!provider) comments = "no CDN provider detected by locedge";
        console.log(`${site}: provider=${provider || "-"} city=${city || "-"} cache=${cacheStatus || "-"}`);
    } catch (err) {
        comments = `page failed to load: ${err.message}`;
        console.log(`${site}: FAILED (${err.message})`);
    }
    rows.push([site, VANTAGE, provider, city, cacheStatus, comments].map(csv).join(","));
    await page.close();
}

await browser.close();
const outPath = "results/new_providers_one_pi.csv";
writeFileSync(outPath, rows.join("\n") + "\n");
console.log(`\nSaved: ${outPath}`);

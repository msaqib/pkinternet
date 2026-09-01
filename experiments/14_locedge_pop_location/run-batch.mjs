// Batch-runs capture + locate over data/pk_cdn_targets.csv, one browser
// instance reused across sites (a fresh Chromium launch per site is the
// slow part). Writes one HAR per site into results/har/ and one summary
// CSV into results/.
import { readFileSync, writeFileSync, mkdirSync, existsSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import puppeteer from "puppeteer";
import PuppeteerHar from "puppeteer-har";
import locedge from "./index.js";

const __dirname = dirname(fileURLToPath(import.meta.url));
const TARGETS_CSV = join(__dirname, "../../data/pk_cdn_targets.csv");
const HAR_DIR = join(__dirname, "results/har");
const stamp = new Date().toISOString().replace(/[:.]/g, "-");
const SUMMARY_CSV = join(__dirname, `results/batch_summary_${stamp}.csv`);

mkdirSync(HAR_DIR, { recursive: true });

const targets = readFileSync(TARGETS_CSV, "utf-8")
    .split("\n")
    .map((l) => l.trim())
    .filter((l) => l && !l.startsWith("#"))
    .map((l) => {
        const [hostname, expectedProvider, category] = l.split(",");
        return { hostname, expectedProvider, category };
    });

const browser = await puppeteer.launch();
const rows = ["hostname,expected_provider,category,detected_provider,pop,location,cache_status,error"];

for (const { hostname, expectedProvider, category } of targets) {
    const harPath = join(HAR_DIR, `${hostname}.har`);
    const page = await browser.newPage();
    const har = new PuppeteerHar(page);
    let row;
    try {
        await har.start({ path: harPath });
        await page.goto(`https://${hostname}`, { waitUntil: "networkidle2", timeout: 60000 });
        await har.stop();

        const parsed = locedge(JSON.parse(readFileSync(harPath, "utf-8")));
        const topEntry = parsed.log.entries.find((e) => e.request.url.includes(hostname));
        const info = topEntry?._edgeInfo ?? {};
        row = [hostname, expectedProvider, category, info.provider ?? "", info.pop ?? "",
            info.location ?? "", info.cacheStatus ?? "", ""];
        console.log(`${hostname}: provider=${info.provider ?? "-"} pop=${info.pop ?? "-"} location=${info.location ?? "-"}`);
    } catch (err) {
        row = [hostname, expectedProvider, category, "", "", "", "", err.message.replace(/,/g, ";")];
        console.log(`${hostname}: FAILED (${err.message})`);
    }
    rows.push(row.map((v) => `"${v}"`).join(","));
    await page.close();
}

await browser.close();
writeFileSync(SUMMARY_CSV, rows.join("\n") + "\n");
console.log(`\nSummary written to ${SUMMARY_CSV}`);

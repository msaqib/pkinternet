// Re-parses already-captured HAR files for honda.com.pk and zu.edu.pk with
// a fix: pick the LAST entry matching the exact base URL (so a 307-then-403
// pair resolves to the 403, which carries real Cloudflare headers), instead
// of the first entry containing the site name anywhere in its URL.
import { readFileSync, readdirSync } from "fs";
import { join } from "path";
import locedge from "./index.js";

const DUMP_DIR = "results/headers_dump_2026-09-02T15-02-59-268Z";
const SITES = ["honda.com.pk", "zu.edu.pk"];
const vantages = readdirSync(DUMP_DIR);

for (const site of SITES) {
    console.log(`=== ${site} ===`);
    for (const vantage of vantages) {
        const harPath = join(DUMP_DIR, vantage, `${site}.har`);
        try {
            const har = JSON.parse(readFileSync(harPath, "utf-8"));
            const parsed = locedge(har);
            const baseUrl = `https://${site}/`;
            const matches = parsed.log.entries.filter((e) => e.request.url === baseUrl);
            const last = matches[matches.length - 1];
            const info = last?._edgeInfo ?? {};
            console.log(`  ${vantage}: provider=${info.provider ?? "-"} city=${info.location ?? "-"} cache=${info.cacheStatus ?? "-"} (status ${last?.response.status})`);
        } catch (err) {
            console.log(`  ${vantage}: no HAR file (${err.code === "ENOENT" ? "not tested" : err.message})`);
        }
    }
}

import { readFileSync } from "fs";
import locedge from "./index.js";

const [, , harFile] = process.argv;

if (!harFile) {
    console.error("Usage: node locate-cdn.mjs <capture.har>");
    process.exit(1);
}

const har = JSON.parse(readFileSync(harFile, "utf-8"));
const result = locedge(har);

result.log.entries.forEach((entry) => {
    const info = entry._edgeInfo;
    if (!info || (!info.provider && !info.location && !info.cacheStatus)) return;
    console.log(entry.request.url);
    console.log(`  provider:     ${info.provider ?? "-"}`);
    console.log(`  pop:          ${info.pop ?? "-"}`);
    console.log(`  location:     ${info.location ?? "-"}`);
    console.log(`  cacheStatus:  ${info.cacheStatus ?? "-"}`);
    console.log("");
});

import puppeteer from "puppeteer";
import PuppeteerHar from "puppeteer-har";

const [, , url, outFile] = process.argv;

if (!url || !outFile) {
    console.error("Usage: node capture-har.mjs <url> <output.har>");
    process.exit(1);
}

const target = /^https?:\/\//i.test(url) ? url : `https://${url}`;

const browser = await puppeteer.launch();
const page = await browser.newPage();
const har = new PuppeteerHar(page);

await har.start({ path: outFile });
await page.goto(target, { waitUntil: "networkidle2", timeout: 60000 });
await har.stop();
await browser.close();

console.log(`Saved HAR for ${target} -> ${outFile}`);

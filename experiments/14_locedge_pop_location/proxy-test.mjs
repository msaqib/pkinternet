// Confirms the SOCKS tunnel to a Pi is really being used: launches a
// browser proxied through localhost:1080 and checks what IP a
// what's-my-ip service reports back.
import puppeteer from "puppeteer";

const browser = await puppeteer.launch({
    args: ["--proxy-server=socks5://127.0.0.1:1080"],
});
const page = await browser.newPage();
await page.goto("https://ipinfo.io/json", { waitUntil: "networkidle2", timeout: 20000 });
const text = await page.evaluate(() => document.body.innerText);
console.log(text);
await browser.close();

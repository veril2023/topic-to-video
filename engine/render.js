#!/usr/bin/env node
/* ============================================================================
 * render.js — 通用逐帧渲染器
 *
 * 原理：开一个本地 HTTP 服务托管集目录 → 用 headless Chrome 打开 standalone.html
 *      → 逐帧 videoTimeline.seek(t) → 截图存 JPG。
 *
 * 为什么不用 Chrome 的录屏或 CSS 动画导出：
 *   逐帧 seek 才能保证「第 N 帧 = 时刻 N/fps 的画面状态」严格对应，
 *   且可以随时断点续渲、单独抽某一帧检查。
 *
 * 用法：
 *   node render.js <集目录> probe 12.5 30 60.2     # 抽指定秒数的帧到 probe_<ep>/
 *   node render.js <集目录> cover 7.0              # 只抽一张封面候选 → cover_raw.jpg
 *   node render.js <集目录> full                   # 全量渲染（已存在的帧自动跳过）
 *   node render.js <集目录> full --from 120 --to 150   # 只渲一段（改完局部验证用）
 *
 * 环境变量：
 *   MEV_CHROME   指定 Chrome/Chromium 可执行文件
 *   MEV_PORT     HTTP 端口（默认 8920）
 *   MEV_CDP      CDP 端口（默认 9466）
 *   MEV_FPS      帧率（默认 24）
 * ==========================================================================*/
'use strict';

const puppeteer = require('puppeteer-core');
const http = require('http');
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');

/* ------------------------------------------------------------------ 参数解析 */
const args = process.argv.slice(2);
const EP_DIR = path.resolve(args[0] || '.');
const MODE = args[1] || 'probe';

function numFlag(name, dflt) {
  const i = args.indexOf('--' + name);
  return i >= 0 ? Number(args[i + 1]) : dflt;
}
const FROM = numFlag('from', 0);
const TO = numFlag('to', Infinity);
const FPS = Number(process.env.MEV_FPS || 24);
const W = 1080, H = 1920;

/* 位置参数：probe/cover 模式下剩下的都是时间点 */
const TIMES = args.slice(2).filter(a => !a.startsWith('--') && !isNaN(Number(a))).map(Number);

if (!fs.existsSync(EP_DIR)) {
  console.error('集目录不存在: ' + EP_DIR);
  process.exit(2);
}

/* --------------------------------------------------------------- Chrome 探测
 * 顺序：显式指定 → 项目已下载的 playwright/hyperframes 缓存 → 系统 Chrome/Edge → PATH。
 * 找不到时给出可执行的修复提示，而不是让 puppeteer 抛一句看不懂的错。
 */
function findChrome() {
  const cands = [];
  if (process.env.MEV_CHROME) cands.push(process.env.MEV_CHROME);

  const roots = [
    path.join(process.env.HOME || process.env.USERPROFILE || '', '.cache', 'ms-playwright'),
    path.join(process.env.HOME || process.env.USERPROFILE || '', '.cache', 'hyperframes', 'chrome'),
    path.join(process.env.HOME || process.env.USERPROFILE || '', 'AppData', 'Local', 'ms-playwright'),
  ];
  for (const root of roots) {
    if (!fs.existsSync(root)) continue;
    let dirs = [];
    try { dirs = fs.readdirSync(root); } catch (e) { }
    for (const d of dirs) {
      for (const rel of [
        ['chrome-win64', 'chrome.exe'],
        ['chrome-linux', 'chrome'],
        ['chrome-mac', 'Chromium.app', 'Contents', 'MacOS', 'Chromium'],
        ['chrome-headless-shell-win64', 'chrome-headless-shell.exe'],
        ['chrome-headless-shell-linux64', 'chrome-headless-shell'],
      ]) {
        cands.push(path.join(root, d, ...rel));
      }
    }
  }

  const sys = process.platform === 'win32'
    ? ['C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
       'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
       'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
       'C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe']
    : process.platform === 'darwin'
      ? ['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
         '/Applications/Chromium.app/Contents/MacOS/Chromium']
      : ['/usr/bin/google-chrome', '/usr/bin/chromium', '/usr/bin/chromium-browser'];
  cands.push(...sys);

  for (const c of cands) if (c && fs.existsSync(c)) return c;
  console.error(
    '\n找不到 Chrome / Chromium。三种解决方式（任选其一）：\n' +
    '  1) 装 Google Chrome，或\n' +
    '  2) npx playwright install chromium，然后重跑，或\n' +
    '  3) 设置环境变量 MEV_CHROME=<可执行文件绝对路径>\n'
  );
  process.exit(3);
}

/* --------------------------------------------------------- HTTP 静态文件服务
 * 必须走 http:// 而不是 file://：file:// 下 Chrome 会限制同目录资源加载，
 * 且部分版本的截图行为不一致。
 *
 * 服务根是「项目根」而不是「集目录」，这样集内的 ../engine/engine.js 与
 * ../brand.css 都能正常加载 —— 全项目只保留一份 engine 和一份品牌变量，
 * 避免每集复制一份造成多副本漂移（改了 engine 但某一集没同步是最难查的 bug）。
 */
const ROOT_DIR = path.dirname(EP_DIR);
const EP_SLUG = path.basename(EP_DIR);

function startServer(port) {
  const TYPES = {
    '.html': 'text/html; charset=utf-8', '.js': 'application/javascript; charset=utf-8',
    '.css': 'text/css; charset=utf-8', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
    '.png': 'image/png', '.svg': 'image/svg+xml', '.json': 'application/json',
  };
  const server = http.createServer((req, res) => {
    const rel = decodeURIComponent(req.url.split('?')[0]);
    const fp = path.resolve(ROOT_DIR, rel.replace(/^\/+/, ''));
    if (!fp.startsWith(ROOT_DIR) || !fs.existsSync(fp) || !fs.statSync(fp).isFile()) {
      res.writeHead(404); res.end('not found'); return;
    }
    res.writeHead(200, { 'Content-Type': TYPES[path.extname(fp).toLowerCase()] || 'application/octet-stream' });
    fs.createReadStream(fp).pipe(res);
  });
  return new Promise((ok, fail) => {
    server.once('error', err => fail(err));
    server.listen(port, '127.0.0.1', () => ok(server));
  });
}

/* ------------------------------------------------------------ 启动 headless Chrome
 * 这一段比看起来复杂，因为踩过三个坑：
 *   ① 残留的 chrome 进程会锁住 user-data-dir，新进程启动即退出 —— 所以每次尝试
 *      换一个 profile 目录，而不是复用同一个。
 *   ② chrome-headless-shell 本身就是无头二进制，再传 --headless=new 会被拒绝启动；
 *      完整版 chrome 则必须传 --headless。按文件名区分。
 *   ③ CDP 端口可能被上一次的会话占着（TIME_WAIT 不影响监听，但别的进程会），
 *      所以每次尝试也换端口。
 * 三次都失败才报错，且错误信息里给出可执行的排查方向。
 */
const sleep = ms => new Promise(r => setTimeout(r, ms));

function chromeArgs(chromePath, cdpPort, profile) {
  const isShell = /chrome-headless-shell/i.test(chromePath);
  const headless = isShell ? [] : ['--headless=new'];
  return [
    `--remote-debugging-port=${cdpPort}`,
    `--window-size=${W},${H}`,
    ...headless,
    '--disable-gpu', '--no-sandbox', '--hide-scrollbars',
    '--disable-dev-shm-usage', '--mute-audio', '--force-color-profile=srgb',
    `--user-data-dir=${profile}`,
    '--disable-logging', '--disable-breakpad', '--no-first-run',
  ];
}

async function connectChrome(chromePath, baseProfile, baseCdp) {
  let lastErr = '(无)';
  for (let attempt = 0; attempt < 3; attempt++) {
    const cdpPort = baseCdp + attempt * 11;
    const profile = `${baseProfile}_${attempt}`;
    try { fs.mkdirSync(profile, { recursive: true }); } catch (e) { }

    const proc = spawn(chromePath, chromeArgs(chromePath, cdpPort, profile), { stdio: 'ignore' });
    let died = null;
    proc.on('exit', c => { died = c; });

    for (let i = 0; i < 50; i++) {
      await sleep(300);
      if (died !== null) { lastErr = `Chrome 启动即退出（code ${died}）`; break; }
      try {
        const browser = await puppeteer.connect({
          browserURL: `http://127.0.0.1:${cdpPort}`,
          defaultViewport: { width: W, height: H, deviceScaleFactor: 1 },
          protocolTimeout: 180000,
        });
        console.log(`[cdp] 已连接 端口 ${cdpPort}  profile ${path.basename(profile)}`);
        return { browser, proc };
      } catch (e) {
        lastErr = e.message.split('\n')[0];
      }
    }
    try { proc.kill(); } catch (e) { }
    await sleep(400);
  }
  throw new Error(
    '无法连接 Chrome CDP。最后一次错误：' + lastErr + '\n' +
    '排查：1) 结束残留的 chrome / chrome-headless-shell 进程；' +
    '2) 确认 --user-data-dir 所在目录可写；' +
    '3) 设 MEV_CHROME 指向完整版 Google Chrome 而不是 headless-shell。'
  );
}
async function shoot(client, t) {
  await client.send('Runtime.evaluate', {
    expression: `void window.videoTimeline.seek(${t})`, returnByValue: true,
  });
  const shot = await client.send('Page.captureScreenshot', { format: 'jpeg', quality: 84 });
  return Buffer.from(shot.data, 'base64');
}

async function main() {
  const HTML = fs.existsSync(path.join(EP_DIR, 'standalone.html')) ? 'standalone.html' : null;
  if (!HTML) {
    console.error('找不到 ' + path.join(EP_DIR, 'standalone.html') + '，请先跑 assemble.py');
    process.exit(2);
  }

  /* 从目录名取集号。兼容 `01_标题` 与 `ep01_标题`，统一补成两位。
   * 必须和 mux.py 保持同一规则，否则渲染到 frames_ep1 而合片去读 frames_ep01，
   * 报「找不到帧目录」——这类不一致最难查，所以两边都只认「开头的数字」。 */
  const rawEp = (path.basename(EP_DIR).match(/^(?:ep)?(\d+)/i) || [, '0'])[1];
  const epTag = rawEp.padStart(2, '0');
  const FRAMES = path.join(EP_DIR, 'frames_ep' + epTag);
  const PROBE = path.join(EP_DIR, 'probe_ep' + epTag);
  const chrome = findChrome();
  console.log('[chrome] ' + chrome);

  let port = Number(process.env.MEV_PORT || 8920);
  let cdp = Number(process.env.MEV_CDP || 9466);
  let server;
  for (let i = 0; i < 40; i++) {
    try { server = await startServer(port); break; }
    catch (e) { port++; }
  }
  if (!server) { console.error('找不到可用 HTTP 端口'); process.exit(3); }
  console.log(`[server] http://127.0.0.1:${port}/`);

  let chromeProc, browser;
  try {
    /* 每集独立 profile 目录；重试时再加后缀，避免上一次的锁没释放 */
    const profile = path.join(EP_DIR, 'chrome_tmp_ep' + epTag);
    const conn = await connectChrome(chrome, profile, Number(process.env.MEV_CDP || 9466));
    browser = conn.browser;
    chromeProc = conn.proc;

    const pages = await browser.pages();
    const page = pages.length ? pages[0] : await browser.newPage();
    const client = await page.createCDPSession();
    await client.send('Page.enable');
    await page.goto(`http://127.0.0.1:${port}/${encodeURIComponent(EP_SLUG)}/${HTML}`,
      { waitUntil: 'load', timeout: 60000 });

    /* 等时间轴就绪。engine.js 的 MV.start() 之后 window.videoTimeline 才存在。 */
    let ready = false;
    for (let i = 0; i < 100; i++) {
      const r = await client.send('Runtime.evaluate', {
        expression: 'typeof window.videoTimeline!=="undefined" && window.getDuration()>0',
        returnByValue: true,
      });
      if (r.result.value) { ready = true; break; }
      await new Promise(r => setTimeout(r, 200));
    }
    if (!ready) throw new Error('window.videoTimeline 未就绪：检查场景脚本是否抛错（见下方 console 输出）');

    const duration = (await client.send('Runtime.evaluate', {
      expression: 'window.getDuration()', returnByValue: true,
    })).result.value;
    console.log(`[timeline] duration=${duration.toFixed(2)}s  fps=${FPS}  预计 ${Math.ceil(duration * FPS)} 帧`);

    /* ---------------- probe：抽帧看画面 ---------------- */
    if (MODE === 'probe') {
      fs.mkdirSync(PROBE, { recursive: true });
      for (const t of TIMES) {
        const buf = await shoot(client, t);
        const f = path.join(PROBE, `t${t.toFixed(2).padStart(8, '0')}.jpg`);
        fs.writeFileSync(f, buf);
        console.log('probe -> ' + f);
      }
      console.log('probe 完成：用 Read 工具逐张看图，不要只信代码');
      return;
    }

    /* ---------------- cover：抽封面候选 ----------------
     * 抽封面时先隐藏字幕。
     * 原因：3:4 封面要从 9:16 画面裁出来，而字幕在 y=1430 附近，
     * 3:4 只能保留到 y=1440 —— 字幕会被切掉下半截（实测）。
     * 封面本来就不该带正文字幕，所以直接不画字幕，裁切就不会伤到任何东西。
     */
    if (MODE === 'cover') {
      const t = TIMES[0] || 7.0;
      await client.send('Runtime.evaluate', {
        expression: `(function(){
          void window.videoTimeline.seek(${t});
          var s=document.getElementById('sub'); if(s) s.style.display='none';
        })()`, returnByValue: true,
      });
      fs.writeFileSync(path.join(EP_DIR, 'cover_raw.jpg'),
        await client.send('Page.captureScreenshot', { format: 'jpeg', quality: 92 })
          .then(r => Buffer.from(r.data, 'base64')));
      console.log('cover_raw.jpg saved @ ' + t + 's（已隐藏字幕，1080×1920）');
      return;
    }

    /* ---------------- full：全量渲染 ---------------- */
    if (MODE !== 'full') { console.error('未知模式: ' + MODE); process.exit(2); }

    fs.mkdirSync(FRAMES, { recursive: true });
    const total = Math.ceil(duration * FPS);
    const f0 = Math.max(0, Math.floor(FROM * FPS));
    const f1 = Math.min(total, Math.ceil(TO === Infinity ? total : TO * FPS));
    console.log(`[render] 帧区间 ${f0}..${f1}（共 ${f1 - f0}）`);

    const t0 = Date.now();
    let done = 0, skipped = 0;
    for (let f = f0; f < f1; f++) {
      const outPath = path.join(FRAMES, `frame_${String(f).padStart(6, '0')}.jpg`);
      if (fs.existsSync(outPath) && fs.statSync(outPath).size > 1000) { skipped++; continue; }
      fs.writeFileSync(outPath, await shoot(client, f / FPS));
      done++;
      if (done % 120 === 0) {
        const el = (Date.now() - t0) / 1000;
        const speed = done / el;
        console.log(`  ${done}/${f1 - f0}  ${speed.toFixed(2)} f/s  剩余 ${((f1 - f0 - done) / speed / 60).toFixed(1)} min`);
      }
    }
    console.log(`[render] 完成：新渲 ${done} 帧，跳过已有 ${skipped} 帧，耗时 ${((Date.now() - t0) / 60000).toFixed(1)} min`);

  } catch (e) {
    console.error('RENDER ERROR: ' + (e && e.stack ? e.stack : e));
    process.exitCode = 1;
  } finally {
    if (browser) { try { await browser.disconnect(); } catch (e) { } }
    if (chromeProc) { try { chromeProc.kill(); } catch (e) { } }
    if (server) { try { server.close(); if (server.closeAllConnections) server.closeAllConnections(); } catch (e) { } }
    setTimeout(() => process.exit(process.exitCode || 0), 300);
  }
}

main();

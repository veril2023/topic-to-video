// QC-26 图形-文本重叠门 + 残影文本门（QM-25b 之后新增）
// 补 QC-24 的两个盲点：
//   A) 图形(circle/ellipse/path/polygon/line/image) 与 文本 的 bbox 重叠  -> 红圈压字 / 点阵压字
//   B) 残影文本：把文本 opacity 阈值从 0.35 降到 0.15，抓淡出没退干净的叠字
// 用法: node qc26_overlap.js <ep_html> <port_dbg> <port_http> <outfile> [offset]
const puppeteer = require('puppeteer-core'), http = require('http'), fs = require('fs'), path = require('path');
const { spawn } = require('child_process');

const HTML = process.argv[2];
const PDBG = parseInt(process.argv[3], 10);
const PHTTP = parseInt(process.argv[4], 10);
const OUT = process.argv[5];
const OFFSET = parseFloat(process.argv[6] || '0');   // 与最终 mp4 的时间偏移(帧表起始)

const P = path.dirname(path.resolve(HTML));
function findChrome() {
  // 跨平台 Chrome/Chromium 路径探测
  const home = process.env.USERPROFILE || process.env.HOME || '';
  const cands = [process.env.MEV_CHROME];
  // Windows
  if (process.platform === 'win32') {
    cands.push('C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe');
    cands.push('C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe');
    if (home) cands.push(path.join(home, '.cache', 'hyperframes', 'chrome', 'chrome-headless-shell'));
  }
  // macOS
  if (process.platform === 'darwin') {
    cands.push('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome');
    cands.push('/Applications/Chromium.app/Contents/MacOS/Chromium');
  }
  // Linux
  if (process.platform === 'linux') {
    cands.push('/usr/bin/google-chrome');
    cands.push('/usr/bin/chromium');
    cands.push('/usr/bin/chromium-browser');
  }
  // 通用兜底：扫描 hyperframes 缓存目录（如果存在）
  if (home) {
    const hfBase = path.join(home, '.cache', 'hyperframes', 'chrome');
    try {
      for (const d of fs.readdirSync(hfBase)) {
        cands.push(path.join(hfBase, d, 'chrome-headless-shell-win64', 'chrome-headless-shell.exe'));
        cands.push(path.join(hfBase, d, 'chrome-headless-shell-linux64', 'chrome-headless-shell'));
        cands.push(path.join(hfBase, d, 'chrome-mac', 'Chromium.app', 'Contents', 'MacOS', 'Chromium'));
      }
    } catch (e) { }
  }
  for (const c of cands) if (c && fs.existsSync(c)) return c;
  return 'chrome-headless-shell';
}
const CH = findChrome();
const FPS = 24;

const srv = http.createServer((q, r) => {
  const fp = path.join(P, decodeURIComponent(q.url === '/' ? path.basename(HTML) : q.url.split('?')[0]));
  if (fs.existsSync(fp) && fs.statSync(fp).isFile()) {
    const t = { '.html': 'text/html; charset=utf-8', '.js': 'application/javascript', '.jpg': 'image/jpeg', '.png': 'image/png' };
    r.writeHead(200, { 'Content-Type': t[path.extname(fp)] || 'application/octet-stream' });
    fs.createReadStream(fp).pipe(r);
  } else { r.writeHead(404); r.end('NF'); }
});

const EXPR = `(() => {
  const op = el => { let o = 1, n = el;
    while (n && n.nodeType === 1) { const v = parseFloat(getComputedStyle(n).opacity); if (!isNaN(v)) o *= v; n = n.parentElement; }
    return o; };
  const owner = el => { let n = el; while (n && n.nodeType === 1) { if (n.id) return n.id; n = n.parentElement; } return '?'; };
  const T = [], S = [];
  // ---- 文本 ----
  document.querySelectorAll('div,span,li').forEach(el => {
    if (el.closest('svg') || el.childElementCount > 0) return;
    const tx = (el.textContent || '').trim(); if (!tx) return;
    const o = op(el);
    const rg = document.createRange(); rg.selectNodeContents(el);
    for (const r of rg.getClientRects()) {
      if (r.width < 8 || r.height < 8) continue;
      T.push({ id: owner(el), kind:'t', o:+o.toFixed(3), txt: tx.slice(0,20),
               b:[Math.round(r.left),Math.round(r.top),Math.round(r.right),Math.round(r.bottom)] });
    }
  });
  document.querySelectorAll('svg text').forEach(el => {
    const o = op(el); const r = el.getBoundingClientRect();
    if (r.width < 8 || r.height < 8) return;
    T.push({ id: owner(el), kind:'t', o:+o.toFixed(3), txt:(el.textContent||'').trim().slice(0,20),
             b:[Math.round(r.left),Math.round(r.top),Math.round(r.right),Math.round(r.bottom)] });
  });
  // ---- 图形（rect 单独走“边线穿越”判据；其余走 bbox 面积）----
  document.querySelectorAll('svg circle, svg ellipse, svg polygon, svg polyline, svg image, svg path, svg line, svg rect').forEach(el => {
    const o = op(el); if (o < 0.30) return;
    const cs = getComputedStyle(el);
    const isRect = el.tagName.toLowerCase() === 'rect';
    const fa = parseFloat(cs.fillOpacity || '1') * (cs.fill === 'none' ? 0 : 1);
    const sa = parseFloat(cs.strokeOpacity || '1') * (cs.stroke === 'none' ? 0 : 1);
    if (fa <= 0 && sa <= 0) return;
    if (isRect && sa <= 0) return;   // 无描边的矩形撑不出“线压字”，其填充区属背景板
    const r = el.getBoundingClientRect();
    if (r.width < 10 || r.height < 10) return;
    if (r.width * r.height > 900000) return;   // 整幅底图不算
    S.push({ id: owner(el), kind:'s', tag: el.tagName, o:+o.toFixed(3),
             isRect: isRect ? 1 : 0, sw: parseFloat(cs.strokeWidth) || 2,
             fill: fa > 0.25 ? 1 : 0, stroke: sa > 0.25 ? 1 : 0,
             b:[Math.round(r.left),Math.round(r.top),Math.round(r.right),Math.round(r.bottom)] });
  });
  return JSON.stringify({ T: T, S: S });
})()`;

/* rect 专用：只有 4 条边线会压字（填充区是背景色，不算）。
   判定要点——线的位置必须落在文字 bbox 内部（左右/上下各留 15% 边距），
   否则“框线紧贴文字顶边但没穿过”会被误判成 100% 穿透（ep04 罗马数字格实测过这个假阳性）。
   竖线：覆盖文字高度 >=50%；横线：覆盖文字宽度 >=50%。 */
function rectEdgeHit(rb, tb, sw) {
  const t = Math.max(1.5, (parseFloat(sw) || 2) / 2);
  const th = tb[3] - tb[1], tw = tb[2] - tb[0];
  for (const lx of [rb[0], rb[2]]) {
    if (lx > tb[0] + tw * 0.15 && lx < tb[2] - tw * 0.15) {
      const h = Math.min(rb[3], tb[3]) - Math.max(rb[1], tb[1]);
      if (h >= th * 0.5) return { r: h / th, k: 'v' };
    }
  }
  for (const ly of [rb[1], rb[3]]) {
    if (ly > tb[1] + th * 0.15 && ly < tb[3] - th * 0.15) {
      const w = Math.min(rb[2], tb[2]) - Math.max(rb[0], tb[0]);
      if (w >= tw * 0.5) return { r: w / tw, k: 'h' };
    }
  }
  return null;
}

function inter(a, b) {
  const w = Math.min(a[2], b[2]) - Math.max(a[0], b[0]);
  const h = Math.min(a[3], b[3]) - Math.max(a[1], b[1]);
  return w > 0 && h > 0 ? w * h : 0;
}
const area = b => (b[2] - b[0]) * (b[3] - b[1]);

async function main() {
  let chromeProc = null, browser = null;
  const lines = [];
  try {
    await new Promise(r => srv.listen(PHTTP, '127.0.0.1', r));
    chromeProc = spawn(CH, ['--remote-debugging-port=' + PDBG, '--window-size=1080,1920', '--headless', '--disable-gpu',
      '--no-sandbox', '--hide-scrollbars', '--disable-dev-shm-usage', '--mute-audio',
      '--user-data-dir=' + path.join(P, 'chrome_tmp_qc26_' + PDBG), '--no-first-run'], { stdio: 'ignore' });
    await new Promise(r => setTimeout(r, 4000));
    browser = await puppeteer.connect({ browserURL: 'http://127.0.0.1:' + PDBG, defaultViewport: { width: 1080, height: 1920, deviceScaleFactor: 1 }, protocolTimeout: 240000 });
    const pgs = await browser.pages();
    const pg = pgs.length ? pgs[0] : await browser.newPage();
    const c = await pg.createCDPSession(); await c.send('Page.enable');
    pg.on('pageerror', e => console.log('  PAGE ERR', e.message));
    await c.send('Page.navigate', { url: 'http://127.0.0.1:' + PHTTP + '/' + path.basename(HTML) });
    for (let i = 0; i < 80; i++) {
      const o = await c.send('Runtime.evaluate', { expression: 'typeof window.videoTimeline!=="undefined"', returnByValue: true });
      if (o.result.value) break;
      await new Promise(r => setTimeout(r, 500));
    }
    const dur = (await c.send('Runtime.evaluate', { expression: 'window.getDuration()', returnByValue: true })).result.value;
    const N = Math.ceil(dur * FPS) + 1;
    const aggG = new Map();   // 图形×文本
    const aggT = new Map();   // 文本×文本(残影)
    for (let i = 0; i < N; i++) {
      const t = i / FPS + OFFSET;
      await c.send('Runtime.evaluate', { expression: `void(window.videoTimeline.seek(${i / FPS}))`, returnByValue: true });
      const r = await c.send('Runtime.evaluate', { expression: EXPR, returnByValue: true });
      const D = JSON.parse(r.result.value);
      // A) 图形 × 文本
      for (const s of D.S) for (const x of D.T) {
        if (Math.min(s.o, x.o) < 0.40) continue;
        let ratio, ktag;
        if (s.isRect) {
          const hit = rectEdgeHit(s.b, x.b, s.sw);
          if (!hit) continue;
          ratio = hit.r; ktag = '-edge' + hit.k;
        } else {
          const I = inter(s.b, x.b); if (!I) continue;
          ratio = I / Math.min(area(s.b), area(x.b));
          if (ratio < 0.30) continue;
          ktag = '';
        }
        // 描边类（含 rect 边线）且文字很实 -> 降级为 WARN；有填充且压字 -> FAIL
        const lvl = (!s.isRect && s.fill && x.o >= 0.55) ? 'FAIL' : 'WARN';
        const key = lvl + '|' + s.id + ':' + s.tag + ktag + ' × ' + x.id + '|' + x.txt;
        if (!aggG.has(key)) aggG.set(key, { n: 0, t0: t, t1: t, worst: 0, sa: s.b, sb: x.b, lvl });
        const g = aggG.get(key); g.n++; g.t1 = t;
        if (ratio > g.worst) { g.worst = ratio; g.sa = s.b; g.sb = x.b; }
      }
      // B) 文本 × 文本（残影档，阈值 0.15）
      for (let a = 0; a < D.T.length; a++) for (let b = a + 1; b < D.T.length; b++) {
        const A = D.T[a], B = D.T[b];
        if (A.id === B.id) continue;
        if (Math.min(A.o, B.o) < 0.15) continue;
        const I = inter(A.b, B.b); if (!I) continue;
        const ratio = I / Math.min(area(A.b), area(B.b));
        if (ratio < 0.25) continue;
        const lvl = Math.min(A.o, B.o) < 0.35 ? 'GHOST' : 'FAIL';
        const key = lvl + '|' + A.id + '|' + A.txt + ' × ' + B.id + '|' + B.txt;
        if (!aggT.has(key)) aggT.set(key, { n: 0, t0: t, t1: t, worst: 0, sa: A.b, sb: B.b, lvl, oa: A.o, ob: B.o });
        const g = aggT.get(key); g.n++; g.t1 = t; g.oa = Math.min(g.oa, A.o); g.ob = Math.min(g.ob, B.o);
        if (ratio > g.worst) { g.worst = ratio; g.sa = A.b; g.sb = B.b; }
      }
      if (i % 480 === 0) console.log(`  ...${i}/${N}  shape×text=${aggG.size} text×text=${aggT.size}`);
    }
    lines.push('='.repeat(76));
    lines.push('QC-26 图形-文本重叠门 + 残影文本门   ' + path.basename(HTML));
    lines.push('扫 ' + N + ' 帧 @24fps   （A: shape×text  >=30% & 双方op>=0.40）');
    lines.push('                    （A-rect: 矩形边线沿字高/字宽穿透 >=55%）');
    lines.push('                    （B: text×text  >=25% & min(op)>=0.15）');
    lines.push('='.repeat(76));
    lines.push('');
    lines.push('### A 图形 × 文本  共 ' + aggG.size + ' 对');
    for (const [k, g] of [...aggG.entries()].sort((x, y) => y[1].n - x[1].n)) {
      lines.push(`  [${g.lvl}] ${g.n}帧 t=${g.t0.toFixed(2)}..${g.t1.toFixed(2)} max=${(g.worst * 100).toFixed(0)}%`);
      lines.push(`      ${k}`);
      lines.push(`      S=${JSON.stringify(g.sa)}  T=${JSON.stringify(g.sb)}`);
    }
    if (!aggG.size) lines.push('  (无)');
    lines.push('');
    lines.push('### B 文本 × 文本(含残影)  共 ' + aggT.size + ' 对');
    for (const [k, g] of [...aggT.entries()].sort((x, y) => y[1].n - x[1].n)) {
      lines.push(`  [${g.lvl}] ${g.n}帧 t=${g.t0.toFixed(2)}..${g.t1.toFixed(2)} max=${(g.worst * 100).toFixed(0)}% minOp=${g.oa.toFixed(2)}`);
      lines.push(`      ${k}`);
      lines.push(`      A=${JSON.stringify(g.sa)}  B=${JSON.stringify(g.sb)}`);
    }
    if (!aggT.size) lines.push('  (无)');
    const out = lines.join('\n');
    fs.writeFileSync(OUT, out, 'utf-8');
    console.log('\n' + out);
  } catch (e) { console.error('ERR:', e && e.stack ? e.stack : e); }
  finally {
    if (browser) try { await browser.disconnect(); } catch (e) {}
    if (chromeProc) try { chromeProc.kill(); } catch (e) {}
    srv.close(); if (srv.closeAllConnections) srv.closeAllConnections();
    setTimeout(() => process.exit(0), 300);
  }
}
main();

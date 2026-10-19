// render_xhs_palette.js — 《万物有数》ep01 小红书图文 · 鲜艳底色多方案
// 用法：PAL=teal|terra|saffron OUT=目录 LIMIT=n node render_xhs_palette.js
// 结构完全沿用 v3（博物馆图录骨架 + 品牌区），只换色彩基底
const puppeteer = require('puppeteer-core');
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');

// 跨平台 Chrome/Chromium 路径探测
function findChrome() {
  const home = process.env.USERPROFILE || process.env.HOME || '';
  const cands = [process.env.MEV_CHROME];
  if (process.platform === 'win32') {
    cands.push('C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe');
    cands.push('C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe');
  } else if (process.platform === 'darwin') {
    cands.push('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome');
    cands.push('/Applications/Chromium.app/Contents/MacOS/Chromium');
  } else {
    cands.push('/usr/bin/google-chrome');
    cands.push('/usr/bin/chromium');
    cands.push('/usr/bin/chromium-browser');
  }
  if (home) {
    const hfBase = path.join(home, '.cache', 'hyperframes', 'chrome');
    try {
      for (const d of fs.readdirSync(hfBase)) {
        cands.push(path.join(hfBase, d, 'chrome-headless-shell-win64', 'chrome-headless-shell.exe'));
        cands.push(path.join(hfBase, d, 'chrome-headless-shell-linux64', 'chrome-headless-shell'));
      }
    } catch (e) { }
  }
  for (const c of cands) if (c && fs.existsSync(c)) return c;
  return 'chrome-headless-shell';
}
const CHROME_PATH = findChrome();
const CDP_PORT = 9499;

/* ── 默认色（SVG 图形生成时用，随后按方案整体置换）── */
const AMBER = '#E8A33D';
const BONE = '#EDE3D2';
const DIM = '#7D8797';
const BG = '#121821';
const H = 560;

/* ═══ 配色方案 ═══
   teal   · 孔雀青：饱和的深青绿，金色刻痕在青底上极跳
   terra  · 赭红陶土：朱砂到赭石，最贴古文明气质
   saffron· 明黄：真正明亮的底色 + 深褐墨字（浅底方案）
*/
const PALETTES = {
  teal: {
    id: 'teal', name: '孔雀青',
    amber: '#F0B44A', amberRgb: '240,180,74',
    bone: '#F1EDE2', boneRgb: '241,237,226',
    dim: '#8FC0BA',
    artBg: '#075B52',
    layers: [
      'radial-gradient(ellipse 900px 620px at 50% 38%, rgba(20,190,172,.34) 0%, rgba(20,190,172,0) 62%)',
      'radial-gradient(ellipse 1000px 540px at 50% -10%, rgba(240,180,74,.17) 0%, rgba(240,180,74,0) 56%)',
      'radial-gradient(ellipse 720px 520px at 88% 112%, rgba(8,120,110,.55) 0%, rgba(8,120,110,0) 62%)',
      'linear-gradient(166deg,#032322 0%,#075049 34%,#0B6E62 62%,#032322 100%)',
    ],
    beam: 'linear-gradient(126deg, rgba(255,235,190,.09) 0%, rgba(255,235,190,.02) 26%, rgba(255,235,190,0) 44%)',
    vig: 'radial-gradient(ellipse 1120px 940px at 50% 46%, rgba(0,0,0,0) 42%, rgba(0,20,18,.52) 100%)',
    frame1: 'rgba(247,222,170,.26)', frame2: 'rgba(247,222,170,.09)', tick: 'rgba(247,222,170,.55)',
    ink: '#F4F1E7', cap: '#B6D6D0',
    meta: '#9DC4BE', pg: '#7FB0AA', botSl: '#7FAEA9', botB: '#A9CCC6',
    hr: 'rgba(240,180,74,0) 0%, rgba(240,180,74,.30) 10%, #F0B44A 44%, #FBE7BE 50%, #F0B44A 56%, rgba(240,180,74,.30) 90%, rgba(240,180,74,0) 100%',
    grayMap: {
      '#2C333F': '#0A3D39', '#1B212B': '#072A27', '#141A23': '#051E1C',
      '#8E5A2A': '#0D675C',
      '#5C6675': '#6E9E97',
      '#4B5563': '#4E857E', '#8A94A4': '#7FAEA9',
    },
  },
  terra: {
    id: 'terra', name: '赭红陶土',
    amber: '#F5BE52', amberRgb: '245,190,82',
    bone: '#F6E6CC', boneRgb: '246,230,204',
    dim: '#C9977A',
    artBg: '#8A2B12',
    layers: [
      'radial-gradient(ellipse 900px 620px at 50% 38%, rgba(234,110,20,.38) 0%, rgba(234,110,20,0) 62%)',
      'radial-gradient(ellipse 1000px 540px at 50% -10%, rgba(251,191,36,.20) 0%, rgba(251,191,36,0) 56%)',
      'radial-gradient(ellipse 720px 520px at 88% 112%, rgba(146,36,12,.60) 0%, rgba(146,36,12,0) 62%)',
      'linear-gradient(166deg,#280A04 0%,#5C1B0B 34%,#8C2D12 62%,#280A04 100%)',
    ],
    beam: 'linear-gradient(126deg, rgba(255,214,150,.10) 0%, rgba(255,214,150,.025) 26%, rgba(255,214,150,0) 44%)',
    vig: 'radial-gradient(ellipse 1120px 940px at 50% 46%, rgba(0,0,0,0) 42%, rgba(40,8,2,.55) 100%)',
    frame1: 'rgba(255,208,150,.28)', frame2: 'rgba(255,208,150,.10)', tick: 'rgba(255,208,150,.58)',
    ink: '#FCEFDC', cap: '#E0B79A',
    meta: '#DCB093', pg: '#C68F6B', botSl: '#C9987A', botB: '#E0B698',
    hr: 'rgba(245,190,82,0) 0%, rgba(245,190,82,.30) 10%, #F5BE52 44%, #FFE3AE 50%, #F5BE52 56%, rgba(245,190,82,.30) 90%, rgba(245,190,82,0) 100%',
    grayMap: {
      '#2C333F': '#611D0D', '#1B212B': '#481309', '#141A23': '#360F07',
      '#8E5A2A': '#38110A', '#4B5563': '#A96A4C', '#8A94A4': '#C79A80',
    },
  },
  saffron: {
    id: 'saffron', name: '明黄',
    amber: '#7A3C06', amberRgb: '122,60,6',
    bone: '#2C1907', boneRgb: '44,25,7',
    dim: '#8A6033',
    artBg: '#F1BB54',
    layers: [
      'radial-gradient(ellipse 900px 620px at 50% 38%, rgba(255,228,158,.90) 0%, rgba(255,228,158,0) 62%)',
      'radial-gradient(ellipse 1000px 540px at 50% -10%, rgba(255,255,255,.55) 0%, rgba(255,255,255,0) 55%)',
      'linear-gradient(166deg,#E8A138 0%,#F4BE4C 34%,#F7CB63 62%,#E8A138 100%)',
    ],
    beam: 'linear-gradient(126deg, rgba(255,255,255,.16) 0%, rgba(255,255,255,.05) 26%, rgba(255,255,255,0) 44%)',
    vig: 'radial-gradient(ellipse 1120px 940px at 50% 46%, rgba(0,0,0,0) 44%, rgba(120,64,8,.28) 100%)',
    frame1: 'rgba(92,52,10,.32)', frame2: 'rgba(92,52,10,.13)', tick: 'rgba(92,52,10,.48)',
    ink: '#2C1907', cap: '#6B4520',
    meta: '#7A5320', pg: '#96682E', botSl: '#8A6031', botB: '#6B4620',
    hr: 'rgba(122,60,6,0) 0%, rgba(122,60,6,.35) 10%, #7A3C06 44%, #B4781F 50%, #7A3C06 56%, rgba(122,60,6,.35) 90%, rgba(122,60,6,0) 100%',
    grayMap: {
      '#4B5563': '#A0703A', '#5C6675': '#9C7038', '#8A94A4': '#8A6033',
      'rgba(255,255,255,0.035)': 'rgba(92,52,10,0.07)',
      'rgba(255,255,255,0.02)': 'rgba(92,52,10,0.05)',
      'rgba(0,0,0,0.42)': 'rgba(92,52,10,0.30)',
    },
  },
};

const P = PALETTES[process.env.PAL || 'teal'];
const OUT_DIR = path.join(__dirname, process.env.OUT || P.id);
const LIMIT = Number(process.env.LIMIT || 99);

/* ── Logo：断口圆环（印章）+ 行星点（宇宙）+ 三根刻痕柱（伊尚戈骨）── */
function logoMark(size, uid) {
  return `<svg width="${size}" height="${size}" viewBox="0 0 64 64" fill="none">
  <defs><linearGradient id="lg${uid}" gradientUnits="userSpaceOnUse" x1="10" y1="6" x2="54" y2="58">
    <stop offset="0%" stop-color="#FBE7BE"/><stop offset="44%" stop-color="#E8A33D"/><stop offset="100%" stop-color="#B5762A"/>
  </linearGradient></defs>
  <circle cx="32" cy="32" r="25.4" fill="rgba(232,163,61,0.10)"/>
  <path d="M48.6 8.2 A29 29 0 1 1 15.4 8.2" stroke="url(#lg${uid})" stroke-width="2.6" stroke-linecap="round"/>
  <circle cx="32" cy="5.8" r="3.9" fill="url(#lg${uid})"/>
  <line x1="22.8" y1="22.8" x2="22.8" y2="43.2" stroke="url(#lg${uid})" stroke-width="3.4" stroke-linecap="round"/>
  <line x1="32"   y1="16.6" x2="32"   y2="48.2" stroke="url(#lg${uid})" stroke-width="3.4" stroke-linecap="round"/>
  <line x1="41.2" y1="20.2" x2="41.2" y2="45.8" stroke="url(#lg${uid})" stroke-width="3.4" stroke-linecap="round"/>
</svg>`;
}

const GRAIN = "data:image/svg+xml;charset=utf-8,%3Csvg xmlns='http://www.w3.org/2000/svg' width='180' height='180'%3E%3Cfilter id='g'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.82' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='180' height='180' filter='url(%23g)' opacity='0.9'/%3E%3C/svg%3E";

const CSS = `
* { margin:0; padding:0; box-sizing:border-box; }
html, body { width:1080px; height:1440px; overflow:hidden; }
body { background:#080B0F; color:${BONE}; position:relative;
  font-family:"Noto Sans SC","Microsoft YaHei",Arial,sans-serif;
  -webkit-font-smoothing:antialiased; }

.bg-base { position:absolute; inset:0; background:${P.layers.join(',\n    ')}; }
.bg-beam { position:absolute; inset:0; background:${P.beam}; }
.bg-vig { position:absolute; inset:0; background:${P.vig}; }
.grain { position:absolute; inset:0; opacity:.075; mix-blend-mode:overlay;
  background-image:url("${GRAIN}"); background-size:180px 180px; }

.frame { position:absolute; inset:34px; border:1px solid ${P.frame1}; }
.frame::after { content:''; position:absolute; inset:9px; border:1px solid ${P.frame2}; }
.tick { position:absolute; width:19px; height:19px; border:0 solid ${P.tick}; }
.tick.tl { top:20px; left:20px; border-top-width:1px; border-left-width:1px; }
.tick.tr { top:20px; right:20px; border-top-width:1px; border-right-width:1px; }
.tick.bl { bottom:20px; left:20px; border-bottom-width:1px; border-left-width:1px; }
.tick.br { bottom:20px; right:20px; border-bottom-width:1px; border-right-width:1px; }

.page { position:relative; z-index:3; width:100%; height:100%;
  padding:56px 78px 50px; display:flex; flex-direction:column; }

.brandrow { flex:0 0 92px; display:flex; justify-content:space-between; align-items:center; }
.brand { display:flex; align-items:center; gap:17px; }
.mark { display:block; width:68px; height:68px; }
.btext { display:flex; flex-direction:column; gap:10px; }
.wname { font-family:"Noto Serif SC",serif; font-size:47px; font-weight:700;
  letter-spacing:.24em; color:${P.ink}; line-height:1; }
.wslog { font-size:12.5px; font-weight:300; letter-spacing:.30em;
  color:${P.amber}; opacity:.92; line-height:1; }
.meta { display:flex; flex-direction:column; align-items:flex-end; gap:11px; }
.ep { font-size:17.5px; letter-spacing:.10em; color:${P.meta}; font-weight:300; }
.ep i { font-family:Georgia,serif; font-style:normal; font-size:16.5px;
  letter-spacing:.15em; color:${P.amber}; }
.pg { font-family:Georgia,serif; font-size:16.5px; letter-spacing:.2em; color:${P.pg}; }

.hr { flex:0 0 1px; margin-top:26px; background:linear-gradient(90deg, ${P.hr}); }

.title { flex:0 0 300px; margin-top:34px; font-family:"Noto Serif SC",serif;
  font-size:60px; line-height:1.52; font-weight:500; letter-spacing:.02em; color:${P.ink}; }
.title b { color:${P.amber}; font-weight:700; }
.title .num { font-family:Georgia,serif; font-weight:700; font-size:1.05em; color:${P.amber}; }

.art { flex:1 1 auto; display:flex; align-items:center; justify-content:center; min-height:0; }
.art svg { width:100%; height:auto; max-height:100%; display:block; }

.cap { flex:0 0 auto; display:flex; gap:18px; align-items:center; padding-top:24px; }
.cap .dash { flex:0 0 42px; height:1px; background:${P.amber}; opacity:.75; }
.cap p { font-size:26px; font-weight:300; line-height:1.5; color:${P.cap}; letter-spacing:.03em; }
.cap p em { color:${P.amber}; font-style:normal; }

.bot { flex:0 0 auto; display:flex; justify-content:space-between; align-items:center;
  margin-top:24px; padding-top:20px; border-top:1px solid ${P.frame2}; }
.bot .sl { font-size:12.5px; letter-spacing:.30em; color:${P.botSl}; font-weight:300; }
.bmark { display:flex; align-items:center; gap:9px; }
.bmark b { font-family:"Noto Serif SC",serif; font-size:14.5px; font-weight:600;
  letter-spacing:.26em; color:${P.botB}; }

.qmark { display:block; font-size:104px; line-height:1.05; color:${P.amber}; font-weight:400; letter-spacing:0; }
.qbody { display:block; font-size:46px; line-height:1.62; letter-spacing:.03em; }
`;

/* ── 整页色彩置换：SVG 图形与 logo 一律按方案换色 ── */
function recolor(h) {
  let s = h.split('#E8A33D').join(P.amber);
  s = s.split('232,163,61').join(P.amberRgb);
  s = s.split('#EDE3D2').join(P.bone);
  s = s.split('237,227,210').join(P.boneRgb);
  s = s.split('#7D8797').join(P.dim);
  s = s.split('#121821').join(P.artBg);
  for (const [k, v] of Object.entries(P.grayMap)) s = s.split(k).join(v);
  return s;
}

const svgOpen = () => `<svg viewBox="0 0 880 ${H}" xmlns="http://www.w3.org/2000/svg">`;
const svgClose = () => `</svg>`;
const DEFS = `<defs>
  <marker id="ah" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto">
    <path d="M0,0 L7,3 L0,6" fill="none" stroke="${AMBER}" stroke-opacity="0.8" stroke-width="1.5"/>
  </marker>
</defs>`;

function tallyColumn(x, w, n, top, h, groups = 1) {
  const gap = groups > 1 ? 22 : 0;
  const gh = (h - gap * (groups - 1)) / groups;
  const per = n / groups;
  const step = per > 1 ? gh / (per - 1) : 0;
  let out = '';
  for (let g = 0; g < groups; g++) {
    const gy = top + g * (gh + gap);
    for (let i = 0; i < per; i++) {
      const y = gy + i * step;
      out += `<line x1="${x}" y1="${y.toFixed(1)}" x2="${x + w}" y2="${y.toFixed(1)}" stroke="${AMBER}" stroke-opacity="0.66" stroke-width="2" stroke-linecap="round"/>`;
    }
  }
  return out;
}

function sheep(cx, cy, s = 1, dim = false) {
  const op = dim ? 0.30 : 0.80;
  return `<g transform="translate(${cx},${cy}) scale(${s})">
    <ellipse cx="0" cy="0" rx="58" ry="35" fill="rgba(237,227,210,0.06)" stroke="${BONE}" stroke-opacity="${op}" stroke-width="2.2"/>
    <ellipse cx="64" cy="-14" rx="23" ry="19" fill="rgba(237,227,210,0.08)" stroke="${BONE}" stroke-opacity="${op}" stroke-width="2.2"/>
    <ellipse cx="58" cy="-33" rx="11" ry="6" transform="rotate(-28 58 -33)" fill="rgba(237,227,210,0.08)" stroke="${BONE}" stroke-opacity="${op}" stroke-width="2"/>
    <circle cx="73" cy="-17" r="2.8" fill="${AMBER}" fill-opacity="${dim ? 0.3 : 1}"/>
    <path d="M -38,30 v32 M -14,33 v29 M 12,33 v29 M 36,30 v32" stroke="${BONE}" stroke-opacity="${op * 0.85}" stroke-width="2.2" stroke-linecap="round"/>
  </g>`;
}

function stone(cx, cy, r = 25, dashed = false) {
  if (dashed) return `<ellipse cx="${cx}" cy="${cy}" rx="${r + 6}" ry="${r - 2}" fill="none" stroke="${AMBER}" stroke-opacity="0.5" stroke-width="2" stroke-dasharray="6 7"/>`;
  return `<ellipse cx="${cx}" cy="${cy}" rx="${r + 6}" ry="${r - 2}" fill="rgba(232,163,61,0.13)" stroke="${AMBER}" stroke-opacity="0.88" stroke-width="2.2"/>`;
}

const slides = [];

/* ── 01 封面 · 168 道真实刻痕 ── */
slides.push({
  idx: 1,
  title: `两万年前<br>有人在这根骨头上<br>刻了 <b class="num">168</b> 道痕`,
  art: (() => {
    const cols = [{ x: 148, n: 48, g: 3 }, { x: 388, n: 60, g: 4 }, { x: 628, n: 60, g: 4 }];
    const top = 34, h = 364, w = 112;
    let s = svgOpen() + DEFS;
    s += `<defs><linearGradient id="boneG" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#2C333F"/><stop offset="52%" stop-color="#1B212B"/><stop offset="100%" stop-color="#141A23"/>
    </linearGradient></defs>`;
    cols.forEach((c) => {
      s += `<rect x="${c.x}" y="${top - 26}" width="${w}" height="${h + 52}" rx="56"
              fill="url(#boneG)" stroke="${AMBER}" stroke-opacity="0.32" stroke-width="2"/>`;
      s += tallyColumn(c.x + 14, w - 28, c.n, top, h, c.g);
      s += `<text x="${c.x + w / 2}" y="${top + h + 72}" text-anchor="middle"
              font-family="Georgia, serif" font-size="44" fill="${AMBER}">${c.n}</text>`;
    });
    s += `<line x1="148" y1="${top + h + 106}" x2="740" y2="${top + h + 106}" stroke="${AMBER}" stroke-opacity="0.22" stroke-width="1.5"/>`;
    s += `<text x="444" y="${top + h + 152}" text-anchor="middle" font-size="26" letter-spacing="7" fill="${DIM}">三 列 · 共 168 道</text>`;
    return s + svgClose();
  })(),
  cap: `比最早的账本，早了一万五千年。它在<em>记什么</em>？`,
});

/* ── 02 时间轴 ── */
slides.push({
  idx: 2,
  title: `然后人类<br>又等了一万五千年<br>才发明文字`,
  art: (() => {
    const x0 = 66, x1 = 812, y = 240;
    const boneX = x0 + 34;
    const textX = x0 + (x1 - x0) * 0.735;
    let s = svgOpen() + DEFS;
    s += `<line x1="${x0}" y1="${y}" x2="${x1}" y2="${y}" stroke="#4B5563" stroke-width="2"/>`;
    s += `<line x1="${boneX}" y1="${y}" x2="${textX}" y2="${y}" stroke="${AMBER}" stroke-opacity="0.55" stroke-width="6" stroke-linecap="round"/>`;
    s += `<circle cx="${boneX}" cy="${y}" r="13" fill="${AMBER}"/>`;
    s += `<circle cx="${boneX}" cy="${y}" r="27" fill="none" stroke="${AMBER}" stroke-opacity="0.32" stroke-width="1.6"/>`;
    s += `<text x="${boneX}" y="${y - 92}" text-anchor="middle" font-family="Georgia, serif" font-size="40" fill="${BONE}">-20,000</text>`;
    s += `<text x="${boneX}" y="${y - 54}" text-anchor="middle" font-size="23" letter-spacing="5" fill="${AMBER}">骨 痕</text>`;
    s += `<rect x="${textX - 16}" y="${y - 16}" width="32" height="32" fill="${BG}" stroke="${BONE}" stroke-opacity="0.92" stroke-width="2.4"/>`;
    s += `<line x1="${textX - 7}" y1="${y + 7}" x2="${textX + 7}" y2="${y - 7}" stroke="${BONE}" stroke-opacity="0.92" stroke-width="2.4"/>`;
    s += `<text x="${textX}" y="${y - 92}" text-anchor="middle" font-family="Georgia, serif" font-size="40" fill="${BONE}">-5,300</text>`;
    s += `<text x="${textX}" y="${y - 54}" text-anchor="middle" font-size="23" letter-spacing="5" fill="${BONE}" fill-opacity="0.85">文 字</text>`;
    const midY = y + 104;
    s += `<path d="M ${boneX} ${y + 36} L ${boneX} ${midY} L ${textX} ${midY} L ${textX} ${y + 36}"
            fill="none" stroke="${AMBER}" stroke-opacity="0.42" stroke-width="1.6"/>`;
    s += `<text x="${(boneX + textX) / 2}" y="${midY + 54}" text-anchor="middle"
            font-family="Georgia, serif" font-size="42" fill="${AMBER}">15,000</text>`;
    s += `<text x="${(boneX + textX) / 2}" y="${midY + 96}" text-anchor="middle"
            font-size="23" letter-spacing="7" fill="${DIM}">年 的 空 白</text>`;
    s += `<line x1="${x1}" y1="${y - 8}" x2="${x1}" y2="${y + 8}" stroke="#5C6675" stroke-width="2"/>`;
    s += `<text x="${x1}" y="${y + 40}" text-anchor="middle" font-size="21" letter-spacing="3" fill="#5C6675">今 天</text>`;
    return s + svgClose();
  })(),
  cap: `刻痕之后，人类沉默了整整一万五千年。`,
});

/* ── 03 陶筹困局 ── */
slides.push({
  idx: 3,
  title: `一袋大麦<br>加一只羊<br>等于什么？`,
  art: (() => {
    let s = svgOpen() + DEFS;
    s += `<defs>
      <linearGradient id="cone" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="rgba(232,163,61,0.32)"/><stop offset="100%" stop-color="rgba(232,163,61,0.06)"/>
      </linearGradient>
      <radialGradient id="ball" cx="32%" cy="28%">
        <stop offset="0%" stop-color="rgba(232,163,61,0.40)"/><stop offset="62%" stop-color="rgba(232,163,61,0.11)"/><stop offset="100%" stop-color="rgba(232,163,61,0.03)"/>
      </radialGradient>
    </defs>`;
    s += `<path d="M 208 74 L 296 350 L 120 350 Z" fill="url(#cone)" stroke="${AMBER}" stroke-opacity="0.92" stroke-width="2.6" stroke-linejoin="round"/>`;
    s += `<ellipse cx="208" cy="350" rx="88" ry="16" fill="none" stroke="${AMBER}" stroke-opacity="0.55" stroke-width="2"/>`;
    s += `<circle cx="440" cy="212" r="54" fill="none" stroke="${AMBER}" stroke-opacity="0.40" stroke-width="2"/>`;
    s += `<line x1="440" y1="182" x2="440" y2="242" stroke="${AMBER}" stroke-width="3.4" stroke-linecap="round"/>`;
    s += `<line x1="410" y1="212" x2="470" y2="212" stroke="${AMBER}" stroke-width="3.4" stroke-linecap="round"/>`;
    s += `<circle cx="672" cy="212" r="100" fill="url(#ball)" stroke="${AMBER}" stroke-opacity="0.92" stroke-width="2.6"/>`;
    s += `<text x="208" y="410" text-anchor="middle" font-size="26" letter-spacing="4" fill="${BONE}" fill-opacity="0.88">一 袋 大 麦</text>`;
    s += `<text x="672" y="410" text-anchor="middle" font-size="26" letter-spacing="4" fill="${BONE}" fill-opacity="0.88">一 只 羊</text>`;
    s += `<line x1="336" y1="446" x2="548" y2="446" stroke="${AMBER}" stroke-opacity="0.52" stroke-width="3"/>`;
    s += `<line x1="336" y1="476" x2="548" y2="476" stroke="${AMBER}" stroke-opacity="0.52" stroke-width="3"/>`;
    s += `<text x="440" y="556" text-anchor="middle" font-family="Georgia, serif" font-size="104" fill="${AMBER}" fill-opacity="0.92">?</text>`;
    return s + svgClose();
  })(),
  cap: `圆锥加圆球，不是五个什么——这是麻烦的起点。`,
});

/* ── 04 羊与石子 ── */
slides.push({
  idx: 4,
  title: `你数的<br>不是羊`,
  art: (() => {
    const ys = 148, yt = 378;
    const xs = [146, 356, 566];
    const xEmpty = 762;
    let s = svgOpen() + DEFS;
    xs.forEach((x) => {
      s += `<line x1="${x}" y1="${ys + 66}" x2="${x}" y2="${yt - 34}" stroke="${AMBER}"
              stroke-opacity="0.42" stroke-width="2" stroke-dasharray="4 7"/>`;
      s += sheep(x, ys, 0.76);
      s += stone(x, yt, 23);
    });
    s += sheep(xEmpty, ys, 0.76, true);
    s += `<line x1="${xEmpty}" y1="${ys + 66}" x2="${xEmpty}" y2="${yt - 34}" stroke="${AMBER}"
            stroke-opacity="0.28" stroke-width="2" stroke-dasharray="4 7"/>`;
    s += stone(xEmpty, yt, 23, true);
    s += `<text x="${xEmpty}" y="${ys - 62}" text-anchor="middle" font-size="21" letter-spacing="2" fill="${BONE}" fill-opacity="0.45">少 了</text>`;
    s += `<text x="${xEmpty}" y="${yt + 62}" text-anchor="middle" font-size="21" letter-spacing="2" fill="${AMBER}" fill-opacity="0.85">多 出 来 的</text>`;
    s += `<line x1="104" y1="486" x2="776" y2="486" stroke="${AMBER}" stroke-opacity="0.20" stroke-width="1.5"/>`;
    s += `<text x="440" y="536" text-anchor="middle" font-size="28" letter-spacing="2" fill="${BONE}" fill-opacity="0.9">少一只羊 ＝ 多一颗石子</text>`;
    return s + svgClose();
  })(),
  cap: `羊没进你的脑子，<em>关系</em>进去了。`,
});

/* ── 05 压印成符 ── */
slides.push({
  idx: 5,
  title: `形状<br>代表了东西`,
  art: (() => {
    let s = svgOpen() + DEFS;
    const by = 246, bw = 228, bh = 160;
    const xs = [46, 326, 606];
    xs.forEach((x) => {
      s += `<rect x="${x}" y="${by}" width="${bw}" height="${bh}" rx="10"
              fill="rgba(255,255,255,0.035)" stroke="#4B5563" stroke-width="2"/>`;
    });
    const x1 = xs[0];
    s += `<path d="M ${x1 + 62} 128 L ${x1 + 100} 194 L ${x1 + 24} 194 Z" fill="rgba(232,163,61,0.26)" stroke="${AMBER}" stroke-width="2.4"/>`;
    s += `<circle cx="${x1 + 160}" cy="164" r="26" fill="rgba(232,163,61,0.22)" stroke="${AMBER}" stroke-width="2.4"/>`;
    s += `<path d="M ${x1 + 62} 202 v 32" stroke="${AMBER}" stroke-opacity="0.85" stroke-width="3" marker-end="url(#ah)"/>`;
    s += `<path d="M ${x1 + 160} 198 v 36" stroke="${AMBER}" stroke-opacity="0.85" stroke-width="3" marker-end="url(#ah)"/>`;
    const x2 = xs[1];
    s += `<path d="M ${x2 + 62} 280 L ${x2 + 100} 346 L ${x2 + 24} 346 Z" fill="rgba(0,0,0,0.42)" stroke="${AMBER}" stroke-opacity="0.9" stroke-width="2.2"/>`;
    s += `<circle cx="${x2 + 160}" cy="318" r="26" fill="rgba(0,0,0,0.42)" stroke="${BONE}" stroke-opacity="0.75" stroke-width="2.2"/>`;
    s += `<path d="M ${x2 - 46} ${by + bh / 2} H ${x2 - 12}" stroke="${AMBER}" stroke-opacity="0.6" stroke-width="2.4" marker-end="url(#ah)"/>`;
    const x3 = xs[2];
    s += `<circle cx="${x3 + 112}" cy="${by + 72}" r="92" fill="rgba(232,163,61,0.07)" stroke="${AMBER}" stroke-opacity="0.30" stroke-width="1.6"/>`;
    s += `<path d="M ${x3 + 74} ${by + 40} L ${x3 + 112} ${by + 108} L ${x3 + 36} ${by + 108} Z" fill="rgba(232,163,61,0.34)" stroke="${AMBER}" stroke-width="2.6"/>`;
    s += `<circle cx="${x3 + 172}" cy="${by + 84}" r="25" fill="rgba(232,163,61,0.26)" stroke="${AMBER}" stroke-width="2.6"/>`;
    s += `<path d="M ${x3 - 46} ${by + bh / 2} H ${x3 - 12}" stroke="${AMBER}" stroke-opacity="0.6" stroke-width="2.4" marker-end="url(#ah)"/>`;
    s += `<text x="${x1 + bw / 2}" y="462" text-anchor="middle" font-size="23" letter-spacing="4" fill="${DIM}">① 按 下 去</text>`;
    s += `<text x="${x2 + bw / 2}" y="462" text-anchor="middle" font-size="23" letter-spacing="4" fill="${DIM}">② 留 下 痕 迹</text>`;
    s += `<text x="${x3 + bw / 2}" y="462" text-anchor="middle" font-size="23" letter-spacing="4" fill="${AMBER}">③ 形 状 独 立</text>`;
    s += `<text x="${x1 + bw / 2}" y="508" text-anchor="middle" font-size="22" fill="#5C6675">陶筹压在湿泥上</text>`;
    s += `<text x="${x2 + bw / 2}" y="508" text-anchor="middle" font-size="22" fill="#5C6675">圆锥变成楔形</text>`;
    s += `<text x="${x3 + bw / 2}" y="508" text-anchor="middle" font-size="22" fill="#7D8797">不用再带陶筹</text>`;
    return s + svgClose();
  })(),
  cap: `下一次记账，他不需要带陶筹了。`,
});

/* ── 06 抽象漏斗 ── */
slides.push({
  idx: 6,
  title: `抹掉是什么<br>只留下<br>有几个`,
  art: (() => {
    let s = svgOpen() + DEFS;
    s += `<defs><linearGradient id="funnelG" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="rgba(232,163,61,0.18)"/><stop offset="100%" stop-color="rgba(232,163,61,0.02)"/>
    </linearGradient></defs>`;
    const groups = [
      { x: 190, label: '羊', icon: (x, y) => sheep(x, y, 0.40) },
      { x: 440, label: '日子', icon: (x, y) => `<rect x="${x - 19}" y="${y - 22}" width="38" height="40" rx="5" fill="rgba(237,227,210,0.10)" stroke="${BONE}" stroke-opacity="0.72" stroke-width="2"/><line x1="${x - 19}" y1="${y - 9}" x2="${x + 19}" y2="${y - 9}" stroke="${BONE}" stroke-opacity="0.5" stroke-width="1.8"/>` },
      { x: 690, label: '星星', icon: (x, y) => `<path d="M ${x} ${y - 22} L ${x + 6} ${y - 6} L ${x + 22} ${y - 5} L ${x + 10} ${y + 6} L ${x + 14} ${y + 21} L ${x} ${y + 12} L ${x - 14} ${y + 21} L ${x - 10} ${y + 6} L ${x - 22} ${y - 5} L ${x - 6} ${y - 6} Z" fill="rgba(232,163,61,0.18)" stroke="${AMBER}" stroke-opacity="0.85" stroke-width="2"/>` },
    ];
    groups.forEach((g) => {
      for (let i = 0; i < 3; i++) s += g.icon(g.x - 64 + i * 64, 62);
      s += `<text x="${g.x}" y="142" text-anchor="middle" font-size="24" letter-spacing="5" fill="${DIM}">${g.label}</text>`;
      s += `<text x="${g.x}" y="188" text-anchor="middle" font-family="Georgia, serif" font-size="32" fill="${AMBER}" fill-opacity="0.9">3</text>`;
      s += `<path d="M ${g.x} 202 v 34" stroke="${AMBER}" stroke-opacity="0.45" stroke-width="2.4" marker-end="url(#ah)"/>`;
    });
    s += `<path d="M 90 262 L 790 262 L 502 462 L 378 462 Z" fill="url(#funnelG)" stroke="${AMBER}" stroke-opacity="0.55" stroke-width="2.6" stroke-linejoin="round"/>`;
    s += `<circle cx="292" cy="312" r="3.4" fill="${AMBER}" fill-opacity="0.55"/>`;
    s += `<circle cx="472" cy="342" r="3" fill="${BONE}" fill-opacity="0.30"/>`;
    s += `<circle cx="392" cy="396" r="2.8" fill="${AMBER}" fill-opacity="0.45"/>`;
    s += `<circle cx="566" cy="306" r="2.8" fill="${BONE}" fill-opacity="0.22"/>`;
    s += `<circle cx="606" cy="368" r="3" fill="${AMBER}" fill-opacity="0.30"/>`;
    s += `<line x1="440" y1="462" x2="440" y2="496" stroke="${AMBER}" stroke-opacity="0.55" stroke-width="3"/>`;
    s += `<text x="440" y="552" text-anchor="middle" font-family="Georgia, serif" font-size="94" font-weight="700" fill="${AMBER}">3</text>`;
    return s + svgClose();
  })(),
  cap: `"三"不属于羊，也不属于大麦。`,
});

/* ── 07 文明链条 ── */
slides.push({
  idx: 7,
  title: `同一个「数」<br>长出了<br>整个文明`,
  art: (() => {
    let s = svgOpen() + DEFS;
    const nodes = [
      { x: 140, y: 112, t: '数', icon: 'tally' },
      { x: 440, y: 112, t: '天文', icon: 'star' },
      { x: 740, y: 112, t: '几何', icon: 'tri' },
      { x: 740, y: 400, t: '历法', icon: 'cal' },
      { x: 440, y: 400, t: '力学', icon: 'arc' },
      { x: 140, y: 400, t: '计算机', icon: 'chip' },
    ];
    s += `<line x1="195" y1="112" x2="385" y2="112" stroke="${AMBER}" stroke-opacity="0.34" stroke-width="2"/>`;
    s += `<line x1="495" y1="112" x2="685" y2="112" stroke="${AMBER}" stroke-opacity="0.34" stroke-width="2"/>`;
    s += `<path d="M 796 150 C 866 250 866 350 800 386" fill="none" stroke="${AMBER}" stroke-opacity="0.34" stroke-width="2" marker-end="url(#ah)"/>`;
    s += `<line x1="685" y1="400" x2="560" y2="400" stroke="${AMBER}" stroke-opacity="0.34" stroke-width="2" marker-end="url(#ah)"/>`;
    s += `<line x1="385" y1="400" x2="200" y2="400" stroke="${AMBER}" stroke-opacity="0.34" stroke-width="2" marker-end="url(#ah)"/>`;
    const icons = {
      tally: `<line x1="-20" y1="-16" x2="20" y2="-16" stroke="${AMBER}" stroke-width="2.8" stroke-linecap="round"/>
              <line x1="-20" y1="0" x2="20" y2="0" stroke="${AMBER}" stroke-width="2.8" stroke-linecap="round"/>
              <line x1="-20" y1="16" x2="20" y2="16" stroke="${AMBER}" stroke-width="2.8" stroke-linecap="round"/>`,
      star: `<path d="M 0 -24 L 7 -7 L 24 -5 L 11 6 L 15 24 L 0 14 L -15 24 L -11 6 L -24 -5 L -7 -7 Z" fill="none" stroke="${AMBER}" stroke-width="2.4"/>`,
      tri: `<path d="M 0 -24 L 24 20 L -24 20 Z" fill="none" stroke="${AMBER}" stroke-width="2.6"/>
            <circle cx="0" cy="5" r="6.5" fill="none" stroke="${AMBER}" stroke-width="2"/>`,
      cal: `<rect x="-22" y="-20" width="44" height="40" rx="4" fill="none" stroke="${AMBER}" stroke-width="2.4"/>
            <line x1="-22" y1="-7" x2="22" y2="-7" stroke="${AMBER}" stroke-width="2.2"/>
            <circle cx="-9" cy="7" r="2.8" fill="${AMBER}"/><circle cx="7" cy="7" r="2.8" fill="${AMBER}"/>`,
      arc: `<path d="M -24 18 Q 0 -28 24 18" fill="none" stroke="${AMBER}" stroke-width="2.6"/>
            <circle cx="24" cy="18" r="4.5" fill="${AMBER}"/>`,
      chip: `<rect x="-20" y="-20" width="40" height="40" rx="5" fill="none" stroke="${AMBER}" stroke-width="2.4"/>
             <rect x="-9" y="-9" width="18" height="18" fill="none" stroke="${AMBER}" stroke-width="2"/>`,
    };
    nodes.forEach((n, i) => {
      const isKey = i === 0;
      s += `<circle cx="${n.x}" cy="${n.y}" r="55" fill="${isKey ? 'rgba(232,163,61,0.13)' : BG}"
              stroke="${AMBER}" stroke-opacity="${isKey ? 0.8 : 0.36}" stroke-width="2"/>`;
      s += `<g transform="translate(${n.x},${n.y})">${icons[n.icon]}</g>`;
      s += `<text x="${n.x}" y="${n.y + 90}" text-anchor="middle" font-size="26" letter-spacing="3"
              fill="${isKey ? AMBER : BONE}" fill-opacity="${isKey ? 1 : 0.82}">${n.t}</text>`;
    });
    return s + svgClose();
  })(),
  cap: `抹掉内容，只留下关系。手机到现在还在做这件事。`,
});

/* ── 08 金句 ── */
slides.push({
  idx: 8,
  title: `<span class="qmark">数</span>
          <span class="qbody">是唯一一个人类能拿在手里<br>却完全没有重量的东西</span>`,
  titleStyle: 'display:flex;flex-direction:column;justify-content:center;',
  art: (() => {
    let s = svgOpen();
    s += `<text x="440" y="400" text-anchor="middle" font-family="Georgia, serif" font-size="430"
            fill="rgba(237,227,210,0.075)" stroke="#EDE3D2" stroke-opacity="0.55" stroke-width="2.6">3</text>`;
    return s + svgClose();
  })(),
  cap: `你摸不到"三"。但羊会死，"三"不死。`,
});

/* ── 09 母题 ── */
slides.push({
  idx: 9,
  title: `数学<br>是被<b>发明</b>的<br>还是被发现的？`,
  art: (() => {
    let s = svgOpen();
    s += `<circle cx="244" cy="176" r="118" fill="rgba(232,163,61,0.11)" stroke="${AMBER}" stroke-opacity="0.85" stroke-width="2.6"/>`;
    s += `<text x="244" y="166" text-anchor="middle" font-size="40" letter-spacing="5" fill="${AMBER}">发 明</text>`;
    s += `<text x="244" y="242" text-anchor="middle" font-family="Georgia, serif" font-size="62" fill="${BONE}" fill-opacity="0.78">1</text>`;
    s += `<circle cx="636" cy="176" r="118" fill="rgba(255,255,255,0.02)" stroke="#4B5563" stroke-width="2.6"/>`;
    s += `<text x="636" y="166" text-anchor="middle" font-size="40" letter-spacing="5" fill="${BONE}" fill-opacity="0.70">发 现</text>`;
    s += `<text x="636" y="242" text-anchor="middle" font-family="Georgia, serif" font-size="62" fill="${BONE}" fill-opacity="0.28">0</text>`;
    s += `<text x="440" y="192" text-anchor="middle" font-family="Georgia, serif" font-size="34" letter-spacing="2" fill="#8A94A4">VS</text>`;
    s += `<line x1="128" y1="376" x2="752" y2="376" stroke="${AMBER}" stroke-opacity="0.20" stroke-width="1.5"/>`;
    s += `<text x="440" y="428" text-anchor="middle" font-size="25" letter-spacing="5" fill="${DIM}">第 1 集 · 记 分 1 : 0</text>`;
    s += `<text x="440" y="476" text-anchor="middle" font-size="23" letter-spacing="2" fill="${BONE}" fill-opacity="0.5">67 集之后揭晓</text>`;
    return s + svgClose();
  })(),
  cap: `第 1 集记分：发明 +1。你站哪边？`,
});

function pageHTML(s, total) {
  const p2 = String(s.idx).padStart(2, '0');
  const html = `<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8"><style>${CSS}</style></head>
<body>
  <div class="bg-base"></div><div class="bg-beam"></div><div class="bg-vig"></div><div class="grain"></div>
  <div class="frame"></div>
  <i class="tick tl"></i><i class="tick tr"></i><i class="tick bl"></i><i class="tick br"></i>
  <div class="page">
    <div class="brandrow">
      <div class="brand">
        <span class="mark">${logoMark(68, 'h')}</span>
        <span class="btext">
          <span class="wname">万物有数</span>
          <span class="wslog">数学是宇宙的通行证</span>
        </span>
      </div>
      <div class="meta">
        <span class="ep"><i>EP.${p2}</i> · 骨头上的刻痕</span>
        <span class="pg">${p2} / ${String(total).padStart(2, '0')}</span>
      </div>
    </div>
    <div class="hr"></div>
    <h1 class="title" style="${s.titleStyle || ''}">${s.title}</h1>
    <div class="art">${s.art}</div>
    <div class="cap"><span class="dash"></span><p>${s.cap}</p></div>
    <div class="bot">
      <span class="sl">数学是宇宙的通行证</span>
      <span class="bmark">${logoMark(19, 'f')}<b>万物有数</b></span>
    </div>
  </div>
</body></html>`;
  return recolor(html);
}

const NAMES = ['01-封面', '02-时间轴', '03-困局', '04-羊与石子', '05-压印成符', '06-抽象漏斗', '07-文明链条', '08-金句', '09-母题'];

async function main() {
  fs.mkdirSync(OUT_DIR, { recursive: true });
  let chromeProc = null, browser = null;
  try {
    chromeProc = spawn(CHROME_PATH, [
      `--remote-debugging-port=${CDP_PORT}`,
      '--headless', '--disable-gpu', '--no-sandbox', '--hide-scrollbars',
      '--disable-dev-shm-usage', '--force-color-profile=srgb',
      '--disable-logging', '--disable-breakpad', '--no-first-run',
    ], { stdio: 'ignore' });
    await new Promise(r => setTimeout(r, 4000));

    browser = await puppeteer.connect({
      browserURL: `http://127.0.0.1:${CDP_PORT}`,
      defaultViewport: { width: 1080, height: 1440, deviceScaleFactor: 1 },
      protocolTimeout: 60000,
    });
    const page = (await browser.pages())[0] || await browser.newPage();
    await page.setViewport({ width: 1080, height: 1440, deviceScaleFactor: 1 });

    const n = Math.min(LIMIT, slides.length);
    for (let i = 0; i < n; i++) {
      await page.setContent(pageHTML(slides[i], slides.length), { waitUntil: 'load', timeout: 30000 });
      await new Promise(r => setTimeout(r, 700));
      const out = path.join(OUT_DIR, `${NAMES[i]}.png`);
      await page.screenshot({ path: out, type: 'png' });
      console.log(`✓ [${P.name}] ${NAMES[i]}.png  ${(fs.statSync(out).size / 1024).toFixed(0)} KB`);
    }
    console.log(`\n✅ ${P.name} 完成 ${n} 张 → ${OUT_DIR}`);
  } catch (e) {
    console.error('❌', e.message);
    process.exit(1);
  } finally {
    if (browser) await browser.close();
    if (chromeProc) chromeProc.kill();
  }
}

main();

// render_xhs_ep03_v2.js — 《万物有数》ep03《生下来就会数吗》小红书九图 · v2 自然图鉴风
// 反馈重做：①加插画插画（丛林/乌鸦/婴儿/坚果场景 + 手绘涂鸦元素）②解释全改大白话 ③版式清爽有节奏
// 用法：PAL=teal|terra OUT=目录 LIMIT=n MEASURE=1 node render_xhs_ep03_v2.js
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
const CDP_PORT = 9512;

const EP_NAME = '生下来就会数吗';

/* ── 默认色（生成 SVG 时用，随后按方案整体置换）── */
const AMBER = '#E8A33D';
const BONE = '#EDE3D2';
const DIM = '#7D8797';
const BG = '#121821';
const H = 560;

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
      '#5C6675': '#A96A4C', '#4B5563': '#A96A4C', '#8A94A4': '#C79A80',
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

/* v2：标题区固定 300px，三行 60px 大字 + 金色下划线 */
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

.qmark { display:block; font-size:96px; line-height:1.05; color:${P.amber};
  font-family:Georgia,serif; font-weight:700; letter-spacing:.02em; }
.qbody { display:block; font-size:44px; line-height:1.6; letter-spacing:.03em; }
`;

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

/* ── v2 自然图鉴风 · 手绘涂鸦元素 ── */
const DOODLE = {
  // 爆炸框（手写感叹）
  boom(cx, cy, r, text, fs = 26) {
    let pts = '';
    const spikes = 12;
    for (let i = 0; i < spikes * 2; i++) {
      const a = (i / (spikes * 2)) * 360 * Math.PI / 180;
      const rr = i % 2 === 0 ? r : r * 0.72;
      pts += `${(cx + Math.cos(a) * rr).toFixed(1)},${(cy + Math.sin(a) * rr).toFixed(1)} `;
    }
    return `<polygon points="${pts.trim()}" fill="rgba(232,163,61,0.18)" stroke="${AMBER}"
      stroke-width="2.6" stroke-linejoin="round"/>
    <text x="${cx}" y="${cy + fs * 0.35}" text-anchor="middle" font-family="Noto Sans SC, sans-serif"
      font-size="${fs}" font-weight="700" fill="${AMBER}">${text}</text>`;
  },
  // 对勾（手写成功）
  check(cx, cy, s = 1) {
    return `<g transform="translate(${cx},${cy}) scale(${s})">
      <path d="M -22 0 L -6 16 L 24 -22" fill="none" stroke="${AMBER}" stroke-width="5"
        stroke-linecap="round" stroke-linejoin="round"/>
    </g>`;
  },
  // 虚线手圈（强调某块）
  handEllipse(cx, cy, rx, ry) {
    return `<ellipse cx="${cx}" cy="${cy}" rx="${rx}" ry="${ry}" fill="none" stroke="${AMBER}"
      stroke-width="2.6" stroke-dasharray="7 7" stroke-opacity="0.7"/>`;
  },
  // 小星星点缀
  star(cx, cy, s = 1) {
    return `<path d="M ${cx} ${cy - 10 * s} L ${cx + 2.6 * s} ${cy - 3 * s} L ${cx + 10 * s} ${cy}
      L ${cx + 2.6 * s} ${cy + 3 * s} L ${cx} ${cy + 10 * s} L ${cx - 2.6 * s} ${cy + 3 * s}
      L ${cx - 10 * s} ${cy} L ${cx - 2.6 * s} ${cy - 3 * s} Z"
      fill="${AMBER}" fill-opacity="0.6"/>`;
  },
};

/* ── 丛林场景（v3：纯剪影，不画底色块，融入背景）· dy 整体上移 ── */
function jungleScene(dy = 0) {
  let s = '';
  // 月亮
  s += `<circle cx="790" cy="${120 - dy}" r="30" fill="#EDE3D2" fill-opacity="0.20"/>`;
  // 远处树影（暗色剪影，从画面底部升起，不画底色矩形）
  s += `<path d="M 0 ${500 - dy} Q 120 ${320 - dy} 250 ${480 - dy} Q 360 ${340 - dy} 470 ${490 - dy} Q 590 ${320 - dy} 700 ${480 - dy} Q 800 ${360 - dy} 880 ${500 - dy} L 880 ${560 - dy} L 0 ${560 - dy} Z"
        fill="#121821" fill-opacity="0.55"/>`;
  // 篝火（居中靠下）
  s += `<g transform="translate(440,${470 - dy})">
    <line x1="-26" y1="14" x2="26" y2="14" stroke="#8E5A2A" stroke-width="5" stroke-linecap="round"/>
    <path d="M 0 -34 C 14 -12 10 14 0 18 C -10 14 -14 -12 0 -34 Z" fill="${AMBER}" fill-opacity="0.9"/>
    <path d="M 0 -20 C 8 -6 6 8 0 10 C -6 8 -8 -6 0 -20 Z" fill="#FBE7BE" fill-opacity="0.85"/>
  </g>`;
  // 火星
  s += DOODLE.star(418, 430 - dy, 0.7) + DOODLE.star(470, 424 - dy, 0.6) + DOODLE.star(440, 416 - dy, 0.5);
  return s;
}

/* ── 拟人化乌鸦（圆润，有眼睛，站在坚果堆上）── */
function crow2(cx, cy, k = 1) {
  return `<g transform="translate(${cx},${cy}) scale(${k})">
    <ellipse cx="0" cy="6" rx="42" ry="34" fill="${AMBER}" fill-opacity="0.95"/>
    <ellipse cx="6" cy="24" rx="22" ry="16" fill="#FBE7BE" fill-opacity="0.55"/>
    <circle cx="26" cy="-14" r="22" fill="${AMBER}"/>
    <circle cx="34" cy="-18" r="7" fill="#121821"/>
    <circle cx="36" cy="-20" r="2.4" fill="#FBE7BE"/>
    <path d="M 46 -14 L 66 -8 L 46 -2 Z" fill="#FBE7BE"/>
    <path d="M -40 30 Q -52 44 -40 50 L -2 46" fill="${AMBER}"/>
    <line x1="-16" y1="40" x2="-16" y2="56" stroke="#8E5A2A" stroke-width="3.4" stroke-linecap="round"/>
    <line x1="8" y1="40" x2="8" y2="56" stroke="#8E5A2A" stroke-width="3.4" stroke-linecap="round"/>
  </g>`;
}

/* ── 一颗巴西坚果（卡通版，有裂口和叶子）── */
function nut2(cx, cy, s = 1) {
  return `<g transform="translate(${cx},${cy}) scale(${s})">
    <path d="M -18 -30 Q -30 -12 -22 18 Q -10 34 0 34 Q 10 34 22 18 Q 30 -12 18 -30 Q 0 -40 -18 -30 Z"
      fill="rgba(232,163,61,0.28)" stroke="${AMBER}" stroke-width="2.6"/>
    <path d="M -12 -22 Q 0 -8 12 -22" fill="none" stroke="#EDE3D2" stroke-opacity="0.6" stroke-width="2"/>
    <path d="M 0 -34 Q 14 -44 22 -38 Q 12 -30 0 -34 Z" fill="#8E5A2A"/>
  </g>`;
}

/* ── 婴儿脸（圆润 + 呆萌，无脸化保留五官但不写实）── */
function baby(cx, cy, k = 1) {
  return `<g transform="translate(${cx},${cy}) scale(${k})">
    <circle cx="0" cy="0" r="34" fill="#EDE3D2" fill-opacity="0.9"/>
    <circle cx="-12" cy="-4" r="4.4" fill="#121821"/>
    <circle cx="12" cy="-4" r="4.4" fill="#121821"/>
    <path d="M -14 12 Q 0 22 14 12" fill="none" stroke="#121821" stroke-width="3" stroke-linecap="round"/>
    <circle cx="-18" cy="8" r="5" fill="${AMBER}" fill-opacity="0.4"/>
    <circle cx="18" cy="8" r="5" fill="${AMBER}" fill-opacity="0.4"/>
  </g>`;
}

/* ── 点阵（subitizing）── */
function dotField(cx, cy, n, spacing = 46, r = 10, op = 0.9) {
  const cols = Math.ceil(Math.sqrt(n));
  const rows = Math.ceil(n / cols);
  let s = '';
  for (let i = 0; i < n; i++) {
    const c = i % cols, row = Math.floor(i / cols);
    const x = cx + (c - (cols - 1) / 2) * spacing;
    const y = cy + (row - (rows - 1) / 2) * spacing;
    s += `<circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="${r}"
            fill="${AMBER}" fill-opacity="${op}"/>`;
  }
  return s;
}

const slides = [];

/* ── 01 封面 · 丛林里，乌鸦在坚果堆之间选 4 ── */
slides.push({
  idx: 1,
  title: `一只乌鸦没学过数<br>却<b>选对了</b>`,
  art: (() => {
    let s = svgOpen() + DEFS;
    s += jungleScene(26);
    // 左堆 3（整体上移）
    s += nut2(250, 220, 1.1) + nut2(200, 300, 1.1) + nut2(300, 300, 1.1);
    s += `<text x="250" y="378" text-anchor="middle" font-family="Georgia, serif" font-size="44"
            fill="${BONE}" fill-opacity="0.55">3</text>`;
    // 右堆 4（被选中，整体上移）
    s += nut2(600, 200, 1.25) + nut2(540, 300, 1.25) + nut2(660, 300, 1.25) + nut2(600, 370, 1.25);
    s += `<text x="600" y="404" text-anchor="middle" font-family="Georgia, serif" font-size="44"
            fill="${AMBER}">4</text>`;
    s += DOODLE.handEllipse(600, 290, 130, 120);
    s += DOODLE.boom(700, 120, 52, '选它！', 28);
    s += crow2(440, 250, 1.1);
    s += `<text x="440" y="120" text-anchor="middle" font-family="Noto Serif SC, serif" font-size="30"
            fill="${AMBER}">没人教过它数数</text>`;
    s += `<text x="440" y="166" text-anchor="middle" font-family="Noto Sans SC, sans-serif" font-size="24"
            fill="${BONE}" fill-opacity="0.8">它却知道哪堆更多</text>`;
    return s + svgClose();
  })(),
  cap: `它<em>没数过</em>，但选对了。`,
});

/* ── 02 困局 · 丛林里的部落，没有"一"这个词 ── */
slides.push({
  idx: 2,
  title: `有个部落<br>连<b>「一」</b>都没有词`,
  art: (() => {
    let s = svgOpen();
    s += jungleScene(14);
    // 部落剪影（无脸）+ 罐子（整体上移）
    s += `<g transform="translate(300,204)">
      <circle cx="0" cy="-40" r="22" fill="#121821"/>
      <path d="M -30 -18 L 30 -18 L 22 70 L -22 70 Z" fill="#121821"/>
    </g>`;
    s += `<g transform="translate(460,244)">
      <rect x="-46" y="-30" width="92" height="90" rx="8" fill="rgba(232,163,61,0.12)"
        stroke="${AMBER}" stroke-width="2.6"/>
      <line x1="-46" y1="6" x2="46" y2="6" stroke="${AMBER}" stroke-opacity="0.5" stroke-width="2"/>
      ${[0, 1, 2].map(i => `<circle cx="${-20 + i * 20}" cy="44" r="8" fill="${AMBER}" fill-opacity="0.85"/>`).join('')}
    </g>`;
    s += `<text x="460" y="374" text-anchor="middle" font-family="Noto Sans SC, sans-serif" font-size="24"
            fill="${BONE}" fill-opacity="0.8">一罐子坚果</text>`;
    // 数词工具箱（整体上移）
    s += `<g transform="translate(650,154)">
      <rect x="-90" y="-50" width="180" height="130" rx="12" fill="rgba(232,163,61,0.1)"
        stroke="${AMBER}" stroke-width="2.6"/>
      <text x="0" y="-18" text-anchor="middle" font-family="Noto Sans SC, sans-serif" font-size="24"
        fill="${DIM}">数 词</text>
      ${['一', '二', '三'].map((ch, i) => {
        const solid = i === 0;
        return `<text x="${-50 + i * 50}" y="50" text-anchor="middle" font-family="Noto Sans SC, sans-serif"
          font-size="42" font-weight="700" fill="${AMBER}" fill-opacity="${solid ? 0.95 : 0.4}">${ch}</text>`;
      }).join('')}
    </g>`;
    s += `<text x="440" y="432" text-anchor="middle" font-family="Noto Sans SC, sans-serif" font-size="26"
            fill="${AMBER}">语言里连「一」都没有</text>`;
    return s + svgClose();
  })(),
  cap: `他们不会数，但<em>能配出来</em>。`,
});

/* ── 03 动手 · 点阵：四颗以内一眼，40 vs 44 就懵 ── */
slides.push({
  idx: 3,
  title: `四颗以内不用数<br><b>一眼就懂</b>`,
  art: (() => {
    let s = svgOpen();
    s += `<text x="70" y="44" font-family="Noto Sans SC, sans-serif" font-size="24"
            fill="${AMBER}">4 颗 → 一眼就懂</text>`;
    s += dotField(170, 120, 4, 54, 13, 0.92);
    s += DOODLE.check(270, 120, 0.8);
    s += `<text x="430" y="44" font-family="Noto Sans SC, sans-serif" font-size="24"
            fill="${DIM}">7 颗 → 得数了</text>`;
    s += dotField(540, 120, 7, 54, 13, 0.85);
    s += `<line x1="70" y1="200" x2="810" y2="200" stroke="${AMBER}" stroke-opacity="0.22" stroke-width="1.5"/>`;
    s += `<text x="440" y="230" text-anchor="middle" font-family="Noto Sans SC, sans-serif" font-size="24"
            letter-spacing="3" fill="${AMBER}" fill-opacity="0.85">两堆对比 · 哪堆多？</text>`;
    // 8 vs 16（轻松）
    s += dotField(160, 300, 8, 42, 9, 0.85);
    s += `<text x="160" y="370" text-anchor="middle" font-family="Georgia, serif" font-size="34" fill="${BONE}">8</text>`;
    s += dotField(410, 300, 16, 32, 7.5, 0.72);
    s += `<text x="410" y="370" text-anchor="middle" font-family="Georgia, serif" font-size="34" fill="${BONE}">16</text>`;
    s += `<text x="285" y="300" text-anchor="middle" font-family="Georgia, serif" font-size="46" fill="${AMBER}">›</text>`;
    s += `<text x="285" y="410" text-anchor="middle" font-family="Noto Sans SC, sans-serif" font-size="22"
            fill="${DIM}">轻松</text>`;
    s += DOODLE.check(285, 370, 0.7);
    // 40 vs 44（懵）
    s += dotField(660, 300, 40, 20, 4.4, 0.55);
    s += `<text x="660" y="370" text-anchor="middle" font-family="Georgia, serif" font-size="34"
            fill="${AMBER}">40 / 44</text>`;
    s += `<text x="660" y="410" text-anchor="middle" font-family="Noto Sans SC, sans-serif" font-size="22"
            fill="${DIM}">懵</text>`;
    s += DOODLE.boom(760, 260, 44, '？', 34);
    return s + svgClose();
  })(),
  cap: `同样差 4，<em>40 对 44</em> 就懵了。`,
});

/* ── 04 造物 · 你量的是"几倍"，不是"差几个"（韦伯律）── */
slides.push({
  idx: 4,
  title: `你量的不是差几个<br>是<b>几倍</b>`,
  art: (() => {
    let s = svgOpen() + DEFS;
    const group = (gx, a, b, label, note) => {
      let g = '';
      g += dotField(gx, 108, a, 34, 7, 0.85);
      g += `<text x="${gx - 108}" y="208" font-family="Georgia, serif" font-size="34" fill="${BONE}">${a}</text>`;
      g += dotField(gx, 278, b, 34, 6, 0.7);
      g += `<text x="${gx - 108}" y="338" font-family="Georgia, serif" font-size="34" fill="${AMBER}">${b}</text>`;
      g += `<text x="${gx + 88}" y="228" font-family="Georgia, serif" font-size="30" fill="${AMBER}">${label}</text>`;
      g += `<text x="${gx}" y="378" text-anchor="middle" font-family="Noto Sans SC, sans-serif" font-size="22"
            fill="${DIM}">${note}</text>`;
      return g;
    };
    s += group(210, 8, 16, '×2', '一眼分清');
    s += `<line x1="440" y1="78" x2="440" y2="378" stroke="${AMBER}" stroke-opacity="0.22" stroke-width="1.5"/>`;
    s += group(650, 16, 24, '×1.5', '要皱眉');
    // 比值尺
    s += `<text x="70" y="440" font-family="Noto Sans SC, sans-serif" font-size="23" letter-spacing="2"
            fill="${AMBER}">身体里这把尺</text>`;
    const rx0 = 70, rx1 = 810, ry = 470;
    s += `<line x1="${rx0}" y1="${ry}" x2="${rx1}" y2="${ry}" stroke="${AMBER}" stroke-opacity="0.55" stroke-width="3"/>`;
    [0, 1, 2, 4, 8, 16].forEach((v, i) => {
      const xs = rx0 + Math.log2(v + 1) / Math.log2(17) * (rx1 - rx0);
      const big = i >= 4;
      s += `<line x1="${xs.toFixed(1)}" y1="${ry - (big ? 16 : 10)}" x2="${xs.toFixed(1)}" y2="${ry + (big ? 16 : 10)}"
              stroke="${BONE}" stroke-opacity="${big ? 0.9 : 0.6}" stroke-width="${big ? 3 : 2}"/>`;
      s += `<text x="${xs.toFixed(1)}" y="${ry + 42}" text-anchor="middle" font-family="Georgia, serif"
              font-size="19" fill="${big ? AMBER : BONE}" fill-opacity="${big ? 1 : 0.72}">${v}</text>`;
    });
    s += `<text x="440" y="522" text-anchor="middle" font-family="Noto Sans SC, sans-serif" font-size="20"
            fill="${DIM}">越往右越挤：数越大，越难分</text>`;
    return s + svgClose();
  })(),
  cap: `差几倍，才分得清——这叫<b>韦伯律</b>。`,
});

/* ── 05 穿透 · 三亿年前的鱼，到今天的你 ── */
slides.push({
  idx: 5,
  title: `这把尺<br>比你的大脑<b>老得多</b>`,
  art: (() => {
    const nodes = [
      { x: 110, y: 200, yr: '3 亿年前', t: '鱼', icon: 'fish', key: true },
      { x: 290, y: 200, yr: '猴子', t: '比多比少', icon: 'dot', key: false },
      { x: 470, y: 200, yr: '蜜蜂', t: '会分大小', icon: 'hex', key: false },
      { x: 650, y: 200, yr: '乌鸦', t: '懂"零"', icon: 'crow', key: false },
      { x: 800, y: 200, yr: '今天', t: '你', icon: 'you', key: true },
    ];
    let s = svgOpen() + DEFS;
    s += `<line x1="110" y1="200" x2="800" y2="200" stroke="${AMBER}" stroke-opacity="0.42" stroke-width="2.6"/>`;
    const ic = {
      fish: `<path d="M -18 0 C -8 -10 6 -10 16 -2 L 24 -8 L 24 8 L 16 2 C 6 10 -8 10 -18 0 Z"
              fill="none" stroke="${AMBER}" stroke-width="2.4" stroke-linejoin="round"/>
            <circle cx="8" cy="-2" r="2" fill="${AMBER}"/>`,
      dot: `<circle cx="0" cy="0" r="12" fill="none" stroke="${AMBER}" stroke-width="2.4"/>
            <circle cx="0" cy="0" r="3.4" fill="${AMBER}"/>`,
      hex: `<path d="M 0 -14 L 12 -7 L 12 7 L 0 14 L -12 7 L -12 -7 Z"
              fill="none" stroke="${AMBER}" stroke-width="2.4" stroke-linejoin="round"/>`,
      crow: `<path d="M -14 4 C -8 -6 2 -8 10 -4 L 18 -7 C 14 0 8 2 4 2 C 2 10 -6 12 -12 8 Z"
              fill="${AMBER}" fill-opacity="0.92"/>`,
      you: `<circle cx="0" cy="-8" r="7" fill="none" stroke="${AMBER}" stroke-width="2.4"/>
            <path d="M -14 14 C -14 2 14 2 14 14" fill="none" stroke="${AMBER}" stroke-width="2.4"/>`,
    };
    nodes.forEach((n) => {
      s += `<circle cx="${n.x}" cy="${n.y}" r="${n.key ? 36 : 26}"
              fill="${n.key ? 'rgba(232,163,61,0.16)' : BG}"
              stroke="${AMBER}" stroke-opacity="${n.key ? 0.92 : 0.5}" stroke-width="2.2"/>`;
      s += `<g transform="translate(${n.x},${n.y})">${ic[n.icon]}</g>`;
      s += `<text x="${n.x}" y="${n.y - 62}" text-anchor="middle" font-family="Georgia, serif"
              font-size="24" fill="${n.key ? AMBER : BONE}" fill-opacity="${n.key ? 1 : 0.78}">${n.yr}</text>`;
      s += `<text x="${n.x}" y="${n.y + 64}" text-anchor="middle" font-family="Noto Sans SC, sans-serif"
              font-size="22" fill="${BONE}" fill-opacity="${n.key ? 0.95 : 0.7}">${n.t}</text>`;
    });
    s += `<text x="440" y="390" text-anchor="middle" font-family="Noto Serif SC, serif" font-size="32"
            fill="${AMBER}">三亿年前，它就在</text>`;
    s += `<text x="440" y="432" text-anchor="middle" font-family="Noto Sans SC, sans-serif" font-size="24"
            fill="${DIM}">数感，比语言还老</text>`;
    return s + svgClose();
  })(),
  cap: `你、乌鸦、蜜蜂，<em>同一把尺</em>。`,
});

/* ── 06 对数尺 · 耳朵、眼睛、音乐都用它 ── */
slides.push({
  idx: 6,
  title: `耳朵、眼睛、音乐<br>都在用<b>对数尺</b>`,
  art: (() => {
    let s = svgOpen();
    const axis = (x, label, note, iconFn) => {
      let g = '';
      g += `<g transform="translate(${x},66)">${iconFn}</g>`;
      g += `<text x="${x}" y="118" text-anchor="middle" font-family="Noto Sans SC, sans-serif"
              font-size="24" fill="${AMBER}">${label}</text>`;
      g += `<line x1="${x}" y1="146" x2="${x}" y2="440" stroke="${BONE}" stroke-opacity="0.42" stroke-width="2.4"/>`;
      [0, 1, 2, 4, 8, 16].forEach((v, i) => {
        const yv = 146 + (i / 5) * 294;
        const major = i % 2 === 0;
        g += `<line x1="${x - (major ? 16 : 9)}" y1="${yv.toFixed(1)}" x2="${x + (major ? 16 : 9)}"
                y2="${yv.toFixed(1)}" stroke="${AMBER}" stroke-opacity="${major ? 0.95 : 0.5}"
                stroke-width="${major ? 3 : 1.8}"/>`;
        if (major) {
          g += `<text x="${x + 26}" y="${(yv + 5).toFixed(1)}" font-family="Georgia, serif" font-size="19"
                  fill="${BONE}" fill-opacity="0.8">${v}</text>`;
        }
      });
      g += `<text x="${x}" y="478" text-anchor="middle" font-family="Noto Sans SC, sans-serif" font-size="22"
              fill="${DIM}">${note}</text>`;
      return g;
    };
    s += axis(196, '耳朵 · 响度', '响 10 倍才"响 1 档"',
      `<path d="M -16 0 A 16 16 0 0 1 16 0 L 16 6 L -16 6 Z" fill="${AMBER}" fill-opacity="0.9"/>
       <circle cx="0" cy="-2" r="5" fill="${BG}"/>`);
    s += axis(440, '眼睛 · 星星', '亮 100 倍才"亮 5 等"',
      DOODLE.star(0, 0, 1.3));
    s += axis(684, '音乐 · 八度', '频率翻 1 倍就"高 1 度"',
      `<path d="M -14 8 L 14 8 L 0 -14 Z" fill="${AMBER}" fill-opacity="0.9"/>
       <line x1="0" y1="-14" x2="0" y2="14" stroke="${AMBER}" stroke-width="2.4"/>`);
    s += `<text x="440" y="524" text-anchor="middle" font-family="Noto Sans SC, sans-serif" font-size="25"
            fill="${BONE}" fill-opacity="0.9">身体天生就这么量世界</text>`;
    return s + svgClose();
  })(),
  cap: `感官刻度，<em>上紧下松</em>。`,
});

/* ── 07 金句 · 生下来就会量，数数是造出来的 ── */
slides.push({
  idx: 7,
  title: `<span class="qmark">量</span>
          <span class="qbody">你生下来就会量，<br>数数是<b>造</b>出来的</span>`,
  titleStyle: 'display:flex;flex-direction:column;justify-content:center;',
  art: (() => {
    let s = svgOpen();
    s += `<text x="440" y="410" text-anchor="middle" font-family="Georgia, serif" font-size="330"
            fill="rgba(237,227,210,0.075)" stroke="#EDE3D2" stroke-opacity="0.55" stroke-width="2.6">量</text>`;
    return s + svgClose();
  })(),
  cap: `数感是<b>发现</b>，数数是<b>发明</b>。`,
});

/* ── 08 母题 · 记分 2 : 2 ── */
slides.push({
  idx: 8,
  title: `数感是发现<br>数数是发明<br>打平 <b class="num">2 : 2</b>`,
  art: (() => {
    let s = svgOpen();
    s += `<circle cx="244" cy="176" r="118" fill="rgba(232,163,61,0.13)" stroke="${AMBER}" stroke-opacity="0.88" stroke-width="2.6"/>`;
    s += `<text x="244" y="166" text-anchor="middle" font-family="Noto Sans SC, sans-serif" font-size="38" letter-spacing="5" fill="${AMBER}">发现</text>`;
    s += `<text x="244" y="242" text-anchor="middle" font-family="Georgia, serif" font-size="62" fill="${BONE}" fill-opacity="0.85">2</text>`;
    s += `<circle cx="636" cy="176" r="118" fill="rgba(232,163,61,0.13)" stroke="${AMBER}" stroke-opacity="0.88" stroke-width="2.6"/>`;
    s += `<text x="636" y="166" text-anchor="middle" font-family="Noto Sans SC, sans-serif" font-size="38" letter-spacing="5" fill="${AMBER}">发明</text>`;
    s += `<text x="636" y="242" text-anchor="middle" font-family="Georgia, serif" font-size="62" fill="${BONE}" fill-opacity="0.85">2</text>`;
    s += `<text x="440" y="192" text-anchor="middle" font-family="Georgia, serif" font-size="34" letter-spacing="2" fill="#8A94A4">VS</text>`;
    s += `<line x1="128" y1="376" x2="752" y2="376" stroke="${AMBER}" stroke-opacity="0.20" stroke-width="1.5"/>`;
    s += `<text x="440" y="428" text-anchor="middle" font-family="Noto Sans SC, sans-serif" font-size="25" letter-spacing="5" fill="${AMBER}">第 3 集 · 记 分 2 : 2</text>`;
    s += `<text x="440" y="476" text-anchor="middle" font-family="Noto Sans SC, sans-serif" font-size="23" letter-spacing="2" fill="${BONE}" fill-opacity="0.5">65 集 之 后 揭 晓</text>`;
    return s + svgClose();
  })(),
  cap: `第一次<em>打平</em>，数感与数词各一分。`,
});

/* ── 09 预告 · 那个让欧洲害怕的符号「零」── */
slides.push({
  idx: 9,
  title: `下集：让欧洲<br>害怕的<b>那个符号</b>`,
  art: (() => {
    let s = svgOpen() + DEFS;
    // 图形整体上移：坚果(左) → 圆圈0(右) 居中于 y≈280
    s += nut2(170, 250, 0.95);
    s += `<text x="170" y="332" text-anchor="middle" font-family="Noto Sans SC, sans-serif" font-size="22"
            fill="${DIM}">一颗都没有</text>`;
    s += `<line x1="244" y1="250" x2="330" y2="250" stroke="${AMBER}" stroke-opacity="0.6" stroke-width="2.4"
            marker-end="url(#ah)"/>`;
    s += `<circle cx="470" cy="250" r="112" fill="rgba(232,163,61,0.12)"
            stroke="${AMBER}" stroke-opacity="0.92" stroke-width="3"/>`;
    s += `<text x="470" y="284" text-anchor="middle" font-family="Georgia, serif" font-size="140" font-weight="700"
            fill="${AMBER}">0</text>`;
    s += `<text x="470" y="372" text-anchor="middle" font-family="Noto Sans SC, sans-serif" font-size="24" letter-spacing="3"
            fill="${BONE}" fill-opacity="0.85">代表"空"，却也最大的数</text>`;
    s += `<line x1="90" y1="424" x2="790" y2="424" stroke="${AMBER}" stroke-opacity="0.18" stroke-width="1.5"/>`;
    s += `<text x="440" y="470" text-anchor="middle" font-family="Noto Sans SC, sans-serif" font-size="25" letter-spacing="2"
            fill="${AMBER}">最晚出生，也最让人害怕</text>`;
    s += `<text x="440" y="506" text-anchor="middle" font-family="Noto Sans SC, sans-serif" font-size="22" letter-spacing="2"
            fill="${DIM}">下一集 · 零</text>`;
    return s + svgClose();
  })(),
  cap: `最奇怪的发明，代表<em>一颗都没有</em>。`,
});

/* ── v2 版式骨架：幕标签 + 大白话标题 + 插画场景 + 脚注 ── */
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
        <span class="ep"><i>EP.${p2}</i> · ${EP_NAME}</span>
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

const NAMES = ['01-封面', '02-困局', '03-动手', '04-造物', '05-穿透', '06-对数尺', '07-金句', '08-母题', '09-预告'];

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
      if (process.env.MEASURE) {
        const m = await page.evaluate(() => {
          const g = (sel) => { const e = document.querySelector(sel); if (!e) return null;
            const r = e.getBoundingClientRect(); return [Math.round(r.top), Math.round(r.bottom)]; };
          return { brand: g('.brandrow'), title: g('.title'), art: g('.art'), svg: g('.art svg'), cap: g('.cap'), bot: g('.bot') };
        });
        console.log('MEASURE', i + 1, JSON.stringify(m));
      }
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

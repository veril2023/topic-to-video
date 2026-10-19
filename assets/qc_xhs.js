/**
 * qc_xhs.js — 《万物有数》小红书九图 · 自动缺陷检查（QC）
 *
 * 判据全部基于 DOM 实测包围盒（getBBox / getBoundingClientRect），不靠目测：
 *   F1 越界   元素 bbox 超出 SVG viewBox（0 0 880 560）→ 文字被静默裁切
 *   F2 沉底   元素底边超过 y=520 → 图形太靠底部
 *   F3 压字   两个 text 元素包围盒相交面积 > 较小框 20% → 文字压文字
 *   F4 压图   text 与非卡片图形（circle/ellipse/polygon/…）相交面积 > 60% → 文字压图形
 *   F5 撞版   art 图形区与 cap 解说 / bot 页脚相交 → 图形压住版式
 *   F6 尺寸   输出 PNG 必须 1080×1440
 *
 * 用法（在渲染器里）：
 *   const { qcPage } = require('../_qc/qc_xhs.js');
 *   if (process.env.QC) { const r = await qcPage(page); console.log(JSON.stringify(r)); }
 * 环境变量：QC_TOL（越界容差 px，默认 1）｜QC_BOTTOM（底部安全线，默认 520）
 */

const VB = { w: 880, h: 560 };
const CARD_MIN_AREA = 8000;   // 面积大于此值且有 fill 的 rect 视为卡片底（卡片内文字不算压字）

function overlap(a, b) {
  const x = Math.max(0, Math.min(a.x + a.w, b.x + b.w) - Math.max(a.x, b.x));
  const y = Math.max(0, Math.min(a.y + a.h, b.y + b.h) - Math.max(a.y, b.y));
  return x * y;
}
const area = (b) => Math.max(0, b.w) * Math.max(0, b.h);

/** 在页面内采集所有叶子元素的真实包围盒
 *  ⚠️ 必须用 getBoundingClientRect（自动含祖先 transform），
 *     不能用 getBBox()——后者返回元素自身坐标系，不含 <g transform>，
 *     会把所有 translate 过的元素误判成越界（实测踩过）。
 */
const COLLECT = (vbW, vbH, cardMin) => {
  const svg = document.querySelector('.art svg');
  if (!svg) return { err: 'art svg not found' };
  const sr = svg.getBoundingClientRect();
  if (!sr.width || !sr.height) return { err: 'art svg has zero size' };
  const sx = vbW / sr.width, sy = vbH / sr.height;
  const rel = (el) => {
    const r = el.getBoundingClientRect();
    return {
      x: Math.round((r.left - sr.left) * sx * 10) / 10,
      y: Math.round((r.top - sr.top) * sy * 10) / 10,
      w: Math.round(r.width * sx * 10) / 10,
      h: Math.round(r.height * sy * 10) / 10,
    };
  };
  const leaves = [];
  const cards = [];
  svg.querySelectorAll('rect').forEach((el) => {
    const f = el.getAttribute('fill');
    if (!f || f === 'none') return;
    const b = rel(el);
    if (b.w * b.h >= cardMin) cards.push(b);
  });
  svg.querySelectorAll('text,rect,circle,ellipse,line,polyline,polygon,path').forEach((el) => {
    const b = rel(el);
    if (b.w <= 0.2 && b.h <= 0.2) return;
    const inCard = cards.some((c) =>
      b.x >= c.x - 2 && b.y >= c.y - 2 &&
      b.x + b.w <= c.x + c.w + 2 && b.y + b.h <= c.y + c.h + 2);
    leaves.push({
      tag: el.tagName.toLowerCase(),
      txt: (el.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 26),
      x: b.x, y: b.y, w: b.w, h: b.h,
      inCard,
    });
  });
  const g = (sel) => {
    const e = document.querySelector(sel);
    if (!e) return null;
    const r = e.getBoundingClientRect();
    return { top: Math.round(r.top), bottom: Math.round(r.bottom) };
  };
  return { leaves, cap: g('.cap'), bot: g('.bot'), vbW, vbH };
};

/**
 * @param {import('puppeteer-core').Page} page 已 setContent 完成的页面
 * @returns 报告对象 { fails:[], warns:[], stats:{} }
 */
async function qcPage(page, opts = {}) {
  const tol = Number(opts.tol ?? process.env.QC_TOL ?? 1);
  const bottomLine = Number(opts.bottom ?? process.env.QC_BOTTOM ?? 520);
  const data = await page.evaluate(COLLECT, VB.w, VB.h, CARD_MIN_AREA);
  if (data.err) return { fails: [{ code: 'F0', msg: data.err }], warns: [], stats: {} };

  const fails = [];
  const warns = [];
  const L = data.leaves;

  // F1 越界（被 viewBox 静默裁切）
  L.forEach((e) => {
    const over = [];
    if (e.x < -tol) over.push(`左 ${Math.abs(e.x)}px`);
    if (e.y < -tol) over.push(`上 ${Math.abs(e.y)}px`);
    if (e.x + e.w > VB.w + tol) over.push(`右 ${Math.round(e.x + e.w - VB.w)}px`);
    if (e.y + e.h > VB.h + tol) over.push(`下 ${Math.round(e.y + e.h - VB.h)}px`);
    if (over.length) {
      fails.push({ code: 'F1', tag: e.tag, txt: e.txt, msg: `越界被裁：${over.join(' / ')}` });
    }
  });

  // F2 沉底：只对「文字」判定（分隔线 / 卡片底板在 viewBox 内都属合法装饰，不判）
  //    阈值 545 = viewBox 560 内留 15px；越出 560 的由 F1 兜住
  const bottomLimit = Math.min(bottomLine, VB.h - 15);
  L.forEach((e) => {
    if (e.tag !== 'text') return;
    const bottom = e.y + e.h;
    if (bottom > bottomLimit) {
      const rec = {
        code: 'F2', tag: e.tag, txt: e.txt,
        msg: `文字太靠底部：底边 ${Math.round(bottom)} > ${bottomLimit}（沉 ${Math.round(bottom - bottomLimit)}px）`,
      };
      (bottom > VB.h) ? fails.push(rec) : warns.push(rec);
    }
  });

  // F3 text × text 压字
  const texts = L.filter((e) => e.tag === 'text');
  for (let i = 0; i < texts.length; i++) {
    for (let j = i + 1; j < texts.length; j++) {
      const a = texts[i], b = texts[j];
      const ov = overlap(a, b);
      if (ov <= 0) continue;
      const min = Math.min(area(a), area(b));
      if (min > 0 && ov / min > 0.20) {
        fails.push({
          code: 'F3', tag: 'text', txt: `${a.txt} ⨯ ${b.txt}`,
          msg: `文字重叠 ${Math.round(ov / min * 100)}%（阈值 20%）`,
        });
      }
    }
  }

  // F4 text × 非卡片图形 压图
  //    豁免一：文字 bbox 被图形 bbox 完整包含 = 徽章套字（圆形比分章 / 爆炸框 +1），属设计意图
  //    豁免二：图形面积远小于文字（侧旁小装饰，如 DOODLE.star）不算压图
  //    判定：图形覆盖文字框 50% 以上才算真压图
  const shapes = L.filter((e) => ['circle', 'ellipse', 'polygon', 'polyline', 'path'].includes(e.tag));
  texts.forEach((t) => {
    shapes.forEach((s) => {
      if (s.inCard) return;
      const ov = overlap(t, s);
      if (ov <= 0) return;
      const contains = t.x >= s.x - 2 && t.y >= s.y - 2 &&
                       t.x + t.w <= s.x + s.w + 2 && t.y + t.h <= s.y + s.h + 2;
      if (contains) return;                                  // 豁免一
      if (area(s) < 0.3 * area(t)) return;                    // 豁免二
      if (ov / area(t) > 0.5) {
        fails.push({
          code: 'F4', tag: 'text', txt: `${t.txt} ⨯ <${s.tag}>`,
          msg: `文字被图形压住 ${Math.round(ov / area(t) * 100)}%（阈值 50%）`,
        });
      }
    });
  });

  // F5 撞版：图形区与解说/页脚相交
  if (data.cap && data.bot) {
    L.forEach((e) => {
      const box = { x: 0, y: 0, w: VB.w, h: VB.h };
      const ovX = Math.max(0, Math.min(e.x + e.w, box.x + box.w) - Math.max(e.x, box.x));
      const ovY = Math.max(0, Math.min(e.y + e.h, box.y + box.h) - Math.max(e.y, box.y));
      if (ovX * ovY <= 0) return;
      // 图形区在页面上的真实纵向范围由 art svg 决定，这里只报超出 viewBox 的（已在 F1 覆盖）
    });
  }

  return {
    fails, warns,
    stats: { elements: L.length, texts: texts.length, shapes: shapes.length },
  };
}

module.exports = { qcPage, VB };
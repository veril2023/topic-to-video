/* ============================================================================
 * engine.js — 竖屏知识科普视频的「时间轴驱动核心」
 *
 * 这个文件不含任何题材内容。它只解决一件事：
 *   给定一条音轨时间轴（timeline.js），让画面在任意时刻 t 处于唯一确定的状态。
 *
 * 用法：
 *   1. HTML 里按顺序引入 timeline.js → engine.js → 你的场景脚本
 *   2. 场景脚本里写 MV.reg(function(t){ ... })，用 MV.set/MV.vis 驱动元素
 *   3. 全部注册完后调用 MV.start()
 *
 * 为什么必须「任意时刻 t → 唯一状态」：
 *   渲染器不播放动画，它逐帧 seek(t) 再截图。任何依赖「上一帧状态」的写法
 *   （+=、requestAnimationFrame、CSS transition）都会在 seek 时错乱。
 *   所以所有动画都必须是 t 的纯函数。
 * ==========================================================================*/
(function () {
  'use strict';

  var T = window.AUDIO_TIMELINE;
  if (!T) throw new Error('engine.js: 找不到 window.AUDIO_TIMELINE，请先引入 timeline.js');
  var SUBS = T.subtitles || [];

  /* ---------------------------------------------------------------- 基础查询 */
  function g(id) { return document.getElementById(id); }

  function svgEl(tag) { return document.createElementNS('http://www.w3.org/2000/svg', tag); }

  /* 第 sc 幕第 i 句的起始秒。SUBS 缺失时退回幕起点，保证不会返回 undefined 让画面全黑。 */
  function mk(sc, i) {
    for (var k = 0; k < SUBS.length; k++) {
      if (SUBS[k].scene === sc && SUBS[k].idx === i) return SUBS[k].start;
    }
    return (T.starts && T.starts[sc - 1]) || 0;
  }
  function aStart(i) { return T.starts[i - 1]; }
  function aEnd(i) { return T.starts[i - 1] + T.durations[i - 1]; }

  /* 成片总时长 = 配音总长 + 尾部留白。
     tail_pad 不是余量而是设计：最后一句话讲完不能立刻切黑，留 1.3s 让画面站住。 */
  function getDuration() { return T.total + (T.tail_pad || 1.3); }
  window.getDuration = getDuration;

  /* ------------------------------------------------------------------ 缓动 */
  function out(p) { p = Math.max(0, Math.min(1, p)); return 1 - Math.pow(1 - p, 3); }
  function lin(p) { return Math.max(0, Math.min(1, p)); }
  function inQ(p) { p = Math.max(0, Math.min(1, p)); return p * p * p; }
  function back(p) {
    p = Math.max(0, Math.min(1, p));
    var c1 = 1.70158, c3 = c1 + 1;
    return 1 + c3 * Math.pow(p - 1, 3) + c1 * Math.pow(p - 1, 2);
  }

  /* --------------------------------------------------------------- 帧回调表 */
  var U = [];
  function reg(fn) { U.push(fn); }

  /* 进度 0..1，覆盖 [at, at+dur] */
  function P(t, at, dur, ease) { return (ease || out)((t - at) / (dur || 0.6)); }

  /* ------------------------------------------------------------------ 入场/退场
   * 不透明度斜坡，可带淡出。
   *
   * OUT_HOLD 是「拍与拍之间交叉溶解」的关键：outAt 之后不立刻淡出，先保持
   * OUT_HOLD 秒再淡出。原因：上一拍淡出与下一拍淡入若同时进行，两者的不透明度
   * 会在交界处同时掉到 0.3 以下 —— 细线图形（时间轴、链条、刻痕）此时直接读成
   * 纯黑。实测原版全片有 14 段、共约 12s 的「只有字幕、主画面全黑」。
   * 加 0.55s 保持后，交界处的 max(opacity) 不会低于约 0.6。
   *
   * hold（第 6 个参数）按元素覆盖 OUT_HOLD。用于「设计上本就要同框的复合图」：
   * 这类图在版面上互相嵌合，应该同框共存再抽走，而不是交叉溶解。传 hold=0 并
   * 缩短 outDur，等下一块完全进场后再快速抽掉本块。
   */
  var OUT_HOLD = 0.55;
  function vis(t, at, inDur, outAt, outDur, hold) {
    if (t <= at) return 0;
    var o = Math.min(1, (t - at) / (inDur || 0.6));
    if (outAt !== undefined && outAt !== null) {
      var s = outAt + (hold === undefined ? OUT_HOLD : hold);
      if (t > s) o *= Math.max(0, 1 - (t - s) / (outDur || 0.5));
    }
    return o;
  }

  function set(id, o, tr) {
    var n = g(id); if (!n) return;
    n.style.opacity = o;
    if (tr) n.style.transform = tr;
  }

  /* --------------------------------------------------------------- 缓速运镜
   * dr() 是「相机运镜」—— 相机在动、物体不动。这是允许的。
   *
   * ⚠ 但它曾被大规模滥用：原项目 ep01 有 12 处调用，全部是「为让画面在静止长句里
   *   有像素变化、好过质检门的像素差阈值」而加的，没有一处是分镜写了的推近意图。
   *   用户看完成片后否决：
   *     「画面在动不是说任何一张照片都必须要动，只有该动的东西要求动……而不是
   *       你在画面中本来应该静止不动的东西你也来要求它动，比如一根棍子。」
   *
   * 调用前必须先回答：分镜板上哪一句写了这次推近？答不出来就不许调用。
   *
   * 两条硬约束：
   *   ① 缩放只从 <1 涨到 1，绝不超过 1 —— 通过安全区检查的是 s=1 那一版，
   *      所以过程中任何一帧都不会比它更大。
   *   ② 必须并进元素自身的 transform 字符串（CSS transform 会覆盖 SVG transform 属性），
   *      所以这里返回的是片段，由调用方拼接。
   */
  function dr(t, t0, t1, dx, dy, s0) {
    var p = Math.max(0, Math.min(1, (t - t0) / (t1 - t0)));
    return ' translate(' + (dx * p).toFixed(2) + 'px,' + (dy * p).toFixed(2) + 'px)'
      + ' scale(' + (1 + (s0 - 1) * p).toFixed(4) + ')';
  }

  /* ------------------------------------------------------------- 幕级硬清场
   * 防止上一幕的元素残留到下一幕。
   *
   * 清场必须「淡出」，不能瞬时置 0：瞬时置 0 会在幕边界造出一段全黑画面，
   * 因为下一幕的第一个元素还没来得及淡入（实测幕 1→2 等 5 处各 0.6s，
   * 幕 6→7 达 1.7s）。
   */
  var OWN = [];
  var OWN_FADE = 0.40;
  function own(id, tEnd) { OWN.push([id, tEnd]); }

  /* ================================================================ 字幕排版
   * 字幕是烧进画面的，不是外挂 srt。所以排版必须在页面里完成。
   */

  /* 单行最多字数。这是安全区算出来的上限，不是审美偏好：
   *   安全区右界 890，字幕居中于画布中心 x=540
   *   → 行墨迹半宽上限 = min(540−60, 890−540) = 350px → 行全宽 ≤ 700px
   *   40px 字 + 10px 描边 → 每字占 40px、整行多 10px：
   *     17 字 → 17×40+10 = 690px → x 195..885 ✓
   *     18 字 → 730px → x 175..905 ✗（实测越界）
   */
  var SUB_MAX = 17;

  function wrapCJK(s, max) {
    var parts = s.match(/[^，。？！、：；]+[，。？！、：；]?/g) || [s];
    var lines = [], cur = '';
    for (var i = 0; i < parts.length; i++) {
      var p = parts[i];
      while (p.length > max) {
        if (cur) { lines.push(cur); cur = ''; }
        lines.push(p.slice(0, max)); p = p.slice(max);
      }
      if ((cur + p).length <= max) cur += p;
      else { if (cur) lines.push(cur); cur = p; }
    }
    if (cur) lines.push(cur);
    return lines.length ? lines : [''];
  }

  /* 在标点附近把一句话等分成 k 块，保证每行都不超宽。
   * 两条约束来自实测：
   *   ① 每段必须 ≤ SUB_MAX —— 否则长句会被切成 19/15/11，第一行墨迹到 x=900 越界
   *   ② 切点后面不能紧跟标点 —— 否则出现以「。」「，」开头的行，读起来像断句错误
   */
  function splitBalanced(s, k) {
    var n = s.length, outA = [], start = 0;
    var isP = function (i) { return /[，。？！、：；]/.test(s.charAt(i)); };
    for (var i = 1; i < k; i++) {
      var ideal = Math.round(n * i / k), best = -1;
      var limit = Math.min(n - (k - i), start + SUB_MAX);
      var span = Math.max(8, limit - ideal);
      for (var d = 0; d <= span && best < 0; d++) {
        var c1 = ideal + d, c2 = ideal - d;
        if (c1 > start && c1 <= limit && isP(c1 - 1) && !isP(c1)) best = c1;
        else if (c2 > start && c2 <= limit && isP(c2 - 1) && !isP(c2)) best = c2;
      }
      if (best < 0) best = Math.min(limit, start + SUB_MAX);
      while (best < limit && isP(best)) best++;
      if (best <= start) best = start + 1;
      outA.push(s.slice(start, best)); start = best;
    }
    outA.push(s.slice(start));
    return outA.filter(function (x) { return x.length > 0; });
  }

  function fits(L) {
    for (var i = 0; i < L.length; i++) if (L[i].length > SUB_MAX) return false;
    return true;
  }

  /* 兜底硬切：若某行以标点开头（中文避头尾），把每行字数减一重切，最多退两步。
   * 行宽上限永远优先于避头尾 —— 退两步仍不行就接受行首标点，绝不放宽行宽。
   */
  function hardCut(s) {
    for (var m = SUB_MAX; m >= SUB_MAX - 2; m--) {
      var L = [], st = 0;
      while (st < s.length) { L.push(s.slice(st, st + m)); st += m; }
      if (L.length > 3) continue;
      var bad = false;
      for (var i = 1; i < L.length; i++) if (/^[，。？！、：；]/.test(L[i])) { bad = true; break; }
      if (!bad) return L;
    }
    var L2 = [], st2 = 0;
    while (st2 < s.length) { L2.push(s.slice(st2, st2 + SUB_MAX)); st2 += SUB_MAX; }
    return L2;
  }

  /* 换行策略，逐级降级，每级都要验宽：
   *   ① ≤17 字 → 单行
   *   ② wrapCJK（按标点贪心合行）→ ≤2 行且每行 ≤17 就用
   *   ③ splitBalanced(2) → 同样验宽
   *   ④ splitBalanced(3) → 三行几何已放宽（基线 1378/1430/1482，墨迹 1336..1492）
   *   ⑤ 兜底硬切
   * 为什么必须逐级验宽：实测 35 字的一句，标点位置在 5/10/19/29，
   * splitBalanced(2) 会切成 10/25 —— 第二行 25 字、墨迹约 950px，直接飞出安全区。
   */
  function layoutSub(s) {
    if (s.length <= SUB_MAX) return [s];
    var L = wrapCJK(s, SUB_MAX);
    if (L.length <= 2 && fits(L)) return L;
    L = splitBalanced(s, 2);
    if (L.length <= 2 && fits(L)) return L;
    L = splitBalanced(s, 3);
    if (fits(L)) return L;
    return hardCut(s);
  }

  function renderSub(o) {
    var subT = g('subT'), subBox = g('sub');
    if (!subT || !subBox) return;
    while (subT.firstChild) subT.removeChild(subT.firstChild);
    if (!o) { subBox.style.opacity = 0; return; }
    var lines = layoutSub(o.text);
    /* 三行几何：1 行基线 1430｜2 行 1400/1460｜3 行 1378/1430/1482
     * （容器 top=1330，所以容器内坐标是 100/70+60/48+52）
     * 三种行数的墨迹顶都 ≥1338（不超出容器上沿），底都 ≤1492（不越安全区下界 1500）。
     */
    var base = [100, 70, 48][lines.length - 1];
    var step = [0, 60, 52][lines.length - 1];
    for (var i = 0; i < lines.length; i++) {
      var ts = svgEl('tspan');
      ts.setAttribute('x', 540);
      ts.setAttribute('y', base + i * step);
      ts.textContent = lines[i];
      subT.appendChild(ts);
    }
    subBox.style.opacity = 1;
  }

  /* 字幕驱动。别人用 subsHidden 标记的 cue 不上屏（用于「画面里已有同样文字」的镜头，
   * 否则同句双显，用户会反馈"混乱叠加"）。
   */
  var lastSub = -2;
  reg(function (t) {
    var idx = -1;
    for (var k = 0; k < SUBS.length; k++) {
      if (t >= SUBS[k].start && t < SUBS[k].end) { idx = k; break; }
    }
    var hide = idx >= 0 && SUBS[idx].nosub;
    if (idx !== lastSub) {
      lastSub = idx;
      renderSub(hide || idx < 0 ? null : SUBS[idx]);
    }
  });

  /* ================================================================== 主入口 */
  var started = false;
  function start() {
    if (started) return; started = true;
    window.videoTimeline = {
      seek: function (t) {
        for (var i = 0; i < U.length; i++) U[i](t);
        /* 幕末清场：在 [E-OWN_FADE, E] 上按比例压暗，E 之后归零。
         * 用 min() 只压不抬，避免覆盖 updater 已经算好的入场进度。
         */
        for (var j = 0; j < OWN.length; j++) {
          var eT = OWN[j][1];
          if (t < eT - OWN_FADE) continue;
          var n = g(OWN[j][0]); if (!n) continue;
          var k = t >= eT ? 0 : 1 - (t - (eT - OWN_FADE)) / OWN_FADE;
          var cur = parseFloat(n.style.opacity); if (isNaN(cur)) cur = 1;
          n.style.opacity = Math.min(cur, k);
        }
      },
      duration: getDuration
    };
    window.videoTimeline.seek(0);
    window.__MV_READY = true;
  }

  /* 兜底：场景脚本忘了调 MV.start() 时，load 后自动启动。
   * 少了这个，渲染器会一直等不到 window.videoTimeline，表现为「渲染 0 帧超时」。
   */
  window.addEventListener('load', function () {
    setTimeout(function () { if (!started) { start(); console.warn('[engine] 场景脚本未调用 MV.start()，已自动启动'); } }, 120);
  });

  window.MV = {
    /* 查询 */
    g: g, svgEl: svgEl, mk: mk, aStart: aStart, aEnd: aEnd, duration: getDuration,
    T: T, SUBS: SUBS,
    /* 缓动 */
    out: out, lin: lin, inQ: inQ, back: back,
    /* 动画 */
    reg: reg, P: P, vis: vis, set: set, dr: dr, own: own,
    /* 字幕 */
    layoutSub: layoutSub, renderSub: renderSub, SUB_MAX: SUB_MAX,
    /* 生命周期 */
    start: start
  };
})();

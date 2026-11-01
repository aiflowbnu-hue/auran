// Scene timeline v2: AI-illustrated "Blaze" sprites with limited (pose-swap) animation.
// Needs rig.js (colors + math helpers), window.TIMELINE and window.SPRITES (manifest) + images under sprites/.

const W = 1280, H = 720;
C.bg = '#E4E9F2';
const TL = window.TIMELINE;
const SC = {};
TL.scenes.forEach((s, i) => { SC[s.id] = Object.assign({}, s, { end: i + 1 < TL.scenes.length ? TL.scenes[i + 1].start : TL.total }); });
function at(id, phrase) {
  const s = SC[id], i = s.text.indexOf(phrase);
  if (i < 0) throw new Error(`phrase not found: ${id} / ${phrase}`);
  return s.start + s.dur * (i / s.text.length);
}

// ---------- sprites ----------
const IMG = {};
window.ready = Promise.all(Object.keys(window.SPRITES).map(n => new Promise((res, rej) => {
  const im = new Image(); im.onload = res; im.onerror = () => rej(new Error('sprite ' + n)); im.src = `sprites/${n}.png`; IMG[n] = im;
})));
// draw sprite `name` so that the bbox of `ref` (default: itself) has its bottom-centre at (x, y), scaled by s
function spr(ctx, name, x, y, s, o = {}) {
  const ref = window.SPRITES[o.ref || name], im = IMG[name];
  const [x0, , x1, y1] = ref.bbox;
  ctx.save();
  ctx.globalAlpha = o.alpha ?? 1;
  ctx.translate(x, y); ctx.scale(s * (o.sx || 1), s * (o.sy || 1)); if (o.rot) ctx.rotate(o.rot);
  ctx.drawImage(im, -(x0 + x1) / 2, -y1);
  ctx.restore();
}
// glow part of a sprite: tint only its pixels inside a circle (sprite coords) with red
const tintCache = {};
function sprGlow(ctx, name, x, y, s, cx, cy, r, amt, o = {}) {
  spr(ctx, name, x, y, s, o);
  if (amt <= 0) return;
  const im = IMG[name];
  let c = tintCache[name];
  if (!c) { c = tintCache[name] = document.createElement('canvas'); c.width = im.width; c.height = im.height; }
  const g = c.getContext('2d');
  g.globalCompositeOperation = 'source-over'; g.clearRect(0, 0, c.width, c.height); g.drawImage(im, 0, 0);
  g.globalCompositeOperation = 'source-atop';
  const grd = g.createRadialGradient(cx, cy, 0, cx, cy, r);
  grd.addColorStop(0, `rgba(255,40,20,${0.85 * amt})`); grd.addColorStop(1, 'rgba(255,40,20,0)');
  g.fillStyle = grd; g.fillRect(0, 0, c.width, c.height);
  const ref = window.SPRITES[o.ref || name], [x0, , x1, y1] = ref.bbox;
  ctx.save(); ctx.translate(x, y); ctx.scale(s, s); ctx.globalCompositeOperation = 'lighter'; ctx.globalAlpha = 0.6;
  ctx.drawImage(c, -(x0 + x1) / 2, -y1); ctx.restore();
}
// pose-swap animation: returns 0 (frame a) .. 1 (frame b) with short blends
function swapW(t, period, aHold, toB, bHold) {
  const p = ((t % period) + period) % period;
  if (p < aHold) return 0;
  if (p < aHold + toB) return ease((p - aHold) / toB);
  if (p < aHold + toB + bHold) return 1;
  return 1 - ease((p - aHold - toB - bHold) / Math.max(0.001, period - aHold - toB - bHold));
}
function pair(ctx, base, w, x, y, s, o = {}) {
  const ref = base + '_a';
  const bob = o.bob ?? 0;
  if (w < 1) spr(ctx, base + '_a', x, y, s, { ref, sy: 1 + bob });
  if (w > 0) spr(ctx, base + '_b', x, y, s, { ref, alpha: w < 1 ? w : 1, sy: 1 + bob });
}

// ---------- easing / drawing helpers ----------
const ease = x => { x = clamp(x); return x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2; };
const easeOut = x => 1 - Math.pow(1 - clamp(x), 3);
const back = x => { x = clamp(x); const c1 = 1.9, c3 = c1 + 1; return 1 + c3 * Math.pow(x - 1, 3) + c1 * Math.pow(x - 1, 2); };
const FONT = (size, w = 900) => `italic ${w} ${size}px Inter, "Inter Display", sans-serif`;
const breathe = t => 1 + 0.006 * Math.sin(t * 2.4);

function cam(ctx, cx, cy, z, fn) { ctx.save(); ctx.translate(W / 2, H / 2); ctx.scale(z, z); ctx.translate(-cx, -cy); fn(); ctx.restore(); }
function bg(ctx, color = C.bg) { ctx.fillStyle = color; ctx.fillRect(0, 0, W, H); }
function roundRect(ctx, x, y, w, h, r) {
  ctx.beginPath(); ctx.moveTo(x + r, y); ctx.arcTo(x + w, y, x + w, y + h, r); ctx.arcTo(x + w, y + h, x, y + h, r);
  ctx.arcTo(x, y + h, x, y, r); ctx.arcTo(x, y, x + w, y, r); ctx.closePath();
}
function popText(ctx, txt, x, y, size, dt, o = {}) {
  if (dt < 0) return;
  const out = o.until !== undefined && dt > o.until ? clamp((dt - o.until) / 0.2) : 0;
  const s = back(dt / 0.38) * (1 - out);
  if (s <= 0.001) return;
  ctx.save(); ctx.translate(x, y); ctx.rotate(o.rot || 0); ctx.scale(s, s);
  ctx.font = FONT(size); ctx.textAlign = o.align || 'center'; ctx.textBaseline = 'middle';
  ctx.lineJoin = 'round'; ctx.lineWidth = size * 0.22; ctx.strokeStyle = o.stroke || C.white; ctx.strokeText(txt, 0, 0);
  ctx.fillStyle = o.color || C.navy; ctx.fillText(txt, 0, 0);
  ctx.restore();
}
function badge(ctx, txt, x, y, size, dt, color = C.red, o = {}) {
  if (dt < 0) return;
  const out = o.until !== undefined && dt > o.until ? clamp((dt - o.until) / 0.2) : 0;
  const s = back(dt / 0.38) * (1 - out);
  if (s <= 0.001) return;
  ctx.save(); ctx.translate(x, y); ctx.rotate(o.rot ?? -0.04); ctx.scale(s, s);
  ctx.font = FONT(size); const w = ctx.measureText(txt).width + size * 1.1, h = size * 1.55;
  ctx.fillStyle = C.line; roundRect(ctx, -w / 2 + 5, -h / 2 + 6, w, h, h * 0.3); ctx.fill();
  ctx.fillStyle = color; roundRect(ctx, -w / 2, -h / 2, w, h, h * 0.3); ctx.fill();
  ctx.lineWidth = 4; ctx.strokeStyle = C.line; ctx.stroke();
  ctx.fillStyle = C.white; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText(txt, 0, 2);
  ctx.restore();
}
function sparkle(ctx, x, y, dt, size = 26) {
  if (dt < 0 || dt > 0.9) return;
  const s = Math.sin(clamp(dt / 0.9) * Math.PI) * size;
  ctx.save(); ctx.translate(x, y); ctx.rotate(dt * 2); ctx.fillStyle = C.white; ctx.strokeStyle = C.line; ctx.lineWidth = 3;
  ctx.beginPath();
  for (let i = 0; i < 8; i++) { const r = i % 2 ? s * 0.3 : s; const a = i * Math.PI / 4; ctx.lineTo(Math.cos(a) * r, Math.sin(a) * r); }
  ctx.closePath(); ctx.fill(); ctx.stroke(); ctx.restore();
}
function check(ctx, x, y, dt, ok = true) {
  if (dt < 0) return;
  const s = back(dt / 0.35);
  ctx.save(); ctx.translate(x, y); ctx.scale(s, s);
  ctx.fillStyle = ok ? C.green : C.red; ctx.strokeStyle = C.line; ctx.lineWidth = 5;
  ctx.beginPath(); ctx.arc(0, 0, 30, 0, Math.PI * 2); ctx.fill(); ctx.stroke();
  ctx.strokeStyle = C.white; ctx.lineWidth = 8; ctx.lineCap = 'round'; ctx.beginPath();
  if (ok) { ctx.moveTo(-13, 1); ctx.lineTo(-3, 11); ctx.lineTo(14, -10); }
  else { ctx.moveTo(-11, -11); ctx.lineTo(11, 11); ctx.moveTo(11, -11); ctx.lineTo(-11, 11); }
  ctx.stroke(); ctx.restore();
}
function arrow(ctx, x1, y1, x2, y2, color = C.red, w = 8) {
  const a = Math.atan2(y2 - y1, x2 - x1);
  ctx.save(); ctx.strokeStyle = color; ctx.fillStyle = color; ctx.lineWidth = w; ctx.lineCap = 'round';
  ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2 - Math.cos(a) * 12, y2 - Math.sin(a) * 12); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(x2, y2); ctx.lineTo(x2 - Math.cos(a - 0.5) * 26, y2 - Math.sin(a - 0.5) * 26);
  ctx.lineTo(x2 - Math.cos(a + 0.5) * 26, y2 - Math.sin(a + 0.5) * 26); ctx.closePath(); ctx.fill(); ctx.restore();
}
function sunburst(ctx, x, y, t, alpha, color = C.gold) {
  if (alpha <= 0) return;
  ctx.save(); ctx.globalAlpha = alpha; ctx.translate(x, y); ctx.rotate(t * 0.4); ctx.fillStyle = color;
  for (let i = 0; i < 16; i++) { ctx.beginPath(); ctx.moveTo(0, 0); ctx.arc(0, 0, 1500, i * Math.PI / 8, i * Math.PI / 8 + Math.PI / 16); ctx.closePath(); ctx.fill(); }
  ctx.restore();
}
function bubble(ctx, x, y, r, dt, fn, o = {}) {
  if (dt < 0) return;
  const out = o.until !== undefined && dt > o.until ? clamp((dt - o.until) / 0.25) : 0;
  const s = back(dt / 0.4) * (1 - out);
  if (s <= 0.001) return;
  ctx.save(); ctx.translate(x, y); ctx.scale(s, s);
  ctx.fillStyle = C.line; ctx.beginPath(); ctx.arc(5, 7, r + 6, 0, Math.PI * 2); ctx.fill();
  ctx.save(); ctx.beginPath(); ctx.arc(0, 0, r, 0, Math.PI * 2); ctx.clip();
  ctx.fillStyle = o.fill || '#F4F6FA'; ctx.fillRect(-r, -r, 2 * r, 2 * r); fn(); ctx.restore();
  ctx.lineWidth = 7; ctx.strokeStyle = C.line; ctx.beginPath(); ctx.arc(0, 0, r, 0, Math.PI * 2); ctx.stroke();
  ctx.restore();
}
function flames(ctx, x, y, t, k = 1) {
  for (let i = 0; i < 6; i++) {
    const ph = (t * 1.6 + i / 6) % 1;
    const fx = x - 45 * k + i * 18 * k + Math.sin(t * 8 + i) * 5, fy = y - ph * 90 * k;
    const s = ((1 - ph) * 18 + 5) * k;
    ctx.save(); ctx.globalAlpha = 1 - ph; ctx.fillStyle = i % 2 ? C.gold : '#FF7A2F'; ctx.strokeStyle = C.line; ctx.lineWidth = 2.5;
    ctx.beginPath(); ctx.moveTo(fx, fy - s * 1.6); ctx.quadraticCurveTo(fx + s, fy, fx, fy + s * 0.6); ctx.quadraticCurveTo(fx - s, fy, fx, fy - s * 1.6);
    ctx.fill(); ctx.stroke(); ctx.restore();
  }
}
function cameraIcon(ctx, x, y, dt) {
  const s = back(dt / 0.35);
  ctx.save(); ctx.translate(x, y); ctx.scale(s, s); ctx.rotate(0.12);
  ctx.fillStyle = '#3B4256'; ctx.strokeStyle = C.line; ctx.lineWidth = 5;
  roundRect(ctx, -55, -36, 110, 76, 14); ctx.fill(); ctx.stroke();
  roundRect(ctx, -22, -50, 44, 18, 6); ctx.fill(); ctx.stroke();
  ctx.fillStyle = '#9EC9FF'; ctx.beginPath(); ctx.arc(0, 2, 24, 0, Math.PI * 2); ctx.fill(); ctx.stroke();
  ctx.fillStyle = C.red; ctx.beginPath(); ctx.arc(38, -22, 6, 0, Math.PI * 2); ctx.fill();
  ctx.restore();
}
function cursor(ctx, x, y) {
  ctx.save(); ctx.translate(x, y); ctx.fillStyle = C.white; ctx.strokeStyle = C.line; ctx.lineWidth = 4;
  ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(0, 46); ctx.lineTo(12, 35); ctx.lineTo(22, 56); ctx.lineTo(31, 52); ctx.lineTo(21, 31); ctx.lineTo(36, 30); ctx.closePath();
  ctx.fill(); ctx.stroke(); ctx.restore();
}
function titleCard(ctx, sc, t, num, name) {
  const u = t - sc.start;
  ctx.save(); ctx.translate(W * (1 - ease(u / 0.3)), 0);
  bg(ctx, '#4A5674');
  popText(ctx, num, W / 2, 290, 58, u - 0.15, { color: C.white, stroke: '#4A5674' });
  popText(ctx, name, W / 2, 385, 80, u - 0.25, { color: C.white, stroke: '#4A5674' });
  const lw = 480 * ease((u - 0.45) / 0.4);
  ctx.fillStyle = '#FF8A2A'; ctx.fillRect(W / 2 - lw / 2, 445, lw, 8);
  ctx.restore();
}
const setsBadge = (ctx, dt, txt) => badge(ctx, txt, 640, 90, 50, dt - 0.05, C.navy);

// rep curves
const dipW = t => swapW(t, 2.2, 0.7, 0.18, 0.75);
const pushW = t => swapW(t, 2.4, 0.9, 0.22, 1.0);  // 'slow' down (long hold), snap back up
const kneeW = t => swapW(t, 2.2, 0.6, 0.6, 0.5);
const oheW = t => swapW(t + 0.6, 2.4, 0.8, 0.2, 0.8);

// common placements (bottom-centre of the reference bbox)
const DIPS = [640, 640, 0.78], PUSH = [640, 610, 0.8], KNEE = [640, 610, 0.8], OHE = [640, 690, 0.78], HOOK = [640, 690, 0.84], SHIRT = [640, 700, 0.84];
const dips = (ctx, t, w) => pair(ctx, 'dips', w ?? dipW(t), ...DIPS);
const push = (ctx, t, w) => pair(ctx, 'push', w ?? pushW(t), ...PUSH);
const ohe = (ctx, t, w) => pair(ctx, 'ohe', w ?? oheW(t), ...OHE);

// ---------- scenes ----------
const SCENES = {
  hook(ctx, t, sc) {
    const u = t - sc.start, tSpag = at('hook', 'cooked spaghetti');
    cam(ctx, 640, 380, 1.0 + 0.1 * ease(u / 5.5), () => {
      const noodle = t > tSpag;
      const jig = noodle ? Math.sin((t - tSpag) * 30) * 0.03 * Math.max(0, 1 - (t - tSpag) * 2.5) : 0;
      pair(ctx, 'hook', noodle ? 1 : 0, HOOK[0], HOOK[1], HOOK[2] * breathe(t), { bob: jig });
    });
    sparkle(ctx, 760, 150, t - at('hook', 'biceps'), 34);
    popText(ctx, 'BICEPS DAY', 1000, 250, 62, t - at('hook', 'biceps'), { rot: -0.06, until: tSpag - at('hook', 'biceps') });
    badge(ctx, 'SPAGHETTI ARMS', 1010, 300, 48, t - tSpag, C.red, { rot: 0.05 });
  },

  fact(ctx, t, sc) {
    const tTrain = at('fact', 'Train them'), tTwo = at('fact', 'two thirds');
    if (t < tTrain) {
      bg(ctx, '#F4F6FA');
      popText(ctx, 'YOUR UPPER ARM', W / 2, 120, 50, t - sc.start - 0.1);
      const A = [360, 380], B = [920, 380], grow = ease((t - sc.start) / 0.5);
      ctx.save(); ctx.translate(640, 380); ctx.scale(grow, grow); ctx.translate(-640, -380);
      ctx.beginPath(); capsulePath(ctx, A, B, 95, 80); ctx.lineWidth = 12; ctx.strokeStyle = C.line; ctx.stroke();
      ctx.fillStyle = '#B5263E'; ctx.fill();
      ctx.save(); ctx.clip();
      const split = 380 - 95 + 190 / 3;
      ctx.globalAlpha = 0.9;
      ctx.fillStyle = C.blue; ctx.fillRect(250, 200, 760 * ease((t - at('fact', 'triceps')) / 0.5), split - 200);
      ctx.fillStyle = '#FF5A3C'; ctx.fillRect(250, split, 760 * ease((t - tTwo) / 0.7), 300);
      ctx.restore();
      ctx.strokeStyle = C.line; ctx.lineWidth = 5; ctx.setLineDash([14, 10]);
      ctx.beginPath(); ctx.moveTo(280, split); ctx.lineTo(1000, split); ctx.stroke(); ctx.setLineDash([]);
      ctx.restore();
      popText(ctx, 'BICEPS  1/3', 640, 230, 46, t - at('fact', 'triceps') - 0.2, { color: C.blue });
      popText(ctx, 'TRICEPS  2/3', 640, 560, 64, t - tTwo, { color: C.red });
      sparkle(ctx, 900, 520, t - tTwo - 0.2, 34);
      return;
    }
    const tRip = at('fact', 'begging for mercy');
    const shake = t > tRip ? Math.sin((t - tRip) * 50) * 8 * Math.max(0, 1 - (t - tRip) * 3) : 0;
    cam(ctx, 640 + shake, 380, 1.05 + 0.05 * ease((t - tTrain) / 3), () => {
      pair(ctx, 'shirt', t > tRip ? 1 : 0, SHIRT[0], SHIRT[1], SHIRT[2] * (1 + 0.012 * Math.sin(t * 9)));
    });
    popText(ctx, 'MERCY!', 1040, 200, 72, t - tRip, { color: C.red, rot: 0.08 });
    sparkle(ctx, 880, 260, t - tRip, 40);
    sparkle(ctx, 960, 420, t - tRip - 0.15, 28);
  },

  promise(ctx, t, sc) {
    const tGo = at('promise', "Let's go");
    if (t < tGo) {
      cam(ctx, 640, 380, 1.0, () => spr(ctx, 'point', 640, 690, 0.8 * breathe(t)));
    } else {
      sunburst(ctx, 640, 420, t, 0.3 * ease((t - tGo) / 0.3), '#FFD27A');
      const hop = Math.abs(Math.sin((t - tGo) * 7)) * 22 * Math.max(0, 1 - (t - tGo) / 1.2);
      const pop = back((t - tGo) / 0.3);
      cam(ctx, 640, 380, 1.0, () => spr(ctx, 'fistpump', 640, 700 - hop, 0.8 * pop));
    }
    badge(ctx, '3 MOVES', 260, 150, 60, t - at('promise', 'Three moves'), C.navy, { rot: -0.05 });
    badge(ctx, 'NO FANCY GEAR', 1020, 150, 52, t - at('promise', 'No fancy'), C.red, { rot: 0.04 });
    popText(ctx, "LET'S GO!", 640, 640, 84, t - tGo, { color: C.red, rot: -0.04 });
  },

  dips_t(ctx, t, sc) { titleCard(ctx, sc, t, '#1', 'BENCH DIPS'); },
  dia_t(ctx, t, sc) { titleCard(ctx, sc, t, '#2', 'DIAMOND PUSH-UPS'); },
  ohe_t(ctx, t, sc) { titleCard(ctx, sc, t, '#3', 'OVERHEAD EXTENSIONS'); },

  dips_how(ctx, t, sc) {
    const t90 = at('dips_how', 'ninety degrees');
    cam(ctx, 640, 400, 1.08, () => dips(ctx, t));
    popText(ctx, 'HANDS ON BENCH', 250, 130, 44, t - at('dips_how', 'Hands on a bench'), { until: at('dips_how', 'legs out') - at('dips_how', 'Hands on a bench') + 0.6 });
    popText(ctx, 'FINGERS FORWARD', 250, 190, 36, t - at('dips_how', 'fingers forward'), { color: C.red, until: at('dips_how', 'legs out') - at('dips_how', 'fingers forward') + 0.6 });
    popText(ctx, 'LEGS OUT →', 1020, 470, 48, t - at('dips_how', 'legs out'), { until: at('dips_how', 'Lower until') - at('dips_how', 'legs out') + 0.4 });
    badge(ctx, 'ELBOWS 90°', 1010, 140, 54, t - t90, C.red);
    if (t > at('dips_how', 'push back up')) arrow(ctx, 1110, 360, 1110, 250 - 14 * Math.sin(t * 6), C.green);
  },
  dips_err(ctx, t, sc) {
    const tShrug = at('dips_err', "don't let your shoulders"), tTurtle = at('dips_err', 'not a turtle');
    cam(ctx, 640, 400, 1.08, () => dips(ctx, t));
    check(ctx, 200, 120, t - sc.start - 0.2, true);
    popText(ctx, 'BACK CLOSE TO BENCH', 250, 120, 40, t - sc.start - 0.25, { align: 'left', until: tShrug - sc.start - 0.25 });
    bubble(ctx, 1040, 230, 165, t - tShrug, () => spr(ctx, 'shrug', 30, 175, 0.36));
    check(ctx, 1160, 95, t - tShrug - 0.3, false);
    popText(ctx, 'SHOULDERS ≠ EARS', 1040, 430, 38, t - tShrug - 0.4, { color: C.red });
    badge(ctx, 'LIFTER, NOT A TURTLE', 640, 660, 44, t - tTurtle, C.green, { rot: -0.02 });
  },
  dips_sets(ctx, t, sc) { cam(ctx, 640, 400, 1.08, () => dips(ctx, t)); setsBadge(ctx, t - sc.start, '3 SETS × 12 REPS'); },

  dia_how(ctx, t, sc) {
    const tLower = at('dia_how', 'Lower slow');
    const moving = t > tLower - 0.2;
    cam(ctx, 640, 420, 1.05, () => push(ctx, t - tLower + 0.2, moving ? undefined : 0));
    bubble(ctx, 1030, 200, 165, t - sc.start - 0.25, () => spr(ctx, 'diamond_hands', 0, 150, 0.36), { until: tLower - sc.start - 0.25 });
    popText(ctx, 'DIAMOND HANDS', 1030, 405, 40, t - at('dia_how', 'diamond'), { until: tLower - at('dia_how', 'diamond') });
    popText(ctx, 'UNDER YOUR CHEST', 300, 130, 42, t - at('dia_how', 'right under'), { color: C.red, until: tLower - at('dia_how', 'right under') });
    if (moving) {
      const w = pushW(t - tLower + 0.2), p = ((t - tLower + 0.2) % 2.4);
      if (p < 2.1) popText(ctx, 'SLOW ↓', 1050, 130, 62, 1, { color: C.blue });
      else popText(ctx, 'HARD ↑', 1050, 130, 68, 1, { color: C.red });
    }
  },
  dia_easy(ctx, t, sc) {
    const tWatch = at('dia_easy', "Nobody's"), tAm = at('dia_easy', 'Well, I am');
    cam(ctx, 640, 420, 1.05, () => pair(ctx, 'knee', t > tAm - 0.2 ? 1 : kneeW(t), ...KNEE));
    badge(ctx, 'KNEES = OK', 260, 120, 46, t - sc.start - 0.3, C.green);
    popText(ctx, "NOBODY'S WATCHING...", 900, 120, 40, t - tWatch, { until: tAm - tWatch + 0.1 });
    if (t > tAm) {
      const d = t - tAm;
      cameraIcon(ctx, 1150, 120, d);
      popText(ctx, '...EXCEPT ME', 900, 120, 48, d - 0.2, { color: C.red });
      ctx.fillStyle = `rgba(255,255,255,${Math.max(0, 0.85 - d * 3)})`; ctx.fillRect(0, 0, W, H);
    }
  },
  dia_sets(ctx, t, sc) { cam(ctx, 640, 420, 1.05, () => push(ctx, t)); setsBadge(ctx, t - sc.start, '3 SETS × 8–10 REPS'); },

  ohe_how(ctx, t, sc) {
    const tPack = at('ohe_how', 'or a backpack'), tElb = at('ohe_how', 'Elbows point'), tExt = at('ohe_how', 'Extend up');
    const pack = t > tPack && t < tElb;
    cam(ctx, 640, 380, 1.0, () => {
      if (pack) spr(ctx, 'backpack', OHE[0], OHE[1], OHE[2] * 1.02 * back((t - tPack) / 0.3));
      else ohe(ctx, t, t < tExt ? 0 : undefined);
    });
    popText(ctx, 'DUMBBELL', 300, 560, 48, t - at('ohe_how', 'Grab a dumbbell'), { until: tPack - at('ohe_how', 'Grab a dumbbell') });
    badge(ctx, 'OR: BACKPACK + BOOKS', 330, 560, 40, t - tPack, C.navy, { until: tElb - tPack });
    sparkle(ctx, 520, 200, t - tPack, 34);
    if (t > tElb && t < tExt + 0.8) arrow(ctx, 760, 260, 760, 120 - 8 * Math.sin(t * 8), C.red);
    popText(ctx, 'ELBOWS → CEILING', 1010, 190, 44, t - tElb, { color: C.red, until: tExt - tElb + 0.6 });
    if (t > tExt + 0.6) {
      const up = oheW(t) > 0.5;
      popText(ctx, up ? 'EXTEND ↑' : 'LOWER SLOW ↓', 1010, 190, 54, 1, { color: up ? C.red : C.blue });
    }
  },
  ohe_burn(ctx, t, sc) {
    const u = t - sc.start;
    // zoom on the raised arm of the bent (stretch) frame; triceps ≈ sprite (470, 200)
    const z = lerp(1.0, 2.0, ease(u / 0.8));
    const s = OHE[2], ref = window.SPRITES.ohe_a, [x0, , x1, y1] = ref.bbox;
    const tx = OHE[0] + (470 - (x0 + x1) / 2) * s, ty = OHE[1] + (200 - y1) * s;
    cam(ctx, lerp(640, tx, ease(u / 0.8)), lerp(380, ty + 40, ease(u / 0.8)), z, () => {
      sprGlow(ctx, 'ohe_a', OHE[0], OHE[1], s, 470, 200, 110, 0.6 + 0.4 * Math.sin(t * 9) ** 2, { ref: 'ohe_a' });
      flames(ctx, tx, ty - 10, t, 0.8);
    });
    badge(ctx, 'STRETCH = GROWTH', 640, 640, 54, t - at('ohe_burn', 'growth') + 0.1, C.red);
  },
  ohe_sets(ctx, t, sc) { cam(ctx, 640, 380, 1.0, () => ohe(ctx, t)); setsBadge(ctx, t - sc.start, '3 SETS × 12 REPS'); },

  recap(ctx, t, sc) {
    const tMonth = at('recap', 'Give it a month'), tRip = at('recap', 'sleeves suffer');
    if (t < tMonth) {
      const t3 = at('recap', 'Three moves');
      popText(ctx, "THAT'S IT!", 640, 330, 90, t - sc.start - 0.05, { color: C.red, until: t3 - sc.start - 0.25 });
      const items = [['DIPS', c => pair(c, 'dips', dipW(t), 0, 150, 0.33)], ['DIAMOND', c => pair(c, 'push', pushW(t), 0, 110, 0.32)], ['OVERHEAD', c => pair(c, 'ohe', oheW(t), 0, 160, 0.36)]];
      items.forEach(([name, fn], i) => {
        const x = 300 + i * 340, dt = t - t3 - i * 0.25;
        bubble(ctx, x, 320, 145, dt, () => fn(ctx));
        popText(ctx, name, x, 510, 40, dt - 0.15);
      });
      badge(ctx, '3 SETS • 2× A WEEK', 640, 630, 46, t - at('recap', 'three sets'), C.red);
      return;
    }
    const shake = t > tRip ? Math.sin((t - tRip) * 50) * 8 * Math.max(0, 1 - (t - tRip) * 3) : 0;
    cam(ctx, 640 + shake, 380, 1.05, () => pair(ctx, 'shirt', t > tRip ? 1 : 0, ...SHIRT));
    badge(ctx, '1 MONTH LATER', 260, 120, 48, t - tMonth, C.navy);
    sparkle(ctx, 880, 260, t - tRip, 40);
  },

  outro(ctx, t, sc) {
    const tSub = at('outro', 'Subscribe');
    cam(ctx, 640, 380, 1.0, () => spr(ctx, 'point', 380, 700, 0.8 * breathe(t)));
    const d = t - tSub;
    if (d > 0) {
      const clicked = d > 0.9;
      const s = back(d / 0.4) * (clicked && d < 1.05 ? 0.92 : 1);
      ctx.save(); ctx.translate(900, 330); ctx.scale(s, s);
      ctx.fillStyle = C.line; roundRect(ctx, -170 + 6, -48 + 7, 340, 96, 24); ctx.fill();
      ctx.fillStyle = clicked ? '#8C8C96' : C.red; roundRect(ctx, -170, -48, 340, 96, 24); ctx.fill();
      ctx.lineWidth = 5; ctx.strokeStyle = C.line; ctx.stroke();
      ctx.fillStyle = C.white; ctx.font = FONT(clicked ? 38 : 44); ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
      ctx.fillText(clicked ? 'SUBSCRIBED ✓' : 'SUBSCRIBE', 0, 3);
      ctx.restore();
      const cp = lerpP([1200, 640], [940, 350], ease((d - 0.2) / 0.6));
      cursor(ctx, cp[0], cp[1]);
      popText(ctx, 'SEE YOU ON THE NEXT REP', 900, 460, 34, d - 1.0);
    }
    const fade = clamp((t - (TL.total - 0.7)) / 0.7);
    if (fade > 0) { ctx.fillStyle = `rgba(31,42,68,${fade})`; ctx.fillRect(0, 0, W, H); }
  },
};

// ---------- frame + cues ----------
const CUT_SCENES = new Set(['fact', 'promise', 'dips_how', 'dia_how', 'ohe_how', 'recap', 'outro']);
window.renderFrame = function (t) {
  const ctx = document.getElementById('c').getContext('2d');
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.imageSmoothingQuality = 'high';
  bg(ctx);
  let cur = TL.scenes[0];
  for (const s of TL.scenes) if (t >= s.start) cur = s;
  const sc = SC[cur.id];
  ctx.save();
  if (CUT_SCENES.has(sc.id)) {
    const z = 1 + 0.06 * (1 - easeOut((t - sc.start) / 0.3));
    ctx.translate(W / 2, H / 2); ctx.scale(z, z); ctx.translate(-W / 2, -H / 2);
  }
  SCENES[sc.id](ctx, t, sc);
  ctx.restore();
};

window.CUES = [
  ['sparkle', at('hook', 'biceps'), 0.5], ['boing', at('hook', 'cooked spaghetti'), 0.8],
  ['whoosh', SC.fact.start, 0.5], ['pop', at('fact', 'triceps') + 0.2, 0.6], ['pop', at('fact', 'two thirds'), 0.7],
  ['sparkle', at('fact', 'two thirds') + 0.2, 0.5], ['whoosh', at('fact', 'Train them'), 0.5], ['rip', at('fact', 'begging for mercy'), 0.9],
  ['whoosh', SC.promise.start, 0.5], ['pop', at('promise', 'Three moves'), 0.7], ['pop', at('promise', 'No fancy'), 0.7], ['punch', at('promise', "Let's go"), 0.7],
  ['swoosh_title', SC.dips_t.start, 0.8], ['whoosh', SC.dips_how.start, 0.5],
  ['pop', at('dips_how', 'Hands on a bench'), 0.5], ['pop', at('dips_how', 'legs out'), 0.5], ['tick', at('dips_how', 'ninety degrees'), 0.8],
  ['pop', SC.dips_err.start + 0.2, 0.5], ['buzzer', at('dips_err', "don't let your shoulders") + 0.3, 0.6], ['pop', at('dips_err', 'not a turtle'), 0.6],
  ['ding', SC.dips_sets.start, 0.7],
  ['swoosh_title', SC.dia_t.start, 0.8], ['whoosh', SC.dia_how.start, 0.5], ['pop', SC.dia_how.start + 0.25, 0.5],
  ['pop', SC.dia_easy.start + 0.3, 0.5], ['shutter', at('dia_easy', 'Well, I am'), 0.9],
  ['ding', SC.dia_sets.start, 0.7],
  ['swoosh_title', SC.ohe_t.start, 0.8], ['whoosh', SC.ohe_how.start, 0.5], ['pop', at('ohe_how', 'or a backpack'), 0.6], ['sparkle', at('ohe_how', 'or a backpack'), 0.4],
  ['pop', at('ohe_how', 'Elbows point'), 0.5], ['sizzle', SC.ohe_burn.start + 0.2, 0.6], ['pop', at('ohe_burn', 'growth'), 0.5],
  ['ding', SC.ohe_sets.start, 0.7],
  ['whoosh', SC.recap.start, 0.5], ['pop', at('recap', 'Three moves'), 0.5], ['pop', at('recap', 'Three moves') + 0.25, 0.5], ['pop', at('recap', 'Three moves') + 0.5, 0.5],
  ['pop', at('recap', 'three sets'), 0.5], ['whoosh', at('recap', 'Give it a month'), 0.5], ['rip', at('recap', 'sleeves suffer'), 0.9],
  ['pop', at('outro', 'Subscribe'), 0.6], ['tick', at('outro', 'Subscribe') + 0.9, 0.9], ['sparkle', at('outro', 'Subscribe') + 0.95, 0.5],
].map(([name, t, vol]) => ({ name, t: Math.max(0, t), vol }));

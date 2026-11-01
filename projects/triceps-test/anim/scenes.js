// Scene timeline for "3 Tricep Moves". Requires rig.js and window.TIMELINE (from build/timeline.json).
// window.renderFrame(t) draws the frame at time t (seconds); window.CUES lists sound-effect cues.

const W = 1280, H = 720;
const TL = window.TIMELINE;
const SC = {};
TL.scenes.forEach((s, i) => { SC[s.id] = Object.assign({}, s, { end: i + 1 < TL.scenes.length ? TL.scenes[i + 1].start : TL.total }); });
// approximate time a phrase is spoken inside a scene (even speech rate)
function at(id, phrase) {
  const s = SC[id], i = s.text.indexOf(phrase);
  if (i < 0) throw new Error(`phrase not found: ${id} / ${phrase}`);
  return s.start + s.dur * (i / s.text.length);
}

// ---------- easing / helpers ----------
const ease = x => { x = clamp(x); return x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2; };
const easeOut = x => 1 - Math.pow(1 - clamp(x), 3);
const back = x => { x = clamp(x); const c1 = 1.9, c3 = c1 + 1; return 1 + c3 * Math.pow(x - 1, 3) + c1 * Math.pow(x - 1, 2); };
const since = (t, t0) => t - t0;
const wave = (t, period) => 0.5 - 0.5 * Math.cos(2 * Math.PI * t / period);
const FONT = (size, w = 900) => `italic ${w} ${size}px Inter, "Inter Display", sans-serif`;

function cam(ctx, cx, cy, z, fn) {
  ctx.save(); ctx.translate(W / 2, H / 2); ctx.scale(z, z); ctx.translate(-cx, -cy); fn(); ctx.restore();
}
function bg(ctx, color = C.bg) { ctx.fillStyle = color; ctx.fillRect(0, 0, W, H); }
function floor(ctx) {
  ctx.fillStyle = C.floor; ctx.fillRect(-2000, FLOOR, 5000, 2000);
  ctx.strokeStyle = C.line; ctx.lineWidth = 5; ctx.beginPath(); ctx.moveTo(-2000, FLOOR); ctx.lineTo(3000, FLOOR); ctx.stroke();
}
function shadow(ctx, x, w = 90) {
  ctx.fillStyle = 'rgba(80,40,10,0.14)'; ctx.beginPath(); ctx.ellipse(x, FLOOR + 6, w, 9, 0, 0, Math.PI * 2); ctx.fill();
}
// pop-in text with outline. dt = time since it appeared (s)
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
  ctx.save(); ctx.translate(x, y); ctx.rotate(o.rot || -0.04); ctx.scale(s, s);
  ctx.font = FONT(size); const w = ctx.measureText(txt).width + size * 1.1, h = size * 1.55;
  ctx.fillStyle = C.line; roundRect(ctx, -w / 2 + 5, -h / 2 + 6, w, h, h * 0.3); ctx.fill();
  ctx.fillStyle = color; roundRect(ctx, -w / 2, -h / 2, w, h, h * 0.3); ctx.fill();
  ctx.lineWidth = 4; ctx.strokeStyle = C.line; ctx.stroke();
  ctx.fillStyle = C.white; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText(txt, 0, 2);
  ctx.restore();
}
function roundRect(ctx, x, y, w, h, r) {
  ctx.beginPath(); ctx.moveTo(x + r, y); ctx.arcTo(x + w, y, x + w, y + h, r); ctx.arcTo(x + w, y + h, x, y + h, r);
  ctx.arcTo(x, y + h, x, y, r); ctx.arcTo(x, y, x + w, y, r); ctx.closePath();
}
function sparkle(ctx, x, y, dt, size = 26) {
  if (dt < 0 || dt > 0.9) return;
  const s = Math.sin(clamp(dt / 0.9) * Math.PI) * size;
  ctx.save(); ctx.translate(x, y); ctx.rotate(dt * 2); ctx.fillStyle = C.gold; ctx.strokeStyle = C.line; ctx.lineWidth = 3;
  ctx.beginPath();
  for (let i = 0; i < 8; i++) { const r = i % 2 ? s * 0.32 : s; const a = i * Math.PI / 4; ctx.lineTo(Math.cos(a) * r, Math.sin(a) * r); }
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
function arrow(ctx, x1, y1, x2, y2, color = C.red, w = 7) {
  const a = Math.atan2(y2 - y1, x2 - x1);
  ctx.save(); ctx.strokeStyle = color; ctx.fillStyle = color; ctx.lineWidth = w; ctx.lineCap = 'round';
  ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2 - Math.cos(a) * 12, y2 - Math.sin(a) * 12); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(x2, y2); ctx.lineTo(x2 - Math.cos(a - 0.5) * 24, y2 - Math.sin(a - 0.5) * 24);
  ctx.lineTo(x2 - Math.cos(a + 0.5) * 24, y2 - Math.sin(a + 0.5) * 24); ctx.closePath(); ctx.fill(); ctx.restore();
}
function sunburst(ctx, x, y, t, alpha) {
  if (alpha <= 0) return;
  ctx.save(); ctx.globalAlpha = alpha; ctx.translate(x, y); ctx.rotate(t * 0.4); ctx.fillStyle = C.gold;
  for (let i = 0; i < 16; i++) {
    ctx.beginPath(); ctx.moveTo(0, 0); ctx.arc(0, 0, 1400, i * Math.PI / 8, i * Math.PI / 8 + Math.PI / 16); ctx.closePath(); ctx.fill();
  }
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
  ctx.fillStyle = o.fill || '#FFF6EA'; ctx.fillRect(-r, -r, 2 * r, 2 * r); fn(); ctx.restore();
  ctx.lineWidth = 7; ctx.strokeStyle = C.line; ctx.beginPath(); ctx.arc(0, 0, r, 0, Math.PI * 2); ctx.stroke();
  ctx.restore();
}
const blinkAt = t => (t % 3.3) < 0.11;

// ---------- props ----------
function bench(ctx) {
  const { x1, x2, top } = BENCH;
  drawGroup(ctx, [
    { t: 'poly', p: [[x1 + 14, top + 10], [x1 + 30, top + 10], [x1 + 30, FLOOR], [x1 + 14, FLOOR]], f: '#7A4E2D' },
    { t: 'poly', p: [[x2 - 30, top + 10], [x2 - 14, top + 10], [x2 - 14, FLOOR], [x2 - 30, FLOOR]], f: '#7A4E2D' },
    { t: 'poly', p: [[x1, top], [x2, top], [x2, top + 20], [x1, top + 20]], f: '#A0693D' },
  ]);
}

// ---------- rep curves ----------
const dipU = t => wave(t, 2.2);
function pushU(t) {
  const p = t % 2.4;
  if (p < 1.6) return ease(p / 1.6);
  if (p < 2.05) return 1 - easeOut((p - 1.6) / 0.45);
  return 0;
}
const oheU = t => wave(t + 1.1, 2.4);

// ---------- reusable exercise views ----------
function dipsView(ctx, t, o = {}) {
  floor(ctx); bench(ctx); shadow(ctx, 560, 110);
  const u = o.u !== undefined ? o.u : dipU(t);
  const p = poseDips(u);
  if (o.shrug) p.neckOff = -16;
  return { k: drawCharacter(ctx, p, { glow: o.glow ?? 0.15 + 0.45 * u, blink: blinkAt(t), mouth: u > 0.7 ? 'grit' : null }), u };
}
function pushView(ctx, t, o = {}) {
  floor(ctx); shadow(ctx, 480, 170);
  const u = o.u !== undefined ? o.u : pushU(t);
  const p = posePushup(u, o.knees);
  return { k: drawCharacter(ctx, p, { glow: o.glow ?? 0.15 + 0.45 * u, blink: blinkAt(t), look: o.look || 0, mouth: u > 0.7 ? 'grit' : null }), u };
}
function oheView(ctx, t, o = {}) {
  floor(ctx); shadow(ctx, 640, 70);
  const u = o.u !== undefined ? o.u : oheU(t);
  const p = poseOverhead(u);
  return { k: drawCharacter(ctx, p, { glow: o.glow ?? 0.15 + 0.5 * u, blink: blinkAt(t), dumbbell: !o.backpack, backpack: o.backpack, armBehindHead: true, mouth: u > 0.7 ? 'grit' : null }), u };
}

function titleCard(ctx, sc, t, num, name) {
  const u = t - sc.start;
  const x = W * (1 - ease(u / 0.3));
  ctx.save(); ctx.translate(x, 0);
  bg(ctx, C.navy);
  ctx.fillStyle = 'rgba(255,255,255,0.05)';
  for (let i = -2; i < 12; i++) { ctx.beginPath(); ctx.moveTo(i * 140 + u * 40, 0); ctx.lineTo(i * 140 + 70 + u * 40, 0); ctx.lineTo(i * 140 - 130 + u * 40, H); ctx.lineTo(i * 140 - 200 + u * 40, H); ctx.fill(); }
  popText(ctx, num, W / 2, 285, 56, u - 0.15, { color: C.gold, stroke: C.navy });
  popText(ctx, name, W / 2, 375, 84, u - 0.25, { color: C.white, stroke: C.navy });
  const lw = 520 * ease((u - 0.45) / 0.4);
  ctx.fillStyle = C.red; ctx.fillRect(W / 2 - lw / 2, 438, lw, 10);
  ctx.restore();
}

// ---------- scenes ----------
const SCENES = {
  hook(ctx, t, sc) {
    const u = t - sc.start;
    const tSpag = at('hook', 'cooked spaghetti');
    cam(ctx, 640, 405, 1.5 + 0.12 * ease(u / 5), () => {
      floor(ctx); shadow(ctx, 640);
      const noodle = t > tSpag;
      const p = poseFlex(640);
      p.armF.a2 += Math.sin(t * 7) * deg(6);
      const k = drawCharacter(ctx, p, { blink: blinkAt(t), mouth: noodle ? 'o' : 'smile', sweat: noodle, brow: noodle ? -3 : 2,
        noodle: noodle ? { t } : null });
      if (!noodle) sparkle(ctx, k.armF[0][0] + 10, k.armF[0][1] - 40, t - at('hook', 'biceps'), 30);
    });
    popText(ctx, 'BICEPS DAY', 960, 260, 64, t - at('hook', 'biceps'), { rot: -0.06, until: tSpag - at('hook', 'biceps') });
    badge(ctx, 'SPAGHETTI ARMS', 1020, 300, 50, t - tSpag, C.red, { rot: 0.05 });
  },

  fact(ctx, t, sc) {
    const tTrain = at('fact', 'Train them');
    const tTwo = at('fact', 'two thirds');
    if (t < tTrain) {
      bg(ctx, '#FFF6EA');
      popText(ctx, 'YOUR UPPER ARM', W / 2, 120, 50, t - sc.start - 0.1);
      const A = [360, 380], B = [920, 380];
      const grow = ease((t - sc.start) / 0.5);
      ctx.save(); ctx.translate(640, 380); ctx.scale(grow, grow); ctx.translate(-640, -380);
      ctx.beginPath(); capsulePath(ctx, A, B, 95, 80); ctx.lineWidth = 12; ctx.strokeStyle = C.line; ctx.stroke();
      ctx.fillStyle = C.skin; ctx.fill();
      ctx.save(); ctx.clip();
      const split = 380 - 95 + 190 / 3;
      const bi = ease((t - at('fact', 'triceps')) / 0.5);
      ctx.globalAlpha = 0.85;
      ctx.fillStyle = C.blue; ctx.fillRect(250, 200, 760 * bi, split - 200);
      const tr = ease((t - tTwo) / 0.7);
      ctx.fillStyle = C.red; ctx.fillRect(250, split, 760 * tr, 300);
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
    const u = t - tTrain;
    cam(ctx, 640, 405, 1.6, () => {
      floor(ctx); shadow(ctx, 640);
      const p = poseFlex(640);
      p.armF.a2 += Math.sin(t * 9) * deg(5);
      const ripped = t > tRip;
      const k = drawCharacter(ctx, p, { shirt: true, sleeves: !ripped, glow: 0.3 + 0.3 * Math.sin(t * 9) ** 2, blink: blinkAt(t), mouth: 'smile', brow: 3 });
      if (ripped) sleeveBits(ctx, k.armF[0], t - tRip);
    });
    popText(ctx, 'MERCY!', 950, 190, 70, t - tRip, { color: C.red, rot: 0.08 });
    sparkle(ctx, 760, 260, t - tRip, 36);
  },

  promise(ctx, t, sc) {
    const tGo = at('promise', "Let's go");
    sunburst(ctx, 640, 470, t, 0.35 * ease((t - tGo) / 0.3));
    badge(ctx, '3 MOVES', 280, 130, 60, t - at('promise', 'Three moves'), C.navy, { rot: -0.05 });
    badge(ctx, 'NO FANCY GEAR', 1000, 130, 52, t - at('promise', 'No fancy'), C.red, { rot: 0.04 });
    cam(ctx, 640, 360, 1.1, () => {
      floor(ctx); shadow(ctx, 640);
      const jump = t > tGo ? Math.abs(Math.sin((t - tGo) * 6)) * 30 * Math.max(0, 1 - (t - tGo) / 1.2) : 0;
      const p = t > tGo ? poseStand(640, { armF: { a1: deg(-80), a2: deg(-20) }, armB: { a1: deg(-100), a2: deg(-20) } }) : poseStand(640);
      p.pelvis = add(p.pelvis, [0, -jump]);
      if (jump) { p.legF = { ik: [648, FLOOR - 8 - jump], bend: -1 }; p.legB = { ik: [630, FLOOR - 8 - jump], bend: -1 }; }
      drawCharacter(ctx, p, { blink: blinkAt(t), mouth: 'smile', brow: 3 });
    });
    popText(ctx, "LET'S GO!", 640, 640, 80, t - tGo, { color: C.red, rot: -0.04 });
  },

  dips_t(ctx, t, sc) { titleCard(ctx, sc, t, '#1', 'BENCH DIPS'); },
  dia_t(ctx, t, sc) { titleCard(ctx, sc, t, '#2', 'DIAMOND PUSH-UPS'); },
  ohe_t(ctx, t, sc) { titleCard(ctx, sc, t, '#3', 'OVERHEAD EXTENSIONS'); },

  dips_how(ctx, t, sc) {
    let r;
    cam(ctx, 500, 450, 1.7, () => {
      r = dipsView(ctx, t);
      const t90 = at('dips_how', 'ninety degrees');
      if (t > t90) {
        const [E] = r.k.armF; const a = clamp((r.u - 0.6) / 0.4);
        ctx.save(); ctx.globalAlpha = a; ctx.strokeStyle = C.red; ctx.lineWidth = 5;
        ctx.beginPath(); ctx.arc(E[0], E[1], 34, deg(-80), deg(10)); ctx.stroke(); ctx.restore();
      }
    });
    popText(ctx, 'HANDS ON BENCH', 240, 300, 44, t - at('dips_how', 'Hands on a bench'), { until: at('dips_how', 'legs out') - at('dips_how', 'Hands on a bench') + 0.6 });
    popText(ctx, 'FINGERS FORWARD', 240, 360, 36, t - at('dips_how', 'fingers forward'), { color: C.red, until: at('dips_how', 'legs out') - at('dips_how', 'fingers forward') + 0.6 });
    popText(ctx, 'LEGS OUT', 1000, 560, 48, t - at('dips_how', 'legs out'), { until: at('dips_how', 'Lower until') - at('dips_how', 'legs out') + 0.4 });
    badge(ctx, 'ELBOWS 90°', 960, 160, 54, t - at('dips_how', 'ninety degrees'), C.red);
    if (t > at('dips_how', 'push back up')) arrow(ctx, 1040, 330, 1040, 230 - 20 * Math.sin(t * 6), C.green);
  },
  dips_err(ctx, t, sc) {
    const tShrug = at('dips_err', "don't let your shoulders");
    const tTurtle = at('dips_err', 'not a turtle');
    cam(ctx, 500, 450, 1.7, () => dipsView(ctx, t));
    check(ctx, 250, 170, t - sc.start - 0.2, true);
    popText(ctx, 'BACK CLOSE', 420, 170, 48, t - sc.start - 0.25, { align: 'left', until: tShrug - sc.start - 0.25 });
    bubble(ctx, 990, 250, 150, t - tShrug, () => {
      ctx.translate(0, 0); ctx.scale(2.1, 2.1); ctx.translate(-482, -330);
      bench(ctx); drawCharacter(ctx, Object.assign(poseDips(0.7), { neckOff: -18 }), { mouth: 'grit', brow: -3, blink: blinkAt(t) });
    });
    check(ctx, 1100, 130, t - tShrug - 0.3, false);
    popText(ctx, 'SHOULDERS ≠ EARS', 990, 440, 40, t - tShrug - 0.4, { color: C.red });
    badge(ctx, 'LIFTER, NOT A TURTLE', 640, 640, 46, t - tTurtle, C.green, { rot: -0.02 });
  },
  dips_sets(ctx, t, sc) {
    cam(ctx, 500, 450, 1.7, () => dipsView(ctx, t));
    setsBadge(ctx, t - sc.start, '3 SETS × 12 REPS');
  },

  dia_how(ctx, t, sc) {
    const tLower = at('dia_how', 'Lower slow');
    const moving = t > tLower - 0.3;
    let r;
    cam(ctx, 485, 495, 1.65, () => { r = pushView(ctx, t - tLower + 0.3, { u: moving ? undefined : 0 }); });
    bubble(ctx, 300, 210, 150, t - sc.start - 0.3, () => diamondHands(ctx, t), { until: tLower - sc.start - 0.3 });
    popText(ctx, 'DIAMOND HANDS', 300, 410, 40, t - at('dia_how', 'diamond'), { until: tLower - at('dia_how', 'diamond') });
    popText(ctx, 'UNDER YOUR CHEST', 960, 130, 44, t - at('dia_how', 'right under'), { color: C.red, until: tLower - at('dia_how', 'right under') });
    if (moving) {
      const p = (t - tLower + 0.3) % 2.4;
      if (p < 1.6) popText(ctx, 'SLOW ↓', 1060, 130, 60, 1, { color: C.blue });
      else if (p < 2.1) popText(ctx, 'HARD ↑', 1060, 130, 66, 1, { color: C.red });
    }
  },
  dia_easy(ctx, t, sc) {
    const tWatch = at('dia_easy', "Nobody's");
    const tAm = at('dia_easy', 'Well, I am');
    cam(ctx, 520, 500, 1.65, () => { pushView(ctx, t, { knees: true, look: t > tAm ? 3 : 0 }); });
    badge(ctx, 'KNEES = OK', 330, 160, 46, t - sc.start - 0.3, C.green);
    popText(ctx, "NOBODY'S WATCHING...", 900, 170, 40, t - tWatch, { until: tAm - tWatch + 0.1 });
    if (t > tAm) {
      const d = t - tAm;
      cameraIcon(ctx, 1080, 170, d);
      popText(ctx, '...EXCEPT ME', 860, 170, 48, d - 0.2, { color: C.red });
      ctx.fillStyle = `rgba(255,255,255,${Math.max(0, 0.85 - d * 3)})`; ctx.fillRect(0, 0, W, H);
    }
  },
  dia_sets(ctx, t, sc) {
    cam(ctx, 485, 495, 1.65, () => pushView(ctx, t));
    setsBadge(ctx, t - sc.start, '3 SETS × 8–10 REPS');
  },

  ohe_how(ctx, t, sc) {
    const tPack = at('ohe_how', 'or a backpack'), tHold = at('ohe_how', 'and hold');
    const tElb = at('ohe_how', 'Elbows point'), tExt = at('ohe_how', 'Extend up');
    const pack = t > tPack && t < tElb;
    let r;
    cam(ctx, 640, 360, 1.45, () => {
      r = oheView(ctx, t, { backpack: pack });
      if (t > tElb && t < tExt + 0.6) {
        const E = r.k.armF[0];
        arrow(ctx, E[0] + 50, E[1] + 30, E[0] + 50, E[1] - 40 - 6 * Math.sin(t * 8), C.red, 6);
      }
    });
    popText(ctx, 'DUMBBELL', 300, 560, 48, t - at('ohe_how', 'Grab a dumbbell'), { until: tPack - at('ohe_how', 'Grab a dumbbell') });
    badge(ctx, 'OR: BACKPACK + BOOKS', 300, 560, 40, t - tPack, C.navy, { until: tElb - tPack });
    sparkle(ctx, 700, 150, t - tPack, 34);
    popText(ctx, 'ELBOWS → CEILING', 960, 190, 44, t - tElb, { color: C.red, until: tExt - tElb + 0.6 });
    if (t > tExt) {
      const up = r.u < 0.5;
      popText(ctx, up ? 'EXTEND ↑' : 'LOWER SLOW ↓', 960, 190, 54, t - tExt - 0.6, { color: up ? C.red : C.blue });
    }
  },
  ohe_burn(ctx, t, sc) {
    const u = t - sc.start;
    let r;
    cam(ctx, 650, 260, lerp(1.45, 2.2, ease(u / 0.8)), () => {
      r = oheView(ctx, t, { u: 0.85 + 0.15 * Math.sin(t * 2), glow: 0.55 + 0.35 * Math.sin(t * 10) ** 2 });
      flames(ctx, lerpP(r.k.armF[0], r.k.S, 0.5), t);
    });
    badge(ctx, 'STRETCH = GROWTH', 640, 620, 54, u - at('ohe_burn', 'growth') + sc.start + 0.1, C.red);
  },
  ohe_sets(ctx, t, sc) {
    cam(ctx, 640, 360, 1.45, () => oheView(ctx, t));
    setsBadge(ctx, t - sc.start, '3 SETS × 12 REPS');
  },

  recap(ctx, t, sc) {
    const tMonth = at('recap', 'Give it a month'), tRip = at('recap', 'sleeves suffer');
    if (t < tMonth) {
      const t3 = at('recap', 'Three moves');
      const items = [['DIPS', dipsMini], ['DIAMOND', pushMini], ['OVERHEAD', oheMini]];
      items.forEach(([name, fn], i) => {
        const x = 300 + i * 340, dt = t - t3 - i * 0.25;
        bubble(ctx, x, 320, 140, dt, () => fn(ctx, t));
        popText(ctx, name, x, 505, 40, dt - 0.15);
      });
      popText(ctx, "THAT'S IT!", 640, 330, 90, t - sc.start - 0.05, { color: C.red, until: t3 - sc.start - 0.25 });
      badge(ctx, '3 SETS • 2× A WEEK', 640, 620, 46, t - at('recap', 'three sets'), C.red);
      return;
    }
    cam(ctx, 640, 405, 1.6, () => {
      floor(ctx); shadow(ctx, 640);
      const p = poseFlex(640); p.armF.a2 += Math.sin(t * 9) * deg(5);
      const k = drawCharacter(ctx, p, { shirt: true, sleeves: t < tRip, glow: 0.4, blink: blinkAt(t), mouth: 'smile', brow: 3 });
      if (t > tRip) sleeveBits(ctx, k.armF[0], t - tRip);
    });
    badge(ctx, '1 MONTH LATER', 300, 300, 50, t - tMonth, C.navy);
    sparkle(ctx, 760, 260, t - tRip, 40);
  },

  outro(ctx, t, sc) {
    const tSub = at('outro', 'Subscribe');
    cam(ctx, 560, 420, 1.25, () => {
      floor(ctx); shadow(ctx, 420);
      drawCharacter(ctx, poseWave(420, t), { blink: blinkAt(t), mouth: 'smile', brow: 3 });
    });
    const d = t - tSub;
    if (d > 0) {
      const clicked = d > 0.9;
      const s = back(d / 0.4) * (clicked && d < 1.05 ? 0.92 : 1);
      ctx.save(); ctx.translate(860, 340); ctx.scale(s, s);
      ctx.fillStyle = C.line; roundRect(ctx, -170 + 6, -48 + 7, 340, 96, 24); ctx.fill();
      ctx.fillStyle = clicked ? '#8C8C96' : C.red; roundRect(ctx, -170, -48, 340, 96, 24); ctx.fill();
      ctx.lineWidth = 5; ctx.strokeStyle = C.line; ctx.stroke();
      ctx.fillStyle = C.white; ctx.font = FONT(clicked ? 38 : 44); ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
      ctx.fillText(clicked ? 'SUBSCRIBED ✓' : 'SUBSCRIBE', 0, 3);
      ctx.restore();
      // cursor
      const cp = lerpP([1180, 640], [900, 360], ease((d - 0.2) / 0.6));
      cursor(ctx, cp[0], cp[1]);
      popText(ctx, 'SEE YOU ON THE NEXT REP', 860, 470, 34, d - 1.0);
    }
    const fade = clamp((t - (TL.total - 0.7)) / 0.7);
    if (fade > 0) { ctx.fillStyle = `rgba(31,42,68,${fade})`; ctx.fillRect(0, 0, W, H); }
  },
};

// ---------- extra drawings ----------
function setsBadge(ctx, dt, txt) { badge(ctx, txt, 640, 130, 52, dt - 0.05, C.navy); }
function sleeveBits(ctx, S, dt) {
  [[-1, -1.3], [1.2, -1.0], [0.3, -1.6]].forEach(([vx, vy], i) => {
    const x = S[0] + vx * 260 * dt, y = S[1] + vy * 260 * dt + 600 * dt * dt;
    ctx.save(); ctx.translate(x, y); ctx.rotate(dt * (4 + i)); ctx.fillStyle = C.shirt; ctx.strokeStyle = C.line; ctx.lineWidth = 4;
    ctx.beginPath(); ctx.moveTo(-18, -10); ctx.lineTo(12, -14); ctx.lineTo(20, 4); ctx.lineTo(4, 14); ctx.lineTo(-14, 8); ctx.closePath();
    ctx.fill(); ctx.stroke(); ctx.restore();
  });
}
function flames(ctx, c, t) {
  for (let i = 0; i < 5; i++) {
    const ph = (t * 1.6 + i / 5) % 1;
    const x = c[0] - 30 + i * 15 + Math.sin(t * 8 + i) * 4, y = c[1] - ph * 70;
    const s = (1 - ph) * 16 + 4;
    ctx.save(); ctx.globalAlpha = 1 - ph; ctx.fillStyle = i % 2 ? C.gold : '#FF7A2F'; ctx.strokeStyle = C.line; ctx.lineWidth = 2;
    ctx.beginPath(); ctx.moveTo(x, y - s * 1.6); ctx.quadraticCurveTo(x + s, y, x, y + s * 0.6); ctx.quadraticCurveTo(x - s, y, x, y - s * 1.6);
    ctx.fill(); ctx.stroke(); ctx.restore();
  }
}
function diamondHands(ctx, t) {
  // top-down view of two hands making a diamond
  ctx.save(); ctx.scale(1.15, 1.15);
  for (const sgn of [-1, 1]) {
    ctx.save(); ctx.scale(sgn, 1);
    const shapes = [
      { t: 'cap', a: [70, 60], b: [95, 140], r1: 34, r2: 30, f: C.skin },       // palm + wrist
      { t: 'cap', a: [62, 30], b: [6, -40], r1: 10, r2: 9, f: C.skin },         // index finger to top
      { t: 'cap', a: [58, 70], b: [6, 34], r1: 10, r2: 9, f: C.skin },          // thumb to bottom
      { t: 'cap', a: [80, 30], b: [62, -52], r1: 9, r2: 8, f: C.skin },
      { t: 'cap', a: [96, 34], b: [92, -48], r1: 9, r2: 8, f: C.skin },
      { t: 'cap', a: [108, 44], b: [118, -30], r1: 8, r2: 7, f: C.skin },
    ];
    drawGroup(ctx, shapes);
    ctx.restore();
  }
  const pulse = 0.6 + 0.4 * Math.sin(t * 6);
  ctx.strokeStyle = C.red; ctx.lineWidth = 6; ctx.globalAlpha = pulse;
  ctx.beginPath(); ctx.moveTo(0, -36); ctx.lineTo(44, 0); ctx.lineTo(0, 30); ctx.lineTo(-44, 0); ctx.closePath(); ctx.stroke();
  ctx.restore();
}
function cameraIcon(ctx, x, y, dt) {
  const s = back(dt / 0.35);
  ctx.save(); ctx.translate(x, y); ctx.scale(s, s); ctx.rotate(0.12);
  ctx.fillStyle = '#3B4256'; ctx.strokeStyle = C.line; ctx.lineWidth = 5;
  roundRect(ctx, -55, -36, 110, 76, 14); ctx.fill(); ctx.stroke();
  ctx.fillStyle = '#3B4256'; roundRect(ctx, -22, -50, 44, 18, 6); ctx.fill(); ctx.stroke();
  ctx.fillStyle = '#9EC9FF'; ctx.beginPath(); ctx.arc(0, 2, 24, 0, Math.PI * 2); ctx.fill(); ctx.stroke();
  ctx.fillStyle = C.red; ctx.beginPath(); ctx.arc(38, -22, 6, 0, Math.PI * 2); ctx.fill();
  ctx.restore();
}
function cursor(ctx, x, y) {
  ctx.save(); ctx.translate(x, y); ctx.fillStyle = C.white; ctx.strokeStyle = C.line; ctx.lineWidth = 4;
  ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(0, 46); ctx.lineTo(12, 35); ctx.lineTo(22, 56); ctx.lineTo(31, 52); ctx.lineTo(21, 31); ctx.lineTo(36, 30); ctx.closePath();
  ctx.fill(); ctx.stroke(); ctx.restore();
}
function dipsMini(ctx, t) { ctx.scale(0.62, 0.62); ctx.translate(-520, -430); dipsView(ctx, t); }
function pushMini(ctx, t) { ctx.scale(0.62, 0.62); ctx.translate(-470, -470); pushView(ctx, t); }
function oheMini(ctx, t) { ctx.scale(0.55, 0.55); ctx.translate(-640, -380); oheView(ctx, t); }

// ---------- frame + cues ----------
const CUT_SCENES = new Set(['fact', 'promise', 'dips_how', 'dia_how', 'ohe_how', 'recap', 'outro']);
window.renderFrame = function (t) {
  const ctx = document.getElementById('c').getContext('2d');
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  bg(ctx);
  let cur = TL.scenes[0];
  for (const s of TL.scenes) if (t >= s.start) cur = s;
  const sc = SC[cur.id];
  ctx.save();
  if (CUT_SCENES.has(sc.id)) { // zoom-punch on cuts
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
  ['swoosh_title', SC.dia_t.start, 0.8], ['whoosh', SC.dia_how.start, 0.5], ['pop', SC.dia_how.start + 0.3, 0.5],
  ['pop', SC.dia_easy.start + 0.3, 0.5], ['shutter', at('dia_easy', 'Well, I am'), 0.9],
  ['ding', SC.dia_sets.start, 0.7],
  ['swoosh_title', SC.ohe_t.start, 0.8], ['whoosh', SC.ohe_how.start, 0.5], ['pop', at('ohe_how', 'or a backpack'), 0.6], ['sparkle', at('ohe_how', 'or a backpack'), 0.4],
  ['pop', at('ohe_how', 'Elbows point'), 0.5], ['sizzle', SC.ohe_burn.start + 0.2, 0.6], ['pop', at('ohe_burn', 'growth'), 0.5],
  ['ding', SC.ohe_sets.start, 0.7],
  ['whoosh', SC.recap.start, 0.5], ['pop', at('recap', 'Three moves'), 0.5], ['pop', at('recap', 'Three moves') + 0.25, 0.5], ['pop', at('recap', 'Three moves') + 0.5, 0.5],
  ['pop', at('recap', 'three sets'), 0.5], ['whoosh', at('recap', 'Give it a month'), 0.5], ['rip', at('recap', 'sleeves suffer'), 0.9],
  ['pop', at('outro', 'Subscribe'), 0.6], ['tick', at('outro', 'Subscribe') + 0.9, 0.9], ['sparkle', at('outro', 'Subscribe') + 0.95, 0.5],
].map(([name, t, vol]) => ({ name, t: Math.max(0, t), vol }));

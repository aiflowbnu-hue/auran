// 2D cartoon character rig, drawn with Canvas 2D.
// Original mascot "Coach Ember": orange skin, red headband, navy shorts, faceless except one big eye.
// Side view, facing right. Poses are joint angles / IK targets in world pixels.

const C = {
  skin: '#F4A259', skinBack: '#D88A45', shade: 'rgba(150,70,20,0.28)',
  line: '#1E1B2E', shorts: '#2E3A6B', shortsBack: '#222C52',
  band: '#E63946', shirt: '#2BB3A3', shirtBack: '#23968A',
  bg: '#FBEEDC', navy: '#1F2A44', red: '#E63946', green: '#2BB673', white: '#FFFFFF',
  gold: '#FFC94A', blue: '#4C7BD9', floor: '#E9D6BC',
};
const LEN = { head: 27, neck: 11, torso: 110, ua: 64, fa: 60, th: 70, sh: 66, foot: 26 };
const OUT = 4.5; // outline half-width

const deg = d => d * Math.PI / 180;
const dir = a => [Math.cos(a), Math.sin(a)];
const add = (p, v, s = 1) => [p[0] + v[0] * s, p[1] + v[1] * s];
const sub = (a, b) => [a[0] - b[0], a[1] - b[1]];
const len = v => Math.hypot(v[0], v[1]);
const ang = v => Math.atan2(v[1], v[0]);
const lerp = (a, b, t) => a + (b - a) * t;
const lerpP = (a, b, t) => [lerp(a[0], b[0], t), lerp(a[1], b[1], t)];
const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
const normA = a => { while (a > Math.PI) a -= 2 * Math.PI; while (a < -Math.PI) a += 2 * Math.PI; return a; };

// two-bone IK: returns [mid, end]
function ik(A, T, l1, l2, bend) {
  const v = sub(T, A);
  let d = clamp(len(v), Math.abs(l1 - l2) + 0.01, l1 + l2 - 0.01);
  const base = ang(v);
  const c = clamp((l1 * l1 + d * d - l2 * l2) / (2 * l1 * d), -1, 1);
  const a1 = base + bend * Math.acos(c);
  const M = add(A, dir(a1), l1);
  const E = add(M, dir(ang(sub(T, M))), l2);
  return [M, E];
}

function limbJoints(root, spec, l1, l2) {
  if (spec.pts) return spec.pts;
  if (spec.ik) return ik(root, spec.ik, l1, l2, spec.bend || 1);
  const M = add(root, dir(spec.a1), l1);
  return [M, add(M, dir(spec.a1 + spec.a2), l2)];
}

// ---------- shape helpers (union-outline: stroke pass, then fill pass) ----------
function capsulePath(ctx, A, B, r1, r2) {
  const a = ang(sub(B, A));
  ctx.moveTo(...add(A, dir(a + Math.PI / 2), r1));
  ctx.arc(A[0], A[1], r1, a + Math.PI / 2, a - Math.PI / 2);
  ctx.lineTo(...add(B, dir(a - Math.PI / 2), r2));
  ctx.arc(B[0], B[1], r2, a - Math.PI / 2, a + Math.PI / 2);
  ctx.closePath();
}
function shapePath(ctx, s) {
  ctx.beginPath();
  if (s.t === 'cap') capsulePath(ctx, s.a, s.b, s.r1, s.r2);
  else if (s.t === 'ell') ctx.ellipse(s.c[0], s.c[1], s.rx, s.ry, s.rot || 0, 0, Math.PI * 2);
  else if (s.t === 'poly') { ctx.moveTo(...s.p[0]); s.p.slice(1).forEach(q => ctx.lineTo(...q)); ctx.closePath(); }
}
function drawGroup(ctx, shapes) {
  ctx.lineJoin = 'round';
  ctx.strokeStyle = C.line; ctx.lineWidth = OUT * 2;
  for (const s of shapes) { if (s.noOutline) continue; shapePath(ctx, s); ctx.stroke(); }
  for (const s of shapes) {
    shapePath(ctx, s); ctx.fillStyle = s.f; ctx.fill();
    if (s.glow) { ctx.save(); ctx.globalAlpha = s.glow; ctx.fillStyle = C.red; ctx.fill(); ctx.restore(); }
  }
}

// ---------- skeleton ----------
function skeleton(p) {
  const P = p.pelvis;
  const at = p.torsoA ?? deg(-90);
  const S = add(P, dir(at), LEN.torso);
  const neckLen = LEN.neck + (p.neckOff || 0);
  const N = add(S, dir(at + (p.neckA || 0)), neckLen);
  const H = add(N, dir(at + (p.neckA || 0)), LEN.head * 0.85);
  const SB = add(S, [-5, -2]);
  const PB = add(P, [-4, -2]);
  const armF = limbJoints(S, p.armF, LEN.ua, LEN.fa);
  const armB = limbJoints(SB, p.armB || p.armF, LEN.ua, LEN.fa);
  const legF = limbJoints(P, p.legF, LEN.th, LEN.sh);
  const legB = limbJoints(PB, p.legB || p.legF, LEN.th, LEN.sh);
  return { P, PB, S, SB, N, H, at, armF, armB, legF, legB };
}

function armShapes(S, [E, W], fill, glow, sign, sleeve) {
  const aU = ang(sub(E, S)), aF = ang(sub(W, E));
  let rel = normA(aF - aU);
  const sg = Math.abs(rel) > 0.08 ? Math.sign(rel) : (sign || -1);
  const perp = [-Math.sin(aU), Math.cos(aU)];
  const nb = [perp[0] * sg, perp[1] * sg]; // bicep side
  const mid = lerpP(S, E, 0.48);
  const shapes = [
    { t: 'ell', c: add(mid, nb, -9), rx: LEN.ua * 0.4, ry: 14, rot: aU, f: fill, glow }, // triceps
    { t: 'ell', c: add(mid, nb, 7), rx: LEN.ua * 0.32, ry: 12, rot: aU, f: fill },       // biceps
    { t: 'cap', a: S, b: E, r1: 18, r2: 11, f: fill },
    { t: 'cap', a: E, b: W, r1: 13, r2: 9, f: fill },
    { t: 'ell', c: lerpP(E, W, 0.3), rx: LEN.fa * 0.28, ry: 12, rot: aF, f: fill },
    { t: 'ell', c: add(W, dir(aF), 6), rx: 12, ry: 11, rot: aF, f: fill },
  ];
  if (sleeve) shapes.push({ t: 'cap', a: S, b: lerpP(S, E, 0.45), r1: 19, r2: 16, f: sleeve });
  return shapes;
}
function legShapes(P, [K, A], fill, shorts, face) {
  const fdir = face === 'up' ? deg(-80) : 0;
  return [
    { t: 'cap', a: P, b: K, r1: 22, r2: 13, f: fill },
    { t: 'ell', c: lerpP(P, K, 0.45), rx: LEN.th * 0.38, ry: 17, rot: ang(sub(K, P)), f: fill },
    { t: 'cap', a: K, b: A, r1: 13, r2: 8, f: fill },
    { t: 'ell', c: add(lerpP(K, A, 0.3), [-4, 0]), rx: LEN.sh * 0.25, ry: 11, rot: ang(sub(A, K)), f: fill },
    { t: 'cap', a: A, b: add(A, dir(fdir), LEN.foot), r1: 8, r2: 7, f: fill },
    { t: 'cap', a: P, b: lerpP(P, K, 0.5), r1: 24, r2: 20, f: shorts },
  ];
}

// draw character. opts: {glow, blink, look, mouth, shirt, sleeves, noodle, shrug, dumbbell, backpack, sweat}
function drawCharacter(ctx, p, o = {}) {
  const k = skeleton(p);
  ctx.save();
  if (p.flip) { ctx.translate(k.P[0], 0); ctx.scale(-1, 1); ctx.translate(-k.P[0], 0); }
  const glow = o.glow || 0;
  const shirtF = o.shirt ? C.shirt : null, shirtB = o.shirt ? C.shirtBack : null;
  // back arm & back leg
  drawGroup(ctx, armShapes(k.SB, k.armB, C.skinBack, glow * 0.6, p.armSign, o.sleeves ? shirtB : null));
  if (o.dumbbell && o.dumbbellBoth) drawDumbbell(ctx, k.armB[1], ang(sub(k.armB[1], k.armB[0])), 0.95);
  drawGroup(ctx, legShapes(k.PB, k.legB, C.skinBack, C.shortsBack, p.footUp));
  // torso
  const at = k.at, perp = dir(at + Math.PI / 2); // perp points to the back for a right-facing upright torso
  const torso = [
    { t: 'ell', c: add(lerpP(k.P, k.S, 0.1), perp, 10), rx: 26, ry: 24, rot: at, f: C.skin },      // glute
    { t: 'cap', a: k.P, b: k.S, r1: 29, r2: 38, f: shirtF || C.skin },
    { t: 'ell', c: add(lerpP(k.P, k.S, 0.78), perp, -16), rx: 34, ry: 28, rot: at, f: shirtF || C.skin }, // chest
    { t: 'ell', c: add(lerpP(k.P, k.S, 0.7), perp, 14), rx: 34, ry: 20, rot: at, f: shirtF || C.skin },   // lats
    { t: 'cap', a: k.P, b: add(k.P, dir(at), 30), r1: 32, r2: 31, f: C.shorts },
  ];
  drawGroup(ctx, torso);
  if (!o.shirt) { // ab lines
    ctx.strokeStyle = C.shade; ctx.lineWidth = 3; ctx.lineCap = 'round';
    for (let i = 0; i < 3; i++) {
      const c = add(lerpP(k.P, k.S, 0.36 + i * 0.13), perp, -22);
      ctx.beginPath(); ctx.moveTo(...add(c, dir(at + Math.PI / 2), -6)); ctx.lineTo(...add(c, dir(at + Math.PI / 2), 6)); ctx.stroke();
    }
  }
  // front leg
  drawGroup(ctx, legShapes(k.P, k.legF, C.skin, C.shorts, p.footUp));
  // front arm (optionally behind the head, e.g. overhead extensions) + head
  const frontArm = () => {
    if (o.noodle) drawNoodleArm(ctx, k.S, o.noodle);
    else drawGroup(ctx, armShapes(k.S, k.armF, C.skin, glow, p.armSign, o.sleeves ? shirtF : null));
    if (o.dumbbell) drawDumbbell(ctx, k.armF[1], ang(sub(k.armF[1], k.armF[0])), 1);
    if (o.backpack) drawBackpack(ctx, k.armF[1], ang(sub(k.armF[1], k.armF[0])));
  };
  if (o.armBehindHead) { frontArm(); drawHead(ctx, k, o); ctx.restore(); return k; }
  drawHead(ctx, k, o);
  if (o.noodle) drawNoodleArm(ctx, k.S, o.noodle);
  else drawGroup(ctx, armShapes(k.S, k.armF, C.skin, glow, p.armSign, o.sleeves ? shirtF : null));
  if (o.dumbbell) drawDumbbell(ctx, k.armF[1], ang(sub(k.armF[1], k.armF[0])), 1);
  if (o.backpack) drawBackpack(ctx, k.armF[1], ang(sub(k.armF[1], k.armF[0])));
  ctx.restore();
  return k;
}

function drawHead(ctx, k, o) {
  const a = k.at + 0; // head axis
  const up = dir(a), fwd = dir(a + Math.PI / 2 * -1); // fwd: rotate -90 => facing direction for upright
  const F = [-fwd[0], -fwd[1]]; // forward (right when upright)
  drawGroup(ctx, [
    { t: 'cap', a: k.S, b: k.N, r1: 15, r2: 14, f: C.skin },
    { t: 'ell', c: k.H, rx: LEN.head * 1.02, ry: LEN.head * 0.92, rot: a, f: C.skin },
    { t: 'ell', c: add(k.H, F, 14), rx: 12, ry: 13, rot: a, f: C.skin }, // face/jaw bump
  ]);
  // headband
  ctx.save();
  ctx.beginPath(); ctx.ellipse(k.H[0], k.H[1], LEN.head * 1.02, LEN.head * 0.92, a, 0, Math.PI * 2); ctx.clip();
  const bc = add(k.H, up, 12);
  ctx.translate(...bc); ctx.rotate(a + Math.PI / 2);
  ctx.fillStyle = C.band; ctx.fillRect(-40, -6, 80, 11);
  ctx.restore();
  ctx.save(); ctx.translate(...bc); ctx.rotate(a + Math.PI / 2);
  ctx.strokeStyle = C.line; ctx.lineWidth = 3;
  // tails of the band at the back
  ctx.fillStyle = C.band;
  ctx.beginPath(); ctx.moveTo(-26, -3); ctx.lineTo(-44, 6); ctx.lineTo(-40, 12); ctx.lineTo(-25, 5); ctx.closePath(); ctx.fill(); ctx.stroke();
  ctx.restore();
  // eye
  const E = add(add(k.H, F, 13), up, 3);
  const blink = o.blink ? 0.12 : 1;
  ctx.save(); ctx.translate(...E); ctx.rotate(a + Math.PI / 2);
  ctx.fillStyle = C.white; ctx.strokeStyle = C.line; ctx.lineWidth = 2.5;
  ctx.beginPath(); ctx.ellipse(0, 0, 6.5, 9 * blink, 0, 0, Math.PI * 2); ctx.fill(); ctx.stroke();
  if (blink > 0.5) { ctx.fillStyle = C.line; ctx.beginPath(); ctx.arc(2 + (o.look || 0), 1, 3, 0, Math.PI * 2); ctx.fill(); }
  // brow
  ctx.lineWidth = 3.5; ctx.beginPath(); ctx.moveTo(-6, -13 - (o.brow || 0)); ctx.lineTo(8, -11 + (o.brow || 0) * 0.5); ctx.stroke();
  // mouth
  if (o.mouth) {
    ctx.lineWidth = 3; ctx.beginPath();
    if (o.mouth === 'smile') ctx.arc(8, 16, 7, 0.1 * Math.PI, 0.8 * Math.PI);
    else if (o.mouth === 'grit') { ctx.moveTo(2, 18); ctx.lineTo(14, 18); }
    else if (o.mouth === 'o') { ctx.ellipse(10, 18, 3, 4, 0, 0, Math.PI * 2); }
    ctx.stroke();
  }
  ctx.restore();
  if (o.sweat) {
    const s = add(add(k.H, up, 16), [-fwd[0] * -18, -fwd[1] * -18]);
    ctx.fillStyle = '#7EC8F2'; ctx.strokeStyle = C.line; ctx.lineWidth = 2.5;
    ctx.beginPath(); ctx.moveTo(s[0], s[1] - 12); ctx.quadraticCurveTo(s[0] + 8, s[1], s[0], s[1] + 5);
    ctx.quadraticCurveTo(s[0] - 8, s[1], s[0], s[1] - 12); ctx.fill(); ctx.stroke();
  }
}

function drawNoodleArm(ctx, S, n) {
  // floppy spaghetti arm hanging from the shoulder, wobbling
  const pts = [];
  for (let i = 0; i <= 24; i++) {
    const u = i / 24;
    const x = S[0] + 70 * u + Math.sin(u * 7 + n.t * 9) * 10 * u;
    const y = S[1] + 125 * u * u + 10 * u + Math.cos(u * 5 + n.t * 7) * 6 * u;
    pts.push([x, y]);
  }
  ctx.lineCap = 'round'; ctx.lineJoin = 'round';
  ctx.beginPath(); pts.forEach((q, i) => i ? ctx.lineTo(...q) : ctx.moveTo(...q));
  ctx.strokeStyle = C.line; ctx.lineWidth = 18; ctx.stroke();
  ctx.strokeStyle = C.skin; ctx.lineWidth = 9; ctx.stroke();
  const W = pts[pts.length - 1];
  drawGroup(ctx, [{ t: 'ell', c: W, rx: 9, ry: 8, f: C.skin }]);
}

function drawDumbbell(ctx, W, aF, s = 1) {
  ctx.save(); ctx.translate(...add(W, dir(aF), 6)); ctx.rotate(aF + Math.PI / 2); ctx.scale(s, s);
  drawGroup(ctx, [
    { t: 'cap', a: [-34, 0], b: [34, 0], r1: 5, r2: 5, f: '#9AA3B5' },
    { t: 'cap', a: [-32, -1], b: [-32, 1], r1: 21, r2: 21, f: '#3B4256' },
    { t: 'cap', a: [32, -1], b: [32, 1], r1: 21, r2: 21, f: '#3B4256' },
  ]);
  ctx.restore();
}
function drawBackpack(ctx, W, aF) {
  ctx.save(); ctx.translate(...add(W, dir(aF), 26)); ctx.rotate(aF - Math.PI / 2);
  drawGroup(ctx, [
    { t: 'cap', a: [0, -18], b: [0, 18], r1: 30, r2: 30, f: '#E8833A' },
    { t: 'cap', a: [0, 14], b: [0, 22], r1: 20, r2: 20, f: '#C4652A' },
  ]);
  ctx.strokeStyle = C.line; ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(-18, 6); ctx.lineTo(18, 6); ctx.stroke();
  ctx.restore();
}

// ---------- exercise poses ----------
const FLOOR = 560;
const BENCH = { x1: 300, x2: 480, top: 470 };
function poseDips(u) { // u: 0 top .. 1 bottom
  const hand = [470, BENCH.top - 2];
  const S = lerpP([478, 346], [490, 384], u);
  const at = deg(-98);
  const P = add(S, dir(at), -LEN.torso);
  return { pelvis: P, torsoA: at, neckA: deg(4), armF: { ik: hand, bend: 1 }, armB: { ik: add(hand, [-6, 0]), bend: 1 },
    legF: { ik: [618, FLOOR - 10], bend: -1 }, legB: { ik: [604, FLOOR - 10], bend: -1 }, armSign: -1 };
}
function posePushup(u, knees = false) { // u: 0 up .. 1 down
  const phi = deg(lerp(knees ? 38 : 27, knees ? 18 : 14, u));
  const d = [Math.cos(phi), -Math.sin(phi)];
  let P, legF, legB;
  if (knees) {
    const K = [440, FLOOR - 12];
    P = add(K, d, LEN.th);
    const A = add(K, dir(deg(218)), LEN.sh);
    legF = { pts: [K, A] }; legB = { pts: [add(K, [-6, 0]), add(A, [-6, 0])] };
  } else {
    const A = [330, FLOOR - 10];
    P = add(A, d, LEN.th + LEN.sh);
    const K = lerpP(A, P, LEN.sh / (LEN.th + LEN.sh));
    legF = { pts: [K, A] }; legB = { pts: [add(K, [-6, 0]), add(A, [-6, 0])] };
  }
  const hand = [knees ? 618 : 600, FLOOR - 10];
  return { pelvis: P, torsoA: ang(d), neckA: deg(12), armF: { ik: hand, bend: 1 }, armB: { ik: add(hand, [-8, 0]), bend: 1 },
    legF, legB, armSign: -1, footUp: knees ? 'up' : null };
}
function poseStand(x = 640, extra = {}) {
  const P = [x, FLOOR - LEN.th - LEN.sh - 6];
  return Object.assign({ pelvis: P, torsoA: deg(-90), armF: { a1: deg(96), a2: deg(-14) }, armB: { a1: deg(84), a2: deg(-10) },
    legF: { ik: [x + 8, FLOOR - 8], bend: -1 }, legB: { ik: [x - 10, FLOOR - 8], bend: -1 }, armSign: -1 }, extra);
}
function poseOverhead(u, x = 640) { // u: 0 extended .. 1 bent
  return poseStand(x, {
    armF: { a1: deg(-96), a2: deg(lerp(-6, -140, u)) },
    armB: { a1: deg(-100), a2: deg(lerp(-6, -140, u)) },
    neckA: deg(-6),
  });
}
function poseFlex(x = 640) {
  return poseStand(x, { armF: { a1: deg(-8), a2: deg(-112) }, armB: { a1: deg(110), a2: deg(-30) } });
}
function poseWave(x, t) {
  return poseStand(x, { armF: { a1: deg(-55), a2: deg(-35 + Math.sin(t * 10) * 20) } });
}

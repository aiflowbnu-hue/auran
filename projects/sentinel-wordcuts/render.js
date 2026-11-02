// Edit a short from edit.json: image cuts on the voiceover words with
// zoom-punch, push-in (Ken Burns), bounce-in for text frames, screen shake, SFX and ducked music.
//   node render.js              -> build/sentinel_wordcuts.mp4
//   node render.js --stills 5.2,15.9   -> build/stills/*.png
const { chromium } = require('playwright');
const { spawn, execFileSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const HERE = __dirname, BUILD = path.join(HERE, 'build');
const E = JSON.parse(fs.readFileSync(path.join(HERE, 'edit.json'), 'utf8'));
const [W, H] = E.size, FPS = E.fps;
const voDur = Number(execFileSync('ffprobe', ['-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', path.join(HERE, E.voiceover)]));
const TOTAL = voDur + E.tail;
const args = process.argv.slice(2);
const opt = k => { const i = args.indexOf(k); return i >= 0 ? args[i + 1] : null; };

const PAGE_JS = `
const E = ${JSON.stringify(E)}, W = ${W}, H = ${H}, TOTAL = ${TOTAL};
const IMG = {};
window.ready = Promise.all(E.cuts.map(c => new Promise((res, rej) => {
  const im = new Image(); im.onload = res; im.onerror = () => rej(new Error(c.img)); im.src = 'frames/' + c.img; IMG[c.img] = im;
})));
const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
const easeOut = x => 1 - Math.pow(1 - clamp(x), 3);
// a "group" is a cut plus the following pop-in cuts that only add detail: the push-in continues across them
const groupStart = [];
E.cuts.forEach((c, i) => { groupStart[i] = (i > 0 && c.fx.includes('pop')) ? groupStart[i - 1] : c.start; });
window.renderFrame = t => {
  const ctx = document.getElementById('c').getContext('2d');
  let i = 0; for (let k = 0; k < E.cuts.length; k++) if (t >= E.cuts[k].start) i = k;
  const c = E.cuts[i], u = t - c.start, fx = c.fx, im = IMG[c.img];
  let z = 1, dx = 0, dy = 0;
  if (fx.includes('kb') || fx.includes('pop')) z *= 1 + Math.min(0.04, 0.012 * (t - groupStart[i]));
  if (fx.includes('punch')) z *= 1 + 0.07 * (1 - easeOut(u / 0.28));
  if (fx.includes('pop')) z *= 1 + 0.045 * Math.exp(-u * 9) * Math.cos(u * 26);
  if (fx.includes('shake') && u < 0.45) { const a = 16 * (1 - u / 0.45); dx = Math.sin(u * 95) * a; dy = Math.cos(u * 77) * a * 0.7; }
  const c0 = Math.max(W / im.width, H / im.height), cover = c0 * z;
  const Y0 = H * 0.18, yBase = H / 2 - im.height * c0 / 2;  // zoom about a point near the top so titles stay in frame
  ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.fillStyle = '#000000'; ctx.fillRect(0, 0, W, H);
  ctx.imageSmoothingQuality = 'high';
  ctx.drawImage(im, W / 2 - im.width * cover / 2 + dx, Y0 + (yBase - Y0) * z + dy, im.width * cover, im.height * cover);
  const fade = clamp((t - (TOTAL - 0.5)) / 0.5);
  if (fade > 0) { ctx.fillStyle = 'rgba(0,0,0,' + fade + ')'; ctx.fillRect(0, 0, W, H); }
};`;

async function page() {
  const browser = await chromium.launch();
  const pg = await browser.newPage({ viewport: { width: W, height: H } });
  pg.on('pageerror', e => { console.error('PAGE ERROR', e.message); process.exit(1); });
  const html = `<!doctype html><html><head><meta charset="utf-8"></head><body style="margin:0">
    <canvas id="c" width="${W}" height="${H}"></canvas><script>${PAGE_JS}</script></body></html>`;
  await pg.route('http://edit.local/**', route => {
    const u = new URL(route.request().url());
    if (u.pathname === '/index.html') return route.fulfill({ contentType: 'text/html; charset=utf-8', body: html });
    const f = path.join(HERE, 'assets', decodeURIComponent(u.pathname));
    if (f.startsWith(path.join(HERE, 'assets')) && fs.existsSync(f)) return route.fulfill({ path: f });
    return route.fulfill({ status: 404, body: '' });
  });
  await pg.goto('http://edit.local/index.html');
  await pg.evaluate(() => window.ready);
  return { browser, pg };
}

function mixAudio(out) {
  const ins = [], fl = [], fx = [];
  const add = f => { ins.push('-i', f); return ins.length / 2 - 1; };
  const vo = add(path.join(HERE, E.voiceover));
  const mu = add(path.join(HERE, E.music));
  E.cuts.forEach(c => (c.sfx || []).forEach(([name, off, vol]) => {
    const i = add(path.join(HERE, '..', '..', 'assets', 'sfx', `${name}.mp3`));
    fl.push(`[${i}:a]aresample=44100,aformat=channel_layouts=stereo,volume=${vol * 0.6},adelay=${Math.round((c.start + off) * 1000)}:all=1[s${i}]`);
    fx.push(`[s${i}]`);
  }));
  fl.push(`[${vo}:a]aresample=44100,aformat=channel_layouts=stereo,apad,atrim=0:${TOTAL},asplit=2[vo][key]`);
  fl.push(`[${mu}:a]aresample=44100,aformat=channel_layouts=stereo,atrim=0:${TOTAL},volume=${E.music_volume},afade=t=in:d=0.4,afade=t=out:st=${TOTAL - 1}:d=1[mraw]`);
  fl.push(`[mraw][key]sidechaincompress=threshold=0.03:ratio=5:attack=20:release=300[music]`);
  if (fx.length) {
    fl.push(`${fx.join('')}amix=inputs=${fx.length}:normalize=0[fx]`);
    fl.push(`[vo][music][fx]amix=inputs=3:normalize=0,atrim=0:${TOTAL},loudnorm=I=-14:TP=-1.5:LRA=11[out]`);
  } else {
    fl.push(`[vo][music]amix=inputs=2:normalize=0,atrim=0:${TOTAL},loudnorm=I=-14:TP=-1.5:LRA=11[out]`);
  }
  execFileSync('ffmpeg', ['-y', '-v', 'error', ...ins, '-filter_complex', fl.join(';'), '-map', '[out]', '-c:a', 'aac', '-b:a', '192k', out]);
}

(async () => {
  fs.mkdirSync(BUILD, { recursive: true });
  const { browser, pg } = await page();
  if (opt('--stills')) {
    fs.mkdirSync(path.join(BUILD, 'stills'), { recursive: true });
    for (const t of opt('--stills').split(',').map(Number)) {
      await pg.evaluate(t => window.renderFrame(t), t);
      await pg.locator('#c').screenshot({ path: path.join(BUILD, 'stills', `t${t.toFixed(2).padStart(6, '0')}.png`) });
    }
    return browser.close();
  }
  const silent = path.join(BUILD, 'video_silent.mp4');
  const ff = spawn('ffmpeg', ['-y', '-v', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-',
    '-c:v', 'libx264', '-preset', 'medium', '-crf', '17', '-pix_fmt', 'yuv420p', silent], { stdio: ['pipe', 'inherit', 'inherit'] });
  const n = Math.round(TOTAL * FPS);
  for (let i = 0; i < n; i++) {
    const b64 = await pg.evaluate(t => { window.renderFrame(t); return document.getElementById('c').toDataURL('image/jpeg', 0.94).slice(23); }, i / FPS);
    if (!ff.stdin.write(Buffer.from(b64, 'base64'))) await new Promise(r => ff.stdin.once('drain', r));
  }
  ff.stdin.end(); await new Promise(r => ff.on('close', r));
  await browser.close();
  const audio = path.join(BUILD, 'audio.m4a');
  mixAudio(audio);
  const out = path.join(BUILD, 'sentinel_wordcuts.mp4');
  execFileSync('ffmpeg', ['-y', '-v', 'error', '-i', silent, '-i', audio, '-c:v', 'copy', '-c:a', 'copy', '-shortest', out]);
  console.log('wrote', out, TOTAL.toFixed(2) + 's');
})();

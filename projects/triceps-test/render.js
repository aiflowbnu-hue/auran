// Render the animation to MP4 and mix the audio.
//   node render.js                 full render -> build/triceps_test.mp4
//   node render.js --stills 3,20   PNG stills at given seconds -> build/stills/
//   node render.js --from 19 --to 40   render only a time range (preview, no audio)
const { chromium } = require('playwright');
const { spawn, execFileSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const HERE = __dirname;
const BUILD = path.join(HERE, 'build');
const FPS = 30;
const SCENES_FILE = 'scenes_v2.js';
const args = process.argv.slice(2);
const opt = k => { const i = args.indexOf(k); return i >= 0 ? args[i + 1] : null; };
const timeline = JSON.parse(fs.readFileSync(path.join(BUILD, 'timeline.json'), 'utf8'));

async function page() {
  const browser = await chromium.launch();
  const pg = await browser.newPage({ viewport: { width: 1280, height: 720 } });
  pg.on('pageerror', e => { console.error('PAGE ERROR', e.message); process.exit(1); });
  const js = f => fs.readFileSync(path.join(HERE, 'anim', f), 'utf8');
  const sprites = JSON.parse(fs.readFileSync(path.join(BUILD, 'sprites', 'manifest.json'), 'utf8'));
  const html = `<!doctype html><html><head><meta charset="utf-8"></head><body style="margin:0"><canvas id="c" width="1280" height="720"></canvas>
    <script>window.TIMELINE=${JSON.stringify(timeline)};window.SPRITES=${JSON.stringify(sprites)};</script>
    <script>${js('rig.js')}</script><script>${js(SCENES_FILE)}</script></body></html>`;
  // serve page + sprites from one origin so the canvas is not tainted
  await pg.route('http://render.local/**', route => {
    const u = new URL(route.request().url());
    if (u.pathname === '/index.html') return route.fulfill({ contentType: 'text/html; charset=utf-8', body: html });
    const f = path.join(BUILD, decodeURIComponent(u.pathname));
    if (f.startsWith(BUILD) && fs.existsSync(f)) return route.fulfill({ path: f });
    return route.fulfill({ status: 404, body: '' });
  });
  await pg.goto('http://render.local/index.html');
  await pg.evaluate(async () => { await document.fonts.ready; if (window.ready) await window.ready; });
  return { browser, pg };
}

async function stills(times) {
  const { browser, pg } = await page();
  fs.mkdirSync(path.join(BUILD, 'stills'), { recursive: true });
  for (const t of times) {
    await pg.evaluate(t => window.renderFrame(t), t);
    await pg.locator('#c').screenshot({ path: path.join(BUILD, 'stills', `t${String(t).padStart(5, '0')}.png`) });
  }
  await browser.close();
}

async function video(from, to, out) {
  const { browser, pg } = await page();
  const ff = spawn('ffmpeg', ['-y', '-v', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-',
    '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', out], { stdio: ['pipe', 'inherit', 'inherit'] });
  const n = Math.round((to - from) * FPS);
  for (let i = 0; i < n; i++) {
    const b64 = await pg.evaluate(t => { window.renderFrame(t); return document.getElementById('c').toDataURL('image/jpeg', 0.93).slice(23); }, from + i / FPS);
    if (!ff.stdin.write(Buffer.from(b64, 'base64'))) await new Promise(r => ff.stdin.once('drain', r));
    if (i % 300 === 0) console.log(`frame ${i}/${n}`);
  }
  ff.stdin.end();
  await new Promise(r => ff.on('close', r));
  const cues = await pg.evaluate(() => window.CUES);
  await browser.close();
  return cues;
}

function mixAudio(cues, out) {
  const inputs = [], filters = [], vo = [], sfx = [];
  const T = timeline.total;
  const addIn = f => { inputs.push('-i', f); return inputs.length / 2 - 1; };
  timeline.scenes.forEach(s => {
    const i = addIn(path.join(HERE, s.file));
    filters.push(`[${i}:a]aresample=44100,aformat=channel_layouts=stereo,adelay=${Math.round(s.start * 1000)}:all=1[v${i}]`);
    vo.push(`[v${i}]`);
  });
  cues.forEach(c => {
    const i = addIn(path.join(HERE, '..', '..', 'assets', 'sfx', `${c.name}.mp3`));
    filters.push(`[${i}:a]aresample=44100,aformat=channel_layouts=stereo,volume=${c.vol * 0.55},adelay=${Math.round(c.t * 1000)}:all=1[s${i}]`);
    sfx.push(`[s${i}]`);
  });
  const mi = addIn(path.join(HERE, '..', '..', 'assets', 'music', 'bouncy_rep_timer.mp3'));
  filters.push(`${vo.join('')}amix=inputs=${vo.length}:normalize=0,apad,atrim=0:${T},asplit=2[vo][vokey]`);
  filters.push(`[${mi}:a]aresample=44100,aformat=channel_layouts=stereo,atrim=0:${T},volume=0.22,afade=t=in:d=0.5,afade=t=out:st=${T - 1.5}:d=1.5[mraw]`);
  filters.push(`[mraw][vokey]sidechaincompress=threshold=0.03:ratio=6:attack=20:release=350[music]`);
  filters.push(`${sfx.join('')}amix=inputs=${sfx.length}:normalize=0[fx]`);
  filters.push(`[vo][music][fx]amix=inputs=3:normalize=0,atrim=0:${T},loudnorm=I=-14:TP=-1.5:LRA=11[out]`);
  execFileSync('ffmpeg', ['-y', '-v', 'error', ...inputs, '-filter_complex', filters.join(';'), '-map', '[out]', '-ar', '44100', '-c:a', 'aac', '-b:a', '192k', out]);
}

(async () => {
  fs.mkdirSync(BUILD, { recursive: true });
  if (opt('--stills')) return stills(opt('--stills').split(',').map(Number));
  const from = Number(opt('--from') || 0), to = Number(opt('--to') || timeline.total);
  const silent = path.join(BUILD, from || opt('--to') ? 'preview.mp4' : 'video_silent.mp4');
  const t0 = Date.now();
  const cues = await video(from, to, silent);
  console.log(`video done in ${((Date.now() - t0) / 1000).toFixed(0)}s`);
  if (from || opt('--to')) return;
  const audio = path.join(BUILD, 'audio.m4a');
  mixAudio(cues, audio);
  const final = path.join(BUILD, 'triceps_test_v2.mp4');
  execFileSync('ffmpeg', ['-y', '-v', 'error', '-i', silent, '-i', audio, '-c:v', 'copy', '-c:a', 'copy', '-shortest', final]);
  console.log('wrote', final);
})();

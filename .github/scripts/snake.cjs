// Buat ular kontribusi (terang & gelap) memakai Platane/snk v3.5.0 svg-only, diunduh dari rilis resminya ke folder sementara.
// Untuk dijalankan dari komputer sendiri saat GitHub Actions tidak bisa dipakai. Butuh env GITHUB_TOKEN.
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { execFileSync } = require('node:child_process');

const TAG = 'v3.5.0';
const FILES = ['index.js', '578.index.js', '642.index.js', '680.index.js'];
const USER = process.env.PROFILE_USER || 'zoembut';
const repoRoot = path.resolve(__dirname, '..', '..');
const OUTPUTS = [
  `${repoRoot}/assets/snake-light.svg?palette=github-light&color_snake=#FF2E88&color_dots=#EFEAF5,#FFF3A3,#FFE500,#FF8AC2,#FF2E88`,
  `${repoRoot}/assets/snake-dark.svg?palette=github-dark&color_snake=#FFE500&color_dots=#1F1B2E,#3C2A55,#8B5CF6,#FF2E88,#FFE500`,
];

(async () => {
  if (!process.env.GITHUB_TOKEN) {
    const out = execFileSync('git', ['credential', 'fill'], { input: 'protocol=https\nhost=github.com\n\n' }).toString();
    const m = out.match(/^password=(.*)$/m);
    if (!m) throw new Error('Token GitHub tidak ditemukan. Login GitHub dulu di komputer ini.');
    process.env.GITHUB_TOKEN = m[1].trim();
  }
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'snk-'));
  fs.writeFileSync(path.join(dir, 'package.json'), '{"type":"commonjs"}');
  for (const f of FILES) {
    const res = await fetch(`https://raw.githubusercontent.com/Platane/snk/${TAG}/svg-only/dist/${f}`);
    if (!res.ok) throw new Error(`Gagal mengunduh ${f}: ${res.status}`);
    fs.writeFileSync(path.join(dir, f.replace(/\.js$/, '.cjs')), (await res.text()).replace(/\.index\.js/g, '.index.cjs'));
  }
  execFileSync(process.execPath, [path.join(dir, 'index.cjs')], {
    stdio: 'inherit',
    env: { ...process.env, INPUT_GITHUB_USER_NAME: USER, INPUT_GITHUB_TOKEN: process.env.GITHUB_TOKEN, INPUT_OUTPUTS: OUTPUTS.join('\n') },
  });
  fs.rmSync(dir, { recursive: true, force: true });
})().catch((e) => { console.error(e.message); process.exit(1); });

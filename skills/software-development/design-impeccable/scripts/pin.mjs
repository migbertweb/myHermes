import { execSync } from 'child_process';
import fs from 'fs';
import path from 'path';

const skillDir = path.resolve(new URL('.', import.meta.url).href, '..');

function usage() {
  console.log('Usage: pin.mjs <pin|unpin> <command>');
  process.exit(1);
}

const [,, action, command] = process.argv;
if (!action || !command) usage();

if (!['pin','unpin'].includes(action)) usage;

const harnessDirs = [
  path.join(process.env.HOME, '.claude'),
  path.join(process.env.HOME, '.codex'),
  path.join(process.env.HOME, '.opencode'),
  path.join(process.env.HOME, '.gemini'),
  path.join(process.env.HOME, '.cursor'),
  path.join(process.env.HOME, '.pi'),
];

for (const dir of harnessDirs) {
  const link = path.join(dir, command);
  if (!fs.existsSync(dir)) continue;
  if (action === 'pin') {
    fs.symlinkSync(skillDir, link);
  } else {
    try { fs.unlinkSync(link); } catch {}
  }
}
console.log(`${action === 'pin' ? 'Pinned' : 'Unpinned'}: /${command}`);

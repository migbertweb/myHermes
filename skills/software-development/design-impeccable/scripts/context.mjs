import fs from 'fs';
import path from 'path';

function findRoot() {
  let dir = process.cwd();
  while (dir !== path.dirname(dir)) {
    if (fs.existsSync(path.join(dir, 'PRODUCT.md'))) return dir;
    dir = path.dirname(dir);
  }
  return null;
}

const root = findRoot();
if (!root) {
  console.log('NO_PRODUCT_MD');
  process.exit(0);
}

const product = fs.readFileSync(path.join(root, 'PRODUCT.md'), 'utf8');
const designPath = path.join(root, 'DESIGN.md');
const design = fs.existsSync(designPath) ? fs.readFileSync(designPath, 'utf8') : null;

console.log('```md');
console.log(product.trim());
if (design) {
  console.log('\n---\n');
  console.log(design.trim());
}
console.log('```');
